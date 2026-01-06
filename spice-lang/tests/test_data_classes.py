"""Tests for data class declarations."""

from types import SimpleNamespace

from spice.compilation.checks import MethodOverloadResolver
from spice.lexer import Lexer
from spice.parser import Parser, DataClassDeclaration
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


class TestDataClasses:
    """Tests for data class declarations."""

    def test_simple_data_class(self):
        """Test simple data class without methods."""
        code = "data class Point(x: int, y: int);"
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], DataClassDeclaration)
        assert ast.body[0].name == "Point"
        assert len(ast.body[0].fields) == 2
        assert ast.body[0].fields[0].name == "x"
        assert ast.body[0].fields[0].type_annotation == "int"
        assert ast.body[0].fields[1].name == "y"
        assert ast.body[0].fields[1].type_annotation == "int"

    def test_data_class_with_methods(self):
        """Test data class with methods."""
        code = """
data class Person(name: str, age: int) {
    def greet() -> str {
        return f"Hi";
    }
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], DataClassDeclaration)
        assert ast.body[0].name == "Person"
        assert len(ast.body[0].fields) == 2
        assert len(ast.body[0].body) == 1  # One method

    def test_data_class_transformer(self):
        """Test data class transformation to Python."""
        code = "data class Point(x: int, y: int);"
        output = transform_source(code)

        presentIn(output, "from dataclasses import dataclass")
        presentIn(output, "@dataclass")
        presentIn(output, "class Point:")
        presentIn(output, "x: int")
        presentIn(output, "y: int")

    def test_multiline_parameters(self):
        """Test data class with multiline parameter declarations."""
        code = """
data class Config(
    host: str,
    port: int,
    debug: bool
);
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], DataClassDeclaration)
        assert ast.body[0].name == "Config"
        assert len(ast.body[0].fields) == 3
        assert ast.body[0].fields[0].name == "host"
        assert ast.body[0].fields[1].name == "port"
        assert ast.body[0].fields[2].name == "debug"

    def test_multiline_function_parameters(self):
        """Test function with multiline parameter declarations."""
        from spice.parser import FunctionDeclaration

        code = """
def create_user(
    name: str,
    email: str,
    age: int
) -> None {
    pass;
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], FunctionDeclaration)
        assert ast.body[0].name == "create_user"
        assert len(ast.body[0].params) == 3
        assert ast.body[0].params[0].name == "name"
        assert ast.body[0].params[1].name == "email"
        assert ast.body[0].params[2].name == "age"
