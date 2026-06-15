# =============================================================================
# Data classes
# =============================================================================
#
# Python has `@dataclass`; Spice makes it a declaration form so the fields live
# right in the header:
#
#   data class Name(field1: Type1, field2: Type2)
#
# That single line generates the constructor, `__repr__` and `__eq__` for you -
# it compiles to a Python `@dataclass`. Add `{ ... }` to attach methods.


# A bare data class can end at the newline since no body is needed
data class Point(x: int, y: int)

data class Config(
    host: str,
    port: int,
    debug: bool
)


# With a body, a data class can carry methods alongside its generated fields.
data class Rectangle(width: float, height: float) {
    def area() -> float {
        return self.width * self.height
    }

    def is_square() -> bool {
        return self.width == self.height
    }
}


def main() -> None {
    # Constructor, repr and equality all come for free.
    p: Point = Point(10, 20)
    print(p)                       # Point(x=10, y=20)
    print(f"p.x = {p.x}")
    print(f"equal? {p == Point(10, 20)}")

    cfg: Config = Config("localhost", 8080, True)
    print(cfg)

    r: Rectangle = Rectangle(4.0, 4.0)
    print(f"area = {r.area()}, square? {r.is_square()}")
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 020-data_classes.spc -o build
#     python build/020-data_classes.py
# -----------------------------------------------------------------------------
