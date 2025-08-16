"""Tests for the Spice to Python transformer."""

from spice.lexer import Lexer
from spice.parser import Parser
from spice.transformer import Transformer
from testutils import (
    presentIn, assert_contains_all, assert_count,
    log_test_start, log_test_result, debug_diff, safe_assert,
    assert_lacking
)


class TestTransformer:
    """Test transformer functionality."""

    def transform_source(self, source: str) -> str:
        """Helper to transform source code."""
        try:
            lexer = Lexer()
            tokens = lexer.tokenize(source)

            # Log tokenization for debugging
            print(f"🔍 Tokenized {len(tokens)} tokens:", flush=True)
            for i, token in enumerate(tokens):
                print(f"   {i:2}: {token.type.name:15} = {repr(token.value)}", flush=True)

            parser = Parser()
            ast = parser.parse(tokens)
            transformer = Transformer()
            return transformer.transform(ast)
        except Exception as e:
            print(f"\n❌ PARSING/TRANSFORMATION FAILED: {type(e).__name__}", flush=True)
            print(f"   Error: {e}", flush=True)
            print(f"   Source code that failed:", flush=True)
            for i, line in enumerate(source.strip().split('\n'), 1):
                print(f"   {i:2}: {line}", flush=True)
            print(flush=True)
            raise

    def test_interface_to_protocol(self):
        """Test interface transformation to Protocol."""
        source = """interface Drawable {
    def draw(x: int, y: int) -> None;
}"""

        log_test_start("test_interface_to_protocol", source)
        result = self.transform_source(source)
        log_test_result("test_interface_to_protocol", result)

        assert_contains_all(result, [
            "from typing import Protocol",
            "from abc import ABC, abstractmethod",
            "class Drawable(Protocol):",
            "def draw(self, x: int, y: int) -> None:",
            "..."
        ], "interface to protocol transformation")

    def test_interface_with_inheritance(self):
        """Test interface with base transformation."""
        source = """interface Colorable extends Drawable {
    def set_color(color: str) -> None;
}"""

        log_test_start("test_interface_with_inheritance", source)
        result = self.transform_source(source)
        log_test_result("test_interface_with_inheritance", result)

        assert_contains_all(result, [
            "class Colorable(Protocol, Drawable):",
            "def set_color(self, color: str) -> None:"
        ], "interface inheritance transformation")

    def test_empty_interface(self):
        """Test empty interface transformation."""
        source = """interface Empty {
}"""

        log_test_start("test_empty_interface", source)
        result = self.transform_source(source)
        log_test_result("test_empty_interface", result)

        assert_contains_all(result, [
            "class Empty(Protocol):",
            "pass"
        ], "empty interface transformation")

    def test_multiple_methods(self):
        """Test interface with multiple methods."""
        source = """interface Shape {
    def area() -> float;
    def perimeter() -> float;
    def draw(x: int, y: int) -> None;
}"""

        log_test_start("test_multiple_methods", source)
        result = self.transform_source(source)
        log_test_result("test_multiple_methods", result)

        # Check individual method signatures
        assert_contains_all(result, [
            "def area(self) -> float:",
            "def perimeter(self) -> float:",
            "def draw(self, x: int, y: int) -> None:"
        ], "multiple method signatures")

        # Check exact counts
        assert_lacking(result, "@abstractmethod", "Interface methods should not have @abstractmethod since it uses Protocol")
        assert_count(result, "...", 3, "stub statements")

    def test_no_imports_when_not_needed(self):
        """Test that imports are not added when not needed."""
        source = ""  # Empty file

        log_test_start("test_no_imports_when_not_needed", source)
        result = self.transform_source(source)
        log_test_result("test_no_imports_when_not_needed", result)

        # Use safe_assert for negative assertions with debug info
        safe_assert(
            "from typing import Protocol" not in result,
            "Protocol import should not be present in empty file",
            f"Result: {repr(result)}"
        )
        safe_assert(
            "from abc import ABC" not in result,
            "ABC import should not be present in empty file",
            f"Result: {repr(result)}"
        )
        safe_assert(
            "from typing import final" not in result,
            "final import should not be present in empty file",
            f"Result: {repr(result)}"
        )

    def test_abstract_class(self):
        """Test abstract class transformation."""
        source = """abstract class Animal {
    abstract def make_sound() -> str;

    def eat() -> None {
        pass;
    }
}"""

        log_test_start("test_abstract_class", source)
        result = self.transform_source(source)
        log_test_result("test_abstract_class", result)

        assert_contains_all(result, [
            "from abc import ABC, abstractmethod",
            "class Animal(ABC):",
            "@abstractmethod",
            "def make_sound(self) -> str:",
            "def eat(self) -> None:"
        ], "abstract class transformation")

    def test_final_class(self):
        """Test final class transformation."""
        source = """final class Dog {
    def bark() -> None {
        pass;
    }
}"""

        log_test_start("test_final_class", source)
        result = self.transform_source(source)
        log_test_result("test_final_class", result)

        assert_contains_all(result, [
            "from typing import final",
            "@final",
            "class Dog:",
            "def bark(self) -> None:"
        ], "final class transformation")

    def test_static_method(self):
        """Test static method transformation."""
        source = """class Utility {
    static def helper() -> str {
        pass;
    }

    def instance_method() -> None {
        pass;
    }
}"""

        log_test_start("test_static_method", source)
        result = self.transform_source(source)
        log_test_result("test_static_method", result)

        assert_contains_all(result, [
            "@staticmethod",
            "def helper() -> str:",  # No self parameter for static methods
            "def instance_method(self) -> None:"  # Self parameter for instance methods
        ], "static method transformation")

    def test_extends_inheritance(self):
        """Test class inheritance with extends keyword."""
        source = """class Animal {
    def eat() -> None {
        pass;
    }
}

class Dog extends Animal {
    def bark() -> None {
        pass;
    }
}"""

        log_test_start("test_extends_inheritance", source)
        result = self.transform_source(source)
        log_test_result("test_extends_inheritance", result)

        assert_contains_all(result, [
            "class Animal:",
            "class Dog(Animal):",
            "def eat(self) -> None:",
            "def bark(self) -> None:"
        ], "extends inheritance transformation")

    def test_implements_interfaces(self):
        """Test interface implementation with implements keyword."""
        source = """interface Drawable {
    def draw() -> None;
}

interface Colorable {
    def set_color(color: str) -> None;
}

class Shape implements Drawable, Colorable {
    def draw() -> None {
        pass;
    }

    def set_color(self, color: str) -> None {
        pass;
    }
}"""

        log_test_start("test_implements_interfaces", source)
        result = self.transform_source(source)
        log_test_result("test_implements_interfaces", result)

        assert_contains_all(result, [
            "from typing import Protocol",
            "class Drawable(Protocol):",
            "class Colorable(Protocol):",
            "class Shape(Drawable, Colorable):",
            "def draw(self) -> None:",
            "def set_color(self, color: str) -> None:"
        ], "implements interfaces transformation")

    def test_extends_and_implements_combined(self):
        """Test class that both extends and implements."""
        source = """interface Drawable {
    def draw() -> None;
}

abstract class Shape {
    abstract def area() -> float;
}

class Rectangle extends Shape implements Drawable {
    def area(self) -> float {
        pass;
    }

    def draw(self) -> None {
        pass;
    }
}"""

        log_test_start("test_extends_and_implements_combined", source)
        result = self.transform_source(source)
        log_test_result("test_extends_and_implements_combined", result)

        assert_contains_all(result, [
            "from abc import ABC, abstractmethod",
            "from typing import Protocol",
            "class Drawable(Protocol):",
            "class Shape(ABC):",
            "class Rectangle(Shape, Drawable):",  # Inheritance first, then interfaces
            "@abstractmethod",
            "def area(self) -> float:",
            "def draw(self) -> None:"
        ], "extends and implements combined transformation")

    def test_final_method(self):
        """Test final method transformation."""
        source = """class Animal {
    final def get_species() -> str {
        pass;
    }

    def make_sound() -> str {
        pass;
    }
}"""

        log_test_start("test_final_method", source)
        result = self.transform_source(source)
        log_test_result("test_final_method", result)

        assert_contains_all(result, [
            "from typing import final",
            "@final",
            "def get_species(self) -> str:",
            "def make_sound(self) -> str:"
        ], "final method transformation")

    def test_complex_class_hierarchy(self):
        """Test complex class hierarchy with all keywords."""
        source = """interface Drawable {
    def draw() -> None;
}

abstract class Shape {
    abstract def area() -> float;

    final def describe() -> str {
        pass;
    }

    static def get_shape_count() -> int {
        pass;
    }
}

final class Circle extends Shape implements Drawable {
    def area(self) -> float {
        pass;
    }

    def draw(self) -> None {
        pass;
    }

    static def create_unit_circle() -> None {
        pass;
    }
}"""

        log_test_start("test_complex_class_hierarchy", source)
        result = self.transform_source(source)
        log_test_result("test_complex_class_hierarchy", result)

        assert_contains_all(result, [
            "from abc import ABC, abstractmethod",
            "from typing import Protocol",
            "from typing import final",
            "class Drawable(Protocol):",
            "class Shape(ABC):",
            "@final",
            "class Circle(Shape, Drawable):",
            "@abstractmethod",
            "@staticmethod",
            "@final"
        ], "complex class hierarchy transformation")

        # Check that static methods don't have self parameter
        safe_assert(
            "def get_shape_count() -> int:" in result,
            "Static method should not have self parameter"
        )
        safe_assert(
            "def create_unit_circle() -> None:" in result,
            "Static method should not have self parameter"
        )

    def test_standalone_function_vs_method(self):
        """Test that standalone functions don't get self parameter."""
        source = """def standalone_function() -> None {
    pass;
}

class MyClass {
    def method() -> None {
        pass;
    }

    static def static_method() -> None {
        pass;
    }
}"""

        log_test_start("test_standalone_function_vs_method", source)
        result = self.transform_source(source)
        log_test_result("test_standalone_function_vs_method", result)

        assert_contains_all(result, [
            "def standalone_function() -> None:",  # No self
            "def method(self) -> None:",  # Has self
            "@staticmethod",
            "def static_method() -> None:"  # No self for static
        ], "standalone function vs method transformation")
