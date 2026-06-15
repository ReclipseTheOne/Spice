# geometry.spc - a Spice module imported by __main__.spc.
#
# A module is just a .spc file. Other Spice files import from it by its name
# (the file stem), exactly like Python modules. Each imported .spc is compiled
# to a .py sitting next to the entry point's output.

data class Point(x: float, y: float)


def distance(a: Point, b: Point) -> float {
    dx: float = a.x - b.x
    dy: float = a.y - b.y
    return (dx * dx + dy * dy) ** 0.5
}


class Circle {
    def Circle(center: Point, radius: float) {
        self.center = center
        self.radius = radius
    }

    def area() -> float {
        return 3.14159 * self.radius * self.radius
    }

    def contains(p: Point) -> bool {
        return distance(self.center, p) <= self.radius
    }
}
