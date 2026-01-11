"""Tests for Cython code emission."""

from types import SimpleNamespace

from spice.compilation.checks import MethodOverloadResolver
from spice.lexer import Lexer
from spice.parser import Parser
from spice.transformer import Transformer
from testutils import (
    presentIn, assert_contains_all, assert_count,
    log_test_start, log_test_result, assert_lacking
)


class TestCythonEmit:
    """Test Cython code generation."""

    def transform_source(self, source: str, emit: str = "pyx") -> str:
        """Helper to transform source code with specified emit mode."""
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        parser = Parser()
        ast = parser.parse(tokens)

        resolver = MethodOverloadResolver()
        fake_file = SimpleNamespace(ast=ast, method_overload_table={})
        resolver.check(fake_file)

        transformer = Transformer(emit=emit)
        return transformer.transform(ast)

    def test_cython_header(self):
        """Test that Cython output includes proper header."""
        source = """def hello() -> str {
    return "world";
}"""
        log_test_start("test_cython_header", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_header", result)

        assert_contains_all(result, [
            "# cython: language_level=3",
            "Cython file generated with Spice"
        ], "cython header")

    def test_python_header(self):
        """Test that Python output does NOT include Cython header."""
        source = """def hello() -> str {
    return "world";
}"""
        log_test_start("test_python_header", source)
        result = self.transform_source(source, emit="py")
        log_test_result("test_python_header", result)

        assert_lacking(result, "# cython:", "python header should not have cython directive")
        assert_lacking(result, "Cython file generated", "python header should not mention Cython")

    def test_cython_function_cpdef(self):
        """Test that top-level functions use cpdef with C-style return type."""
        source = """def greet(name: str) -> str {
    return f"Hello {name}";
}"""
        log_test_start("test_cython_function_cpdef", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_function_cpdef", result)

        # Cython uses C-style: cpdef str greet(name: str):
        presentIn(result, "cpdef str greet(name: str):", "cpdef with C-style return type")

    def test_python_function_def(self):
        """Test that Python mode still uses def."""
        source = """def greet(name: str) -> str {
    return f"Hello {name}";
}"""
        log_test_start("test_python_function_def", source)
        result = self.transform_source(source, emit="py")
        log_test_result("test_python_function_def", result)

        presentIn(result, "def greet(name: str) -> str:", "def for functions")
        assert_lacking(result, "cpdef", "python should not use cpdef")

    def test_cython_class_cdef(self):
        """Test that classes use cdef class in Cython mode."""
        source = """class Point {
    def __init__(x: int, y: int) {
        self.x = x;
        self.y = y;
    }
}"""
        log_test_start("test_cython_class_cdef", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_class_cdef", result)

        presentIn(result, "cdef class Point:", "cdef class for classes")

    def test_python_class_regular(self):
        """Test that Python mode uses regular class."""
        source = """class Point {
    def __init__(x: int, y: int) {
        self.x = x;
        self.y = y;
    }
}"""
        log_test_start("test_python_class_regular", source)
        result = self.transform_source(source, emit="py")
        log_test_result("test_python_class_regular", result)

        presentIn(result, "class Point:", "regular class in python")
        assert_lacking(result, "cdef class", "python should not use cdef class")

    def test_cython_method_cpdef(self):
        """Test that class methods use cpdef with C-style return type."""
        source = """class Calculator {
    def add(a: int, b: int) -> int {
        return a + b;
    }
}"""
        log_test_start("test_cython_method_cpdef", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_method_cpdef", result)

        # Cython uses C-style: cpdef int add(self, a: int, b: int):
        presentIn(result, "cpdef int add(self, a: int, b: int):", "cpdef with C-style return type")

    def test_cython_type_mapping_float(self):
        """Test that float types are mapped to double in Cython."""
        source = """def calculate(x: float) -> float {
    return x * 2.0;
}"""
        log_test_start("test_cython_type_mapping_float", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_type_mapping_float", result)

        presentIn(result, "x: double", "float -> double mapping")
        # C-style return type: cpdef double calculate(...)
        presentIn(result, "cpdef double calculate", "return type double mapping")

    def test_cython_type_mapping_bool(self):
        """Test that bool types are mapped to bint in Cython."""
        source = """def is_valid(flag: bool) -> bool {
    return flag;
}"""
        log_test_start("test_cython_type_mapping_bool", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_type_mapping_bool", result)

        presentIn(result, "flag: bint", "bool -> bint mapping")
        # C-style return type: cpdef bint is_valid(...)
        presentIn(result, "cpdef bint is_valid", "return type bint mapping")

    def test_cython_no_final_decorator(self):
        """Test that Cython mode omits @final decorator."""
        source = """final class ImmutablePoint {
    def get_x() -> int {
        return 0;
    }
}"""
        log_test_start("test_cython_no_final_decorator", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_no_final_decorator", result)

        assert_lacking(result, "@final", "cython should not use @final decorator")
        presentIn(result, "cdef class ImmutablePoint:", "cdef class without decorator")

    def test_python_final_decorator(self):
        """Test that Python mode includes @final decorator."""
        source = """final class ImmutablePoint {
    def get_x() -> int {
        return 0;
    }
}"""
        log_test_start("test_python_final_decorator", source)
        result = self.transform_source(source, emit="py")
        log_test_result("test_python_final_decorator", result)

        presentIn(result, "@final", "python should use @final decorator")

    def test_cython_no_generic_typevar(self):
        """Test that Cython mode omits Generic[T] (uses monomorphization)."""
        source = """class Box<T> {
    def get() -> T {
        return self.value;
    }
}"""
        log_test_start("test_cython_no_generic_typevar", source)
        result = self.transform_source(source, emit="pyx")
        log_test_result("test_cython_no_generic_typevar", result)

        assert_lacking(result, "Generic[T]", "cython should not use Generic[T]")
        assert_lacking(result, "TypeVar", "cython should not use TypeVar")

    def test_python_generic_typevar(self):
        """Test that Python mode includes Generic[T] and TypeVar."""
        source = """class Box<T> {
    def get() -> T {
        return self.value;
    }
}"""
        log_test_start("test_python_generic_typevar", source)
        result = self.transform_source(source, emit="py")
        log_test_result("test_python_generic_typevar", result)

        presentIn(result, "Generic[T]", "python should use Generic[T]")
        presentIn(result, "TypeVar", "python should use TypeVar")

    def test_exe_mode_same_as_pyx(self):
        """Test that exe mode produces same output as pyx mode."""
        source = """class Calculator {
    def add(a: int, b: int) -> int {
        return a + b;
    }
}"""
        log_test_start("test_exe_mode_same_as_pyx", source)

        result_pyx = self.transform_source(source, emit="pyx")
        result_exe = self.transform_source(source, emit="exe")

        log_test_result("test_exe_mode_pyx", result_pyx)
        log_test_result("test_exe_mode_exe", result_exe)

        assert result_pyx == result_exe, "exe mode should produce same code as pyx mode"
