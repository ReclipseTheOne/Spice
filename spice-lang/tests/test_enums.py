"""Tests for enum declarations."""

from types import SimpleNamespace

from spice.compilation.checks import MethodOverloadResolver
from spice.lexer import Lexer
from spice.parser import Parser, EnumDeclaration
from spice.transformer import Transformer
from testutils import presentIn


def parse_source(source: str):
    """Helper to parse source code into AST."""
    lexer = Lexer()
    tokens = lexer.tokenize(source)
    parser = Parser()
    return parser.parse(tokens)


def transform_source(source: str) -> str:
    """Helper to transform source code."""
    lexer = Lexer()
    tokens = lexer.tokenize(source)
    parser = Parser()
    ast = parser.parse(tokens)

    resolver = MethodOverloadResolver()
    fake_file = SimpleNamespace(ast=ast, method_overload_table={})
    resolver.check(fake_file)

    transformer = Transformer()
    return transformer.transform(ast)


class TestEnums:
    """Tests for enum declarations."""

    def test_simple_enum(self):
        """Test simple enum without constructor."""
        code = "enum Color { RED, GREEN, BLUE }"
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], EnumDeclaration)
        assert ast.body[0].name == "Color"
        assert len(ast.body[0].members) == 3
        assert ast.body[0].members[0].name == "RED"
        assert ast.body[0].members[1].name == "GREEN"
        assert ast.body[0].members[2].name == "BLUE"

    def test_enum_with_args(self):
        """Test enum with constructor arguments."""
        code = """
enum Planet {
    EARTH(5970000, 6371000),
    MARS(639000, 3389000)
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], EnumDeclaration)
        assert ast.body[0].name == "Planet"
        assert len(ast.body[0].members) == 2
        assert ast.body[0].members[0].name == "EARTH"
        assert len(ast.body[0].members[0].args) == 2
        assert ast.body[0].members[1].name == "MARS"
        assert len(ast.body[0].members[1].args) == 2

    def test_enum_with_constructor(self):
        """Test enum with constructor method."""
        code = """
enum Planet {
    EARTH(5970000, 6371000);

    def Planet(self, mass: float, radius: float) -> None {
        self.mass = mass;
    }
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], EnumDeclaration)
        assert ast.body[0].name == "Planet"
        assert len(ast.body[0].members) == 1
        assert len(ast.body[0].body) == 1  # One constructor

    def test_simple_enum_transformer(self):
        """Test simple enum transformation to Python."""
        code = "enum Color { RED, GREEN, BLUE }"
        output = transform_source(code)

        presentIn(output, "from enum import Enum, auto")
        presentIn(output, "class Color(Enum):")
        presentIn(output, "RED = auto()")
        presentIn(output, "GREEN = auto()")
        presentIn(output, "BLUE = auto()")

    def test_enum_with_args_transformer(self):
        """Test enum with args transformation to Python."""
        code = """
enum Planet {
    EARTH(5970000, 6371000),
    MARS(639000, 3389000)
}
"""
        output = transform_source(code)

        presentIn(output, "from enum import Enum")
        presentIn(output, "class Planet(Enum):")
        presentIn(output, "EARTH = (")
        presentIn(output, "MARS = (")
