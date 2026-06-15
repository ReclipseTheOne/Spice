# =============================================================================
# Interfaces
# =============================================================================
#
# Python has no real interface keyword - you reach for `abc.ABC` or `Protocol`.
# Spice adds a first-class `interface`:
#
#   interface Name {
#       def method() -> Type      # signature only, no body
#   }
#
# An interface is a pure contract: only method signatures, no implementations.
# The compiler checks that every required method is actually provided.
#
# Note the bodies are omitted - a signature ends at the newline (a trailing `;`
# is allowed but not required). A class can implement several interfaces at once.


interface Drawable {
    def draw() -> None
    def get_color() -> str
}

interface Resizable {
    def resize(factor: float) -> None
}

interface InteractiveDrawable extends Drawable {
    def on_click() -> None
}


# A class implements one or more interfaces and must supply every method.
class Button implements InteractiveDrawable, Resizable {
    def Button(label: str, color: str) {
        self.label = label
        self.color = color
        self.scale = 1.0
    }

    # From Drawable (inherited into InteractiveDrawable)
    def draw() -> None {
        print(f"[{self.label}] in {self.color}, scale {self.scale}")
    }

    def get_color() -> str {
        return self.color
    }

    # From InteractiveDrawable
    def on_click() -> None {
        print(f"{self.label} clicked")
    }

    # From Resizable
    def resize(factor: float) -> None {
        self.scale = self.scale * factor
    }
}


def main() -> None {
    b: Button = Button("OK", "blue")
    b.draw()
    b.on_click()
    b.resize(2.0)
    b.draw()
    print(f"colour is {b.get_color()}")
}

main()


# -----------------------------------------------------------------------------
# If Button forgot to define `get_color`, compilation would fail with an
# interface-implementation error.
# -----------------------------------------------------------------------------
#
# Compile and run:
#
#     spicy 012-interfaces.spc -o build
#     python build/012-interfaces.py
# -----------------------------------------------------------------------------
