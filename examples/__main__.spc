# Valid directory entry point for Spice
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

final final_var: int = 2;