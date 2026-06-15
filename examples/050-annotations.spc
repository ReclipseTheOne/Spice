# =============================================================================
# Annotations: @ runtime vs @! compile-time
# =============================================================================
#
# Spice has two flavours of annotation, told apart by a single character:
#
#   @name    RUNTIME annotation. Emitted verbatim as a Python decorator, so it
#            behaves exactly like decorators you already know.
#
#   @!name   COMPILE-TIME annotation. Handled by the compiler while building,
#            then stripped from the output. Think of these as MACROS: they get
#            the whole AST block they are attached to and may rewrite, insert or
#            replace nodes in it - they are NOT function wrappers like the
#            decorators that runtime `@` annotations compile to.
#
# `@!foo` and `@!foo(...)` are distinct (bare vs called), and annotations stack.


# -----------------------------------------------------------------------------
# A runtime annotation is just a decorator. Here `trace` runs at import time and
# returns the function unchanged - the `@trace` line ends up in the output.
# -----------------------------------------------------------------------------
def trace(fn: object) -> object {
    print(f"[registered] {fn.__name__}")
    return fn
}


# -----------------------------------------------------------------------------
# `@!print_on_call` is a built-in compile-time annotation. As a macro it rewrites
# the function's AST - inserting a timestamped log line at the top of the body -
# then removes itself. The generated Python has no trace of `@!print_on_call`,
# only the injected print.
# -----------------------------------------------------------------------------
@!print_on_call(time_format="%H:%M:%S")
def greet(name: str) -> None {
    print(f"Hi, {name}")
}


# Annotations stack. The runtime `@trace` stays; the compile-time one is applied
# and removed.
@trace
@!print_on_call
def farewell(name: str) -> None {
    print(f"Bye, {name}")
}


def main() -> None {
    greet("Spice")       # prints "[HH:MM:SS] greet called" then "Hi, Spice"
    farewell("World")
}

main()


# -----------------------------------------------------------------------------
# Compile and inspect the output to see the difference - the `@trace` decorator
# survives, while `@!print_on_call` has been compiled away into a print:
#
#     spicy 050-annotations.spc -o build
#     python build/050-annotations.py
# -----------------------------------------------------------------------------
