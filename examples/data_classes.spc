# =============================================================================
# Data Classes in Spice
# =============================================================================
#
# Data classes provide a concise way to create classes that are primarily
# used to store data. They automatically generate:
#   - __init__() constructor with all fields as parameters
#   - __repr__() for string representation
#   - __eq__() for equality comparison
#   - Field declarations with type annotations
#
# Syntax:
#   data class ClassName(field1: Type1, field2: Type2, ...);
#   data class ClassName(field1: Type1, field2: Type2, ...) { methods }
#
# Compiles to Python's @dataclass decorator.
# =============================================================================

# -----------------------------------------------------------------------------
# Simple Data Class
# -----------------------------------------------------------------------------
# A basic data class with two fields. The semicolon ends the declaration
# when there are no methods.

data class Point(x: int, y: int);

# Usage:
# p = Point(10, 20)
# print(p)        # Point(x=10, y=20)
# print(p.x)      # 10
# print(p == Point(10, 20))  # True


# -----------------------------------------------------------------------------
# Multiline Data Class Declaration
# -----------------------------------------------------------------------------
# Parameters can span multiple lines for readability.
# Newlines are allowed after '(' and after each ','.

data class Config(
    host: str,
    port: int,
    debug: bool
);


# -----------------------------------------------------------------------------
# Data Class with Methods
# -----------------------------------------------------------------------------
# Data classes can have methods in addition to their auto-generated fields.
# Use braces {} to define a body with methods.

data class Person(name: str, age: int) {
    def greet() -> str {
        return f"Hello, my name is {self.name}";
    }

    def is_adult() -> bool {
        return self.age >= 18;
    }

    def have_birthday() -> None {
        self.age = self.age + 1;
    }
}


# -----------------------------------------------------------------------------
# Data Class for Domain Modeling
# -----------------------------------------------------------------------------
# Data classes are ideal for modeling domain entities.

data class Rectangle(width: float, height: float) {
    def area() -> float {
        return self.width * self.height;
    }

    def perimeter() -> float {
        return 2 * (self.width + self.height);
    }

    def is_square() -> bool {
        return self.width == self.height;
    }
}


data class Circle(radius: float) {
    def area() -> float {
        return 3.14159 * self.radius * self.radius;
    }

    def circumference() -> float {
        return 2 * 3.14159 * self.radius;
    }
}


# -----------------------------------------------------------------------------
# Nested Data Classes
# -----------------------------------------------------------------------------
# Data classes can reference other data classes as field types.

data class Address(
    street: str,
    city: str,
    country: str
);

data class Employee(
    id: int,
    name: str,
    email: str
);


# -----------------------------------------------------------------------------
# Main - Demonstrate Usage
# -----------------------------------------------------------------------------

def main() -> None {
    # Simple data class
    p: Point = Point(10, 20);
    print(f"Point: ({p.x}, {p.y})");

    # Data class with methods
    person: Person = Person("Alice", 25);
    print(person.greet());
    print(f"Is adult: {person.is_adult()}");

    # Domain modeling
    rect: Rectangle = Rectangle(5.0, 3.0);
    print(f"Rectangle area: {rect.area()}");
    print(f"Is square: {rect.is_square()}");

    circle: Circle = Circle(2.0);
    print(f"Circle area: {circle.area()}");

    # Nested structures
    addr: Address = Address("123 Main St", "Springfield", "USA");
    emp: Employee = Employee(1, "Bob", "bob@example.com");
    print(f"Employee: {emp.name} at {addr.city}");
}

main();
