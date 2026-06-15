# Drawing primitives.
#
# `Drawable` is the contract every shape honours; `Shape` is an abstract base
# that implements the shared part (a label + a textual description) and leaves
# `area` for concrete shapes to provide.

interface Drawable {
    def area() -> float
    def describe() -> str
}


abstract class Shape implements Drawable {
    def Shape(kind: str) {
        self.kind = kind
    }

    abstract def area() -> float

    def describe() -> str {
        return f"{self.kind}: area={self.area():.2f}"
    }
}


class Circle extends Shape {
    def Circle(radius: float) {
        super("circle")
        self.radius = radius
    }

    def area() -> float {
        return 3.14159 * self.radius * self.radius
    }
}


class Rectangle extends Shape {
    def Rectangle(width: float, height: float) {
        super("rectangle")
        self.width = width
        self.height = height
    }

    def area() -> float {
        return self.width * self.height
    }
}


final class Square extends Rectangle {
    def Square(side: float) {
        super(side, side)
        self.kind = "square"
    }
}
