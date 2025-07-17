"""Tests for slice expression parsing in the Spy parser."""

from lexer import Lexer
from parser import Parser
from parser.ast_nodes import (
    Module, ExpressionStatement, SubscriptExpression, SliceExpression,
    IdentifierExpression, LiteralExpression
)


class TestSliceParsing:
    """Test slice expression parsing functionality."""

    def parse_source(self, source: str):
        """Helper to parse source code."""
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        parser = Parser()
        return parser.parse(tokens)

    def test_simple_index(self):
        """Test simple array/dict indexing."""
        source = "arr[0]"

        ast = self.parse_source(source)

        # Verify structure
        assert isinstance(ast, Module)
        assert len(ast.body) == 1

        stmt = ast.body[0]
        assert isinstance(stmt, ExpressionStatement)

        expr = stmt.expression
        assert isinstance(expr, SubscriptExpression)

        # Check object
        assert isinstance(expr.object, IdentifierExpression)
        assert expr.object.name == "arr"

        # Check index (should be a simple literal, not a slice)
        assert isinstance(expr.index, LiteralExpression)
        assert expr.index.value == "0"
        assert expr.index.literal_type == "number"

    def test_slice_start_stop(self):
        """Test slice with start and stop."""
        source = "arr[1:5]"

        ast = self.parse_source(source)

        # Verify structure
        stmt = ast.body[0]
        expr = stmt.expression
        assert isinstance(expr, SubscriptExpression)

        # Check that index is a slice
        slice_expr = expr.index
        assert isinstance(slice_expr, SliceExpression)

        # Check start
        assert isinstance(slice_expr.start, LiteralExpression)
        assert slice_expr.start.value == "1"

        # Check stop
        assert isinstance(slice_expr.stop, LiteralExpression)
        assert slice_expr.stop.value == "5"

        # Check step (should be None)
        assert slice_expr.step is None

    def test_slice_only_stop(self):
        """Test slice with only stop value."""
        source = "arr[:5]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start is None  # No start
        assert slice_expr.stop.value == "5"  # Has stop
        assert slice_expr.step is None  # No step

    def test_slice_only_start(self):
        """Test slice with only start value."""
        source = "arr[1:]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start.value == "1"  # Has start
        assert slice_expr.stop is None  # No stop
        assert slice_expr.step is None  # No step

    def test_slice_full(self):
        """Test full slice (all elements)."""
        source = "arr[:]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start is None  # No start
        assert slice_expr.stop is None   # No stop
        assert slice_expr.step is None   # No step

    def test_slice_with_step(self):
        """Test slice with start, stop, and step."""
        source = "arr[1:5:2]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start.value == "1"  # Has start
        assert slice_expr.stop.value == "5"   # Has stop
        assert slice_expr.step.value == "2"   # Has step

    def test_slice_only_step(self):
        """Test slice with only step (every nth element)."""
        source = "arr[::2]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start is None      # No start
        assert slice_expr.stop is None       # No stop
        assert slice_expr.step.value == "2"  # Has step

    def test_slice_stop_and_step(self):
        """Test slice with stop and step."""
        source = "arr[:5:2]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start is None      # No start
        assert slice_expr.stop.value == "5"  # Has stop
        assert slice_expr.step.value == "2"  # Has step

    def test_slice_start_and_step(self):
        """Test slice with start and step."""
        source = "arr[1::2]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)
        assert slice_expr.start.value == "1"  # Has start
        assert slice_expr.stop is None        # No stop
        assert slice_expr.step.value == "2"   # Has step

    def test_complex_expressions_in_slice(self):
        """Test slice with complex expressions."""
        source = "arr[a+1:b*2:c-1]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression
        slice_expr = expr.index

        assert isinstance(slice_expr, SliceExpression)

        # All parts should be present but we don't need to check their internal structure
        # Just verify they're not None and are expressions
        assert slice_expr.start is not None
        assert slice_expr.stop is not None
        assert slice_expr.step is not None

    def test_nested_subscript(self):
        """Test nested subscript access."""
        source = "matrix[0][1]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression

        # Outer subscript
        assert isinstance(expr, SubscriptExpression)
        assert expr.index.value == "1"

        # Inner subscript
        inner_expr = expr.object
        assert isinstance(inner_expr, SubscriptExpression)
        assert inner_expr.index.value == "0"

        # Base object
        assert isinstance(inner_expr.object, IdentifierExpression)
        assert inner_expr.object.name == "matrix"

    def test_slice_on_method_call(self):
        """Test slice on method call result."""
        source = "get_array()[1:5]"

        ast = self.parse_source(source)

        stmt = ast.body[0]
        expr = stmt.expression

        # Should be a subscript expression
        assert isinstance(expr, SubscriptExpression)

        # Object should be a call expression
        from parser.ast_nodes import CallExpression
        assert isinstance(expr.object, CallExpression)

        # Index should be a slice
        assert isinstance(expr.index, SliceExpression)
        assert expr.index.start.value == "1"
        assert expr.index.stop.value == "5"
