# =============================================================================
# Composition and Inheritance in Spice
# =============================================================================
#
# Spice provides a rich object-oriented programming model with:
#
# 1. Interfaces - Define contracts that classes must implement
#    interface Name { def method() -> Type; }
#
# 2. Abstract Classes - Base classes with abstract and concrete methods
#    abstract class Name { abstract def method() -> Type; }
#
# 3. Inheritance - Extend classes with `extends` keyword
#    class Child extends Parent { ... }
#
# 4. Interface Implementation - Implement interfaces with `implements`
#    class Name implements Interface1, Interface2 { ... }
#
# 5. Final Classes/Methods - Prevent further extension or override
#    final class Name { ... }
#    final def method() -> Type { ... }
#
# 6. Static Methods - Class-level methods that don't require an instance
#    static def method() -> Type { ... }
#
# Compiles to Python using ABC, Protocol, @final, and @staticmethod.
# =============================================================================


# =============================================================================
# INTERFACES
# =============================================================================
# Interfaces define a contract - a set of methods that implementing classes
# must provide. They contain only method signatures (no implementation).
#
# Syntax:
#   interface Name {
#       def method_name(param: Type) -> ReturnType;
#   }
#
# Interfaces can also extend other interfaces:
#   interface Child extends Parent { ... }

interface Drawable {
    def draw() -> None;
    def get_color() -> str;
}

interface Resizable {
    def resize(factor: float) -> None;
    def get_scale() -> float;
}

# Interface extending another interface
interface InteractiveShape extends Drawable {
    def on_click() -> None;
    def is_selected() -> bool;
}


# =============================================================================
# ABSTRACT CLASSES
# =============================================================================
# Abstract classes can contain both abstract methods (no implementation)
# and concrete methods (with implementation). They cannot be instantiated
# directly - you must create a subclass that implements all abstract methods.
#
# Syntax:
#   abstract class Name {
#       abstract def must_implement() -> Type;  # No body
#       def has_implementation() -> Type { ... }  # Has body
#   }
#
# Abstract classes can implement interfaces and extend other classes.

abstract class Shape implements Drawable {
    # Constructor - note: abstract classes can have constructors
    def Shape(self, color: str) -> None {
        self.color = color;
    }

    # Abstract methods - subclasses MUST implement these
    abstract def get_area() -> float;
    abstract def draw() -> None;

    # Final method - subclasses CANNOT override this
    final def get_color() -> str {
        return self.color;
    }

    # Static method - called on the class, not an instance
    static def get_shape_count() -> int {
        if not hasattr(Shape, '_count') {
            Shape._count = 0;
        }
        return Shape._count;
    }

    # Regular method - subclasses CAN override this
    def get_description() -> str {
        return f"A {self.color} shape";
    }
}


# =============================================================================
# INHERITANCE WITH `extends`
# =============================================================================
# Use `extends` to inherit from a parent class. The child class:
#   - Inherits all non-private methods and attributes
#   - Must implement all abstract methods from parent
#   - Can override non-final methods
#   - Can call parent methods using super()
#
# Syntax:
#   class Child extends Parent { ... }

class Circle extends Shape {
    def Circle(self, color: str, radius: float) -> None {
        # Call parent constructor - super(...) is shorthand for super().__init__(...)
        super(color);
        self.radius = radius;

        # Track instance count
        if hasattr(Shape, '_count') {
            Shape._count += 1;
        } else {
            Shape._count = 1;
        }
    }

    # Implement abstract method from Shape
    def get_area() -> float {
        return 3.14159 * self.radius * self.radius;
    }

    # Implement abstract method from Drawable (via Shape)
    def draw() -> None {
        print(f"Drawing a {self.color} circle with radius {self.radius}");
    }

    # Override the regular method from Shape
    def get_description() -> str {
        return f"A {self.color} circle with radius {self.radius}";
    }

    # Add new method specific to Circle
    def get_circumference() -> float {
        return 2 * 3.14159 * self.radius;
    }
}


# =============================================================================
# FINAL CLASSES
# =============================================================================
# A final class cannot be extended (subclassed). Use this when you want to
# prevent further inheritance, often for:
#   - Utility classes with only static methods
#   - Classes that should not be modified by extension
#   - Security-sensitive implementations
#
# Syntax:
#   final class Name { ... }

final class Square extends Shape {
    def Square(self, color: str, side: float) -> None {
        super(color);
        self.side = side;

        if hasattr(Shape, '_count') {
            Shape._count += 1;
        } else {
            Shape._count = 1;
        }
    }

    def get_area() -> float {
        return self.side * self.side;
    }

    def draw() -> None {
        print(f"Drawing a {self.color} square with side {self.side}");
    }

