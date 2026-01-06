"""Tests for constructor name transformation (ClassName -> __init__)."""

from types import SimpleNamespace

from spice.compilation.checks import MethodOverloadResolver
from spice.lexer import Lexer
from spice.parser import Parser
from spice.transformer import Transformer
from testutils import presentIn, assert_lacking


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


class TestConstructorNameTransformation:
    """Tests for constructor name transformation (ClassName -> __init__)."""

    def test_constructor_transformation(self):
        """Test that constructor using class name is transformed to __init__."""
        code = """
class Person {
    def Person(self, name: str) -> None {
        self.name = name;
    }
}
"""
        output = transform_source(code)

        presentIn(output, "def __init__(self, name: str) -> None:")
        assert_lacking(output, "def Person(self")

    def test_regular_method_not_transformed(self):
        """Test that regular methods are not transformed."""
        code = """
class Person {
    def Person(self, name: str) -> None {
        self.name = name;
    }

    def greet() -> str {
        return self.name;
    }
}
"""
        output = transform_source(code)

        presentIn(output, "def __init__(self, name: str) -> None:")
        presentIn(output, "def greet(self) -> str:")

    def test_enum_constructor_transformation(self):
        """Test that enum constructor is transformed to __init__."""
        code = """
enum Planet {
    EARTH(5970000);

    def Planet(self, mass: float) -> None {
        self.mass = mass;
    }
}
"""
        output = transform_source(code)

        presentIn(output, "def __init__(self, mass: float) -> None:")
        assert_lacking(output, "def Planet(self")

    def test_data_class_constructor_transformation(self):
        """Test that data class constructor is transformed to __init__."""
        code = """
data class Point(x: int, y: int) {
    def Point(self, x: int, y: int) -> None {
        self.x = x;
        self.y = y;
    }
}
"""
        output = transform_source(code)

        # Data classes with explicit constructors should transform the name
        assert_lacking(output, "def Point(self")

    def test_nested_class_constructor(self):
        """Test constructor transformation in nested context."""
        code = """
class Outer {
    def Outer(self) -> None {
        pass;
    }
}

class Inner {
    def Inner(self, value: int) -> None {
        self.value = value;
    }
}
"""
        output = transform_source(code)

        # Both should be transformed
        assert_lacking(output, "def Outer(self")
        assert_lacking(output, "def Inner(self")
        # Count __init__ occurrences
        assert output.count("def __init__") == 2

    def test_super_shorthand(self):
        """Test that super(...) is transformed to super().__init__(...)."""
        code = """
class Parent {
    def Parent(self, x: int) -> None {
        self.x = x;
    }
}

class Child extends Parent {
    def Child(self, x: int, y: int) -> None {
        super(x);
        self.y = y;
    }
}
"""
        output = transform_source(code)

        presentIn(output, "super().__init__(x)")
        assert_lacking(output, "super(x)")

    def test_super_shorthand_multiple_args(self):
        """Test super(...) with multiple arguments."""
        code = """
class Parent {
    def Parent(self, a: int, b: str) -> None {
        pass;
    }
}

class Child extends Parent {
    def Child(self, a: int, b: str, c: float) -> None {
        super(a, b);
    }
}
"""
        output = transform_source(code)

        presentIn(output, "super().__init__(a, b)")
