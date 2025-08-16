"""Restructured expression parsing methods for the Spice parser."""

from typing import Optional, List
from spice.lexer import TokenType
from spice.parser.ast_nodes import (
    Expression, AssignmentExpression, BinaryExpression, UnaryExpression,
    LogicalExpression, CallExpression, AttributeExpression,
    IdentifierExpression, LiteralExpression, ArgumentExpression,
    SubscriptExpression, SliceExpression, ComprehensionExpression,
    DictEntry
)
from spice.errors import ParserError

from spice.printils import expression_parser_log


class ExpressionParser:
    from spice.parser.parser import Parser
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

    def __init__(self, parser: Parser):
        self.parser = parser  # Reference to main parser for helper methods

    # Main entry point
    def parse_expression(self, context="general") -> Optional[Expression]:
        """Parse a full expression including assignments."""
        return self.parse_assignment(context=context)

    # Level 1: Assignment
    def parse_assignment(self, context="general") -> Optional[Expression]:
        """Parse assignment expressions (=, +=, -=, etc.)."""
        expr = self.parse_logical_or(context=context)

        if expr is None:
            return None

        # =
        if self.parser.check(TokenType.ASSIGN):
            op = self.parser.advance().value
            right = self.parse_assignment(context=context)
            if right is None:
                raise ParserError("Expected expression after assignment operator")
            return AssignmentExpression(target=expr, value=right, operator=op)

        # +=, -=, *=, /=, %=, **=, //=
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
                right = self.parse_assignment(context=context)
                if right is None:
                    raise ParserError(f"Expected expression after {op}")
                return AssignmentExpression(target=expr, value=right, operator=op)

        return expr

    # Level 2: Logical OR
    def parse_logical_or(self, context="general") -> Optional[Expression]:
        """Parse logical OR expressions."""
        expr = self.parse_logical_and(context=context)

        while self.parser.match(TokenType.OR, advance_at_newline=True):
            op = self.parser.previous().value
            right = self.parse_logical_and(context=context)
            if right is None:
                raise ParserError("Expected expression after 'or'")
            expr = LogicalExpression(operator=op, left=expr, right=right)

        return expr

    # Level 3: Logical AND
    def parse_logical_and(self, context="general") -> Optional[Expression]:
        """Parse logical AND expressions."""
        expr = self.parse_membership(context=context)

        while self.parser.match(TokenType.AND, advance_at_newline=True):
            op = self.parser.previous().value
            right = self.parse_membership(context=context)
            if right is None:
                raise ParserError("Expected expression after 'and'")
            expr = LogicalExpression(operator=op, left=expr, right=right)

        return expr

    # Level 4: Membership
    def parse_membership(self, context="general") -> Optional[Expression]:
        """Parse membership tests (in, not in, is, is not)."""
        expr = self.parse_equality(context=context)

        while True:
            # in
            if self.parser.match(TokenType.IN):
                right = self.parse_equality(context=context)
                if right is None:
                    raise ParserError("Expected expression after 'in'")
                expr = BinaryExpression(operator='in', left=expr, right=right)

            # not
            elif self.parser.match(TokenType.NOT) and self.parser.check(TokenType.IN):
                self.parser.advance()  # consume 'in'
                right = self.parse_equality(context=context)
                if right is None:
                    raise ParserError("Expected expression after 'not in'")
                expr = BinaryExpression(operator='not in', left=expr, right=right)

            # is
            elif self.parser.match(TokenType.IS):
                if self.parser.match(TokenType.NOT):
                    right = self.parse_equality(context=context)
                    if right is None:
                        raise ParserError("Expected expression after 'is not'")
                    expr = BinaryExpression(operator='is not', left=expr, right=right)
                else:
                    right = self.parse_equality(context=context)
                    if right is None:
                        raise ParserError("Expected expression after 'is'")
                    expr = BinaryExpression(operator='is', left=expr, right=right)

            else:
                break

        return expr

    # Level 5: Equality
    def parse_equality(self, context="general") -> Optional[Expression]:
        """Parse equality comparisons (==, !=)."""
        expr = self.parse_comparison(context=context)

        # ==, !=
        while self.parser.match(TokenType.EQUAL, TokenType.NOTEQUAL):
            op = self.parser.previous().value
            right = self.parse_comparison(context=context)
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)

        return expr

    # Level 6: Comparison
    def parse_comparison(self, context="general") -> Optional[Expression]:
        """Parse comparison operators (<, >, <=, >=)."""
        expr = self.parse_addition(context=context)

        # <, >, <=, >=
        while self.parser.match(TokenType.LESS, TokenType.GREATER,
                               TokenType.LESSEQUAL, TokenType.GREATEREQUAL):
            op = self.parser.previous().value
            right = self.parse_addition(context=context)
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)

        return expr

    # Level 7: Addition/Subtraction
    def parse_addition(self, context="general") -> Optional[Expression]:
        """Parse addition and subtraction."""
        expr = self.parse_multiplication(context=context)

        # +, -
        while self.parser.match(TokenType.PLUS, TokenType.MINUS):
            op = self.parser.previous().value
            right = self.parse_multiplication(context=context)
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)

        return expr

    # Level 8: Multiplication/Division
    def parse_multiplication(self, context="general") -> Optional[Expression]:
        """Parse multiplication, division, and modulo."""
        expr = self.parse_exponentiation(context=context)

        # *, /, %, //
        while self.parser.match(TokenType.STAR, TokenType.SLASH,
                               TokenType.PERCENT, TokenType.DOUBLESLASH):
            op = self.parser.previous().value
            right = self.parse_exponentiation(context=context)
            if right is None:
                raise ParserError(f"Expected expression after '{op}'")
            expr = BinaryExpression(operator=op, left=expr, right=right)

        return expr

    # Level 9: Exponentiation
    def parse_exponentiation(self, context="general") -> Optional[Expression]:
        """Parse exponentiation (**). Right associative!"""
        expr = self.parse_unary(context=context)

        # **
        if self.parser.match(TokenType.DOUBLESTAR):
            op = self.parser.previous().value
            # Right associative - recurse at same level
            right = self.parse_exponentiation(context=context)
            if right is None:
                raise ParserError("Expected expression after '**'")
            return BinaryExpression(operator=op, left=expr, right=right)

        return expr

    # Level 10: Unary
    def parse_unary(self, context="general") -> Optional[Expression]:
        """Parse unary operators (not, -)."""

        # not
        if self.parser.match(TokenType.NOT):
            op = self.parser.previous().value
            expr = self.parse_unary(context=context)  # Allow chaining: not not x
            if expr is None:
                raise ParserError("Expected expression after 'not'")
            return UnaryExpression(operator=op, operand=expr)

        # -
        if self.parser.match(TokenType.MINUS):
            op = self.parser.previous().value
            expr = self.parse_unary(context=context)
            if expr is None:
                raise ParserError("Expected expression after '-'")
            return UnaryExpression(operator=op, operand=expr)

        return self.parse_postfix()

    # Level 11: Postfix operations
    def parse_postfix(self, context="general") -> Optional[Expression]:
        """Parse postfix operations (attribute access, calls, subscripts)."""
        expr = self.parse_primary(context=context)

        if expr is None:
            return None

        while True:

            # alpha.beta
            if self.parser.match(TokenType.DOT):
                if self.parser.verbose:
                    expression_parser_log.info("Parsing postfix .")

                if not self.parser.check(TokenType.IDENTIFIER):
                    raise ParserError("Expected attribute name after '.'")
                else:
                    if self.parser.verbose: expression_parser_log.info("Found attribute: ", self.parser.peek().value)
                attr = self.parser.advance().value
                expr = AttributeExpression(object=expr, attribute=attr)

            # alpha()
            elif self.parser.match(TokenType.LPAREN):
                if self.parser.verbose:
                    expression_parser_log.info("Parsing postfix ()")

                # Function/method call
                args = self.parse_arguments()
                self.parser.consume(TokenType.RPAREN, "Expected ')' after arguments")
                expr = CallExpression(callee=expr, arguments=args)

            # alpha[]
            elif self.parser.match(TokenType.LBRACKET):
                if self.parser.verbose:
                    expression_parser_log.info("Parsing postfix []")

                # Parse the index/slice expression
                index_expr = self.parse_subscript_or_slice()
                self.parser.consume(TokenType.RBRACKET, "Expected ']'")
                expr = SubscriptExpression(object=expr, index=index_expr)

            else:
                break

        return expr

    # Level 12: Primary expressions
    def parse_primary(self, context="general") -> Optional[Expression]:
        """Parse primary expressions (literals, identifiers, parentheses)."""

        # Context-sensitive early termination check
        if self._should_terminate_here(context):
            return None

        # Literals
        if self.parser.match(TokenType.TRUE):
            return LiteralExpression(value=True, literal_type='boolean')

        if self.parser.match(TokenType.FALSE):
            return LiteralExpression(value=False, literal_type='boolean')

        # List literals and list comprehensions
        if self.parser.match(TokenType.LBRACKET):
            # Check for empty list
            if self.parser.check(TokenType.RBRACKET):
                self.parser.advance()
                return LiteralExpression(value=[], literal_type='list')

            # Parse first expression
            first_expr = self.parse_expression(context)
            if first_expr is None:
                raise ParserError("Expected expression in list")

            # Check if it's a list comprehension
            if self.parser.check(TokenType.FOR):
                return self._parse_comprehension(first_expr, 'list')

            # Regular list literal
            elements = [first_expr]
            while self.parser.match(TokenType.COMMA):
                elem = self.parse_expression(context)
                if elem is None:
                    raise ParserError("Expected expression in list")
                elements.append(elem)

            self.parser.consume(TokenType.RBRACKET, "Expected ']' after list elements")
            return LiteralExpression(value=elements, literal_type='list')

        # Set/Dict literals and comprehensions
        if self.parser.match(TokenType.LBRACE):
            # Only parse as literal if NOT in condition context
            if context != "condition":
                # Check for empty dict/set
                if self.parser.check(TokenType.RBRACE):
                    self.parser.advance()
                    return LiteralExpression(value=[], literal_type='dict')  # Empty {} is dict in Python

                # Parse first element/expression
                first_expr = self.parse_expression(context)
                if first_expr is None:
                    raise ParserError("Expected expression in set/dict")

                # Check what type of literal/comprehension this is
                if self.parser.match(TokenType.COLON):
                    # It's a dict (either literal or comprehension)
                    value_expr = self.parse_expression(context)
                    if value_expr is None:
                        raise ParserError("Expected value after ':' in dict")

                    # Check for dict comprehension
                    if self.parser.check(TokenType.FOR):
                        comp = self._parse_comprehension(value_expr, 'dict')
                        comp.key = first_expr  # Store the key expression
                        return comp

                    # Regular dict literal
                    elements = [DictEntry(key=first_expr, value=value_expr)]

                    while self.parser.match(TokenType.COMMA):
                        # Parse key
                        key = self.parse_expression(context)
                        if key is None:
                            break  # Allow trailing comma

                        self.parser.consume(TokenType.COLON, "Expected ':' after dict key")

                        # Parse value
                        value = self.parse_expression(context)
                        if value is None:
                            raise ParserError("Expected value in dict")

                        elements.append(DictEntry(key=key, value=value))

                    self.parser.consume(TokenType.RBRACE, "Expected '}' after dict elements")
                    return LiteralExpression(value=elements, literal_type='dict')

                # Check for set comprehension
                elif self.parser.check(TokenType.FOR):
                    return self._parse_comprehension(first_expr, 'set')

                # Regular set literal
                else:
                    elements = [first_expr]

                    while self.parser.match(TokenType.COMMA):
                        elem = self.parse_expression(context)
                        if elem is None:
                            break  # Allow trailing comma
                        elements.append(elem)

                    self.parser.consume(TokenType.RBRACE, "Expected '}' after set elements")
                    return LiteralExpression(value=elements, literal_type='set')
            else:
                # In condition context, don't consume { - let it terminate
                return None

        if self.parser.match(TokenType.NONE):
            return LiteralExpression(value=None, literal_type='none')

        if self.parser.match(TokenType.NUMBER):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='number')

        if self.parser.match(TokenType.STRING):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='string')

        if self.parser.match(TokenType.FSTRING):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='fstring')

        if self.parser.match(TokenType.FRSTRING):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='frstring')

        if self.parser.match(TokenType.REGEX):
            value = self.parser.previous().value
            return LiteralExpression(value=value, literal_type='regex')

        # Identifiers
        if self.parser.match(TokenType.IDENTIFIER):
            name = self.parser.previous().value
            return IdentifierExpression(name=name)

        # Parenthesized expressions, tuples, and generator expressions
        if self.parser.match(TokenType.LPAREN):
            # Check for empty tuple
            if self.parser.check(TokenType.RPAREN):
                self.parser.advance()
                return LiteralExpression(value=[], literal_type='tuple')

            # Parse first expression
            first_expr = self.parse_expression(context=context)
            if first_expr is None:
                raise ParserError("Expected expression after '('")

            # Check for generator expression
            if self.parser.check(TokenType.FOR):
                comp = self._parse_comprehension(first_expr, 'generator')
                self.parser.consume(TokenType.RPAREN, "Expected ')' after generator expression")
                return comp

            # Check if this is a tuple (has comma) or just a parenthesized expression
            if self.parser.match(TokenType.COMMA):
                # It's a tuple - collect all elements
                elements = [first_expr]

                # Check for trailing comma (single element tuple)
                if self.parser.check(TokenType.RPAREN):
                    self.parser.advance()
                    return LiteralExpression(value=elements, literal_type='tuple')

                # Parse remaining elements
                while True:
                    elem = self.parse_expression(context=context)
                    if elem is None:
                        break  # Allow trailing comma
                    elements.append(elem)

                    if not self.parser.match(TokenType.COMMA):
                        break

                    # Check for trailing comma
                    if self.parser.check(TokenType.RPAREN):
                        break

                self.parser.consume(TokenType.RPAREN, "Expected ')' after tuple elements")
                return LiteralExpression(value=elements, literal_type='tuple')
            else:
                # Just a parenthesized expression
                self.parser.consume(TokenType.RPAREN, "Expected ')' after expression")
                return first_expr

        # Lambda expressions
        if self.parser.match(TokenType.LAMBDA):
            return self.parse_lambda(context=context)

        # If we get here, we couldn't parse a primary expression
        return None


    ##########################################
    ################# UTILS ##################
    ##########################################

    def _should_terminate_here(self, context: str) -> bool:
        """Check if we should terminate parsing based on context."""
        if context == "condition" and self.parser.check(TokenType.LBRACE):
            return self._is_statement_block()

        return False


    def _is_statement_block(self) -> bool:
        """Distinguish between lambda body { and statement block {"""
        # Yes this whole logic is to allow lambda's in a if / while condition

        # If a -> is present, it should only indicate that it's a lambda
        i = self.parser.current - 1
        while i >= 0 and self.parser.tokens[i].type in [TokenType.NEWLINE, TokenType.COMMENT]:
            i -= 1

        if i >= 0 and self.parser.tokens[i].type == TokenType.ARROW:
            return False  # Don't terminate - Lambda

        return True  # Terminate - Statement


    def parse_arguments(self, context="general") -> List[Expression]:
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
                        value = self.parse_expression(context=context)
                        if value is None:
                            raise ParserError(f"Expected value for argument '{name}'")
                        args.append(ArgumentExpression(name=name, value=value))
                    else:
                        # Not a named argument, backtrack
                        self.parser.current = checkpoint
                        expr = self.parse_expression(context=context)
                        if expr is None:
                            raise ParserError("Expected expression as argument")
                        args.append(expr)
                else:
                    # Positional argument
                    expr = self.parse_expression(context=context)
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
    def parse_subscript_or_slice(self) -> Expression:
        """Parse subscript index or slice notation [start:stop:step]."""
        # Check for empty subscript
        if self.parser.check(TokenType.RBRACKET):
            raise ParserError("Empty subscript not allowed")

        # Parse the first expression (could be start of slice or single index)
        first_expr = None
        if not self.parser.check(TokenType.COLON):
            first_expr = self.parse_expression()
            if first_expr is None:
                raise ParserError("Expected expression in subscript")

        # Check if this is a slice (contains :)
        if self.parser.check(TokenType.COLON):
            # This is a slice expression
            start = first_expr
            stop = None
            step = None

            # Consume first colon
            self.parser.advance()

            # Parse stop (optional)
            if not self.parser.check(TokenType.COLON) and not self.parser.check(TokenType.RBRACKET):
                stop = self.parse_expression()
                if stop is None:
                    raise ParserError("Expected expression for slice stop")

            # Check for second colon (step)
            if self.parser.match(TokenType.COLON):
                # Parse step (optional)
                if not self.parser.check(TokenType.RBRACKET):
                    step = self.parse_expression()
                    if step is None:
                        raise ParserError("Expected expression for slice step")

            return SliceExpression(start=start, stop=stop, step=step)
        else:
            # This is a simple index
            if first_expr is None:
                raise ParserError("Expected expression in subscript")
            return first_expr

    # Helper Methods
    def _is_dict_entry(self) -> bool:
        """Check if the next tokens form a dictionary entry (key: value)."""
        # Simple lookahead for common dict patterns
        # Check for: STRING : or IDENTIFIER :
        current_pos = self.parser.current
        if self.parser.tokens[current_pos].type == TokenType.NEWLINE:
            current_pos += 1  # Skip newline if present
            self.parser.advance()

        flag1: bool = current_pos < len(self.parser.tokens) - 1
        flag2: bool = self.parser.tokens[current_pos].type in [TokenType.STRING, TokenType.IDENTIFIER]
        flag3: bool = self.parser.tokens[current_pos + 1].type == TokenType.COLON

        if not flag1:
            if self.parser.verbose:
                expression_parser_log.info("Not enough tokens to form a dictionary entry")
            return False

        if not flag2:
            if self.parser.verbose:
                expression_parser_log.info("Next token is not a valid dictionary key: ", self.parser.tokens[current_pos])
            return False

        if not flag3:
            if self.parser.verbose:
                expression_parser_log.info("Next token is not a colon after key: ", self.parser.tokens[current_pos + 1])
            return False

        return True

    def _parse_comprehension(self, element_expr: Expression, comp_type: str) -> ComprehensionExpression:
        """Parse the comprehension part: for target in iter [if condition]"""

        # Consume 'for'
        self.parser.consume(TokenType.FOR, "Expected 'for' in comprehension")

        # Parse target (loop variable)
        target = self.parse_expression()
        if target is None:
            raise ParserError("Expected target variable in comprehension")

        # Consume 'in'
        self.parser.consume(TokenType.IN, "Expected 'in' in comprehension")

        # Parse iterable
        # We need to be careful here to not consume the closing bracket/brace/paren
        # So we parse with a limited context
        iter_expr = self._parse_comprehension_iter()
        if iter_expr is None:
            raise ParserError("Expected iterable in comprehension")

        # Optional: if condition
        condition = None
        if self.parser.match(TokenType.IF):
            condition = self._parse_comprehension_condition()
            if condition is None:
                raise ParserError("Expected condition after 'if' in comprehension")

        # Handle closing bracket/brace based on comp_type
        if comp_type == 'list':
            self.parser.consume(TokenType.RBRACKET, "Expected ']' after list comprehension")
        elif comp_type in ('set', 'dict'):
            self.parser.consume(TokenType.RBRACE, "Expected '}' after set/dict comprehension")
        # Note: generator expressions handle ) in the calling function

        return ComprehensionExpression(
            element=element_expr,
            target=target,
            iter=iter_expr,
            condition=condition,
            comp_type=comp_type
        )


    def _parse_comprehension_iter(self) -> Optional[Expression]:
        """Parse the iterable expression in a comprehension, stopping at 'if' or closing bracket."""
        # Parse a basic expression but stop at 'if' or closing delimiters
        return self._parse_limited_expression(['if', ']', '}', ')'])


    def _parse_comprehension_condition(self) -> Optional[Expression]:
        """Parse the condition expression in a comprehension, stopping at closing bracket."""
        # Parse a basic expression but stop at closing delimiters
        return self._parse_limited_expression([']', '}', ')'])


    def _parse_limited_expression(self, stop_tokens: list) -> Optional[Expression]:
        """Parse an expression but stop at certain tokens."""
        # This is a simplified expression parser that stops at specific tokens
        # We'll parse up to but not including the stop tokens

        # Save current position to detect if we've parsed anything
        start_pos = self.parser.current

        # Parse a basic expression (without consuming stop tokens)
        # For now, we'll use a simple approach: parse until we hit a stop token
        expr_tokens = []
        depth = 0  # Track nesting depth for parentheses/brackets

        while not self.parser.is_at_end():
            current = self.parser.peek()

            # Check if we hit a stop token at depth 0
            if depth == 0:
                if current.type == TokenType.IF and 'if' in stop_tokens:
                    break
                elif current.type == TokenType.RBRACKET and ']' in stop_tokens:
                    break
                elif current.type == TokenType.RBRACE and '}' in stop_tokens:
                    break
                elif current.type == TokenType.RPAREN and ')' in stop_tokens:
                    break

            # Track nesting depth
            if current.type in (TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE):
                depth += 1
            elif current.type in (TokenType.RPAREN, TokenType.RBRACKET, TokenType.RBRACE):
                depth -= 1
                if depth < 0:  # We hit our closing delimiter
                    break

            self.parser.advance()

        # If we didn't parse anything, return None
        if self.parser.current == start_pos:
            return None

        # Reset position and parse the expression properly
        end_pos = self.parser.current
        self.parser.current = start_pos

        # Now parse the expression knowing where to stop
        expr = self.parse_expression()

        return expr