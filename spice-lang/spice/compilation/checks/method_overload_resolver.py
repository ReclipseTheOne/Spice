"""Compile-time resolver for method overloads."""

from collections import defaultdict
from typing import Dict, List, Optional

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.spicefile import SpiceFile
from spice.parser.ast_nodes import ClassDeclaration, FunctionDeclaration, Parameter, Module


class MethodOverloadResolver(CompileTimeCheck):
    """Resolve method overloads w/ @dispatch"""

    def __init__(self):
        self.errors: List[str] = []

    def check(self, file: SpiceFile) -> bool:
        """Populate overload metadata and decorate overloaded methods"""
        self.errors = []
        file.method_overload_table = {}

        self._process_module(file.ast, file)
        return not self.errors

    def _process_module(self, module: Module, file: SpiceFile):
        """Handle module-level functions and recurse into body"""
        functions_by_name: Dict[str, List[FunctionDeclaration]] = defaultdict(list)
        for node in module.body:
            if isinstance(node, FunctionDeclaration):
                functions_by_name[node.name].append(node)

        self._apply_overload_decorators(functions_by_name, owner_name="__module__", file=file)

        for node in module.body:
            self._process_node(node, file)

    def _process_node(self, node, file: SpiceFile):
        """Recursively process AST nodes looking for classes"""
        if isinstance(node, ClassDeclaration):
            self._process_class(node, file)

        body = getattr(node, "body", None)
        if isinstance(body, list):
            for child in body:
                self._process_node(child, file)

    def _process_class(self, class_node: ClassDeclaration, file: SpiceFile):
        """Group methods by name and add @dispatch"""
        methods_by_name: Dict[str, List[FunctionDeclaration]] = defaultdict(list)

        for member in class_node.body:
            if isinstance(member, FunctionDeclaration):
                methods_by_name[member.name].append(member)

        self._apply_overload_decorators(methods_by_name, owner_name=class_node.name, file=file)

    def _apply_overload_decorators(
        self,
        methods_by_name: Dict[str, List[FunctionDeclaration]],
        owner_name: Optional[str],
        file: SpiceFile,
    ):
        for method_name, methods in methods_by_name.items():
            if len(methods) <= 1:
                continue

            signature_map = file.method_overload_table.setdefault(owner_name or method_name, {})
            seen_signatures: set[str] = set()

            for method in methods:
                signature_key, type_names = self._signature_key(method_name, method.params)
                if signature_key in seen_signatures:
                    prefix = f"{owner_name}." if owner_name and owner_name != '__module__' else ""
                    self.errors.append(
                        f"Duplicate overload for {prefix}{method_name} with signature {signature_key}"
                    )
                    continue

                seen_signatures.add(signature_key)
                decorator = self._build_dispatch_decorator(type_names)
                if decorator not in method.decorators:
                    method.decorators.append(decorator)
                signature_map[signature_key] = decorator

    def _build_dispatch_decorator(self, type_names: List[str]) -> str:
        if not type_names:
            return "@dispatch()"

        args = ", ".join(self._dispatch_type_expr(type_name) for type_name in type_names)
        return f"@dispatch({args})"

    def _dispatch_type_expr(self, type_name: str) -> str:
        """Map Spice type annotations to Python expressions for dispatch"""
        if type_name.lower() == "any":
            return "object"
        if type_name == "None":
            return "type(None)"
        return type_name

    def _signature_key(self, base_name: str, params: List[Parameter]) -> tuple[str, List[str]]:
        """Fancy @Override public String toString() ngl"""
        type_names = [self._param_type_name(param) for param in params]
        if not type_names:
            signature = f"{base_name}()"
        else:
            signature = f"{base_name}({', '.join(type_names)})"
        return signature, type_names

    @staticmethod
    def _param_type_name(param: Parameter) -> str:
        """Return the type annotation or a fallback."""
        if param.type_annotation:
            return param.type_annotation
        return "any"
