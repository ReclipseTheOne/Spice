"""Tests for generic type parameters."""

from types import SimpleNamespace

from spice.compilation.checks import MethodOverloadResolver
from spice.lexer import Lexer
from spice.parser import Parser, ClassDeclaration
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


class TestGenerics:
    """Tests for generic type parameters."""

    def test_generic_class_parsing(self):
        """Test parsing generic class."""
        code = """
class Box<T> {
    def get() -> T {
        return self.value;
    }
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], ClassDeclaration)
        assert ast.body[0].name == "Box"
        assert len(ast.body[0].type_parameters) == 1
        assert ast.body[0].type_parameters[0].name == "T"

    def test_generic_class_with_bound(self):
        """Test parsing generic class with bound."""
        code = """
class Ordered<T extends Comparable> {
    pass;
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], ClassDeclaration)
        assert ast.body[0].name == "Ordered"
        assert len(ast.body[0].type_parameters) == 1
        assert ast.body[0].type_parameters[0].name == "T"
        assert ast.body[0].type_parameters[0].bound == "Comparable"

    def test_multiple_type_parameters(self):
        """Test parsing class with multiple type parameters."""
        code = """
class Pair<K, V> {
    pass;
}
"""
        ast = parse_source(code)

        assert len(ast.body) == 1
        assert isinstance(ast.body[0], ClassDeclaration)
        assert ast.body[0].name == "Pair"
        assert len(ast.body[0].type_parameters) == 2
        assert ast.body[0].type_parameters[0].name == "K"
        assert ast.body[0].type_parameters[1].name == "V"

    def test_generic_class_transformer(self):
        """Test generic class transformation to Python."""
        code = """
class Box<T> {
    def get() -> T {
        return self.value;
    }
}
"""
        output = transform_source(code)

        presentIn(output, "from typing import Generic, TypeVar")
        presentIn(output, "T = TypeVar('T')")
        presentIn(output, "class Box(Generic[T]):")

    def test_bounded_generic_transformer(self):
        """Test bounded generic class transformation to Python."""
        code = """
class Ordered<T extends Comparable> {
    pass;
}
"""
        output = transform_source(code)

        presentIn(output, "from typing import Generic, TypeVar")
        presentIn(output, "T = TypeVar('T', bound=Comparable)")
        presentIn(output, "class Ordered(Generic[T]):")

    def test_multiple_type_params_transformer(self):
        """Test multiple type parameters transformation."""
        code = """
class Pair<K, V> {
    pass;
}
"""
        output = transform_source(code)

        presentIn(output, "from typing import Generic, TypeVar")
        presentIn(output, "K = TypeVar('K')")
        presentIn(output, "V = TypeVar('V')")
        presentIn(output, "class Pair(Generic[K, V]):")
