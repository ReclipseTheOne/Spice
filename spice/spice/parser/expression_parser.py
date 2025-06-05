"""Restructured expression parsing methods for the Spy parser."""

from typing import Optional, List
from lexer import Token, TokenType
from parser.ast_nodes import (
    Expression, AssignmentExpression, BinaryExpression, UnaryExpression,
    LogicalExpression, CallExpression, AttributeExpression, 
    IdentifierExpression, LiteralExpression, ArgumentExpression
)
from errors import ParserError


class ExpressionParser:
    """
    Clean expression parser using recursive descent with explicit precedence levels.
    
    Precedence (lowest to highest):
    1. Assignment (=, +=, -=, etc.)
    2. Logical OR (or)
    3. Logical AND (and)
    4. Membership (in, not in)
    5. Equality (==, !=)
    6. Comparison (<, >, <=, >=)
    7. Addition/Subtraction (+, -)
    8. Multiplication/Division (*, /, %, //)
    9. Exponentiation (**)
    10. Unary (not, -)
    11. Postfix (., (), [])
    12. Primary (literals, identifiers, parentheses)
    """
    
    def __init__(self, parser):
        self.parser = parser  # Reference to main parser for helper methods
    
    # Main entry point
    def parse_expression(self) -> Optional[Expression]:
        """Parse a full expression including assignments."""
        return self.parse_assignment()
    
    # Level 1: Assignment
    def parse_assignment(self) -> Optional[Expression]:
        """Parse assignment expressions (=, +=, -=, etc.)."""
        expr = self.parse_logical_or()
        
        if expr is None:
            return None
            
        # Check for assignment operators
        if self.parser.check(TokenType.ASSIGN):
            op = self.parser.advance().value
            right = self.parse_assignment()  # Right associative
            if right is None:
                raise ParserError("Expected expression after assignment operator")
            return AssignmentExpression(target=expr, value=right, operator=op)
            
        # Compound assignments
        compound_ops = {
            TokenType.PLUSASSIGN: '+=',
            TokenType.MINUSASSIGN: '-=',
            TokenType.STARASSIGN: '*=',
            TokenType.SLASHASSIGN: '/=',
            TokenType.PERCENTASSIGN: '%=',
            TokenType.DOUBLESTARASSIGN: '**=',
            TokenType.DOUBLESLASHASSIGN: '//='
        }
        
        for token_type, op in compound_ops.items():
            if self.parser.match(token_type):
                right = self.parse_assignment()
                if right is None:
                    raise ParserError(f"Expected expression after {op}")
                return AssignmentExpression(target=expr, value=right, operator=op)
        
        return expr
    
    # Level 2: Logical OR
    def parse_logical_or(self) -> Optional[Expression]:
        """Parse logical OR expressions."""
        expr = self.parse_logical_and()
        
        while self.parser.match(TokenType.OR):
            op = self.parser.previous().value
            right = self.parse_logical_and()
            if right is None:
                raise ParserError("Expected expression after 'or'")
            expr = LogicalExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 3: Logical AND
    def parse_logical_and(self) -> Optional[Expression]:
        """Parse logical AND expressions."""
        expr = self.parse_membership()
        
        while self.parser.match(TokenType.AND):
            op = self.parser.previous().value
            right = self.parse_membership()
            if right is None:
                raise ParserError("Expected expression after 'and'")
            expr = LogicalExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 4: Membership
    def parse_membership(self) -> Optional[Expression]:
        """Parse membership tests (in, not in, is, is not)."""
        expr = self.parse_equality()
        
        while True:
            if self.parser.match(TokenType.IN):
                right = self.parse_equality()
                if right is None:
                    raise ParserError("Expected expression after 'in'")
                expr = BinaryExpression(operator='in', left=expr, right=right)
            elif self.parser.match(TokenType.NOT) and self.parser.check(TokenType.IN):
                self.parser.advance()  # consume 'in'
                right = self.parse_equality()
                if right is None:
                    raise ParserError("Expected expression after 'not in'")
                expr = BinaryExpression(operator='not in', left=expr, right=right)
            elif self.parser.match(TokenType.IS):
                if self.parser.match(TokenType.NOT):
                    right = self.parse_equality()
                    if right is None:
                        raise ParserError("Expected expression after 'is not'")
                    expr = BinaryExpression(operator='is not', left=expr, right=right)
                else:
                    right = self.parse_equality()
                    if right is None:
                        raise ParserError("Expected expression after 'is'")
                    expr = BinaryExpression(operator='is', left=expr, right=right)
            else:
                break
        
        return expr
    
    # Level 5: Equality
    def parse_equality(self) -> Optional[Expression]:
        """Parse equality comparisons (==, !=)."""
        expr = self.parse_comparison()
        
        while self.parser.match(TokenType.EQUAL, TokenType.NOTEQUAL):
            op = self.parser.previous().value
            right = self.parse_comparison()
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 6: Comparison
    def parse_comparison(self) -> Optional[Expression]:
        """Parse comparison operators (<, >, <=, >=)."""
        expr = self.parse_addition()
        
        while self.parser.match(TokenType.LESS, TokenType.GREATER, 
                               TokenType.LESSEQUAL, TokenType.GREATEREQUAL):
            op = self.parser.previous().value
            right = self.parse_addition()
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 7: Addition/Subtraction
    def parse_addition(self) -> Optional[Expression]:
        """Parse addition and subtraction."""
        expr = self.parse_multiplication()
        
        while self.parser.match(TokenType.PLUS, TokenType.MINUS):
            op = self.parser.previous().value
            right = self.parse_multiplication()
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 8: Multiplication/Division
    def parse_multiplication(self) -> Optional[Expression]:
        """Parse multiplication, division, and modulo."""
        expr = self.parse_exponentiation()
        
        while self.parser.match(TokenType.STAR, TokenType.SLASH, 
                               TokenType.PERCENT, TokenType.DOUBLESLASH):
            op = self.parser.previous().value
            right = self.parse_exponentiation()
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 9: Exponentiation
    def parse_exponentiation(self) -> Optional[Expression]:
        """Parse exponentiation (**). Right associative!"""
        expr = self.parse_unary()
        
        if self.parser.match(TokenType.DOUBLESTAR):
            op = self.parser.previous().value
            # Right associative - recurse at same level
            right = self.parse_exponentiation()
            if right is None:
                raise ParserError("Expected expression after '**'")
            return BinaryExpression(operator=op, left=expr, right=right)
        
        return expr
    
    # Level 10: Unary
    def parse_unary(self) -> Optional[Expression]:
        """Parse unary operators (not, -)."""
        if self.parser.match(TokenType.NOT):
            op = self.parser.previous().value
            expr = self.parse_unary()  # Allow chaining: not not x
            if expr is None:
                raise ParserError("Expected expression after 'not'")
            return UnaryExpression(operator=op, operand=expr)
        
        if self.parser.match(TokenType.MINUS):
            op = self.parser.previous().value
            expr = self.parse_unary()
            if expr is None:
                raise ParserError("Expected expression after '-'")
            return UnaryExpression(operator=op, operand=expr)
        
        return self.parse_postfix()
    
    # Level 11: Postfix operations
    def parse_postfix(self) -> Optional[Expression]:
        """Parse postfix operations (attribute access, calls, subscripts)."""
        expr = self.parse_primary()
        
        if expr is None:
            return None
        
        while True:
            if self.parser.match(TokenType.DOT):
                # Attribute access
                if not self.parser.check(TokenType.IDENTIFIER):
                    raise ParserError("Expected attribute name after '.'")
                attr = self.parser.advance().value
                expr = AttributeExpression(object=expr, attribute=attr)
                
            elif self.parser.match(TokenType.LPAREN):
                # Function/method call
                args = self.parse_arguments()
                self.parser.consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpression(callee=expr, arguments=args)
                
            elif self.parser.match(TokenType.LBRACKET):
                # Subscript (array/dict access) - not implemented yet
                # For now, just consume and skip
                self.parser.advance()  # Skip the index
                self.parser.consume(TokenType.RBRACKET, "Expected ']'")
                
            else:
                break
        
        return expr
    
    # Level 12: Primary expressions
    def parse_primary(self) -> Optional[Expression]:
        """Parse primary expressions (literals, identifiers, parentheses)."""
        # Literals
        if self.parser.match(TokenType.TRUE):
            return LiteralExpression(value=True, literal_type='boolean')
        
        if self.parser.match(TokenType.FALSE):
            return LiteralExpression(value=False, literal_type='boolean')
        
        if self.parser.match(TokenType.NONE):
            return LiteralExpression(value=None, literal_type='none')
        
        if self.parser.match(TokenType.NUMBER):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='number')
        
        if self.parser.match(TokenType.STRING):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='string')
        
        # f-strings
        if self.parser.check(TokenType.IDENTIFIER) and self.parser.peek().value == 'f':
            self.parser.advance()
            if self.parser.match(TokenType.STRING):
                value = self.parser.previous().value
                return LiteralExpression(value=value, literal_type='fstring')
            else:
                # Put back the 'f' identifier
                self.parser.back()
        
        # Identifiers
        if self.parser.match(TokenType.IDENTIFIER):
            name = self.parser.previous().value
            return IdentifierExpression(name=name)
        
        # Parenthesized expressions
        if self.parser.match(TokenType.LPAREN):
            expr = self.parse_expression()
            self.parser.consume(TokenType.RPAREN, "Expected ')' after expression")
            return expr
        
        # Lambda expressions
        if self.parser.match(TokenType.LAMBDA):
            return self.parse_lambda()
        
        # If we get here, we couldn't parse a primary expression
        return None
    
    # Helper methods
    def parse_arguments(self) -> List[Expression]:
        """Parse function call arguments."""
        args = []
        
        if not self.parser.check(TokenType.RPAREN):
            while True:
                # Try to parse named argument first
                if self.parser.check(TokenType.IDENTIFIER):
                    # Look ahead to see if it's name=value
                    checkpoint = self.parser.current
                    name = self.parser.advance().value
                    
                    if self.parser.match(TokenType.ASSIGN):
                        # Named argument
                        value = self.parse_expression()
                        if value is None:
                            raise ParserError(f"Expected value for argument '{name}'")
                        args.append(ArgumentExpression(name=name, value=value))
                    else:
                        # Not a named argument, backtrack
                        self.parser.current = checkpoint
                        expr = self.parse_expression()
                        if expr is None:
                            raise ParserError("Expected expression as argument")
                        args.append(expr)
                else:
                    # Positional argument
                    expr = self.parse_expression()
                    if expr is None:
                        raise ParserError("Expected expression as argument")
                    args.append(expr)
                
                if not self.parser.match(TokenType.COMMA):
                    break
        
        return args
    
    def parse_lambda(self) -> Expression:
        """Parse lambda expressions."""
        # Implementation depends on your AST structure
        # This is a placeholder
        raise NotImplementedError("Lambda parsing not implemented yet")