    # Final method - even if Square weren't final, this couldn't be overridden
    final def get_perimeter() -> float {
        return 4 * self.side;
    }
}


# =============================================================================
# MULTIPLE INTERFACE IMPLEMENTATION
# =============================================================================
# A class can implement multiple interfaces, providing all required methods.
#
# Syntax:
#   class Name implements Interface1, Interface2 { ... }
#   class Name extends Parent implements Interface1, Interface2 { ... }

class Rectangle extends Shape implements Resizable {
    def Rectangle(self, color: str, width: float, height: float) -> None {
        super(color);
        self.width = width;
        self.height = height;
        self.scale = 1.0;
    }

    # From Shape (abstract)
    def get_area() -> float {
        return self.width * self.height * self.scale * self.scale;
    }

    # From Drawable (via Shape)
    def draw() -> None {
        w: float = self.width * self.scale;
        h: float = self.height * self.scale;
        print(f"Drawing a {self.color} rectangle {w}x{h}");
    }

    # From Resizable interface
    def resize(factor: float) -> None {
        self.scale = self.scale * factor;
    }

    def get_scale() -> float {
        return self.scale;
    }
}


# =============================================================================
# STATIC UTILITY CLASSES
# =============================================================================
# A common pattern is a final class with only static methods - a utility class.
# These provide helper functions without requiring instantiation.
#
# Syntax:
#   final class Utils {
#       static def helper() -> Type { ... }
#   }
#
# Usage:
#   result = Utils.helper()

final class MathUtils {
    static def pi() -> float {
        return 3.14159;
    }

    static def square(x: float) -> float {
        return x * x;
    }

    static def circle_area(radius: float) -> float {
        return MathUtils.pi() * MathUtils.square(radius);
    }

    static def clamp(value: float, min_val: float, max_val: float) -> float {
        if value < min_val {
            return min_val;
        }
        if value > max_val {
            return max_val;
        }
        return value;
    }
}


# =============================================================================
# COMPOSITION OVER INHERITANCE
# =============================================================================
# Sometimes it's better to compose objects rather than inherit.
# A class can contain instances of other classes as attributes.

class Canvas {
    def Canvas(self) -> None {
        self.shapes: list = [];
    }

    def add_shape(shape: Shape) -> None {
        self.shapes.append(shape);
    }

    def draw_all() -> None {
        print("--- Drawing Canvas ---");
        for shape in self.shapes {
            shape.draw();
        }
        print("--- End Canvas ---");
    }

    def total_area() -> float {
        total: float = 0.0;
        for shape in self.shapes {
            total = total + shape.get_area();
        }
        return total;
    }
}


# =============================================================================
# MAIN - Demonstrate All Features
# =============================================================================

def main() -> None {
    print("=== Spice Composition and Inheritance Demo ===\n");

    # Create shapes using inheritance
    circle: Circle = Circle("red", 5.0);
    square: Square = Square("blue", 4.0);
    rect: Rectangle = Rectangle("green", 6.0, 3.0);

    # Polymorphism - treat all as Shape
    print("--- Polymorphism Demo ---");
    shapes: list = [circle, square, rect];

    for shape in shapes {
        print(f"Description: {shape.get_description()}");
        print(f"  Area: {shape.get_area():.2f}");
        print(f"  Color: {shape.get_color()}");
        shape.draw();
        print("");
    }

    # Final method on Square
    print("--- Final Method Demo ---");
    print(f"Square perimeter: {square.get_perimeter()}");
    print("");

    # Interface-specific behavior (Resizable)
    print("--- Interface Demo (Resizable) ---");
    print(f"Rectangle area before resize: {rect.get_area():.2f}");
    rect.resize(2.0);
    print(f"Rectangle area after 2x resize: {rect.get_area():.2f}");
    print(f"Current scale: {rect.get_scale()}");
    print("");

    # Static methods
    print("--- Static Methods Demo ---");
    print(f"Total shapes created: {Shape.get_shape_count()}");
    print(f"Pi value: {MathUtils.pi()}");
    print(f"5 squared: {MathUtils.square(5.0)}");
    print(f"Circle area (r=5): {MathUtils.circle_area(5.0):.2f}");
    print(f"Clamp 15 to [0,10]: {MathUtils.clamp(15.0, 0.0, 10.0)}");
    print("");

    # Composition - Canvas contains shapes
    print("--- Composition Demo (Canvas) ---");
    canvas: Canvas = Canvas();
    canvas.add_shape(Circle("yellow", 2.0));
    canvas.add_shape(Square("purple", 3.0));
    canvas.add_shape(Rectangle("orange", 4.0, 2.0));
    canvas.draw_all();
    print(f"Total canvas area: {canvas.total_area():.2f}");
}

main();
