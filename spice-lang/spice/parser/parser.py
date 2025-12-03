"""Parser for Spice language."""

from typing import List, Optional, Any
from spice.lexer import Token, TokenType
from spice.parser.ast_nodes import (
    Module, InterfaceDeclaration, MethodSignature, Parameter,
    ExpressionStatement, PassStatement, Expression, ReturnStatement,
    IfStatement, ForStatement, WhileStatement, SwitchStatement, CaseClause,
    RaiseStatement, ImportStatement, FinalDeclaration, FunctionDeclaration,
    IdentifierExpression, AnnotatedAssignment
)
from spice.errors import SpiceError, ParserError

from spice.printils import parser_log


class ParseError(SpiceError):
    """Parser error."""
    pass


class Parser:
    """Parse Spice tokens into an AST."""

    def __init__(self):
        self.tokens: List[Token] = []
        self.current = 0

        # Extensions
        from spice.parser.expression_parser import ExpressionParser
        self.expr_parser = ExpressionParser(self)

    def match(self, *types: TokenType, advance_at_newline: bool = False) -> bool:
        """Check if current token matches any of the given types."""
        if advance_at_newline and self.check(TokenType.NEWLINE):
            parser_log.info("Skipped NewLine token on match.")
            self.advance()

        for token_type in types:
            if self.check(token_type):
                parser_log.success(f"Matched token {self.peek()} for: {', '.join([t.name for t in types])}")
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

    def back(self) -> Token:
        """Backtrack one token, return current"""
        if self.current > 0:
            self.current -= 1
            return self.peek(1)
        else:
            self.raise_parser_error("Cannot backtrack beyond start of tokens")

    def is_at_end(self) -> bool:
        """Check if we're at end of tokens."""
        return self.peek().type == TokenType.EOF

    def peek(self, offset: int = 0) -> Token:
        """Return current (+ offset) token without advancing."""
        return self.tokens[self.current + offset]

    def previous(self) -> Token:
        """Return previous token."""
        return self.tokens[self.current - 1]

    def consume(self, token_type: TokenType, message: str) -> Token:
        """Consume token of given type or raise error."""
        if self.check(token_type):
            token = self.advance()
            parser_log.info(f"Consumed token: {token.type.name}" + (f" '{token.value}'" if token.value is not None else ""))
            return token

        self.raise_parser_error(f"{message} at line {self.peek().line} - found {self.peek().type.name} instead")

    def get_tokens(self, start: int = -1, size: Optional[int] = None) -> List[Token]:
        """Get a slice of tokens from start to end."""
        if start < 0:
            start = self.current
        if size is None:
            size = len(self.tokens) - self.current
        return self.tokens[start:(start + size)]

    def raise_parser_error(self, message: str, context_radius: int = 5) -> None:
        """Raise ParserError with contextual token information."""
        token_count = len(self.tokens)
        context_radius = max(context_radius, 0)
        current_index: Optional[int] = None
        current_token: Optional[Token] = None

        if token_count:
            current_index = min(max(self.current, 0), token_count - 1)
            current_token = self.tokens[current_index]

        location = ""
        if current_token is not None:
            filename = current_token.filename or "<unknown>"
            location = (f" (token {current_index} @ {filename}:"
                        f"{current_token.line}:{current_token.column} "
                        f"{current_token.type.name})")

        token_context = self._format_token_context(current_index, context_radius)
        full_message = message + location
        if token_context:
            full_message += f"\n\nToken context:\n{token_context}"

        raise ParserError(full_message)

    def _format_token_context(self, current_index: Optional[int], radius: int) -> str:
        """Return a formatted string showing tokens around the current index."""
        if not self.tokens:
            return "No tokens available."

        if current_index is None:
            current_index = min(max(self.current, 0), len(self.tokens) - 1)

        start = max(current_index - radius, 0)
        end = min(current_index + radius + 1, len(self.tokens))
        lines: List[str] = []

        for idx in range(start, end):
            token = self.tokens[idx]
            pointer = "->" if idx == current_index else "  "
            value_repr = "" if token.value is None else repr(token.value)
            filename = token.filename or "<unknown>"
            lines.append(
                f"{pointer} [{idx}] {token.type.name} {value_repr} @ {filename}:{token.line}:{token.column}"
            )

        return "\n".join(lines)


    def parse(self, tokens: List[Token]) -> Module:
        """Parse tokens into an AST."""
        self.tokens = tokens
        self.current = 0
        parser_log.info(f"Starting parsing with {len(tokens)} tokens")

        statements = []
        while not self.is_at_end():
            # Skip newlines at module level
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            stmt = self.parse_statement()
            if stmt:
                parser_log.info(f"Added statement: {type(stmt).__name__}")
                statements.append(stmt)
        parser_log.success(f"Finished parsing: Generated AST with {len(statements)} top-level statements")
        return Module(body=statements)


    ##########################################
    ################# UTILS ##################
    ##########################################

    # Pretty empty atm :p
    def _consume_compiler_flags(self, allowed_next: Optional[List[TokenType]] = None) -> List[str]:
        """Consume zero or more compiler flag blocks like [flag1, flag2]."""
        flags: List[str] = []
        start_index = self.current

        while self.check(TokenType.LBRACKET):
            self.advance()  # consume '['
            flags.extend(self._parse_compiler_flag_values())
            self.consume(TokenType.RBRACKET, "Expected ']' after compiler flags")

            # Allow trailing commas/newlines by skipping newlines
            while self.match(TokenType.NEWLINE):
                continue
            # Skip inline comments between flag blocks and declarations
            while self.check(TokenType.COMMENT):
                self.advance()
                while self.match(TokenType.NEWLINE):
                    continue

        if not flags:
            return flags

        if allowed_next is not None:
            next_type = self._peek_next_non_newline_type()
            if next_type not in allowed_next:
                # Roll back and treat the '[' as normal token (likely a list literal)
                self.current = start_index
                return []

        return flags

    def _parse_compiler_flag_values(self) -> List[str]:
        """Parse the values inside a compiler flag block."""
        values: List[str] = []

        # Empty block
        if self.check(TokenType.RBRACKET):
            return values

        while True:
            if self.check(TokenType.IDENTIFIER, TokenType.STRING):
                token = self.advance()
                values.append(str(token.value))
            else:
                self.raise_parser_error("Expected compiler flag identifier or string")

            if not self.match(TokenType.COMMA):
                break

        return values

    def _parse_type_annotation_string(self) -> str:
        """Parse a type annotation expression."""
        parts: List[str] = []
        bracket_depth = 0

        stop_tokens = {TokenType.ASSIGN, TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE}
        while not self.check(*stop_tokens):
            if self.check(TokenType.IDENTIFIER):
                parts.append(str(self.advance().value))
            elif self.match(TokenType.LBRACKET):
                parts.append('[')
                bracket_depth += 1
            elif self.match(TokenType.RBRACKET):
                if bracket_depth == 0:
                    break
                parts.append(']')
                bracket_depth -= 1
            elif self.match(TokenType.COMMA):
                parts.append(', ')
            elif self.match(TokenType.DOT):
                parts.append('.')
            else:
                break

        return ''.join(parts).strip()

    def _looks_like_typed_declaration(self) -> bool:
        """Determine if the next tokens represent a typed variable declaration."""
        if not self.check(TokenType.IDENTIFIER):
            return False
        next_type = self._peek_next_non_newline_type(self.current + 1)
        return next_type == TokenType.COLON

    def _peek_next_non_newline_type(self, start_index: Optional[int] = None) -> TokenType:
        """Peek ahead to find the next non-newline/comment token type."""
        lookahead = self.current if start_index is None else start_index
        while lookahead < len(self.tokens):
            token_type = self.tokens[lookahead].type
            if token_type not in (TokenType.NEWLINE, TokenType.COMMENT):
                return token_type
            lookahead += 1
        return TokenType.EOF

    ##########################################
    ################ CLASSES #################
    ##########################################

    # Any methods handling class declarations, interfaces, methods, etc.

    def parse_interface(self) -> InterfaceDeclaration:
        """Parse interface declaration."""
        name = self.consume(TokenType.IDENTIFIER, "Expected interface name").value
        parser_log.info(f"Parsing interface '{name}'")

        # Optional base interfaces
        bases = []
        if self.match(TokenType.EXTENDS):
            base = self.consume(TokenType.IDENTIFIER, "Expected base interface").value
            bases.append(base)
            parser_log.info(f"Added base interface: {base}")

            while self.match(TokenType.COMMA):
                base = self.consume(TokenType.IDENTIFIER, "Expected base interface").value
                bases.append(base)
                parser_log.info(f"Added base interface: {base}")

        # Interface body
        self.consume(TokenType.LBRACE, "Expected '{' after interface declaration")
        parser_log.info("Parsing C-style interface body")

        methods = self.parse_interface_body()
        parser_log.info(f"Completed interface '{name}' with {len(methods)} methods")

        return InterfaceDeclaration(name, methods, bases if bases else [])


    def parse_interface_body(self) -> List[MethodSignature]:
        """Parse interface body with curly braces."""
        methods = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            if self.match(TokenType.DEF):
                method = self.parse_method_signature()
                methods.append(method)
                parser_log.info(f"Added method signature: {method.name}")
            else:
                self.raise_parser_error(f"Expected method signature, got {self.peek()}")

        self.consume(TokenType.RBRACE, "Expected '}' after interface body")
        return methods


    def parse_class(self, compiler_flags: Optional[List[str]] = None):
        """Parse class declaration."""
        from spice.parser.ast_nodes import ClassDeclaration

        # Handle modifiers
        is_abstract = False
        is_final = False

        if self.match(TokenType.ABSTRACT):
            is_abstract = True
            parser_log.info("Class is abstract")
        elif self.match(TokenType.FINAL):
            is_final = True
            parser_log.info("Class is final")

        # Consume 'class' keyword
        self.consume(TokenType.CLASS, "Expected 'class' keyword")

        # Class name
        name = self.consume(TokenType.IDENTIFIER, "Expected class name").value
        parser_log.info(f"Parsing class '{name}'")

        # Optional base classes and interfaces
        bases = []  # For extended classes
        interfaces = []  # For implemented interfaces

        if self.match(TokenType.LPAREN):
            parser_log.info("Parsing Python-style inheritance")
            # Python-style: class Dog(Animal)
            if not self.check(TokenType.RPAREN):
                base = self.consume(TokenType.IDENTIFIER, "Expected base class").value
                bases.append(base)
                parser_log.info(f"Added base class: {base}")
                while self.match(TokenType.COMMA):
                    base = self.consume(TokenType.IDENTIFIER, "Expected base class").value
                    bases.append(base)
                    parser_log.info(f"Added base class: {base}")
            self.consume(TokenType.RPAREN, "Expected ')' after base classes")
        elif self.match(TokenType.EXTENDS):
            parser_log.info("Parsing Java-style inheritance")
            # Java-style: class Dog extends Animal
            base = self.consume(TokenType.IDENTIFIER, "Expected base class").value
            bases.append(base)
            parser_log.info(f"Added base class: {base}")

        # Handle implements keyword for interfaces
        if self.match(TokenType.IMPLEMENTS):
            parser_log.info("Parsing implemented interfaces")
            # implements Interface1, Interface2, ...
            interface = self.consume(TokenType.IDENTIFIER, "Expected interface name").value
            interfaces.append(interface)
            parser_log.info(f"Added implemented interface: {interface}")
            while self.match(TokenType.COMMA):
                interface = self.consume(TokenType.IDENTIFIER, "Expected interface name").value
                interfaces.append(interface)
                parser_log.info(f"Added implemented interface: {interface}")

        # Class body
        self.consume(TokenType.LBRACE, "Expected '{' after class declaration")

        # Parse class body
        parser_log.info("Parsing class body")
        body = self.parse_class_body()

        self.consume(TokenType.RBRACE, "Expected '}' after class body")
        parser_log.info(f"Completed class '{name}' with {len(body)} members")

        declaration = ClassDeclaration(
            name=name,
            body=body,
            bases=bases,
            interfaces=interfaces,
            is_abstract=is_abstract,
            is_final=is_final
        )

        declaration.compiler_flags = list(compiler_flags or [])
        return declaration

    def parse_class_body(self):
        """Parse class body statements."""
        body = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            # Skip newlines
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            # Skip comments
            if self.check(TokenType.COMMENT):
                self.advance()
                continue

            # Parse class member
            parser_log.info("Parsing class member")
            member_flags = self._consume_compiler_flags(
                [TokenType.STATIC, TokenType.ABSTRACT, TokenType.FINAL, TokenType.DEF]
            )
            stmt = self.parse_class_member(compiler_flags=member_flags)
            if stmt:
                if member_flags and not isinstance(stmt, FunctionDeclaration):
                    self.raise_parser_error("Compiler flags can only be applied to methods inside classes")
                parser_log.info(f"Added class member: {type(stmt).__name__}")
                body.append(stmt)
            elif member_flags:
                self.raise_parser_error("Compiler flags must be followed by a method declaration inside classes")

        return body


    def parse_class_member(self, is_interface: bool = False, compiler_flags: Optional[List[str]] = None):
        """Parse a class member (method or field)."""
        # Check for static modifier
        is_static = False
        is_abstract = False
        is_final = False

        if self.match(TokenType.STATIC):
            is_static = True
            parser_log.info("Method is static")
        elif self.match(TokenType.ABSTRACT):
            is_abstract = True
            parser_log.info("Method is abstract")
        elif self.match(TokenType.FINAL):
            is_final = True
            parser_log.info("Method is final")

        # Method declaration
        if self.match(TokenType.DEF):
            name = self.consume(TokenType.IDENTIFIER, "Expected method name").value
            parser_log.info(f"Parsing method '{name}'")

            # Parameters
            self.consume(TokenType.LPAREN, "Expected '(' after method name")
            params = self.parse_parameters()
            self.consume(TokenType.RPAREN, "Expected ')' after parameters")

            # Return type
            return_type = None
            if self.match(TokenType.ARROW):
                # Handle `-> return_type` syntax
                if self.check(TokenType.IDENTIFIER):
                    return_type = self.advance().value
                elif self.check(TokenType.NONE):
                    return_type = self.advance().value
                elif self.check(TokenType.STRING):
                    return_type = self.advance().value
                else:
                    self.raise_parser_error(f"Expected return type after '->' at line {self.peek().line}")
                parser_log.info(f"Method '{name}' has return type: {return_type}")

            # Method body - abstract methods don't have bodies
            body = []
            if is_abstract or is_interface:
                parser_log.info(f"Registered abstract/interface method '{name}'")
                self.consume(TokenType.SEMICOLON, "Expected ';' after abstract method signature")
                body.append(PassStatement(has_semicolon=True))
                # Abstract methods end here - no body expected
            else:
                # Concrete methods need a body
                self.consume(TokenType.LBRACE, "Expected '{' after method signature")
                parser_log.info(f"Parsing body of method '{name}'")
                body = self.parse_method_body()
                self.consume(TokenType.RBRACE, "Expected '}' after method body")
                parser_log.info(f"Completed body of method '{name}'")

            func_decl = FunctionDeclaration(
                name=name,
                params=params,
                body=body,
                return_type=return_type,
                is_static=is_static,
                is_abstract=is_abstract,
                is_final=is_final
            )
            func_decl.compiler_flags = list(compiler_flags or [])
            return func_decl

        # Field declaration or other statements
        else:
            # Try to parse as a simple statement (e.g., assignment, expression, etc.)
            parser_log.info("Parsing class member as simple statement")
            stmt = self.parse_simple_statement()
            return stmt


    ##########################################
    ############### FUNCTIONS ################
    ##########################################

    # Any methods handling function declarations, arguments, parameters etc.

    def parse_method_signature(self) -> MethodSignature:
        """Parse a method signature."""
        name = self.consume(TokenType.IDENTIFIER, "Expected method name").value

        parser_log.info(f"Parsing method signature '{name}'")

        # Parameters
        self.consume(TokenType.LPAREN, "Expected '(' after method name")
        params = self.parse_parameters()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        # Return type
        return_type = None
        if self.match(TokenType.ARROW):
            # Accept both IDENTIFIER and special types like None
            if self.check(TokenType.IDENTIFIER):
                return_type = self.advance().value
            elif self.check(TokenType.NONE):
                return_type = self.advance().value
            else:
                self.raise_parser_error(f"Expected return type at line {self.peek().line}")

            parser_log.info(f"Method '{name}' has return type: {return_type}")

        # Consume semicolon if present
        self.match(TokenType.SEMICOLON)

        return MethodSignature(name, params, return_type)


    def parse_parameters(self) -> List[Parameter]:
        """Parse function parameters."""
        params = []

        if not self.check(TokenType.RPAREN):
            param = self.parse_parameter()
            params.append(param)
            parser_log.info(f"Added parameter: {param.name}" + (f" with type {param.type_annotation}" if param.type_annotation else ""))

            while self.match(TokenType.COMMA):
                param = self.parse_parameter()
                params.append(param)
                parser_log.info(f"Added parameter: {param.name}" + (f" with type {param.type_annotation}" if param.type_annotation else ""))

        parser_log.info(f"Parsed {len(params)} parameters")
        return params


    def parse_parameter(self) -> Parameter:
        """Parse a single parameter."""
        name = self.consume(TokenType.IDENTIFIER, "Expected parameter name").value

        # Type annotation
        type_annotation = None
        if self.match(TokenType.COLON):
            # Accept both IDENTIFIER and special types like None
            if self.check(TokenType.IDENTIFIER):
                type_annotation = self.advance().value
            elif self.check(TokenType.NONE):
                type_annotation = self.advance().value
            else:
                self.raise_parser_error(f"Expected type annotation at line {self.peek().line}")

        # Default value
        default = None
        if self.match(TokenType.ASSIGN):
            # TODO: Parse expression
            default = self.advance().value
            parser_log.info(f"Parameter {name} has default value: {default}")

        return Parameter(name, type_annotation, default)


    def parse_method_body(self):
        """Parse method body statements."""
        body = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            # Skip newlines
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            # Skip comments
            if self.check(TokenType.COMMENT):
                self.advance()
                continue

            # For now, just parse simple expression statements
            parser_log.info("Parsing statement in method body")
            stmt = self.parse_simple_statement()
            if stmt:
                parser_log.info(f"Added statement to method body: {type(stmt).__name__}")
                body.append(stmt)

        parser_log.info(f"Method body contains {len(body)} statements")
        return body


    def parse_function(self, compiler_flags: Optional[List[str]] = None):
        """Parse function declaration."""
        from spice.parser.ast_nodes import FunctionDeclaration

        name = self.consume(TokenType.IDENTIFIER, "Expected function name").value
        parser_log.info(f"Parsing function '{name}'")

        # Parameters
        self.consume(TokenType.LPAREN, "Expected '(' after function name")
        params = self.parse_parameters()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")

        # Return type
        return_type = None
        if self.match(TokenType.COLON):
            # Handle `: return_type` syntax
            if self.check(TokenType.IDENTIFIER):
                return_type = self.advance().value
            elif self.check(TokenType.NONE):
                return_type = self.advance().value
            else:
                self.raise_parser_error(f"Expected return type after ':' at line {self.peek().line}")
            parser_log.info(f"Function '{name}' has return type: {return_type}")
        elif self.match(TokenType.ARROW):
            # Handle `-> return_type` syntax
            if self.check(TokenType.IDENTIFIER):
                return_type = self.advance().value
            elif self.check(TokenType.NONE):
                return_type = self.advance().value
            else:
                self.raise_parser_error(f"Expected return type after '->' at line {self.peek().line}")
            parser_log.info(f"Function '{name}' has return type: {return_type}")

        # Function body
        self.consume(TokenType.LBRACE, "Expected '{' after function signature")
        parser_log.info(f"Parsing body of function '{name}'")
        body = self.parse_method_body()
        self.consume(TokenType.RBRACE, "Expected '}' after function body")
        parser_log.info(f"Completed body of function '{name}'")

        func_decl = FunctionDeclaration(
            name=name,
            params=params,
            body=body,
            return_type=return_type,
            is_static=False,
            is_abstract=False,
            is_final=False
        )
        func_decl.compiler_flags = list(compiler_flags or [])
        return func_decl


    ##########################################
    ############## EXPRESSIONS ###############
    ##########################################

    def parse_statement(self, context="general"):
        """Parse a statement."""
        parser_log.info(f"Parsing statement at token: {self.peek().type.name}")

        # Skip comments
        if self.check(TokenType.COMMENT):
            self.advance()
            return None

        compiler_flags = self._consume_compiler_flags(
            [TokenType.ABSTRACT, TokenType.FINAL, TokenType.CLASS, TokenType.DEF]
        )

        # Interface declaration
        if self.match(TokenType.INTERFACE):
            if compiler_flags:
                self.raise_parser_error("Compiler flags are only supported for classes and functions")
            parser_log.info("Parsing interface declaration")
            return self.parse_interface()

        # Class declaration with modifiers (final can also start a variable declaration)
        is_final_class = False
        if self.check(TokenType.FINAL):
            next_type = self._peek_next_non_newline_type(self.current + 1)
            is_final_class = next_type == TokenType.CLASS

        if self.check(TokenType.ABSTRACT, TokenType.CLASS) or is_final_class:
            parser_log.info("Parsing class declaration")
            return self.parse_class(compiler_flags=compiler_flags)

        # Function declaration
        if self.match(TokenType.DEF):
            parser_log.info("Parsing function declaration")
            return self.parse_function(compiler_flags=compiler_flags)

        if compiler_flags:
            self.raise_parser_error("Compiler flags must precede a class or function declaration")

        # Final declaration (top-level)
        if self.match(TokenType.FINAL):
            parser_log.info("Parsing top-level final declaration")
            return self.parse_final_declaration()

        # Return statement at top-level (not recommended, but parseable)
        if self.match(TokenType.RETURN):
            parser_log.info("Parsing return statement at top-level")
            value = None
            if not self.check(TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE):
                value = self.parse_expression(context)
            has_semicolon = self.match(TokenType.SEMICOLON)
            parser_log.info(f"Parsed return statement with value: {value}")
            from spice.parser.ast_nodes import ReturnStatement
            return ReturnStatement(value=value, has_semicolon=has_semicolon)

        # Raise statement
        if self.match(TokenType.RAISE):
            parser_log.info("Parsing raise statement")
            return self.parse_raise_statement()

        # Import statement
        if self.check(TokenType.IMPORT, TokenType.FROM):
            parser_log.info("Parsing import statement")
            return self.parse_import_statement()

        if self._looks_like_typed_declaration():
            parser_log.info("Parsing typed declaration at top level")
            return self.parse_typed_declaration()

        # Expression statement
        parser_log.info("Parsing expression statement")
        return self.parse_expression_statement()

    def parse_expression(self, context="general") -> Optional[Expression]:
        """Parse an expression using the clean expression parser."""
        parser_log.info(f"Parsing expression at token: {self.peek().type.name}")

        expr = self.expr_parser.parse_expression()

        if expr is None:
            self.raise_parser_error(f"Could not parse expression at line {self.peek().line}")

        return expr

    def parse_expression_statement(self, context="general") -> Optional[ExpressionStatement]:
        """Parse expression statement."""
        parser_log.info("Parsing expression statement")

        expr = self.parse_expression(context=context)

        if expr is None:
            return None

        has_semicolon = self.match(TokenType.SEMICOLON)

        if has_semicolon:
            parser_log.info("Expression has semicolon")

        return ExpressionStatement(expression=expr, has_semicolon=has_semicolon)

    def parse_simple_statement(self):
        """Parse a simple statement (simplified version)."""
        # Pass statement
        if self.match(TokenType.PASS):
            has_semicolon = self.match(TokenType.SEMICOLON)
            parser_log.info("Parsed pass statement")
            return PassStatement(has_semicolon=has_semicolon)

        # Final declaration
        if self.match(TokenType.FINAL):
            return self.parse_final_declaration()

        # Typed variable declaration
        if self._looks_like_typed_declaration():
            return self.parse_typed_declaration()

        # Return statement
        if self.match(TokenType.RETURN):
            parser_log.info("Parsing return statement")
            value = None
            if not self.check(TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE):
                value = self.parse_expression()
            has_semicolon = self.match(TokenType.SEMICOLON)
            return ReturnStatement(value=value, has_semicolon=has_semicolon)

        # If statement
        if self.match(TokenType.IF):
            return self.parse_if_statement()

        # While statement
        if self.match(TokenType.WHILE):
            return self.parse_while_statement()

        # For statement
        if self.match(TokenType.FOR):
            return self.parse_for_statement()

        # Switch statement
        if self.match(TokenType.SWITCH):
            return self.parse_switch_statement()

        # Raise statement
        if self.match(TokenType.RAISE):
            return self.parse_raise_statement()

        # Import statement
        if self.check(TokenType.IMPORT, TokenType.FROM):
            return self.parse_import_statement()

        # Expression statement
        expr = self.parse_expression()
        if expr:
            has_semicolon = self.match(TokenType.SEMICOLON)
            return ExpressionStatement(expression=expr, has_semicolon=has_semicolon)

        return None

    def parse_typed_declaration(self) -> ExpressionStatement:
        """Parse a typed variable declaration."""
        parser_log.info("Parsing typed variable declaration")
        identifier_token = self.consume(TokenType.IDENTIFIER, "Expected identifier in typed declaration")
        target = IdentifierExpression(name=identifier_token.value)
        self.consume(TokenType.COLON, "Expected ':' in typed declaration")
        type_annotation = self._parse_type_annotation_string()
        if not type_annotation:
            self.raise_parser_error("Expected type annotation after ':'")

        value = None
        if self.match(TokenType.ASSIGN):
            value = self.parse_expression()
            if value is None:
                self.raise_parser_error("Expected value after '=' in typed declaration")

        has_semicolon = self.match(TokenType.SEMICOLON)
        annotated = AnnotatedAssignment(target=target, type_annotation=type_annotation, value=value)
        return ExpressionStatement(expression=annotated, has_semicolon=has_semicolon)

    def parse_final_declaration(self) -> FinalDeclaration:
        """Parse final variable declaration."""
        parser_log.info("Parsing final variable declaration")

        # Parse the identifier
        if not self.check(TokenType.IDENTIFIER):
            self.raise_parser_error("Expected identifier after 'final'")

        identifier = self.parse_expression()

        # Optional type annotation
        type_annotation = None
        if self.match(TokenType.COLON):
            type_annotation = self._parse_type_annotation_string()

        # Must have assignment for final variables
        if not self.match(TokenType.ASSIGN):
            self.raise_parser_error("Final variables must be initialized")

        # Parse the value
        value = self.parse_expression()
        if value is None:
            self.raise_parser_error("Expected value in final declaration")

        # Consume optional semicolon
        self.match(TokenType.SEMICOLON)

        return FinalDeclaration(target=identifier, value=value, type_annotation=type_annotation)

    def parse_if_statement(self) -> IfStatement:
        """Parse if statement with clean condition parsing."""
        parser_log.info("Parsing if statement")

        # Parse condition
        condition = self.parse_expression(context="condition")
        if condition is None:
            self.raise_parser_error("Expected condition after 'if'")

        # Validate it's not an assignment
        from spice.parser.ast_nodes import AssignmentExpression
        if isinstance(condition, AssignmentExpression):
            self.raise_parser_error("Assignment expressions are not allowed as 'if' conditions")

        self.consume(TokenType.LBRACE, "Expected '{' after if condition")
        then_body = self.parse_block()

        else_body = []
        if self.match(TokenType.ELSE):
            if self.check(TokenType.IF):
                # else if - parse as a single statement
                else_body = [self.parse_simple_statement()]
            else:
                self.consume(TokenType.LBRACE, "Expected '{' after 'else'")
                else_body = self.parse_block()

        return IfStatement(condition=condition, then_body=then_body, else_body=else_body)

    def parse_while_statement(self) -> WhileStatement:
        """Parse while statement."""
        parser_log.info("Parsing while statement")

        # Optional parentheses
        has_parens = self.match(TokenType.LPAREN)

        condition = self.parse_expression(context="condition")
        if condition is None:
            self.raise_parser_error("Expected condition after 'while'")

        if has_parens:
            self.consume(TokenType.RPAREN, "Expected ')' after while condition")

        # Validate it's not an assignment
        from spice.parser.ast_nodes import AssignmentExpression
        if isinstance(condition, AssignmentExpression):
            self.raise_parser_error("Assignment expressions are not allowed as 'while' conditions")

        self.consume(TokenType.LBRACE, "Expected '{' after while condition")
        body = self.parse_block()

        return WhileStatement(condition=condition, body=body)

    def parse_for_statement(self) -> ForStatement:
        """Parse for statement."""
        parser_log.info("Parsing for statement")

        # Optional parentheses
        has_parens = self.match(TokenType.LPAREN)

        target = self.parse_expression()
        if target is None:
            self.raise_parser_error("Expected target in for statement")

        if has_parens:
            self.consume(TokenType.RPAREN, "Expected ')' after for header")

        self.consume(TokenType.LBRACE, "Expected '{' after for header")
        body = self.parse_block()

        return ForStatement(target=target, body=body)

    def parse_switch_statement(self) -> SwitchStatement:
        """Parse switch statement."""
        parser_log.info("Parsing switch statement")

        self.consume(TokenType.LPAREN, "Expected '(' after 'switch'")

        expr = self.parse_expression()
        if expr is None:
            self.raise_parser_error("Expected expression after 'switch('")

        self.consume(TokenType.RPAREN, "Expected ')' after switch expression")
        self.consume(TokenType.LBRACE, "Expected '{' after switch header")

        cases = []
        default = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.match(TokenType.CASE):
                case_value = self.parse_expression()
                if case_value is None:
                    self.raise_parser_error("Expected value after 'case'")

                self.consume(TokenType.COLON, "Expected ':' after case value")

                case_body = []
                while not self.check(TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE):
                    if self.match(TokenType.NEWLINE):
                        continue
                    stmt = self.parse_simple_statement()
                    if stmt:
                        case_body.append(stmt)

                cases.append(CaseClause(value=case_value, body=case_body))

            elif self.match(TokenType.DEFAULT):
                self.consume(TokenType.COLON, "Expected ':' after 'default'")

                while not self.check(TokenType.CASE, TokenType.RBRACE):
                    if self.match(TokenType.NEWLINE):
                        continue
                    stmt = self.parse_simple_statement()
                    if stmt:
                        default.append(stmt)
            else:
                # Skip unknown tokens
                self.advance()

        self.consume(TokenType.RBRACE, "Expected '}' after switch block")

        return SwitchStatement(expression=expr, cases=cases, default=default)

    def parse_raise_statement(self) -> RaiseStatement:
        parser_log.info("Parsing raise statement")

        exception = None

        # Check if there's an exception expression
        if not self.check(TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE):
            exception = self.parse_expression()
            if exception:
                parser_log.info(f"Parsed raise exception: {type(exception).__name__}")

        has_semicolon = self.match(TokenType.SEMICOLON)

        parser_log.info(f"Completed raise statement (has_semicolon: {has_semicolon})")

        return RaiseStatement(exception=exception, has_semicolon=has_semicolon)


    def parse_import_statement(self) -> ImportStatement:
        """Parse import statement."""
        parser_log.info("Parsing import statement")

        # Check for 'from module import names' syntax
        if self.match(TokenType.FROM):
            # from module import name1, name2, ...
            module = self.consume(TokenType.IDENTIFIER, "Expected module name after 'from'").value
            parser_log.info(f"Parsing 'from {module} import ...'")

            # Build module path for dotted imports
            while self.match(TokenType.DOT):
                submodule = self.consume(TokenType.IDENTIFIER, "Expected module name after '.'").value
                module += f".{submodule}"
                parser_log.info(f"Extended module path: {module}")

            self.consume(TokenType.IMPORT, "Expected 'import' after module name")

            # Parse imported names
            names = []
            aliases = []

            # First name
            name = self.consume(TokenType.IDENTIFIER, "Expected name to import").value
            names.append(name)

            alias = None
            if self.match(TokenType.AS):
                alias = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'").value
                parser_log.info(f"Import alias: {name} as {alias}")
            aliases.append(alias)

            # Additional names
            while self.match(TokenType.COMMA):
                name = self.consume(TokenType.IDENTIFIER, "Expected name to import").value
                names.append(name)

                alias = None
                if self.match(TokenType.AS):
                    alias = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'").value
                    parser_log.info(f"Import alias: {name} as {alias}")
                aliases.append(alias)

            has_semicolon = self.match(TokenType.SEMICOLON)

            parser_log.info(f"Parsed from import: from {module} import {', '.join(names)}")

            return ImportStatement(
                module=module,
                names=names,
                aliases=aliases,
                is_from_import=True,
                has_semicolon=has_semicolon
            )

        elif self.match(TokenType.IMPORT):
            # import module
            module = self.consume(TokenType.IDENTIFIER, "Expected module name after 'import'").value
            parser_log.info(f"Parsing 'import {module}'")

            # Build module path for dotted imports
            while self.match(TokenType.DOT):
                submodule = self.consume(TokenType.IDENTIFIER, "Expected module name after '.'").value
                module += f".{submodule}"
                parser_log.info(f"Extended module path: {module}")

            # Optional alias
            alias = None
            if self.match(TokenType.AS):
                alias = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'").value
                parser_log.info(f"Import alias: {module} as {alias}")

            has_semicolon = self.match(TokenType.SEMICOLON)

            parser_log.info(f"Parsed import: import {module}" + (f" as {alias}" if alias else ""))

            return ImportStatement(
                module=module,
                names=[],
                aliases=[alias] if alias else [],
                is_from_import=False,
                has_semicolon=has_semicolon
            )

        else:
            self.raise_parser_error("Expected 'import' or 'from' keyword")


    def parse_block(self) -> List[Any]:
        """Parse a block of statements enclosed in braces."""
        body = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.match(TokenType.NEWLINE):
                continue
            if self.match(TokenType.COMMENT):
                continue

            stmt = self.parse_simple_statement()
            if stmt:
                body.append(stmt)

        self.consume(TokenType.RBRACE, "Expected '}' after block")
        return body
