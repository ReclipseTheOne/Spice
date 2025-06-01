"""Transform Spy AST to Python code."""

# Import line will be very long but CTRL + Click doesn't work on * imports and I hate it
from parser import Module, InterfaceDeclaration, MethodSignature, ClassDeclaration, FunctionDeclaration


class Transformer:
    """Transform Spy AST to Python code."""

    def __init__(self):
        self.indent_level = 0
        self.output = []

    def transform(self, ast: Module) -> str:
        """Transform AST to Python code."""
        self.output = []
        self.visit_module(ast)
        return ''.join(self.output)

    def visit_module(self, node: Module):
        """Visit module node."""
        # Add imports if needed
        has_interfaces = any(isinstance(stmt, InterfaceDeclaration) for stmt in node.body)
        has_abstract = any(isinstance(stmt, ClassDeclaration) and stmt.is_abstract for stmt in node.body)
        has_final = any(
            isinstance(stmt, (ClassDeclaration, FunctionDeclaration)) and stmt.is_final
            for stmt in node.body
        )

        if has_interfaces or has_abstract:
            self.output.append("from abc import ABC, abstractmethod\n")

        if has_interfaces:
            self.output.append("from typing import Protocol\n")

        if has_final:
            self.output.append("from typing import final\n")

        if has_interfaces or has_abstract or has_final:
            self.output.append("\n")

        # Visit all statements
        for stmt in node.body:
            stmt.accept(self)

    def visit_interface(self, node: InterfaceDeclaration):
        """Transform interface to Protocol."""
        self.write(f"class {node.name}")

        # Base interfaces
        if node.base_interfaces:
            bases = ", ".join(node.base_interfaces)
            self.write(f"({bases}, Protocol):\n")
        else:
            self.write("(Protocol):\n")

        self.indent_level += 1

        if not node.methods:
            self.write_line("pass")
        else:
            for method in node.methods:
                method.accept(self)

        self.indent_level -= 1
        self.write("\n")

    def visit_method_signature(self, node: MethodSignature):
        """Transform method signature."""
        self.write_line("@abstractmethod")
        self.write_line(f"def {node.name}(")

        # Parameters
        params = []
        for param in node.params:
            param_str = param.name
            if param.type_annotation:
                param_str += f": {param.type_annotation}"
            if param.default is not None:
                param_str += f" = {param.default}"
            params.append(param_str)

        self.output.append(", ".join(params))
        self.output.append(")")

        # Return type
        if node.return_type:
            self.output.append(f" -> {node.return_type}")

        self.output.append(":\n")
        self.indent_level += 1
        self.write_line("pass")
        self.indent_level -= 1

    def visit_class(self, node: ClassDeclaration):
        """Transform class declaration."""
        # Decorators
        if node.is_final:
            self.write_line("@final")

        # Class definition
        self.write(f"class {node.name}")

        # Bases
        bases = []
        if node.is_abstract:
            bases.append("ABC")
        if node.bases:
            bases.extend(node.bases)

        if bases:
            self.write(f"({', '.join(bases)})")

        self.write(":\n")

        self.indent_level += 1

        if not node.body:
            self.write_line("pass")
        else:
            for stmt in node.body:
                stmt.accept(self)

        self.indent_level -= 1
        self.write("\n")

    def visit_function(self, node: FunctionDeclaration):
        """Transform function declaration."""
        # Decorators
        if node.is_static:
            self.write_line("@staticmethod")
        if node.is_abstract:
            self.write_line("@abstractmethod")
        if node.is_final:
            self.write_line("@final")
        if node.decorators:
            for decorator in node.decorators:
                self.write_line(f"@{decorator}")

        # Function definition
        self.write(f"def {node.name}(")

        # Parameters
        params = []
        for param in node.params:
            param_str = param.name
            if param.type_annotation:
                param_str += f": {param.type_annotation}"
            if param.default is not None:
                param_str += f" = {param.default}"
            params.append(param_str)

        self.output.append(", ".join(params))
        self.output.append(")")

        # Return type
        if node.return_type:
            self.output.append(f" -> {node.return_type}")

        self.output.append(":\n")

        self.indent_level += 1

        if not node.body:
            self.write_line("pass")
        else:
            for stmt in node.body:
                stmt.accept(self)

        self.indent_level -= 1

    # Helper methods

    def write(self, text: str):
        """Write text to output."""
        self.output.append(text)

    def write_line(self, text: str):
        """Write indented line to output."""
        self.output.append("    " * self.indent_level + text + "\n")

    def indent(self):
        """Increase indent level."""
        self.indent_level += 1

    def dedent(self):
        """Decrease indent level."""
        self.indent_level -= 1
