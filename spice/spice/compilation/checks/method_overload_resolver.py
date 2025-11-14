"""Compile-time resolver for method overloads."""

from collections import defaultdict
from typing import Dict, List

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.spicefile import SpiceFile
from spice.parser.ast_nodes import ClassDeclaration, FunctionDeclaration, Parameter


class MethodOverloadResolver(CompileTimeCheck):
    """Resolve method overloads by renaming them to unique identifiers."""

    def __init__(self):
        self.errors: List[str] = []

    def check(self, file: SpiceFile) -> bool:
        """Populate the overload table and rewrite method names."""
        self.errors = []
        file.method_overload_table = {}

        for node in file.ast.body:
            self._process_node(node, file)

        return not self.errors

    def _process_node(self, node, file: SpiceFile):
        """Recursively process AST nodes looking for classes."""
        if isinstance(node, ClassDeclaration):
            self._process_class(node, file)

        # Recurse into nested bodies if they exist
        body = getattr(node, "body", None)
        if isinstance(body, list):
            for child in body:
                self._process_node(child, file)

    def _process_class(self, class_node: ClassDeclaration, file: SpiceFile):
        """Group methods by name and rename overloads."""
        methods_by_name: Dict[str, List[FunctionDeclaration]] = defaultdict(list)

        for member in class_node.body:
            if isinstance(member, FunctionDeclaration):
                methods_by_name[member.name].append(member)

        for method_name, methods in methods_by_name.items():
            if len(methods) <= 1:
                continue

            signature_map = file.method_overload_table.setdefault(class_node.name, {})
            used_names: set[str] = set()
            seen_signatures: set[str] = set()

            for method in methods:
                signature_key, type_names = self._signature_key(method_name, method.params)

                if signature_key in seen_signatures:
                    self.errors.append(
                        f"Duplicate overload for {class_node.name}.{method_name} with signature {signature_key}"
                    )
                    continue

                seen_signatures.add(signature_key)

                new_name = self._build_overload_name(method_name, method.params, used_names)
                used_names.add(new_name)
                signature_map[signature_key] = new_name
                method.name = new_name

    def _signature_key(self, base_name: str, params: List[Parameter]) -> tuple[str, List[str]]:
        """Build a human-readable signature key."""
        type_names = [self._param_type_name(param) for param in params]
        if not type_names:
            signature = f"{base_name}()"
        else:
            signature = f"{base_name}({', '.join(type_names)})"
        return signature, type_names

    def _build_overload_name(
        self,
        base_name: str,
        params: List[Parameter],
        used_names: set[str],
    ) -> str:
        """Construct the overload name with type-based suffixes."""
        abbreviations = self._abbreviate_params(params)
        if not abbreviations:
            suffix = "noparams"
        else:
            suffix = "_".join(abbreviations)

        candidate = f"{base_name}_{suffix}"
        counter = 1
        while candidate in used_names:
            counter += 1
            candidate = f"{base_name}_{suffix}_{counter}"
        return candidate

    def _abbreviate_params(self, params: List[Parameter]) -> List[str]:
        """Generate unique abbreviations for parameter types."""
        abbreviations: List[str] = []
        used: set[str] = set()

        for index, param in enumerate(params):
            normalized = self._normalize_type_name(self._param_type_name(param))
            prefix_len = min(3, len(normalized)) or len(normalized)
            prefix_len = prefix_len or 3
            candidate = normalized[:prefix_len].lower()

            while candidate in used and prefix_len < len(normalized):
                prefix_len += 1
                candidate = normalized[:prefix_len].lower()

            if candidate in used:
                param_suffix = param.name.lower() if param.name else f"p{index}"
                temp_candidate = f"{candidate}_{param_suffix}"
                suffix_counter = 1
                unique_candidate = temp_candidate
                while unique_candidate in used:
                    suffix_counter += 1
                    unique_candidate = f"{temp_candidate}{suffix_counter}"
                candidate = unique_candidate

            used.add(candidate)
            abbreviations.append(candidate)

        return abbreviations

    @staticmethod
    def _param_type_name(param: Parameter) -> str:
        """Return the type annotation or a fallback."""
        if param.type_annotation:
            return param.type_annotation
        return "any"

    @staticmethod
    def _normalize_type_name(type_name: str) -> str:
        """Strip non-alphanumeric characters and provide a fallback."""
        cleaned = ''.join(ch for ch in type_name if ch.isalnum())
        return cleaned or "any"
