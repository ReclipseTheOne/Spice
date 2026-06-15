# =============================================================================
# Classes and simple constructors
# =============================================================================
#
# Classes work like Python classes (methods, attributes, `self.x` in bodies),
# with the braces-and-types syntax from 001. Spice adds two pieces of sugar:
#
#   1. No explicit `self` parameter.
#      You never write `self` in a method's parameter list - the transformer
#      adds it for you. You still use `self.x` inside the body to reach state.
#      (Static methods get no `self`; see 015.)
#
#   2. Simple constructors.
#      A method named after the class becomes the constructor:
#
#          def ClassName(...) { ... }   ->   def __init__(self, ...): ...
#
#      `def __init__` still works if you prefer it - the named form is just
#      cleaner to read.


class Vector {
    # Simple constructor: the method name matches the class name.
    def Vector(x: float, y: float) {
        self.x = x
        self.y = y
    }

    def length() -> float {
        return (self.x * self.x + self.y * self.y) ** 0.5
    }

    def add(other: Vector) -> Vector {
        return Vector(self.x + other.x, self.y + other.y)
    }

    def describe() -> str {
        return f"Vector({self.x}, {self.y}) with length {self.length():.3f}"
    }
}


def main() -> None {
    a: Vector = Vector(3.0, 4.0)
    b: Vector = Vector(1.0, 2.0)

    print(a.describe())
    print(b.describe())

    c: Vector = a.add(b)
    print(f"a + b = {c.describe()}")
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 010-classes_and_constructors.spc -o build
#     python build/010-classes_and_constructors.py
# -----------------------------------------------------------------------------
