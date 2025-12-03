"""Tests for the compile-time type checker."""

from types import SimpleNamespace

from spice.lexer import Lexer
from spice.parser import Parser
from spice.compilation.checks import SymbolTableBuilder, TypeChecker
from testutils import log_test_start, log_test_result, safe_assert


class TestTypeChecker:
    """Ensure the type checker validates call sites."""

    def build_file(self, source: str):
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        parser = Parser()
        ast = parser.parse(tokens)
        return SimpleNamespace(ast=ast)

    def run_type_check(self, source: str):
        log_test_start("type_check", source)
        fake_file = self.build_file(source)
        SymbolTableBuilder().check(fake_file)
        checker = TypeChecker()
        result = checker.check(fake_file)
        log_test_result("type_check", str(checker.errors))
        return result, checker.errors

    def test_detects_argument_type_mismatch(self):
        """Using wrong argument types should fail type checking."""
        source = """class A {
    def func(a: int, b: str) -> None {
        return;
    }

    def func(a: int, b: int) -> None {
        return;
    }
}

a = A();
b: str = "b";
c: str = "c";
a.func(b, c);
"""
        result, errors = self.run_type_check(source)
        safe_assert(not result, "Type checker should fail for mismatched arguments", errors)
        safe_assert(any("func" in error for error in errors), "Error should mention method name", errors)

    def test_accepts_matching_arguments(self):
        """Valid argument types should pass the checker."""
        source = """class A {
    def func(a: int, b: str) -> None {
        return;
    }
}

value = 5;
label = "hello";
A().func(value, label);
"""
        result, errors = self.run_type_check(source)
        safe_assert(result, "Type checker should pass for matching arguments", errors)

    def test_requires_annotation_for_non_literal_assignment(self):
        """Assignments from variables/functions must declare types."""
        source = """
value: str = "hello";
alias = value;
"""
        result, errors = self.run_type_check(source)
        safe_assert(
            not result,
            "Type checker should fail when assignment lacks annotation",
            errors,
        )
        safe_assert(
            any("alias" in error for error in errors),
            "Error should mention the variable needing annotation",
            errors,
        )

    def test_constructor_assignment_infers_type(self):
        """Constructors should provide type information automatically."""
        source = """class B {
    def __init__(self) -> None {
        return;
    }
}

inst = B();
inst2 = B();
"""
        result, errors = self.run_type_check(source)
        safe_assert(result, "Constructor assignments should be inferred", errors)
