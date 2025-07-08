"""Transform Spy AST to Python code."""

# Import line will be very long but CTRL + Click doesn't work on * imports and I hate it
from parser import (
    Module, InterfaceDeclaration, MethodSignature, ClassDeclaration,
    FunctionDeclaration, ExpressionStatement, PassStatement,
    AssignmentExpression, IdentifierExpression, AttributeExpression,
    LiteralExpression, CallExpression, ForStatement
)


class Transformer:
    """Transform Spy AST to Python code."""

    def __init__(self, verbose: bool = False):
        self.indent_level = 0
        self.output = []
        self.in_class = False  # Track if we're inside a class
        self.verbose = verbose

    def transform(self, ast: Module) -> str:
        """Transform AST to Python code."""
        if self.verbose:
            print("Starting transformation of AST to Python code")

        self.output = []
        self.visit_module(ast)

        result = ''.join(self.output)

        if self.verbose:
            lines = result.count('\n') + 1
            print(f"Transformation complete: Generated {lines} lines of Python code")

        return result

    def visit_module(self, node: Module):
        """Visit module node."""
        if self.verbose:
            print(f"Processing module with {len(node.body)} top-level statements")

        # Add imports if needed
        has_interfaces = any(isinstance(stmt, InterfaceDeclaration) for stmt in node.body)
        has_abstract = any(isinstance(stmt, ClassDeclaration) and stmt.is_abstract for stmt in node.body)
        has_final = any(
            isinstance(stmt, (ClassDeclaration, FunctionDeclaration)) and stmt.is_final
            for stmt in node.body
        )

        # Also check for final methods within class bodies
        if not has_final:
            for stmt in node.body:
                if isinstance(stmt, ClassDeclaration) and stmt.body:
                    has_final = any(
                        isinstance(method, FunctionDeclaration) and method.is_final
                        for method in stmt.body
                    )
                    if has_final:
                        break

        if has_interfaces or has_abstract:
            if self.verbose:
                print("Adding import for ABC and abstractmethod")
            self.output.append("from abc import ABC, abstractmethod\n")

        if has_interfaces:
            if self.verbose:
                print("Adding import for Protocol")
            self.output.append("from typing import Protocol\n")

        if has_final:
            if self.verbose:
                print("Adding import for final decorator")
            self.output.append("from typing import final\n")

        if has_interfaces or has_abstract or has_final:
            self.output.append("\n")  # Add extra line after imports

        # Visit each statement
        for stmt in node.body:
            if self.verbose:
                print(f"Transforming {type(stmt).__name__}")
            self.visit(stmt)
            self.output.append("\n")  # Add newline after each top-level statement

        # Remove trailing blank line if it exists
        if self.output and self.output[-1].isspace():
            self.output.pop()

    def visit(self, node):
        """Generic visitor method."""
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node):
        """Default visitor for unknown node types."""
        if self.verbose:
            print(f"WARNING: No visitor found for {type(node).__name__}")
        pass

    def visit_InterfaceDeclaration(self, node: InterfaceDeclaration):
        """Visit interface declaration node."""
        if self.verbose:
            print(f"Transforming interface '{node.name}' with {len(node.methods)} methods")

        extensions = f", {', '.join(node.base_interfaces)}" if node.base_interfaces else ""

        # In Python, interfaces are created using Protocol from typing
        self.output.append(f"class {node.name}(Protocol{extensions}):\n")
        self.indent_level += 1

        # Class docstring
        self.output.append(self._indent(f'"""Interface for {node.name}."""\n'))

        if not node.methods:
            self.output.append(self._indent("pass\n"))
        else:
            self.output.append("\n")  # Blank line after docstring

            # Transform each method signature
            for i, method in enumerate(node.methods):
                if self.verbose:
                    print(f"Transforming interface method signature: {method.name}")
                self.visit_MethodSignature(method)
                if i < len(node.methods) - 1:
                    self.output.append("\n")  # Add newlines between methods

        self.indent_level -= 1
        self.output.append("\n")  # Blank line after class

    def visit_MethodSignature(self, node: MethodSignature):
        """Visit method signature node."""
        params_str = ", ".join(self._format_param(param) for param in node.params)

        # Add self parameter if it's a method signature and doesn't already have one
        if not node.params or (node.params and node.params[0].name != "self"):
            params_str = "self" + (", " + params_str if params_str else "")

        return_annotation = f" -> {node.return_type}" if node.return_type else ""

        # Interface methods are abstract method stubs
        self.output.append(self._indent(f"def {node.name}({params_str}){return_annotation}:\n"))
        self.indent_level += 1
        self.output.append(self._indent(f'"""Interface method."""\n'))
        self.output.append(self._indent("...\n"))  # ... is the Ellipsis notation for pass in stub methods
        self.indent_level -= 1


    def visit_ClassDeclaration(self, node: ClassDeclaration):
        """Visit class declaration node."""
        if self.verbose:
            print(f"Transforming class '{node.name}'")
            if node.is_abstract:
                print("Class is abstract")
            if node.is_final:
                print("Class is final")

        self.in_class = True

        # Handle inheritance
        bases = []
        if node.bases:
            bases.extend(node.bases)
        if node.interfaces:
            bases.extend(node.interfaces)

        # For abstract classes with no explicit bases, add ABC as a base
        if node.is_abstract and not bases:
            bases.append("ABC")
            if self.verbose:
                print("Adding ABC as base class for abstract class")

        base_str = f"({', '.join(bases)})" if bases else ""

        # Add final decorator if needed
        if node.is_final:
            if self.verbose:
                print("Adding @final decorator")
            self.output.append("@final\n")

        # Class definition
        self.output.append(f"class {node.name}{base_str}:\n")
        self.indent_level += 1

        # Class body
        if not node.body:
            self.output.append(self._indent("pass\n"))
        else:
            # Add docstring
            self.output.append(self._indent(f'"""{node.name} class."""\n\n'))

            # Transform each class member
            for i, stmt in enumerate(node.body):
                if self.verbose:
                    print(f"Transforming class member: {type(stmt).__name__}")
                self.visit(stmt)
                if i < len(node.body) - 1:
                    self.output.append("\n")

        self.indent_level -= 1
        self.in_class = False

    def visit_FunctionDeclaration(self, node: FunctionDeclaration):
        """Visit function declaration node."""
        if self.verbose:
            print(f"Transforming {'method' if self.in_class else 'function'} '{node.name}'")
            if node.is_abstract:
                print("Method is abstract")
            if node.is_final:
                print("Method is final")
            if node.is_static:
                print("Method is static")

        params = node.params.copy()

        # Add decorators
        decorators = []

        # Static method decorator
        if node.is_static:
            decorators.append("@staticmethod")

        # Abstract method decorator
        if node.is_abstract:
            decorators.append("@abstractmethod")

        # Final decorator
        if node.is_final:
            decorators.append("@final")

        for decorator in decorators:
            self.output.append(self._indent(f"{decorator}\n"))

        # Format parameters
        params_str = ", ".join(self._format_param(param) for param in params)

        # Add self parameter if it's a method and not static
        if self.in_class and not node.is_static:
            if not params or (params and params[0].name != "self"):
                params_str = "self" + (", " + params_str if params_str else "")

        return_annotation = f" -> {node.return_type}" if node.return_type else ""

        # Function definition
        self.output.append(self._indent(f"def {node.name}({params_str}){return_annotation}:\n"))
        self.indent_level += 1

        # Function body
        if node.is_abstract:
            # Abstract methods just need a docstring and a pass statement
            self.output.append(self._indent(f'"""Abstract method."""\n'))
            self.output.append(self._indent("pass\n"))
        elif not node.body:
            # Empty function body
            self.output.append(self._indent("pass\n"))
        else:
            # Add docstring
            self.output.append(self._indent(f'"""{node.name} {"method" if self.in_class else "function"}."""\n'))

            # Transform function body statements
            for stmt in node.body:
                if self.verbose:
                    print(f"Transforming function body statement: {type(stmt).__name__}")
                self.visit(stmt)

        self.indent_level -= 1

    def visit_ExpressionStatement(self, node: ExpressionStatement):
        """Visit expression statement node."""
        if self.verbose:
            print("Transforming expression statement")
        if node.expression:
            self.visit(node.expression)
            self.output.append("\n")

    def visit_PassStatement(self, node: PassStatement):
        """Visit pass statement node."""
        if self.verbose:
            print("Transforming pass statement")
        self.output.append(self._indent("pass\n"))

    def visit_AssignmentExpression(self, node: AssignmentExpression):
        """Visit assignment expression node."""
        if self.verbose:
            print("Transforming assignment expression")
        # Support for +=, -=, *=, /=, etc.
        op = getattr(node, 'operator', '=')  # Default to '=' if not present
        output_before = len(self.output)
        self.visit(node.target)
        target_len = len(self.output) - output_before
        target = ''.join(self.output[-target_len:])
        self.output = self.output[:-target_len]
        self.visit(node.value)
        value_len = len(self.output) - output_before
        value = ''.join(self.output[-value_len:])
        self.output = self.output[:-value_len]
        self.output.append(self._indent(f"{target} {op} {value}"))

    def visit_IdentifierExpression(self, node: IdentifierExpression):
        """Visit identifier expression node."""
        if self.verbose:
            print(f"Transforming identifier: {node.name}")
        self.output.append(node.name)

    def visit_AttributeExpression(self, node: AttributeExpression):
        """Visit attribute expression node."""
        if self.verbose:
            print(f"Transforming attribute access: {node.attribute}")

        # Visit the object
        output_before = len(self.output)

        self.visit(node.object)

        object_len = len(self.output) - output_before
        object_str = ''.join(self.output[-object_len:])
        self.output = self.output[:-object_len]

        self.output.append(f"{object_str}.{node.attribute}")

    def visit_LiteralExpression(self, node: LiteralExpression):
        """Visit literal expression node."""
        if self.verbose:
            print(f"Transforming literal: {node.value}")
        if node.value is None:
            self.output.append("None")
        elif node.literal_type == 'fstring':
            # Emit as Python f-string (assume already valid)
            self.output.append(f"f{repr(node.value)}")
        elif node.literal_type == 'string':
            # String literals need quotes
            self.output.append(repr(node.value))
        else:
            self.output.append(str(node.value))

    def visit_CallExpression(self, node: CallExpression):
        """Visit call expression node."""
        if self.verbose:
            print("Transforming function/method call")
        # Visit the callee
        output_before = len(self.output)
        self.visit(node.callee)
        callee_len = len(self.output) - output_before
        callee_str = ''.join(self.output[-callee_len:])
        self.output = self.output[:-callee_len]
        # Format arguments
        args = []
        for arg in node.arguments:
            arg_output_before = len(self.output)
            self.visit(arg)
            arg_len = len(self.output) - arg_output_before
            arg_str = ''.join(self.output[-arg_len:])
            self.output = self.output[:-arg_len]
            args.append(arg_str)
        arg_str = ", ".join(args)
        self.output.append(f"{callee_str}({arg_str})")

    def visit_ReturnStatement(self, node):
        """Visit return statement node."""
        if self.verbose:
            print("Transforming return statement")
        if node.value is not None:
            output_before = len(self.output)
            self.visit(node.value)
            value_len = len(self.output) - output_before
            value_str = ''.join(self.output[-value_len:])
            self.output = self.output[:-value_len]
            self.output.append(self._indent(f"return {value_str}\n"))
        else:
            self.output.append(self._indent("return\n"))

    def visit_IfStatement(self, node):
        """Visit if statement node."""
        if self.verbose:
            print("Transforming if statement")
        self.output.append(self._indent(f"if "))
        output_before = len(self.output)
        self.visit(node.condition)
        cond_len = len(self.output) - output_before
        cond_str = ''.join(self.output[-cond_len:])
        self.output = self.output[:-cond_len]
        self.output.append(f"{cond_str}:")
        self.output.append("\n")
        self.indent_level += 1
        for stmt in node.then_body:
            self.visit(stmt)
        self.indent_level -= 1
        if node.else_body:
            self.output.append(self._indent("else:\n"))
            self.indent_level += 1
            for stmt in node.else_body:
                self.visit(stmt)
            self.indent_level -= 1

    def visit_ForStatement(self, node: ForStatement):
        """Visit for statement node."""
        if self.verbose:
            print("Transforming for statement")

        self.output.append(self._indent("for "))
        self.output.append(f"{node.target}:")
        self.output.append("\n")

        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

    def visit_WhileStatement(self, node):
        """Visit while statement node."""
        if self.verbose:
            print("Transforming while statement")
        self.output.append(self._indent("while "))
        output_before = len(self.output)
        self.visit(node.condition)
        cond_len = len(self.output) - output_before
        cond_str = ''.join(self.output[-cond_len:])
        self.output = self.output[:-cond_len]
        self.output.append(f"{cond_str}:")
        self.output.append("\n")
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        self.indent_level -= 1

    def visit_SwitchStatement(self, node):
        """Visit switch statement node."""
        if self.verbose:
            print("Transforming switch statement (using if-elif-else)")
        # Python doesn't have switch, so use if-elif-else
        for i, case in enumerate(node.cases):
            if i == 0:
                self.output.append(self._indent("if "))
            else:
                self.output.append(self._indent("elif "))
            output_before = len(self.output)
            self.visit(case.value)
            val_len = len(self.output) - output_before
            val_str = ''.join(self.output[-val_len:])
            self.output = self.output[:-val_len]
            self.output.append(f"{node.expression} == {val_str}:")
            self.output.append("\n")
            self.indent_level += 1
            for stmt in case.body:
                self.visit(stmt)
            self.indent_level -= 1
        if node.default:
            self.output.append(self._indent("else:\n"))
            self.indent_level += 1
            for stmt in node.default:
                self.visit(stmt)
            self.indent_level -= 1

    def visit_CaseClause(self, node):
        # Not used directly; handled in visit_SwitchStatement
        pass

    def visit_LogicalExpression(self, node):
        """Visit logical expression node."""
        left_code = self.expr_to_str(node.left)
        right_code = self.expr_to_str(node.right)
        self.output.append(f"({left_code} {node.operator} {right_code})")

    def visit_UnaryExpression(self, node):
        """Visit unary expression node."""
        operand_code = self.expr_to_str(node.operand)
        self.output.append(f"({node.operator} {operand_code})")

    def visit_BinaryExpression(self, node):
        """Visit binary expression node."""
        left_code = self.visit(node.left)
        right_code = self.visit(node.right)
        self.output.append(f"{left_code} {node.operator} {right_code}")

    def expr_to_str(self, expr):
        """Helper to get code for an expression node as a string."""
        prev_output = self.output
        self.output = []
        self.visit(expr)
        code = ''.join(self.output)
        self.output = prev_output
        return code

    # Helper methods
    def _indent(self, s: str) -> str:
        """Add proper indentation to string."""
        return "    " * self.indent_level + s

    def _format_param(self, param) -> str:
        """Format a function parameter."""
        result = param.name
        if param.type_annotation:
            result += f": {param.type_annotation}"
        if param.default:
            result += f" = {param.default}"
        return result
