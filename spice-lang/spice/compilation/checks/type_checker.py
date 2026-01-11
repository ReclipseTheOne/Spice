from __future__ import annotations

from typing import List, Optional, Tuple, Union

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.checks.interface_checker import CheckError
from spice.compilation.spicefile import SpiceFile
from spice.compilation.symbol_table import (
    SymbolTable,
    VariableSymbol,
    FunctionSymbol,
    ClassSymbol,
)
from spice.parser.ast_nodes import (
    AssignmentExpression,
    AttributeExpression,
    CallExpression,
    ClassDeclaration,
    Expression,
    ExpressionStatement,
    FinalDeclaration,
    FunctionDeclaration,
    IdentifierExpression,
    LiteralExpression,
    Module,
)


class TypeChecker(CompileTimeCheck):
    """Symbol Table parser for illegal type calls"""

    def __init__(self) -> None:
        self.errors: List[Union[str, CheckError]] = []
        self.table: Optional[SymbolTable] = None
        self.scope_stack: List[str] = []
        self._current_node = None  # Track current node for line/column info
        # {var_name: {type_param: concrete_type}}
        self._generic_bindings: dict[str, dict[str, str]] = {}

    def check(self, file: SpiceFile) -> bool:
        if not getattr(file, "symbol_table", None):
            return True

        self.table = file.symbol_table
        self.errors = []
        self.scope_stack = ["global"]
        self._visit_module(file.ast)
        return not self.errors

    def _current_scope(self) -> str:
        return self.scope_stack[-1]

    def _push_scope(self, name: str):
        self.scope_stack.append(name)

    def _pop_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def _visit_module(self, node: Module):
        for stmt in node.body:
            self._visit_node(stmt)

    def _visit_node(self, node):
        if isinstance(node, ClassDeclaration):
            self._visit_class(node)
        elif isinstance(node, FunctionDeclaration):
            self._visit_function(node)
        elif isinstance(node, ExpressionStatement):
            self._visit_expression_statement(node)
        elif isinstance(node, FinalDeclaration):
            pass
        elif hasattr(node, "body") and isinstance(node.body, list):
            for child in node.body:
                self._visit_node(child)

    def _visit_class(self, node: ClassDeclaration):
        self._push_scope(node.name)
        for member in node.body:
            self._visit_node(member)
        self._pop_scope()

    def _visit_function(self, node: FunctionDeclaration):
        scope_name = node.name if self._current_scope() == "global" else f"{self._current_scope()}.{node.name}"
        self._push_scope(scope_name)
        if node.body:
            for stmt in node.body:
                self._visit_node(stmt)
        self._pop_scope()

    def _visit_expression_statement(self, node: ExpressionStatement):
        self._current_node = node
        expr = node.expression
        if isinstance(expr, CallExpression):
            self._check_call_expression(expr)
        elif isinstance(expr, AssignmentExpression):
            if expr.type_annotation is None:
                self._visit_assignment(expr)
        self._current_node = None

    def _visit_assignment(self, node: AssignmentExpression):
        if isinstance(node.value, CallExpression):
            self._check_call_expression(node.value)
        self._enforce_assignment_annotation(node)

    def _check_call_expression(self, node: CallExpression):
        callee_info = self._resolve_callee(node)
        if not callee_info:
            return

        functions, owner, var_name = callee_info
        arg_types = [self._infer_expression_type(arg) for arg in node.arguments]

        if not functions:
            return

        # Get type parameters and existing bindings for generic classes
        type_params = []
        existing_bindings = {}
        if owner and owner in self.table.classes:
            class_symbol = self.table.classes[owner]
            type_params = class_symbol.type_parameters
            if var_name and var_name in self._generic_bindings:
                existing_bindings = self._generic_bindings[var_name]

        for func in functions:
            match_result = self._arguments_match_generic(
                arg_types, func.params, type_params, existing_bindings
            )
            if match_result is not None:
                # Update bindings if we inferred new types
                if var_name and match_result:
                    if var_name not in self._generic_bindings:
                        self._generic_bindings[var_name] = {}
                    self._generic_bindings[var_name].update(match_result)
                return

        arg_desc = ", ".join(str(t) for t in arg_types) if arg_types else ""
        owner_desc = f"{owner}." if owner else ""
        line = getattr(self._current_node, "line", 0) if self._current_node else 0
        column = getattr(self._current_node, "column", 0) if self._current_node else 0
        self.errors.append(CheckError(
            message=f"No overload of {owner_desc}{functions[0].name} matches argument types ({arg_desc})",
            line=line,
            column=column
        ))

    def _arguments_match(self, arg_types: List[Optional[str]], params) -> bool:
        if len(arg_types) != len(params):
            return False

        for arg_type, param in zip(arg_types, params):
            if param.type_annotation is None or arg_type is None:
                return False
            if arg_type != param.type_annotation:
                return False

        return True

    def _resolve_callee(self, node: CallExpression) -> Optional[Tuple[List[FunctionSymbol], Optional[str], Optional[str]]]:
        """Resolve callee to (functions, owner_type, variable_name)."""
        callee = node.callee
        if isinstance(callee, IdentifierExpression):
            scope = self.table.scopes.get("global")
            if scope:
                funcs = scope.functions.get(callee.name, [])
                return funcs, None, None
        elif isinstance(callee, AttributeExpression):
            obj_type = self._infer_expression_type(callee.object)
            var_name = None
            if isinstance(callee.object, IdentifierExpression):
                var_name = callee.object.name
            if obj_type and obj_type in self.table.classes:
                class_symbol = self.table.classes[obj_type]
                funcs = class_symbol.methods.get(callee.attribute, [])
                return funcs, obj_type, var_name
        return None

    def _arguments_match_generic(
        self,
        arg_types: List[Optional[str]],
        params,
        type_params: List[str],
        existing_bindings: dict[str, str]
    ) -> Optional[dict[str, str]]:
        """
        Match arguments to parameters with generic type inference.
        Returns None if no match, or a dict of inferred bindings if match succeeds.
        """
        if len(arg_types) != len(params):
            return None

        # Start with existing bindings
        inferred = dict(existing_bindings)

        for arg_type, param in zip(arg_types, params):
            param_type = param.type_annotation
            if param_type is None or arg_type is None:
                return None

            if param_type in type_params:
                # It's a generic type parameter
                if param_type in inferred:
                    # Already have a binding - check it matches
                    if inferred[param_type] != arg_type:
                        return None
                else:
                    # Infer the type from the argument
                    inferred[param_type] = arg_type
            else:
                # Regular type - must match exactly
                if arg_type != param_type:
                    return None

        # Return only the newly inferred bindings (not existing ones)
        new_bindings = {k: v for k, v in inferred.items() if k not in existing_bindings}
        return new_bindings if new_bindings else {}

    def _enforce_assignment_annotation(self, node: AssignmentExpression):
        if not isinstance(node.target, IdentifierExpression):
            return

        symbol = self._lookup_variable(node.target.name)
        if symbol and symbol.type_annotation:
            return

        if isinstance(node.value, LiteralExpression):
            return

        if isinstance(node.value, CallExpression) and self._is_constructor_call(node.value):
            return

        line = getattr(self._current_node, "line", 0) if self._current_node else 0
        column = getattr(self._current_node, "column", 0) if self._current_node else 0
        self.errors.append(CheckError(
            message=f"Variable '{node.target.name}' must declare a type annotation when assigned from non-literal expression",
            line=line,
            column=column
        ))

    def _is_constructor_call(self, call: CallExpression) -> bool:
        callee = call.callee
        if isinstance(callee, IdentifierExpression):
            return callee.name in self.table.classes
        return False

    def _infer_expression_type(self, expr: Expression) -> Optional[str]:
        if isinstance(expr, IdentifierExpression):
            symbol = self._lookup_variable(expr.name)
            if symbol:
                return symbol.type_annotation
        elif isinstance(expr, LiteralExpression):
            return self._literal_to_type(expr)
        elif isinstance(expr, CallExpression):
            return self._infer_call_return(expr)
        elif isinstance(expr, AttributeExpression):
            return self._infer_attribute_type(expr)
        return None

    def _lookup_variable(self, name: str) -> Optional[VariableSymbol]:
        scope_name = self._current_scope()
        while scope_name:
            scope = self.table.scopes.get(scope_name)
            if scope and name in scope.variables:
                return scope.variables[name]
            scope_name = scope.parent if scope else None
        return None

    def _infer_call_return(self, call: CallExpression) -> Optional[str]:
        callee = call.callee
        if isinstance(callee, IdentifierExpression):
            if callee.name in self.table.classes:
                return callee.name
            scope = self.table.scopes.get("global")
            if scope:
                for func in scope.functions.get(callee.name, []):
                    if func.return_type:
                        return func.return_type
        elif isinstance(callee, AttributeExpression):
            obj_type = self._infer_expression_type(callee.object)
            if obj_type and obj_type in self.table.classes:
                class_symbol = self.table.classes[obj_type]
                methods = class_symbol.methods.get(callee.attribute, [])
                for method in methods:
                    if method.return_type:
                        return method.return_type
        return None

    def _infer_attribute_type(self, attr: AttributeExpression) -> Optional[str]:
        obj_type = self._infer_expression_type(attr.object)
        if not obj_type:
            return None
        if obj_type in self.table.classes:
            class_symbol = self.table.classes[obj_type]
            vars_scope = self.table.scopes.get(class_symbol.name)
            if vars_scope and attr.attribute in vars_scope.variables:
                return vars_scope.variables[attr.attribute].type_annotation
        return None

    def _literal_to_type(self, literal: LiteralExpression) -> Optional[str]:
        mapping = {
            "string": "str",
            "number": "int",
            "boolean": "bool",
        }
        return mapping.get(literal.literal_type)
