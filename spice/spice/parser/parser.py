"""Parser for Spy language."""

from typing import List
from lexer import Token, TokenType
from parser.ast_nodes import Module, InterfaceDeclaration, MethodSignature, Parameter
from errors import SpiceError


class ParseError(SpiceError):
    """Parser error."""
    pass


class Parser:
    """Parse Spy tokens into an AST."""

    def __init__(self):
        self.tokens: List[Token] = []
        self.current = 0

    def parse(self, tokens: List[Token]) -> Module:
        """Parse tokens into an AST."""
        self.tokens = tokens
        self.current = 0

        statements = []
        while not self.is_at_end():
            # Skip newlines at module level
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            stmt = self.parse_statement()
            if stmt:
                statements.append(stmt)

        return Module(body=statements)

    def parse_statement(self):
        """Parse a statement."""
        # Skip comments
        if self.check(TokenType.COMMENT):
            self.advance()
            return None

        # Interface declaration
        if self.match(TokenType.INTERFACE):
            return self.parse_interface()

        # Class declaration with modifiers
        if self.check(TokenType.ABSTRACT, TokenType.FINAL, TokenType.CLASS):
            return self.parse_class()

        # Function declaration
        if self.match(TokenType.DEF):
            return self.parse_function()

        # Expression statement
        return self.parse_expression_statement()

    def parse_interface(self) -> InterfaceDeclaration:
        """Parse interface declaration."""
        name = self.consume(TokenType.IDENTIFIER, "Expected interface name").value

        # Optional base interfaces
        bases = []
        if self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                bases.append(self.consume(TokenType.IDENTIFIER, "Expected base interface").value)
                while self.match(TokenType.COMMA):
                    bases.append(self.consume(TokenType.IDENTIFIER, "Expected base interface").value)
            self.consume(TokenType.RPAREN, "Expected ')' after base interfaces")

        # Interface body
        if self.match(TokenType.LBRACE):
            # C-style block
            methods = self.parse_interface_body_braces()
        else:
            # Python-style block
            self.consume(TokenType.COLON, "Expected ':' after interface declaration")
            self.consume(TokenType.NEWLINE, "Expected newline after ':'")
            methods = self.parse_interface_body_indent()

        return InterfaceDeclaration(name, methods, bases if bases else [])

    def parse_interface_body_braces(self) -> List[MethodSignature]:
        """Parse interface body with curly braces."""
        methods = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            if self.match(TokenType.DEF):
                methods.append(self.parse_method_signature())
            else:
                raise ParseError(f"Expected method signature, got {self.peek()}")

        self.consume(TokenType.RBRACE, "Expected '}' after interface body")
        return methods

    def parse_method_signature(self) -> MethodSignature:
        """Parse a method signature."""
        name = self.consume(TokenType.IDENTIFIER, "Expected method name").value

        # Parameters
        self.consume(TokenType.LPAREN, "Expected '(' after method name")
        params = self.parse_parameters()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        # Return type
        return_type = None
        if self.match(TokenType.ARROW):
            return_type = self.consume(TokenType.IDENTIFIER, "Expected return type").value

        # Consume semicolon if present
        self.match(TokenType.SEMICOLON)

        return MethodSignature(name, params, return_type)

    def parse_parameters(self) -> List[Parameter]:
        """Parse function parameters."""
        params = []

        if not self.check(TokenType.RPAREN):
            params.append(self.parse_parameter())
            while self.match(TokenType.COMMA):
                params.append(self.parse_parameter())

        return params

    def parse_parameter(self) -> Parameter:
        """Parse a single parameter."""
        name = self.consume(TokenType.IDENTIFIER, "Expected parameter name").value

        # Type annotation
        type_annotation = None
        if self.match(TokenType.COLON):
            type_annotation = self.consume(TokenType.IDENTIFIER, "Expected type annotation").value

        # Default value
        default = None
        if self.match(TokenType.ASSIGN):
            # TODO: Parse expression
            default = self.advance().value

        return Parameter(name, type_annotation, default)

    # Helper methods

    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        for token_type in types:
            if self.check(token_type):
                self.advance()
                return True
        return False

    def check(self, *types: TokenType) -> bool:
        """Check if current token is of given type(s)."""
        if self.is_at_end():
            return False
        return self.peek().type in types

    def advance(self) -> Token:
        """Consume current token and return it."""
        if not self.is_at_end():
            self.current += 1
        return self.previous()

    def is_at_end(self) -> bool:
        """Check if we're at end of tokens."""
        return self.peek().type == TokenType.EOF

    def peek(self) -> Token:
        """Return current token without advancing."""
        return self.tokens[self.current]

    def previous(self) -> Token:
        """Return previous token."""
        return self.tokens[self.current - 1]

    def consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of given type or raise error."""
        if self.check(token_type):
            return self.advance()

        raise ParseError(f"{message} at line {self.peek().line}")

    # TODO: Implement remaining parsing methods
    def parse_interface_body_indent(self):
        """Parse Python-style interface body."""
        # TODO: Handle indentation
        return []

    def parse_class(self):
        """Parse class declaration."""
        # TODO: Implement
        pass

    def parse_function(self):
        """Parse function declaration."""
        # TODO: Implement
        pass

    def parse_expression_statement(self):
        """Parse expression statement."""
        # TODO: Implement
        pass