# =============================================================================
# Generics
# =============================================================================
#
# Python expresses generics with `typing.Generic` and `TypeVar` declared
# separately. Spice uses angle-bracket parameters right on the class:
#
#   class Box<T> { ... }
#   class Pair<K, V> { ... }
#   class Sorted<T extends Comparable>
#
# This compiles to `Generic[...]` with the matching `TypeVar`s. Inside the class
# the parameters (`T`, `K`, ...) are usable as ordinary types.


# A container generic over one type.
class Box<T> {
    def Box(value: T) {
        self.value = value
    }

    def get() -> T {
        return self.value
    }
}


# Two type parameters.
class Pair<K, V> {
    def Pair(key: K, value: V) {
        self.key = key
        self.value = value
    }

    def get_key() -> K {
        return self.key
    }

    def get_value() -> V {
        return self.value
    }
}


# A classic generic data structure.
class Stack<T> {
    def Stack() {
        self.items: list = []
    }

    def push(item: T) -> None {
        self.items.append(item)
    }

    def pop() -> T {
        return self.items.pop()
    }

    def is_empty() -> bool {
        return len(self.items) == 0
    }
}


# A bounded type parameter: T must satisfy the Comparable contract.
interface Comparable {
    def compare_to(other: Comparable) -> int
}

class SortedBox<T implements Comparable> {
    def SortedBox(value: T) {
        self.value = value
    }

    def is_greater_than(other: T) -> bool {
        return self.value.compare_to(other) > 0
    }
}


def main() -> None {
    b: Box = Box(42)
    print(f"box holds {b.get()}")

    p: Pair = Pair("answer", 42)
    print(f"pair = ({p.get_key()}, {p.get_value()})")

    s: Stack = Stack()
    s.push(1)
    s.push(2)
    s.push(3)
    print(f"popped {s.pop()}, empty? {s.is_empty()}")
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 030-generics.spc -o build
#     python build/030-generics.py
# -----------------------------------------------------------------------------
