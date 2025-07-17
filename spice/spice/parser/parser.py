"""Parser for Spy language."""

from typing import List, Optional, Any
from lexer import Token, TokenType
from parser.ast_nodes import (
    Module, InterfaceDeclaration, MethodSignature, Parameter,
    ExpressionStatement, PassStatement, Expression, ReturnStatement,
    IfStatement, ForStatement, WhileStatement, SwitchStatement, CaseClause,
    RaiseStatement, ImportStatement
)
from errors import SpiceError


class ParseError(SpiceError):
    """Parser error."""
    pass


class Parser:
    """Parse Spy tokens into an AST."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tokens: List[Token] = []
        self.current = 0

        # Extensions
        from parser.expression_parser import ExpressionParser
        self.expr_parser = ExpressionParser(self)

    def match(self, *types: TokenType, advance_at_newline: bool = False) -> bool:
        """Check if current token matches any of the given types."""
        if advance_at_newline and self.check(TokenType.NEWLINE):
            if self.verbose:
                print("Skipped NewLine token on match.")
            self.advance()

        for token_type in types:
            if self.check(token_type):
                if self.verbose:
                    print(f"Matched token {self.peek()} for: {', '.join([t.name for t in types])}")
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
            raise ParseError("Cannot backtrack beyond start of tokens")

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
            if self.verbose:
                print(f"Consumed token: {token.type.name}" +
                      (f" '{token.value}'" if token.value is not None else ""))
            return token

        if self.verbose:
            print(f"ERROR: {message} - found {self.peek().type.name} instead")
        raise ParseError(f"{message} at line {self.peek().line}")

    def get_tokens(self, start: int = -1, size: Optional[int] = None) -> List[Token]:
        """Get a slice of tokens from start to end."""
        if start < 0:
            start = self.current
        if size is None:
            size = len(self.tokens) - self.current
        return self.tokens[start:(start + size)]


    def parse(self, tokens: List[Token]) -> Module:
        """Parse tokens into an AST."""
        self.tokens = tokens
        self.current = 0

        if self.verbose:
            print(f"Starting parsing with {len(tokens)} tokens")

        statements = []
        while not self.is_at_end():
            # Skip newlines at module level
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue

            stmt = self.parse_statement()
            if stmt:
                if self.verbose:
                    print(f"Added statement: {type(stmt).__name__}")
                statements.append(stmt)

        if self.verbose:
            print(f"Finished parsing: Generated AST with {len(statements)} top-level statements")
        return Module(body=statements)


    ##########################################
    ################# UTILS ##################
    ##########################################

    # Pretty empty atm :p

    ##########################################
    ################ CLASSES #################
    ##########################################

    # Any methods handling class declarations, interfaces, methods, etc.

    def parse_interface(self) -> InterfaceDeclaration:
        """Parse interface declaration."""
        name = self.consume(TokenType.IDENTIFIER, "Expected interface name").value

        if self.verbose:
            print(f"Parsing interface '{name}'")

        # Optional base interfaces
        bases = []
        if self.match(TokenType.EXTENDS):
            base = self.consume(TokenType.IDENTIFIER, "Expected base interface").value
            bases.append(base)
            if self.verbose:
                print(f"Added base interface: {base}")

            while self.match(TokenType.COMMA):
                base = self.consume(TokenType.IDENTIFIER, "Expected base interface").value
                bases.append(base)
                if self.verbose:
                    print(f"Added base interface: {base}")

        # Interface body
        self.consume(TokenType.LBRACE, "Expected '{' after interface declaration")
        if self.verbose:
            print("Parsing C-style interface body")

        methods = self.parse_interface_body()

        if self.verbose:
            print(f"Completed interface '{name}' with {len(methods)} methods")

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
                if self.verbose:
                    print(f"Added method signature: {method.name}")
            else:
                raise ParseError(f"Expected method signature, got {self.peek()}")

        self.consume(TokenType.RBRACE, "Expected '}' after interface body")
        return methods


    def parse_class(self):
        """Parse class declaration."""
        from parser.ast_nodes import ClassDeclaration

        # Handle modifiers
        is_abstract = False
        is_final = False

        if self.match(TokenType.ABSTRACT):
            is_abstract = True
            if self.verbose:
                print("Class is abstract")
        elif self.match(TokenType.FINAL):
            is_final = True
            if self.verbose:
                print("Class is final")

        # Consume 'class' keyword
        self.consume(TokenType.CLASS, "Expected 'class' keyword")

        # Class name
        name = self.consume(TokenType.IDENTIFIER, "Expected class name").value
        if self.verbose:
            print(f"Parsing class '{name}'")

        # Optional base classes and interfaces
        bases = []  # For extended classes
        interfaces = []  # For implemented interfaces

        if self.match(TokenType.LPAREN):
            if self.verbose:
                print("Parsing Python-style inheritance")
            # Python-style: class Dog(Animal)
            if not self.check(TokenType.RPAREN):
                base = self.consume(TokenType.IDENTIFIER, "Expected base class").value
                bases.append(base)
                if self.verbose:
                    print(f"Added base class: {base}")
                while self.match(TokenType.COMMA):
                    base = self.consume(TokenType.IDENTIFIER, "Expected base class").value
                    bases.append(base)
                    if self.verbose:
                        print(f"Added base class: {base}")
            self.consume(TokenType.RPAREN, "Expected ')' after base classes")
        elif self.match(TokenType.EXTENDS):
            if self.verbose:
                print("Parsing Java-style inheritance")
            # Java-style: class Dog extends Animal
            base = self.consume(TokenType.IDENTIFIER, "Expected base class").value
            bases.append(base)
            if self.verbose:
                print(f"Added base class: {base}")

        # Handle implements keyword for interfaces
        if self.match(TokenType.IMPLEMENTS):
            if self.verbose:
                print("Parsing implemented interfaces")
            # implements Interface1, Interface2, ...
            interface = self.consume(TokenType.IDENTIFIER, "Expected interface name").value
            interfaces.append(interface)
            if self.verbose:
                print(f"Added implemented interface: {interface}")
            while self.match(TokenType.COMMA):
                interface = self.consume(TokenType.IDENTIFIER, "Expected interface name").value
                interfaces.append(interface)
                if self.verbose:
                    print(f"Added implemented interface: {interface}")

        # Class body
        self.consume(TokenType.LBRACE, "Expected '{' after class declaration")

        # Parse class body
        if self.verbose:
            print("Parsing class body")
        body = self.parse_class_body()

        self.consume(TokenType.RBRACE, "Expected '}' after class body")

        if self.verbose:
            print(f"Completed class '{name}' with {len(body)} members")

        return ClassDeclaration(
            name=name,
            body=body,
            bases=bases,
            interfaces=interfaces,
            is_abstract=is_abstract,
            is_final=is_final
        )


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
            if self.verbose:
                print("Parsing class member")
            stmt = self.parse_class_member()
            if stmt:
                if self.verbose:
                    print(f"Added class member: {type(stmt).__name__}")
                body.append(stmt)

        return body


    def parse_class_member(self, is_interface: bool = False):
        """Parse a class member (method or field)."""
        from parser.ast_nodes import FunctionDeclaration

        # Check for static modifier
        is_static = False
        is_abstract = False
        is_final = False

        if self.match(TokenType.STATIC):
            is_static = True
            if self.verbose:
                print("Method is static")
        elif self.match(TokenType.ABSTRACT):
            is_abstract = True
            if self.verbose:
                print("Method is abstract")
        elif self.match(TokenType.FINAL):
            is_final = True
            if self.verbose:
                print("Method is final")

        # Method declaration
        if self.match(TokenType.DEF):
            name = self.consume(TokenType.IDENTIFIER, "Expected method name").value
            if self.verbose:
                print(f"Parsing method '{name}'")

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
                    raise ParseError(f"Expected return type after '->' at line {self.peek().line}")
                if self.verbose:
                    print(f"Method '{name}' has return type: {return_type}")

            # Method body - abstract methods don't have bodies
            body = []
            if is_abstract or is_interface:
                if self.verbose:
                    print(f"Registered abstract/interface method '{name}'")
                self.consume(TokenType.SEMICOLON, "Expected ';' after abstract method signature")
                body.append(PassStatement(has_semicolon=True))
                # Abstract methods end here - no body expected
            else:
                # Concrete methods need a body
                self.consume(TokenType.LBRACE, "Expected '{' after method signature")
                if self.verbose:
                    print(f"Parsing body of method '{name}'")
                body = self.parse_method_body()
                self.consume(TokenType.RBRACE, "Expected '}' after method body")
                if self.verbose:
                    print(f"Completed body of method '{name}'")

            return FunctionDeclaration(
                name=name,
                params=params,
                body=body,
                return_type=return_type,
                is_static=is_static,
                is_abstract=is_abstract,
                is_final=is_final
            )

        # Field declaration or other statements
        else:
            # Try to parse as a simple statement (e.g., assignment, expression, etc.)
            if self.verbose:
                print("Parsing class member as simple statement")
            stmt = self.parse_simple_statement()
            return stmt


    ##########################################
    ############### FUNCTIONS ################
    ##########################################

    # Any methods handling function declarations, arguments, parameters etc.

    def parse_method_signature(self) -> MethodSignature:
        """Parse a method signature."""
        name = self.consume(TokenType.IDENTIFIER, "Expected method name").value

        if self.verbose:
            print(f"Parsing method signature '{name}'")

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
                raise ParseError(f"Expected return type at line {self.peek().line}")

            if self.verbose:
                print(f"Method '{name}' has return type: {return_type}")

        # Consume semicolon if present
        self.match(TokenType.SEMICOLON)

        return MethodSignature(name, params, return_type)


    def parse_parameters(self) -> List[Parameter]:
        """Parse function parameters."""
        params = []

        if not self.check(TokenType.RPAREN):
            param = self.parse_parameter()
            params.append(param)
            if self.verbose:
                print(f"Added parameter: {param.name}" +
                    (f" with type {param.type_annotation}" if param.type_annotation else ""))

            while self.match(TokenType.COMMA):
                param = self.parse_parameter()
                params.append(param)
                if self.verbose:
                    print(f"Added parameter: {param.name}" +
                        (f" with type {param.type_annotation}" if param.type_annotation else ""))

        if self.verbose:
            print(f"Parsed {len(params)} parameters")
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
                raise ParseError(f"Expected type annotation at line {self.peek().line}")

        # Default value
        default = None
        if self.match(TokenType.ASSIGN):
            # TODO: Parse expression
            default = self.advance().value
            if self.verbose:
                print(f"Parameter {name} has default value: {default}")

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
            if self.verbose:
                print("Parsing statement in method body")
            stmt = self.parse_simple_statement()
            if stmt:
                if self.verbose:
                    print(f"Added statement to method body: {type(stmt).__name__}")
                body.append(stmt)

        if self.verbose:
            print(f"Method body contains {len(body)} statements")
        return body


    def parse_function(self):
        """Parse function declaration."""
        from parser.ast_nodes import FunctionDeclaration

        name = self.consume(TokenType.IDENTIFIER, "Expected function name").value
        if self.verbose:
            print(f"Parsing function '{name}'")

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
                raise ParseError(f"Expected return type after ':' at line {self.peek().line}")
            if self.verbose:
                print(f"Function '{name}' has return type: {return_type}")
        elif self.match(TokenType.ARROW):
            # Handle `-> return_type` syntax
            if self.check(TokenType.IDENTIFIER):
                return_type = self.advance().value
            elif self.check(TokenType.NONE):
                return_type = self.advance().value
            else:
                raise ParseError(f"Expected return type after '->' at line {self.peek().line}")
            if self.verbose:
                print(f"Function '{name}' has return type: {return_type}")

        # Function body
        self.consume(TokenType.LBRACE, "Expected '{' after function signature")
        if self.verbose:
            print(f"Parsing body of function '{name}'")
        body = self.parse_method_body()
        self.consume(TokenType.RBRACE, "Expected '}' after function body")
        if self.verbose:
            print(f"Completed body of function '{name}'")

        return FunctionDeclaration(
            name=name,
            params=params,
            body=body,
            return_type=return_type,
            is_static=False,
            is_abstract=False,
            is_final=False
        )


    ##########################################
    ############## EXPRESSIONS ###############
    ##########################################

    def parse_statement(self, context="general"):
        """Parse a statement."""
        if self.verbose:
            print(f"Parsing statement at token: {self.peek().type.name}")

        # Skip comments
        if self.check(TokenType.COMMENT):
            self.advance()
            return None

        # Interface declaration
        if self.match(TokenType.INTERFACE):
            if self.verbose:
                print("Parsing interface declaration")
            return self.parse_interface()

        # Class declaration with modifiers
        if self.check(TokenType.ABSTRACT, TokenType.FINAL, TokenType.CLASS):
            if self.verbose:
                print("Parsing class declaration")
            return self.parse_class()

        # Function declaration
        if self.match(TokenType.DEF):
            if self.verbose:
                print("Parsing function declaration")
            return self.parse_function()

        # Return statement at top-level (not recommended, but parseable)
        if self.match(TokenType.RETURN):
            if self.verbose:
                print("Parsing return statement at top-level")
            value = None
            if not self.check(TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE):
                value = self.parse_expression(context)
            has_semicolon = self.match(TokenType.SEMICOLON)
            if self.verbose:
                print(f"Parsed return statement with value: {value}")
            from parser.ast_nodes import ReturnStatement
            return ReturnStatement(value=value, has_semicolon=has_semicolon)

        # Raise statement
        if self.match(TokenType.RAISE):
            if self.verbose:
                print("Parsing raise statement")
            return self.parse_raise_statement()

        # Import statement
        if self.check(TokenType.IMPORT, TokenType.FROM):
            if self.verbose:
                print("Parsing import statement")
            return self.parse_import_statement()

        # Expression statement
        if self.verbose:
            print("Parsing expression statement")
        return self.parse_expression_statement()

    def parse_expression(self, context="general") -> Optional[Expression]:
        """Parse an expression using the clean expression parser."""
        if self.verbose:
            print(f"Parsing expression at token: {self.peek().type.name}")

        expr = self.expr_parser.parse_expression()

        if expr is None and self.verbose:
            raise ParseError(f"Could not parse expression at line {self.peek().line}")

        return expr

    def parse_expression_statement(self, context="general") -> Optional[ExpressionStatement]:
        """Parse expression statement."""
        if self.verbose:
            print("Parsing expression statement")

        expr = self.parse_expression(context=context)

        if expr is None:
            return None

        has_semicolon = self.match(TokenType.SEMICOLON)

        if self.verbose and has_semicolon:
            print("Expression has semicolon")

        return ExpressionStatement(expression=expr, has_semicolon=has_semicolon)

    def parse_simple_statement(self):
        """Parse a simple statement (simplified version)."""
        # Pass statement
        if self.match(TokenType.PASS):
            has_semicolon = self.match(TokenType.SEMICOLON)
            if self.verbose:
                print("Parsed pass statement")
            return PassStatement(has_semicolon=has_semicolon)

        # Return statement
        if self.match(TokenType.RETURN):
            if self.verbose:
                print("Parsing return statement")
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

    def parse_if_statement(self) -> IfStatement:
        """Parse if statement with clean condition parsing."""
        if self.verbose:
            print("Parsing if statement")

        # Parse condition
        condition = self.parse_expression(context="condition")
        if condition is None:
            raise ParseError("Expected condition after 'if'")

        # Validate it's not an assignment
        from parser.ast_nodes import AssignmentExpression
        if isinstance(condition, AssignmentExpression):
            raise ParseError("Assignment expressions are not allowed as 'if' conditions")

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
        if self.verbose:
            print("Parsing while statement")

        # Optional parentheses
        has_parens = self.match(TokenType.LPAREN)

        condition = self.parse_expression(context="condition")
        if condition is None:
            raise ParseError("Expected condition after 'while'")

        if has_parens:
            self.consume(TokenType.RPAREN, "Expected ')' after while condition")

        # Validate it's not an assignment
        from parser.ast_nodes import AssignmentExpression
        if isinstance(condition, AssignmentExpression):
            raise ParseError("Assignment expressions are not allowed as 'while' conditions")

        self.consume(TokenType.LBRACE, "Expected '{' after while condition")
        body = self.parse_block()

        return WhileStatement(condition=condition, body=body)

    def parse_for_statement(self) -> ForStatement:
        """Parse for statement."""
        if self.verbose:
            print("Parsing for statement")

        # Optional parentheses
        has_parens = self.match(TokenType.LPAREN)

        target = self.parse_expression()
        if target is None:
            raise ParseError("Expected target in for statement")

        if has_parens:
            self.consume(TokenType.RPAREN, "Expected ')' after for header")

        self.consume(TokenType.LBRACE, "Expected '{' after for header")
        body = self.parse_block()

        return ForStatement(target=target, body=body)

    def parse_switch_statement(self) -> SwitchStatement:
        """Parse switch statement."""
        if self.verbose:
            print("Parsing switch statement")

        self.consume(TokenType.LPAREN, "Expected '(' after 'switch'")

        expr = self.parse_expression()
        if expr is None:
            raise ParseError("Expected expression after 'switch('")

        self.consume(TokenType.RPAREN, "Expected ')' after switch expression")
        self.consume(TokenType.LBRACE, "Expected '{' after switch header")

        cases = []
        default = []

        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.match(TokenType.CASE):
                case_value = self.parse_expression()
                if case_value is None:
                    raise ParseError("Expected value after 'case'")

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
        if self.verbose:
            print("Parsing raise statement")

        exception = None

        # Check if there's an exception expression
        if not self.check(TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE):
            exception = self.parse_expression()
            if self.verbose and exception:
                print(f"Parsed raise exception: {type(exception).__name__}")

        has_semicolon = self.match(TokenType.SEMICOLON)

        if self.verbose:
            print(f"Completed raise statement (has_semicolon: {has_semicolon})")

        return RaiseStatement(exception=exception, has_semicolon=has_semicolon)


    def parse_import_statement(self) -> ImportStatement:
        """Parse import statement."""
        if self.verbose:
            print("Parsing import statement")

        # Check for 'from module import names' syntax
        if self.match(TokenType.FROM):
            # from module import name1, name2, ...
            module = self.consume(TokenType.IDENTIFIER, "Expected module name after 'from'").value
            if self.verbose:
                print(f"Parsing 'from {module} import ...'")

            # Build module path for dotted imports
            while self.match(TokenType.DOT):
                submodule = self.consume(TokenType.IDENTIFIER, "Expected module name after '.'").value
                module += f".{submodule}"
                if self.verbose:
                    print(f"Extended module path: {module}")

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
                if self.verbose:
                    print(f"Import alias: {name} as {alias}")
            aliases.append(alias)

            # Additional names
            while self.match(TokenType.COMMA):
                name = self.consume(TokenType.IDENTIFIER, "Expected name to import").value
                names.append(name)

                alias = None
                if self.match(TokenType.AS):
                    alias = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'").value
                    if self.verbose:
                        print(f"Import alias: {name} as {alias}")
                aliases.append(alias)

            has_semicolon = self.match(TokenType.SEMICOLON)

            if self.verbose:
                print(f"Parsed from import: from {module} import {', '.join(names)}")

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
            if self.verbose:
                print(f"Parsing 'import {module}'")

            # Build module path for dotted imports
            while self.match(TokenType.DOT):
                submodule = self.consume(TokenType.IDENTIFIER, "Expected module name after '.'").value
                module += f".{submodule}"
                if self.verbose:
                    print(f"Extended module path: {module}")

            # Optional alias
            alias = None
            if self.match(TokenType.AS):
                alias = self.consume(TokenType.IDENTIFIER, "Expected alias after 'as'").value
                if self.verbose:
                    print(f"Import alias: {module} as {alias}")

            has_semicolon = self.match(TokenType.SEMICOLON)

            if self.verbose:
                print(f"Parsed import: import {module}" + (f" as {alias}" if alias else ""))

            return ImportStatement(
                module=module,
                names=[],
                aliases=[alias] if alias else [],
                is_from_import=False,
                has_semicolon=has_semicolon
            )

        else:
            raise ParseError("Expected 'import' or 'from' keyword")


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
