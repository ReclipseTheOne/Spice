# Valid directory entry point for Spice.
# Spicy can take a directory as a path for compilation with the condition that the directory contains a '__main__.spc' file.

from data_classes import Person

interface A {
    def func(a: int, b: str) -> None;
    def func(a: int, b: int) -> None;
}


class B implements A {
    def func(a: int, b: str) -> None {
        return;
    }

    def func(a: int, b: int) -> None {
        return;
    }
}

class C extends B {
    def func(a: int, b: str) -> None {
        return;
    }
}


class D extends Animal {
    def make_sound() -> str {
        return "D-sound";
    }
}