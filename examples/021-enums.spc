# =============================================================================
# Enums
# =============================================================================
#
# Python's `enum.Enum` is a class you subclass and whose members you assign by
# hand. Spice gives enums dedicated syntax that compiles down to `enum.Enum`,
# in three escalating forms.


# -----------------------------------------------------------------------------
# 1. Simple enum - just names. Each member gets an auto-assigned value.
# -----------------------------------------------------------------------------
enum Color { RED, GREEN, BLUE }


enum OrderStatus {
    PENDING,
    CONFIRMED,
    SHIPPED,
    DELIVERED
}


# -----------------------------------------------------------------------------
# 2. Enum with values - each member carries associated data.
# -----------------------------------------------------------------------------
enum HttpStatus {
    OK(200, "Success"),
    NOT_FOUND(404, "Not Found"),
    SERVER_ERROR(500, "Internal Server Error")
}


# -----------------------------------------------------------------------------
# 3. Enum with a constructor and methods.
#    The constructor is the "simple constructor" form from 010 (a method named
#    after the enum). Separate the members from the methods with a `;`.
# -----------------------------------------------------------------------------
enum Planet {
    MERCURY(3.303e23, 2.4397e6),
    EARTH(5.976e24, 6.37814e6),
    MARS(6.421e23, 3.3972e6);

    def Planet(mass: float, radius: float) {
        self.mass = mass
        self.radius = radius
    }

    def surface_gravity() -> float {
        G: float = 6.67430e-11
        return G * self.mass / (self.radius * self.radius)
    }
}


def main() -> None {
    c: Color = Color.RED
    print(f"{c}  name={c.name}  value={c.value}")

    status: OrderStatus = OrderStatus.SHIPPED
    print(status)

    ok: HttpStatus = HttpStatus.NOT_FOUND
    print(ok)

    earth: Planet = Planet.EARTH
    print(f"Earth surface gravity = {earth.surface_gravity():.2f} m/s^2")

    mars: Planet = Planet.MARS
    print(f"Mars surface gravity  = {mars.surface_gravity():.2f} m/s^2")
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 021-enums.spc -o build
#     python build/021-enums.py
# -----------------------------------------------------------------------------
