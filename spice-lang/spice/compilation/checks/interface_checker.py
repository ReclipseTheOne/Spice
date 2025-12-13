"""Interface implementation checker for Spice language."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.spicefile import SpiceFile
from spice.parser.ast_nodes import (
    ClassDeclaration,
    FunctionDeclaration,
    InterfaceDeclaration,
    MethodSignature,
    Module,
    Parameter,
)


@dataclass
class CheckError:
    """Structured error with position info."""
    message: str
    line: int = 0
    column: int = 0

    def __str__(self) -> str:
        return f"{self.message} ({self.line}:{self.column})"


class InterfaceChecker(CompileTimeCheck):
    """Check that classes properly implement their declared interfaces."""

    def __init__(self) -> None:
        self.errors: List[CheckError] = []
        self.interfaces: Dict[str, InterfaceDeclaration] = {}
        self.classes: Dict[str, ClassDeclaration] = {}

    def check(self, file: SpiceFile) -> bool:
        self.errors = []
        self.interfaces = {}
        self.classes = {}

        # First pass: collect all interfaces and classes
        self._collect_declarations(file.ast)

        # Second pass: validate interface implementations
        for class_name, class_decl in self.classes.items():
            for interface_name in class_decl.interfaces:
                self._check_implementation(class_decl, interface_name)

        return len(self.errors) == 0

    def _collect_declarations(self, node: Module):
        """Collect all interface and class declarations."""
        for stmt in node.body:
            if isinstance(stmt, InterfaceDeclaration):
                self.interfaces[stmt.name] = stmt
            elif isinstance(stmt, ClassDeclaration):
                self.classes[stmt.name] = stmt

    def _get_param_signature(self, params: List[Parameter]) -> Tuple[str, ...]:
        """Get a tuple of parameter types for signature matching."""
        return tuple(p.type_annotation or "Any" for p in params)

    def _get_method_param_signature(self, method: FunctionDeclaration) -> Tuple[str, ...]:
        """Get parameter signature excluding 'self'."""
        params = [p for p in method.params if p.name != 'self']
        return self._get_param_signature(params)

    def _check_implementation(self, class_decl: ClassDeclaration, interface_name: str):
        """Check that a class properly implements an interface."""
        interface = self.interfaces.get(interface_name)
        if interface is None:
            self.errors.append(CheckError(
                message=f"Class '{class_decl.name}' implements unknown interface '{interface_name}'",
                line=class_decl.line,
                column=class_decl.column,
            ))
            return

        # Collect all methods from the class, grouped by name
        # Each name maps to a list of (param_signature, method) tuples
        class_methods: Dict[str, List[Tuple[Tuple[str, ...], FunctionDeclaration]]] = {}
        for member in class_decl.body:
            if isinstance(member, FunctionDeclaration):
                sig = self._get_method_param_signature(member)
                class_methods.setdefault(member.name, []).append((sig, member))

        # Check each interface method signature has a matching implementation
        for method_sig in interface.methods:
            self._check_method_implementation(
                class_decl, interface_name, method_sig, class_methods
            )

    def _check_method_implementation(
        self,
        class_decl: ClassDeclaration,
        interface_name: str,
        method_sig: MethodSignature,
        class_methods: Dict[str, List[Tuple[Tuple[str, ...], FunctionDeclaration]]],
    ):
        """Check that a specific interface method signature is implemented correctly."""
        method_name = method_sig.name
        expected_param_sig = self._get_param_signature(method_sig.params)
        expected_return = method_sig.return_type

        # Check if any method with this name exists
        if method_name not in class_methods:
            self.errors.append(CheckError(
                message=f"Class '{class_decl.name}' does not implement method '{method_name}' "
                        f"required by interface '{interface_name}'",
                line=class_decl.line,
                column=class_decl.column,
            ))
            return

        # Find a method with matching parameter signature
        matching_impl: Optional[FunctionDeclaration] = None
        for param_sig, impl in class_methods[method_name]:
            if param_sig == expected_param_sig:
                matching_impl = impl
                break

        if matching_impl is None:
            # No method with matching params - format expected signature
            param_str = ", ".join(
                f"{p.name}: {p.type_annotation}" for p in method_sig.params
            )
            self.errors.append(CheckError(
                message=f"Class '{class_decl.name}' does not implement method "
                        f"'{method_name}({param_str})' required by interface '{interface_name}'",
                line=class_decl.line,
                column=class_decl.column,
            ))
            return

        # Check return type matches
        actual_return = matching_impl.return_type
        if expected_return != actual_return:
            param_str = ", ".join(
                f"{p.name}: {p.type_annotation}" for p in method_sig.params
            )
            self.errors.append(CheckError(
                message=f"Method '{class_decl.name}.{method_name}({param_str})' has return type "
                        f"'{actual_return}' but interface '{interface_name}' expects '{expected_return}'",
                line=matching_impl.line,
                column=matching_impl.column,
            ))
