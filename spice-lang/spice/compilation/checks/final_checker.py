from dataclasses import fields, is_dataclass
from typing import Dict, List, Optional, Set, TYPE_CHECKING, Union

from spice.parser.ast_nodes import (
    ASTNode,
    AssignmentExpression,
    ClassDeclaration,
    ExpressionStatement,
    FinalDeclaration,
    FunctionDeclaration,
    IdentifierExpression,
)
from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.checks.interface_checker import CheckError

if TYPE_CHECKING:
    from spice.compilation.spicefile import SpiceFile

class FinalChecker(CompileTimeCheck):
    """Compile-time checker for final variable reassignments."""

    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self.final_variables: Dict[str, Set[str]] = {'global': set()}
        self.current_scope = 'global'
        self.errors: List[Union[str, CheckError]] = []
        self.class_nodes: Dict[str, ClassDeclaration] = {}
        self.final_methods_by_class: Dict[str, Dict[str, FunctionDeclaration]] = {}

    def check(self, file: "SpiceFile") -> bool:
        self._reset_state()
        self._collect_class_metadata(file.ast.body)
        for node in file.ast.body:
            self._visit_node(node)
        return not self.errors


    def enter_scope(self, scope_name: str):
        """Enter a new scope (function/class)."""
        self.current_scope = scope_name
        if scope_name not in self.final_variables:
            self.final_variables[scope_name] = set()

    def exit_scope(self):
        """Exit current scope."""
        self.current_scope = 'global'

    def register_final(self, var_name: str):
        """Register a variable as final in current scope."""
        if self.current_scope not in self.final_variables:
            self.final_variables[self.current_scope] = set()
        self.final_variables[self.current_scope].add(var_name)

    def check_assignment(self, var_name: str, line: int = 0, column: int = 0):
        """Check if assignment to variable is allowed."""
        scope_vars = self.final_variables.get(self.current_scope, set())
        global_vars = self.final_variables.get('global', set())

        if var_name in scope_vars or var_name in global_vars:
            self.errors.append(CheckError(
                message=f"Cannot reassign final variable '{var_name}'",
                line=line,
                column=column
            ))
            return False
        return True

    def _visit_node(self, node):
        """Visit a node and check for violations."""
        if isinstance(node, FinalDeclaration):
            if isinstance(node.target, IdentifierExpression):
                self.register_final(node.target.name)

        elif isinstance(node, ExpressionStatement):
            self._visit_expression(node.expression)
        elif isinstance(node, AssignmentExpression):
            self._handle_assignment(node)
        elif isinstance(node, FunctionDeclaration):
            old_scope = self.current_scope
            self.enter_scope(node.name)
            for stmt in node.body:
                self._visit_node(stmt)
            self.current_scope = old_scope

        elif isinstance(node, ClassDeclaration):
            old_scope = self.current_scope
            self.enter_scope(node.name)
            self._check_final_method_overrides(node)
            for member in node.body:
                self._visit_node(member)
            self.current_scope = old_scope

        if hasattr(node, 'body') and isinstance(node.body, list):
            for child in node.body:
                self._visit_node(child)

    def _visit_expression(self, expr: Optional[ASTNode]):
        """Traverse expressions searching for assignments."""
        if expr is None:
            return

        if isinstance(expr, AssignmentExpression):
            self._handle_assignment(expr)

        if is_dataclass(expr):
            for field in fields(expr):
                value = getattr(expr, field.name)
                self._visit_expression_field(value)

    def _visit_expression_field(self, value):
        if isinstance(value, list):
            for item in value:
                if isinstance(item, ASTNode):
                    self._visit_expression(item)
        elif isinstance(value, ASTNode):
            self._visit_expression(value)

    def _handle_assignment(self, node: AssignmentExpression):
        if isinstance(node.target, IdentifierExpression):
            self.check_assignment(node.target.name, node.line, node.column)
        self._visit_expression(node.value)

    def _collect_class_metadata(self, nodes: List[ASTNode]):
        """Collect class declarations and their final methods for later checks."""
        for node in nodes:
            if isinstance(node, ClassDeclaration):
                self.class_nodes[node.name] = node

                final_methods = {
                    member.name: member
                    for member in node.body
                    if isinstance(member, FunctionDeclaration) and member.is_final
                }
                if final_methods:
                    self.final_methods_by_class[node.name] = final_methods

                self._collect_class_metadata(node.body)
            elif hasattr(node, 'body') and isinstance(node.body, list):
                self._collect_class_metadata(node.body)

    def _check_final_method_overrides(self, class_node: ClassDeclaration):
        """Ensure subclasses do not override final methods declared in parents."""
        inherited_final_methods = self._collect_inherited_final_methods(class_node)
        if not inherited_final_methods:
            return

        for member in class_node.body:
            if isinstance(member, FunctionDeclaration) and member.name in inherited_final_methods:
                base_name = inherited_final_methods[member.name]
                self.errors.append(CheckError(
                    message=f"Class '{class_node.name}' cannot override final method '{member.name}' defined in '{base_name}'",
                    line=member.line,
                    column=member.column
                ))

    def _collect_inherited_final_methods(self, class_node: ClassDeclaration) -> Dict[str, str]:
        """Gather final methods from all parent classes."""
        inherited: Dict[str, str] = {}

        for base_name in class_node.bases:
            base_methods = self._collect_final_methods_from_base(base_name, set())
            for method_name, origin in base_methods.items():
                inherited.setdefault(method_name, origin)

        return inherited

    def _collect_final_methods_from_base(self, base_name: str, visited: Set[str]) -> Dict[str, str]:
        """Collect final methods from the given base class and its parents."""
        if base_name in visited:
            return {}

        visited.add(base_name)
        methods: Dict[str, str] = {
            method_name: base_name
            for method_name in self.final_methods_by_class.get(base_name, {})
        }

        base_node = self.class_nodes.get(base_name)
        if not base_node:
            return methods

        for ancestor in base_node.bases:
            ancestor_methods = self._collect_final_methods_from_base(ancestor, set(visited))
            for method_name, origin in ancestor_methods.items():
                methods.setdefault(method_name, origin)

        return methods
