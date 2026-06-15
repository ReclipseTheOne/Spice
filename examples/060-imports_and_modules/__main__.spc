# =============================================================================
# Imports and modules
# =============================================================================
#
# Spice programs span multiple files using ordinary Python import syntax. Two
# things are worth calling out:
#
#   1. A `.spc` file can import from another `.spc` file by its module name.
#      The compiler follows the import graph and compiles every reached module.
#
#   2. A DIRECTORY is a valid compilation target as long as it contains a
#      `__main__.spc`. That file is the entry point - which is why this example
#      lives in a folder instead of a single file.
#
# You can mix in plain Python modules too: `import math` (or any .py on the path)
# resolves just like it would in Python.

from geometry import Point, Circle, distance

import math


def main() -> None {
    origin: Point = Point(0.0, 0.0)
    here: Point = Point(3.0, 4.0)

    # Function imported from another .spc module.
    d: float = distance(origin, here)
    print(f"distance = {d}")

    # Class imported from another .spc module.
    c: Circle = Circle(origin, 5.0)
    print(f"circle area     = {c.area():.2f}")
    print(f"contains here?  = {c.contains(here)}")

    # A plain Python module, imported the usual way.
    print(f"math.tau        = {math.tau:.4f}")
}

main()


# -----------------------------------------------------------------------------
# Because this folder has a __main__.spc, you compile the WHOLE directory by
# pointing spicy at it. geometry.spc is compiled automatically as a dependency:
#
#     spicy 060-imports_and_modules -o build
#     python build/__main__.py
# -----------------------------------------------------------------------------
