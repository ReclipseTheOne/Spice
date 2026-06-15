# shapes_renderer - entry point.
#
# Build & run from this folder:
#     python build.spice.py --run

from shapes import Circle, Rectangle, Square
from scene import Scene


def main() -> None {
    scene: Scene = Scene("My Drawing")

    # All three are Drawable, so the Scene accepts them uniformly.
    scene.add(Circle(2.0))
    scene.add(Rectangle(3.0, 4.0))
    scene.add(Square(5.0))

    print(scene.render())
}


main()
