from __future__ import annotations

from typing import List, Optional

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.spicefile import SpiceFile
from spice.compilation.symbol_table import SymbolTable, VariableSymbol, FunctionSymbol, ClassSymbol, InterfaceSymbol
from spice.parser.ast_nodes import (
    AssignmentExpression,
    ClassDeclaration,
    DataClassDeclaration,
    EnumDeclaration,
    ExpressionStatement,
    FinalDeclaration,
    FunctionDeclaration,
    IdentifierExpression,
    InterfaceDeclaration,
    LiteralExpression,
    Module,
    CallExpression,
)


class SymbolTableBuilder(CompileTimeCheck):
    """Collect declarations and store them on the SpiceFile for later checks"""

    def __init__(self) -> None:
        self.symbol_table: Optional[SymbolTable] = None
        self.scope_stack: List[str] = []

    def check(self, file: SpiceFile) -> bool:
        self.symbol_table = SymbolTable()
        self.scope_stack = ["global"]
        self._visit_module(file.ast)
        file.symbol_table = self.symbol_table
        return True

    def _current_scope(self) -> str:
        return self.scope_stack[-1]

    def _push_scope(self, scope_name: str):
        parent = self._current_scope()
        self.symbol_table.ensure_scope(scope_name, parent)
        self.scope_stack.append(scope_name)

    def _pop_scope(self):
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()

    def _add_variable(self, name: str, type_annotation: Optional[str], node):
        scope = self.symbol_table.scopes[self._current_scope()]
        scope.variables[name] = VariableSymbol(
            name=name,
            type_annotation=type_annotation,
            node=node,
        )

    def _add_function(self, func: FunctionDeclaration, owner_scope: Optional[str] = None):
        scope_name = owner_scope or self._current_scope()
        scope = self.symbol_table.scopes.get(scope_name)
        if scope is None:
            parent = self._current_scope() if owner_scope is None else owner_scope
            scope = self.symbol_table.ensure_scope(scope_name, parent)
        func_symbol = FunctionSymbol(
            name=func.name,
            params=func.params,
            return_type=func.return_type,
            node=func,
            scope=scope_name,
        )
        scope.functions.setdefault(func.name, []).append(func_symbol)
        return func_symbol

    def _visit_module(self, node: Module):
        for stmt in node.body:
            self._visit_node(stmt)

    def _visit_node(self, node):
        if isinstance(node, ClassDeclaration):
            self._visit_class(node)
        elif isinstance(node, DataClassDeclaration):
            self._visit_data_class(node)
        elif isinstance(node, EnumDeclaration):
            self._visit_enum(node)
        elif isinstance(node, InterfaceDeclaration):
            self._visit_interface(node)
        elif isinstance(node, FunctionDeclaration):
            self._visit_function(node)
        elif isinstance(node, ExpressionStatement):
            self._visit_expression_statement(node)
        elif isinstance(node, FinalDeclaration):
            self._register_final_declaration(node)
        elif hasattr(node, "body") and isinstance(node.body, list):
            for child in node.body:
                self._visit_node(child)

    def _visit_interface(self, node: InterfaceDeclaration):
        interface_symbol = InterfaceSymbol(name=node.name, node=node, scope=self._current_scope())
        self.symbol_table.interfaces[node.name] = interface_symbol

    def _visit_data_class(self, node: DataClassDeclaration):
        """Visit data class declaration - treat like a regular class."""
        class_symbol = ClassSymbol(name=node.name, node=node, scope=self._current_scope())
        self.symbol_table.classes[node.name] = class_symbol
        class_scope = node.name
        self._push_scope(class_scope)

        # Register fields as variables in the class scope
        for field in node.fields:
            self._add_variable(field.name, field.type_annotation, field)

        for member in node.body:
            if isinstance(member, FunctionDeclaration):
                method_symbol = self._add_function(member, owner_scope=class_scope)
                class_symbol.methods.setdefault(member.name, []).append(method_symbol)
                self._visit_function(member, owner_scope=class_scope)
            else:
                self._visit_node(member)
        self._pop_scope()

    def _visit_enum(self, node: EnumDeclaration):
        """Visit enum declaration - treat like a class."""
        class_symbol = ClassSymbol(name=node.name, node=node, scope=self._current_scope())
        self.symbol_table.classes[node.name] = class_symbol
        class_scope = node.name
        self._push_scope(class_scope)

        # Visit methods if any
        for member in node.body:
            if isinstance(member, FunctionDeclaration):
                method_symbol = self._add_function(member, owner_scope=class_scope)
                class_symbol.methods.setdefault(member.name, []).append(method_symbol)
                self._visit_function(member, owner_scope=class_scope)
            else:
                self._visit_node(member)

        self._pop_scope()

    def _visit_class(self, node: ClassDeclaration):
        type_param_names = [tp.name for tp in node.type_parameters]
        class_symbol = ClassSymbol(
            name=node.name,
            node=node,
            scope=self._current_scope(),
            type_parameters=type_param_names
        )
        self.symbol_table.classes[node.name] = class_symbol
        class_scope = node.name
        self._push_scope(class_scope)
        for member in node.body:
            if isinstance(member, FunctionDeclaration):
                method_symbol = self._add_function(member, owner_scope=class_scope)
                class_symbol.methods.setdefault(member.name, []).append(method_symbol)
                self._visit_function(member, owner_scope=class_scope)
            else:
                self._visit_node(member)
        self._pop_scope()

    def _function_scope_name(self, node: FunctionDeclaration, owner_scope: Optional[str]) -> str:
        if owner_scope:
            return f"{owner_scope}.{node.name}"
        return node.name

    def _visit_function(self, node: FunctionDeclaration, owner_scope: Optional[str] = None):
        if owner_scope is None:
            self._add_function(node, owner_scope)

        scope_name = self._function_scope_name(node, owner_scope)
        self._push_scope(scope_name)

        for param in node.params:
            self._add_variable(param.name, param.type_annotation, param)

        if node.body:
            for stmt in node.body:
                self._visit_node(stmt)

        self._pop_scope()

    def _visit_expression_statement(self, node: ExpressionStatement):
        expr = node.expression
        if isinstance(expr, AssignmentExpression):
            if expr.type_annotation is not None:
                if isinstance(expr.target, IdentifierExpression):
                    self._add_variable(expr.target.name, expr.type_annotation, expr)
            else:
                self._maybe_infer_assignment(expr)

    def _register_final_declaration(self, node: FinalDeclaration):
        target = node.target
        if isinstance(target, IdentifierExpression):
            self._add_variable(target.name, node.type_annotation, node)

    def _maybe_infer_assignment(self, node: AssignmentExpression):
        if not isinstance(node.target, IdentifierExpression):
            return

        inferred_type = None
        if isinstance(node.value, CallExpression):
            inferred_type = self._infer_call_type(node.value)
        elif isinstance(node.value, LiteralExpression):
            inferred_type = self._literal_to_type(node.value)

        if inferred_type:
            self._add_variable(node.target.name, inferred_type, node)

    def _infer_call_type(self, call: CallExpression) -> Optional[str]:
        callee = call.callee
        if isinstance(callee, IdentifierExpression):
            if callee.name in self.symbol_table.classes:
                return callee.name
        return None

    def _literal_to_type(self, literal: LiteralExpression) -> Optional[str]:
        mapping = {
            "string": "str",
            "number": "int",
            "boolean": "bool",
        }
        return mapping.get(literal.literal_type)
