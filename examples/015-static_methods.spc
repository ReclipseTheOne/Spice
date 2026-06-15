# =============================================================================
# Static methods
# =============================================================================
#
# In Python a class-level method needs the `@staticmethod` decorator. Spice
# promotes it to a modifier keyword:
#
#   static def helper() -> Type { ... }
#
# It compiles to `@staticmethod`. A static method belongs to the class, takes no
# `self`, and is called on the class itself.


final class MathUtils {
    static def pi() -> float {
        return 3.14159
    }

    static def square(x: float) -> float {
        return x * x
    }

    static def circle_area(radius: float) -> float {
        return MathUtils.pi() * MathUtils.square(radius)
    }

    static def clamp(value: float, low: float, high: float) -> float {
        if value < low {
            return low
        }
        if value > high {
            return high
        }
        return value
    }
}


class Temperature {
    def Temperature(celsius: float) {
        self.celsius = celsius
    }

    static def from_fahrenheit(f: float) -> Temperature {
        return Temperature((f - 32.0) * 5.0 / 9.0)
    }
}


def main() -> None {
    print(f"pi          = {MathUtils.pi()}")
    print(f"square(5)   = {MathUtils.square(5.0)}")
    print(f"area(r=2)   = {MathUtils.circle_area(2.0):.4f}")
    print(f"clamp 15    = {MathUtils.clamp(15.0, 0.0, 10.0)}")

    t: Temperature = Temperature.from_fahrenheit(212.0)
    print(f"212F        = {t.celsius:.1f}C")
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 015-static_methods.spc -o build
#     python build/015-static_methods.py
# -----------------------------------------------------------------------------
