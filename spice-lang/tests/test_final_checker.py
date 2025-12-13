"""Tests for compile-time final checks."""

from types import SimpleNamespace

from spice.lexer import Lexer
from spice.parser import Parser
from spice.compilation.checks import FinalChecker


class TestFinalCheckerFinalMethods:
    """Ensure final methods cannot be overridden."""

    def _file_from_source(self, source: str):
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        parser = Parser()
        module = parser.parse(tokens)
        return SimpleNamespace(ast=module)

    def test_detects_direct_final_method_override(self):
        source = """
class A {
    final def func() -> None {
        return;
    }
}

class B extends A {
    def func() -> None {
        return;
    }
}
"""
        checker = FinalChecker()
        spice_file = self._file_from_source(source)
        result = checker.check(spice_file)

        assert not result
        assert any("Class 'B' cannot override final method 'func'" in str(error) for error in checker.errors)

    def test_detects_inherited_final_method_override(self):
        source = """
class A {
    final def func() -> None {
        return;
    }
}

class B extends A {
    def helper() -> None {
        return;
    }
}

class C extends B {
    def func() -> None {
        return;
    }
}
"""
        checker = FinalChecker()
        spice_file = self._file_from_source(source)
        result = checker.check(spice_file)

        assert not result
        assert any("Class 'C' cannot override final method 'func' defined in 'A'" in str(error) for error in checker.errors)

    def test_allows_subclass_without_override(self):
        source = """
class A {
    final def func() -> None {
        return;
    }
}

class B extends A {
    def helper() -> None {
        return;
    }
}
"""
        checker = FinalChecker()
        spice_file = self._file_from_source(source)
        result = checker.check(spice_file)

        assert result
        assert not checker.errors

    def test_detects_final_variable_reassignment(self):
        source = """
final a: int = 1;
a = 2;
"""
        checker = FinalChecker()
        spice_file = self._file_from_source(source)
        result = checker.check(spice_file)

        assert not result
        assert any("Cannot reassign final variable 'a'" in str(error) for error in checker.errors)
