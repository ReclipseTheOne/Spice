"""Tests for the generic bound checker.

A bound (`<T extends C>` / `<T implements C>`) only requires that the concrete
type bound to `T` has `C` somewhere in its inheritance tree - reached by any mix
of `extends` / `implements` links. The two keywords are interchangeable.
"""

from spice.lexer import Lexer
from spice.parser import Parser
from spice.compilation import SpiceFile
from spice.compilation.checks import SymbolTableBuilder, GenericBoundChecker
from testutils import log_test_start, log_test_result, safe_assert


def run_bound_check(source: str):
    file = SpiceFile.empty(source)
    file.tokens = Lexer().tokenize(source)
    file.ast = Parser().parse(file.tokens)
    SymbolTableBuilder().check(file)
    checker = GenericBoundChecker()
    log_test_start("generic_bound", source)
    result = checker.check(file)
    log_test_result("generic_bound", str(checker.errors))
    return result, checker.errors


COMMON = """interface Comparable {
    def compare_to(other: Comparable) -> int
}

class Money implements Comparable {
    def Money() -> None {
        self.cents = 0
    }
    def compare_to(other: Comparable) -> int {
        return 0
    }
}

class Plain {
    def Plain() -> None {
        self.x = 0
    }
}

class SortedBox<T extends Comparable> {
    def SortedBox(value: T) -> None {
        self.value = value
    }
}
"""


class TestGenericBounds:
    def test_argument_satisfying_bound_passes(self):
        """Money implements Comparable -> SortedBox(Money()) is fine."""
        source = COMMON + "ok = SortedBox(Money());\n"
        result, errors = run_bound_check(source)
        safe_assert(result, "Money satisfies the Comparable bound", errors)

    def test_argument_violating_bound_fails(self):
        """Plain lacks Comparable -> SortedBox(Plain()) is an error."""
        source = COMMON + "bad = SortedBox(Plain());\n"
        result, errors = run_bound_check(source)
        safe_assert(not result, "Plain should not satisfy the Comparable bound", errors)
        safe_assert(
            any("Comparable" in str(e) and "Plain" in str(e) for e in errors),
            "Error should name the offending type and bound",
            errors,
        )

    def test_transitive_inheritance_satisfies_bound(self):
        """A bound is satisfied through a chain of extends/implements links."""
        source = COMMON + """
class PreciseMoney extends Money {
    def PreciseMoney() -> None {
        super();
    }
}

ok2 = SortedBox(PreciseMoney());
"""
        result, errors = run_bound_check(source)
        safe_assert(result, "PreciseMoney inherits Comparable via Money", errors)

    def test_implements_keyword_in_bound_is_accepted(self):
        """`<T implements C>` is just a synonym for `<T extends C>`."""
        source = COMMON.replace("<T extends Comparable>", "<T implements Comparable>")
        source += "ok = SortedBox(Money());\n"
        result, errors = run_bound_check(source)
        safe_assert(result, "implements bound keyword should be accepted", errors)

    def test_unbounded_generic_is_never_flagged(self):
        """A plain `<T>` has no bound, so anything goes."""
        source = """class Box<T> {
    def Box(value: T) -> None {
        self.value = value
    }
}

anything = Box(Box(123));
"""
        result, errors = run_bound_check(source)
        safe_assert(result, "Unbounded generics accept any argument", errors)
