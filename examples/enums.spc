# =============================================================================
# Enums in Spice
# =============================================================================
#
# Enums (enumerations) define a type with a fixed set of named constants.
# Spice supports three forms of enums:
#
# 1. Simple enums - just named constants
#    enum Color { RED, GREEN, BLUE }
#
# 2. Enums with values - constants with associated data
#    enum Planet { EARTH(mass, radius), MARS(mass, radius) }
#
# 3. Enums with methods - full-featured enums with constructors and methods
#    enum Planet { EARTH(mass); def Planet(self, mass) { ... } }
#
# Compiles to Python's enum.Enum class.
# =============================================================================

# -----------------------------------------------------------------------------
# Simple Enum
# -----------------------------------------------------------------------------
# The most basic form - a set of named constants.
# Each member gets an auto-generated value.

enum Color { RED, GREEN, BLUE }

# Usage:
# c = Color.RED
# print(c)           # Color.RED
# print(c.name)      # "RED"
# print(c.value)     # 1 (auto-assigned)


# -----------------------------------------------------------------------------
# Enum for State Machines
# -----------------------------------------------------------------------------
# Enums are perfect for representing states.

enum OrderStatus {
    PENDING,
    CONFIRMED,
    SHIPPED,
    DELIVERED,
    CANCELLED
}


enum ConnectionState {
    DISCONNECTED,
    CONNECTING,
    CONNECTED,
    ERROR
}


# -----------------------------------------------------------------------------
# Enum with Values
# -----------------------------------------------------------------------------
# Enum members can have associated values passed as constructor arguments.
# Values are stored as tuples when there are multiple arguments.

enum HttpStatus {
    OK(200, "Success"),
    NOT_FOUND(404, "Not Found"),
    SERVER_ERROR(500, "Internal Server Error")
}


enum Direction {
    NORTH(0, 1),
    SOUTH(0, -1),
    EAST(1, 0),
    WEST(-1, 0)
}


# -----------------------------------------------------------------------------
# Enum with Constructor and Methods
# -----------------------------------------------------------------------------
# For full control, define a constructor and methods.
# The constructor name must match the enum name (transforms to __init__).
# Separate members from methods with a semicolon.

enum Planet {
    MERCURY(3.303e23, 2.4397e6),
    VENUS(4.869e24, 6.0518e6),
    EARTH(5.976e24, 6.37814e6),
    MARS(6.421e23, 3.3972e6),
    JUPITER(1.9e27, 7.1492e7),
    SATURN(5.688e26, 6.0268e7),
    URANUS(8.686e25, 2.5559e7),
    NEPTUNE(1.024e26, 2.4746e7);

    def Planet(self, mass: float, radius: float) -> None {
        self.mass = mass;
        self.radius = radius;
    }

    def surface_gravity() -> float {
        # G = gravitational constant
        G: float = 6.67430e-11;
        return G * self.mass / (self.radius * self.radius);
    }

    def surface_weight(other_mass: float) -> float {
        return other_mass * self.surface_gravity();
    }
}


# -----------------------------------------------------------------------------
# Enum for Operations
# -----------------------------------------------------------------------------
# Enums can encapsulate behavior through methods.

enum Operation {
    ADD,
    SUBTRACT,
    MULTIPLY,
    DIVIDE;

    def apply(a: float, b: float) -> float {
        if self == Operation.ADD {
            return a + b;
        }
        if self == Operation.SUBTRACT {
            return a - b;
        }
        if self == Operation.MULTIPLY {
            return a * b;
        }
        if self == Operation.DIVIDE {
            return a / b;
        }
        return 0.0;
    }
}


# -----------------------------------------------------------------------------
# Enum with String Values
# -----------------------------------------------------------------------------
# Useful for mapping to external string representations.

enum LogLevel {
    DEBUG("DEBUG"),
    INFO("INFO"),
    WARNING("WARNING"),
    ERROR("ERROR"),
    CRITICAL("CRITICAL");

    def LogLevel(self, label: str) -> None {
        self.label = label;
    }

    def format_message(msg: str) -> str {
        return f"[{self.label}] {msg}";
    }
}


# -----------------------------------------------------------------------------
# Main - Demonstrate Usage
# -----------------------------------------------------------------------------

def main() -> None {
    # Simple enum
    color: Color = Color.RED;
    print(f"Color: {color}");

    # State enum
    status: OrderStatus = OrderStatus.PENDING;
    print(f"Order status: {status}");

    # Enum with values
    http: HttpStatus = HttpStatus.OK;
    print(f"HTTP: {http}");

    # Direction with coordinates
    dir: Direction = Direction.NORTH;
    print(f"Direction: {dir}");

    # Planet calculations
    earth: Planet = Planet.EARTH;
    print(f"Earth surface gravity: {earth.surface_gravity()} m/s^2");
    print(f"Weight of 70kg on Earth: {earth.surface_weight(70.0)} N");

    mars: Planet = Planet.MARS;
    print(f"Weight of 70kg on Mars: {mars.surface_weight(70.0)} N");

    # Operations
    op: Operation = Operation.ADD;
    result: float = op.apply(10.0, 5.0);
    print(f"10 + 5 = {result}");

    # Logging
    log: LogLevel = LogLevel.INFO;
    print(log.format_message("Application started"));
}

main();
