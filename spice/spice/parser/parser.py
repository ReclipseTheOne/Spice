"""Parser for Spy language."""

from typing import List, Optional
from lexer import Token, TokenType
from lexer.follow_set import check
from parser.ast_nodes import (
    Module, InterfaceDeclaration, MethodSignature, Parameter, 
    ClassDeclaration, FunctionDeclaration, ExpressionStatement, 
    PassStatement, Expression, AssignmentExpression, IdentifierExpression, 
    AttributeExpression, LiteralExpression, CallExpression, ReturnStatement, 
    IfStatement, ForStatement, WhileStatement, SwitchStatement, CaseClause, LogicalExpression,
    UnaryExpression, ArgumentExpression
)
from errors import SpiceError
import copy


class ParseError(SpiceError):
    """Parser error."""
    pass


class Parser:
    """Parse Spy tokens into an AST."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.tokens: List[Token] = []
        self.current = 0

    # Helper methods
    def match(self, *types: TokenType) -> bool:
        """Check if current token matches any of the given types."""
        for token_type in types:
            if self.check(token_type):
                if self.verbose:
                    print(f"Matched token: {token_type.name}")
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


    # Parsing
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
        if self.match(TokenType.LPAREN):
            if not self.check(TokenType.RPAREN):
                base = self.consume(TokenType.IDENTIFIER, "Expected base interface").value
                bases.append(base)
                if self.verbose:
                    print(f"Added base interface: {base}")
                    
                while self.match(TokenType.COMMA):
                    base = self.consume(TokenType.IDENTIFIER, "Expected base interface").value
                    bases.append(base)
                    if self.verbose:
                        print(f"Added base interface: {base}")
            self.consume(TokenType.RPAREN, "Expected ')' after base interfaces")

        # Interface body
        if self.match(TokenType.LBRACE):
            if self.verbose:
                print("Parsing C-style interface body")
            # C-style block
            methods = self.parse_interface_body_braces()
        else:
            if self.verbose:
                print("Parsing Python-style interface body")
            # Python-style block
            self.consume(TokenType.COLON, "Expected ':' after interface declaration")
            self.consume(TokenType.NEWLINE, "Expected newline after ':'")
            methods = self.parse_interface_body_indent()

        if self.verbose:
            print(f"Completed interface '{name}' with {len(methods)} methods")

        return InterfaceDeclaration(name, methods, bases if bases else [])


    def parse_interface_body_braces(self) -> List[MethodSignature]:
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


    def parse_class_member(self):
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
                else:
                    raise ParseError(f"Expected return type after '->' at line {self.peek().line}")
                if self.verbose:
                    print(f"Method '{name}' has return type: {return_type}")
            
            # Method body - abstract methods don't have bodies
            body = None
            if is_abstract:
                if self.verbose:
                    print(f"Abstract method '{name}' has no body")
                self.consume(TokenType.SEMICOLON, "Expected ';' after abstract method signature")
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


    def parse_interface_body_indent(self):
        """Parse Python-style interface body."""
        if self.verbose:
            print("TODO: Implement Python-style interface body parsing")
        # TODO: Handle indentation
        return []


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
    

    def parse_argument(self):
        """Parse a single argument in a function call."""
        from parser.ast_nodes import ArgumentExpression
        
        if self.verbose:
            print("Parsing function call argument")
        
        # Handle named arguments
        if self.match(TokenType.IDENTIFIER):
            name = self.previous().value
            if self.match(TokenType.EQUAL):
                value = self.parse_expression(allow_terminators=False)
                if value is None:
                    raise ParseError(f"Expected value for argument '{name}' at line {self.peek().line}")
                return ArgumentExpression(name=name, value=value)
            else:
                # Positional argument
                return ArgumentExpression(name=name, value=None)
        
        # Positional argument without name
        value = self.parse_expression(allow_terminators=False)
        if value is None:
            raise ParseError("Expected expression as function call argument")
        
        return ArgumentExpression(name=None, value=value)


    def parse_method_call(self, expr):
        """Parse a method call on an expression."""
        from parser.ast_nodes import CallExpression
        
        if self.verbose:
            print(f"Parsing method call on expression: {expr}")
        
        arguments = []
        arguments = self.parse_parameters()

        self.consume(TokenType.RPAREN, "Expected ')' after method call arguments")
        return CallExpression(callee=expr, arguments=arguments)
    

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

    def parse_statement(self):
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
                value = self.parse_expression()
            has_semicolon = self.match(TokenType.SEMICOLON)
            if self.verbose:
                print(f"Parsed return statement with value: {value}")
            from parser.ast_nodes import ReturnStatement
            return ReturnStatement(value=value, has_semicolon=has_semicolon)

        # Expression statement
        if self.verbose:
            print("Parsing expression statement")
        return self.parse_expression_statement()
    

    def parse_simple_statement(self):
        """Parse a simple statement (like expressions, pass, or return)."""
        from parser.ast_nodes import ExpressionStatement, PassStatement, ReturnStatement, IfStatement, ForStatement, WhileStatement, SwitchStatement, CaseClause, IdentifierExpression, LogicalExpression
        
        # Pass
        if self.match(TokenType.PASS):
            has_semicolon = self.match(TokenType.SEMICOLON)
            if self.verbose:
                print("Parsed pass statement")
            return PassStatement(has_semicolon=has_semicolon)
        
        # Return
        if self.match(TokenType.RETURN):
            if self.verbose:
                print("Parsing return statement")
            value = None
            if not self.check(TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.RBRACE):
                value = self.parse_expression()
            has_semicolon = self.match(TokenType.SEMICOLON)
            if self.verbose:
                print(f"Parsed return statement with value: {value}")
            return ReturnStatement(value=value, has_semicolon=has_semicolon)
        
        # If
        if self.match(TokenType.IF):
            if self.verbose:
                print("Parsing if statement")
            
            condition = self.parse_logic_expression()
            
            from parser.ast_nodes import AssignmentExpression, UnaryExpression
            if isinstance(condition, AssignmentExpression):
                raise ParseError("Assignment expressions are not allowed as 'if' conditions")
            
            self.consume(TokenType.LBRACE, "Expected '{' after if condition")

            then_body = self.parse_block()
            else_body = []

            if self.match(TokenType.ELSE):
                if self.match(TokenType.IF):
                    else_body = [self.parse_simple_statement()]
                else:
                    self.consume(TokenType.LBRACE, "Expected '{' after 'else'")
                    else_body = self.parse_block()
            return IfStatement(condition=condition, then_body=then_body, else_body=else_body)
        
        # While
        if self.match(TokenType.WHILE):
            if self.verbose:
                print("Parsing while statement")
            if self.match(TokenType.LPAREN):
                condition = self.parse_expression(allow_terminators=False)
                self.consume(TokenType.RPAREN, "Expected ')' after while condition")
            else:
                condition = self.parse_expression(allow_terminators=False)
            if condition is None:
                raise ParseError("Expected condition after 'while'")
            from parser.ast_nodes import AssignmentExpression
            if isinstance(condition, AssignmentExpression):
                raise ParseError("Assignment expressions are not allowed as 'while' conditions")
            self.consume(TokenType.LBRACE, "Expected '{' after while condition")
            body = self.parse_block()
            return WhileStatement(condition=condition, body=body)
        # For
        if self.match(TokenType.FOR):
            if self.verbose:
                print("Parsing for statement")
            if self.match(TokenType.LPAREN):
                target = self.parse_expression(allow_terminators=False)
                self.consume(TokenType.IN, "Expected 'in' in for statement")
                iterable = self.parse_expression(allow_terminators=False)
                self.consume(TokenType.RPAREN, "Expected ')' after for header")
            else:
                target = self.parse_expression(allow_terminators=False)
                self.consume(TokenType.IN, "Expected 'in' in for statement")
                iterable = self.parse_expression(allow_terminators=False)
            if target is None or iterable is None:
                raise ParseError("Expected target and iterable in for statement")
            self.consume(TokenType.LBRACE, "Expected '{' after for header")
            body = self.parse_block()
            return ForStatement(target=target, iterable=iterable, body=body)
        
        # Switch
        if self.match(TokenType.SWITCH):
            if self.verbose:
                print("Parsing switch statement")
            self.consume(TokenType.LPAREN, "Expected '(' after 'switch'")
            expr = self.parse_expression(allow_terminators=False)
            if expr is None:
                raise Exception("Expected expression after 'switch('")
            self.consume(TokenType.RPAREN, "Expected ')' after switch expression")
            self.consume(TokenType.LBRACE, "Expected '{' after switch header")
            cases = []
            default = []
            while not self.check(TokenType.RBRACE) and not self.is_at_end():
                if self.match(TokenType.CASE):
                    case_value = self.parse_expression(allow_terminators=False)
                    if case_value is None:
                        raise Exception("Expected value after 'case'")
                    self.consume(TokenType.COLON, "Expected ':' after case value")
                    case_body = []
                    while not self.check(TokenType.CASE, TokenType.DEFAULT, TokenType.RBRACE) and not self.is_at_end():
                        if self.check(TokenType.NEWLINE):
                            self.advance()
                            continue
                        stmt = self.parse_simple_statement()
                        if stmt:
                            case_body.append(stmt)
                    cases.append(CaseClause(value=case_value, body=case_body))
                elif self.match(TokenType.DEFAULT):
                    self.consume(TokenType.COLON, "Expected ':' after 'default'")
                    default = []
                    while not self.check(TokenType.CASE, TokenType.RBRACE) and not self.is_at_end():
                        if self.check(TokenType.NEWLINE):
                            self.advance()
                            continue
                        stmt = self.parse_simple_statement()
                        if stmt:
                            default.append(stmt)
                else:
                    # Skip unknown tokens
                    self.advance()
            self.consume(TokenType.RBRACE, "Expected '}' after switch block")
            return SwitchStatement(expression=expr, cases=cases, default=default)
        
        # Expression
        if self.verbose:
            print("Parsing expression")
        expr = self.parse_expression()
        has_semicolon = False
        # Accept either semicolon or newline as statement terminator
        if self.match(TokenType.SEMICOLON):
            has_semicolon = True
        elif self.match(TokenType.NEWLINE):
            has_semicolon = False  # NEWLINE is not a semicolon, but is a valid terminator
        if expr:
            if self.verbose:
                print("Parsed expression statement")
            return ExpressionStatement(expression=expr, has_semicolon=has_semicolon)
        
        return None


    def parse_block(self):
        """Parse a block of statements enclosed in braces."""
        body = []
        while not self.check(TokenType.RBRACE) and not self.is_at_end():
            if self.check(TokenType.NEWLINE):
                self.advance()
                continue
            if self.check(TokenType.COMMENT):
                self.advance()
                continue
            stmt = self.parse_simple_statement()
            if stmt:
                body.append(stmt)
        self.consume(TokenType.RBRACE, "Expected '}' after block")
        return body
    

    def parse_expression_statement(self):
        """Parse expression statement."""
        from parser.ast_nodes import ExpressionStatement
        
        # Parse the expression
        if self.verbose:
            print("Parsing expression statement")
        expr = self.parse_expression()
        
        has_semicolon = False
        if self.check(TokenType.SEMICOLON):
            has_semicolon = True
            self.advance()
            if self.verbose:
                print("Expression has semicolon")
        
        if expr:
            return ExpressionStatement(expression=expr, has_semicolon=has_semicolon)
        return None


    def parse_expression(self, allow_terminators=True):
        """Parse an expression (assignment or regular expression)."""
        if self.verbose:
            print("Parsing expression")
        expr = self.parse_assignment(allow_terminators=allow_terminators)
        if expr is None:
            raise ParseError("Cannot return null expression")
        return expr


    def parse_assignment(self, allow_terminators=True):
        """Parse an assignment expression."""
        expr = self.parse_binary(allow_terminators=allow_terminators)
        from parser.ast_nodes import AssignmentExpression
        
        if (self.verbose):
            print(f"Parsed expression: {expr}")
        
        if self.match(TokenType.EQUAL):
            value = self.parse_expression(allow_terminators=allow_terminators)
            if expr is None:
                raise ParseError("Invalid assignment target (None)")
            return AssignmentExpression(target=expr, value=value, operator="=")
        
        # Compound assignment (+=, -=, etc.)
        for op in [TokenType.PLUSASSIGN, TokenType.MINUSASSIGN, TokenType.STARASSIGN, TokenType.SLASHASSIGN]:
            if self.match(op):
                value = self.parse_expression(allow_terminators=allow_terminators)
                if expr is None:
                    raise ParseError("Invalid assignment target (None)")
                return AssignmentExpression(target=expr, value=value, operator=self.previous().value)
    
        return expr


    def parse_binary(self, precedence=0, allow_terminators=True):
        """Parse a binary or logical expression."""
        left = self.parse_unary(allow_terminators=allow_terminators)
        from parser.ast_nodes import BinaryExpression, LogicalExpression
        while True:
            op = self.peek().type
            op_prec = self.get_precedence(op)
            if op_prec < precedence:
                break
            # If the next token is a statement terminator, do not parse further (only if allowed)
            if allow_terminators and self.check(TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.EOF):
                break
            self.advance()
            right = self.parse_binary(op_prec + 1, allow_terminators=allow_terminators)
            if right is None:
                raise ParseError("Invalid operands for binary/logical expression")
            if left is None:
                raise ParseError("Invalid left operand for binary/logical expression")
            if op in (TokenType.AND, TokenType.OR):
                left = LogicalExpression(operator=self.previous().value, left=left, right=right)
            else:
                left = BinaryExpression(operator=self.previous().value, left=left, right=right)
        return left


    def parse_unary(self, allow_terminators=True):
        """Parse a unary expression."""
        from parser.ast_nodes import UnaryExpression
        if self.match(TokenType.MINUS):
            operand = self.parse_unary(allow_terminators=allow_terminators)
            return UnaryExpression(operator='-', operand=operand)
        return self.parse_not(allow_terminators=allow_terminators)


    def parse_not(self, allow_terminators=True):
        """Parse a logical NOT expression."""
        if self.match(TokenType.NOT):
            operand = self.parse_not(allow_terminators=allow_terminators)
            from parser.ast_nodes import UnaryExpression
            return UnaryExpression(operator='not', operand=operand)
        return self.parse_primary(allow_terminators=allow_terminators)


    def parse_primary(self, allow_terminators=True):
        """Parse primary expressions (identifiers, literals, attribute access, calls, parenthesized, etc.).
        Accepts identifiers and function/method calls as valid logical operands.
        """
        from parser.ast_nodes import IdentifierExpression, LiteralExpression, LogicalExpression
        # End expression if next token is a block, block-like start, or closing parenthesis
        if self.check(TokenType.LBRACE, TokenType.COLON, TokenType.RPAREN):
            if self.verbose:
                print(f"End of expression at token: {self.peek().type.name}")
            return None
        
        # Literals
        if self.match(TokenType.TRUE):
            if self.verbose:
                print("Parsed True literal")
            return self.parse_postfix(LiteralExpression(value=True, literal_type='boolean'))
        
        if self.match(TokenType.FALSE):
            if self.verbose:
                print("Parsed False literal")
            return self.parse_postfix(LiteralExpression(value=False, literal_type='boolean'))
        
        if self.match(TokenType.NONE):
            if self.verbose:
                print("Parsed None literal")
            return self.parse_postfix(LiteralExpression(value=None, literal_type='none'))
        
        if self.match(TokenType.NUMBER):
            value = self.previous().value
            if self.verbose:
                print(f"Parsed number literal: {value}")
            return self.parse_postfix(LiteralExpression(value=value, literal_type='number'))
        
        if self.match(TokenType.STRING):
            value = self.previous().value
            if self.verbose:
                print(f"Parsed string literal: {value}")
            return self.parse_postfix(LiteralExpression(value=value, literal_type='string'))
        
        # Handle f-strings: f"..."
        if self.check(TokenType.IDENTIFIER) and self.peek().value == 'f':
            self.advance()
            if self.match(TokenType.STRING):
                value = self.previous().value
                if self.verbose:
                    print(f"Parsed f-string literal: {value}")
                return self.parse_postfix(LiteralExpression(value=value, literal_type='fstring'))
            else:
                raise ParseError("Expected string after 'f' for f-string literal")
            
        # Identifier or self
        if self.check(TokenType.IDENTIFIER):
            self.advance()
            name = self.previous().value
            if self.verbose:
                print(f"Parsed identifier: {name}")
            expr = IdentifierExpression(name=name)
            return self.parse_postfix(expr)
        
        # Parenthesized expression
        if self.match(TokenType.LPAREN):
            if self.verbose:
                print("Parsing parenthesized expression")
            expr = self.parse_expression()
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            return self.parse_postfix(expr)
        
        # If we can't parse anything, return None
        if self.verbose:
            print(f"Could not parse primary expression from token: {self.peek().type.name}")

        raise ParseError(f"Unexpected token: {self.peek().value} at {self.peek().line}:{self.peek().column}")


    def parse_postfix(self, expr):
        """Parse chained attribute access and calls for any expression.
        This allows identifiers and function/method calls to be used as operands in logical expressions.
        """
        from parser.ast_nodes import AttributeExpression, CallExpression, LogicalExpression

        while True:
            if self.match(TokenType.DOT):
                attribute = self.consume(TokenType.IDENTIFIER, "Expected attribute name after '.'").value
                if self.verbose:
                    print(f"Parsed attribute access: {attribute}")
                expr = AttributeExpression(object=expr, attribute=attribute)
                
            elif self.match(TokenType.LPAREN):
                if self.verbose:
                    print(f"Parsing call expression")
                arguments = []
                if not self.check(TokenType.RPAREN):
                    while True:
                        arg = self.parse_expression(allow_terminators=False)
                        if arg is None:
                            raise ParseError("Expected expression as function call argument")
                        arguments.append(arg)
                        if self.match(TokenType.COMMA):
                            continue
                        elif self.check(TokenType.RPAREN):
                            break
                        else:
                            raise ParseError(f"Expected ',' or ')' after function call argument, got {self.peek().value} at {self.peek().line}:{self.peek().column}")
                self.consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpression(callee=expr, arguments=arguments)
                if self.verbose:
                    print(f"Completed call with {len(arguments)} arguments")
            else:
                break
        return expr


    def get_precedence(self, token_type):
        # Define operator precedences (higher number = higher precedence)
        precedences = {
            TokenType.OR: 1,
            TokenType.AND: 2,
            TokenType.NOT: 3,
            TokenType.EQUAL: 4,
            TokenType.NOTEQUAL: 4,
            TokenType.LESS: 5,
            TokenType.GREATER: 5,
            TokenType.LESSEQUAL: 5,
            TokenType.GREATEREQUAL: 5,
            TokenType.PLUS: 6,
            TokenType.MINUS: 6,
            TokenType.STAR: 7,
            TokenType.SLASH: 7,
            TokenType.PERCENT: 7,
            TokenType.DOUBLESTAR: 8,
            TokenType.DOUBLESLASH: 8,
            TokenType.DOT: 9,  # Attribute access highest
            TokenType.LPAREN: 9,  # Call highest
        }
        return precedences.get(token_type, 0)


    def parse_lambda(self):
        """Parse a lambda expression."""
        from parser.ast_nodes import LambdaExpression
        
        self.consume(TokenType.LAMBDA, "Expected 'lambda' keyword")
        
        # Parameters
        self.consume(TokenType.LPAREN, "Expected '(' after 'lambda'")
        params = self.parse_parameters()
        self.consume(TokenType.RPAREN, "Expected ')' after parameters")
        
        # Return type (optional)
        return_type = None
        if self.match(TokenType.COLON):
            if self.check(TokenType.IDENTIFIER):
                return_type = self.advance().value
            elif self.check(TokenType.NONE):
                return_type = self.advance().value
            else:
                raise ParseError(f"Expected return type after ':' at line {self.peek().line}")
        
        # Expression body
        body = self.parse_expression(allow_terminators=False)
        return LambdaExpression(params=params, body=body, return_type=return_type)


    def parse_logic_expression(self):
        """Parse a generalized boolean expression (for use in if/while/for conditions)."""

        from lexer.tokens import isBoolean, isLogicToken, isValidFirstLogicToken
        expr: Expression

        if self.verbose:
            print("Parsing logic expression")
        
        expr = self.parse_logic_component() # First comp
        while True:
            if self.check(TokenType.AND):
                expr = LogicalExpression(
                    operator='and',
                    left=copy.deepcopy(expr),
                    right=self.parse_logic_component()
                )
                self.advance()
                continue
            elif self.check(TokenType.OR):
                expr = LogicalExpression(
                    operator='or',
                    left=copy.deepcopy(expr),
                    right=self.parse_logic_component()
                )
                self.advance()
                continue
            elif self.check(TokenType.IN):
                expr = LogicalExpression(
                    operator='in',
                    left=copy.deepcopy(expr),
                    right=self.parse_logic_component()
                )
                self.advance()
                continue
            break
        
        if self.verbose:
            print(f"Completed logic expression: {expr}")
        return expr


    def parse_logic_component(self):
        """Parse a single component of a logic expression (identifier, literal, parenthesized expression)."""
        from parser.ast_nodes import IdentifierExpression, LiteralExpression
        
        is_negated = False
        if self.match(TokenType.NOT):
            is_negated = True
            if self.verbose:
                print("Parsed NOT operator")

        expr: Expression
        
        if self.match(TokenType.TRUE):
            expr = LiteralExpression(value=True, literal_type='boolean')
            if self.verbose:
                print("Parsed logical component: True literal")
            
        elif self.match(TokenType.FALSE):
            expr = LiteralExpression(value=False, literal_type='boolean')
            if self.verbose:
                print("Parsed logical component: False literal")

        elif self.match(TokenType.NONE):
            expr = LiteralExpression(value=None, literal_type='none')
            if self.verbose:
                print("Parsed logical component: None literal")

        elif self.match(TokenType.NUMBER):
            expr = LiteralExpression(value=self.previous().value, literal_type='number')
            if self.verbose:
                print("Parsed logical component: Number literal")

        elif self.match(TokenType.STRING):
            expr = LiteralExpression(value=self.previous().value, literal_type='string')
            if self.verbose:
                print("Parsed logical component: String literal")

        elif self.check(TokenType.IDENTIFIER):
            name = self.advance().value
            if self.peek().type == TokenType.LPAREN:
                # This is a function call, not a simple identifier
                if self.verbose:
                    print(f"Parsed logical component: Function Call {name}")
                expr = self.parse_method_call(IdentifierExpression(name=name))
            expr = IdentifierExpression(name=name)
            if self.verbose:
                print("Parsed logical component: Identifier")

        elif self.match(TokenType.LPAREN):
            expr = self.parse_expression(allow_terminators=False)
            self.consume(TokenType.RPAREN, "Expected ')' after expression")
            if self.verbose:
                print("Parsed logical component: Expression")

        else:
            raise ParseError(f"Unexpected token: {self.peek().value} at {self.peek().line}:{self.peek().column}")
        

        if is_negated:
            from parser.ast_nodes import UnaryExpression
            expr = UnaryExpression(operator='not', operand=expr)
            if self.verbose:
                print("Negated expression")
        
        return expr