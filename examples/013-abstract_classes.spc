# =============================================================================
# Abstract classes
# =============================================================================
#
# An abstract class sits between an interface and a concrete class: it can mix
# method signatures that subclasses MUST implement with ordinary methods that
# they inherit as-is. In Python this means `ABC` + `@abstractmethod`; Spice gives
# you keywords:
#
#   abstract class Name {
#       abstract def must_implement() -> Type   # no body, subclass provides it
#       def shared() -> Type { ... }            # concrete, inherited
#   }
#
# Abstract classes can't be instantiated directly, can hold a constructor and
# state, and can implement interfaces.


interface Drawable {
    def draw() -> None
}


abstract class Shape implements Drawable {
    def Shape(color: str) {
        self.color = color
    }

    # Subclasses must implement these.
    abstract def area() -> float
    abstract def draw() -> None

    def describe() -> str {
        return f"A {self.color} shape of area {self.area():.2f}"
    }
}


class Circle extends Shape {
    def Circle(color: str, radius: float) {
        super(color)
        self.radius = radius
    }

    def area() -> float {
        return 3.14159 * self.radius * self.radius
    }

    def draw() -> None {
        print(f"Drawing a {self.color} circle (r={self.radius})")
    }
}


class Square extends Shape {
    def Square(color: str, side: float) {
        super(color)
        self.side = side
    }

    def area() -> float {
        return self.side * self.side
    }

    def draw() -> None {
        print(f"Drawing a {self.color} square (s={self.side})")
    }
}


def main() -> None {
    shapes: list = [Circle("red", 2.0), Square("blue", 3.0)]
    for shape in shapes {
        shape.draw()
        print(shape.describe())     # inherited from the abstract base
    }
}

main()


# -----------------------------------------------------------------------------
# Trying to instantiate `Shape` directly, or forgetting to implement `area`
# in a subclass, is a compile-time error.
# -----------------------------------------------------------------------------
#
# Compile and run:
#
#     spicy 013-abstract_classes.spc -o build
#     python build/013-abstract_classes.py
# -----------------------------------------------------------------------------
