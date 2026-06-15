# A scene collects drawables and renders them polymorphically.
#
# `add` takes the `Drawable` interface, so any shape - Circle, Rectangle,
# Square - is accepted (subtype assignability is checked at compile time).

from shapes import Drawable


class Scene {
    def Scene(title: str) {
        self.title = title
        self.items: list = []
    }

    def add(shape: Drawable) -> None {
        self.items.append(shape)
    }

    def total_area() -> float {
        total: float = 0.0
        for shape in self.items {
            total = total + shape.area()
        }
        return total
    }

    def render() -> str {
        lines: list = [f"=== {self.title} ==="]
        for shape in self.items {
            lines.append(f"  - {shape.describe()}")
        }
        lines.append(f"total area: {self.total_area():.2f}")
        return "\n".join(lines)
    }
}
