# =============================================================================
# Syntax and blocks
# =============================================================================
#
# Spice is Python but with all the spice.
#
# One of the first differences that you can notice is that
# blocks are delimited by braces `{ }`, not by indentation.
#
# Indentation no longer carries meaning.
#
# Statements are still newline-terminated, exactly like Python. A semicolon `;`
# is allowed but optional; you only need one to put several statements on a
# single line.

# So this is valid:
a = 1; b = 2; c = 3

# But also this!
a = 1
b = 2
c = 3

# -----------------------------------------------------------------------------
# Functions
# -----------------------------------------------------------------------------
# Functions are declared with `def`, and the return type is *required*

def add(a: int, b: int) -> int {
    return a + b
}


# A function that returns nothing is annotated `-> None`.

def greet(name: str) -> None {
    print(f"Hello, {name}!")
}


# -----------------------------------------------------------------------------
# Control flow
# -----------------------------------------------------------------------------
# `if` / `elif` / `else`, `for` and `while` all use braces instead of a colon
# and indentation. The conditions themselves are the usual Python expressions.

def classify(n: int) -> str {
    if n < 0 {
        return "negative"
    } elif n == 0 {
        return "zero"
    } else {
        return "positive"
    }
}


def countdown(start: int) -> None {
    i: int = start
    while i > 0 {
        print(i)
        i = i - 1
    }
    print("liftoff")
}


# Nothing is removed. So `for ... in ...` is still valid in Spice

def sum_all(values: list) -> int {
    total: int = 0
    for v in values {
        total = total + v
    }
    return total
}


# -----------------------------------------------------------------------------
# Compile this file to Python (Spice ships the `spicy` compiler):
#
#     spicy 001-syntax_and_blocks.spc -o build
#
# then run the generated module with any Python interpreter:
#
#     python build/001-syntax_and_blocks.py
# -----------------------------------------------------------------------------
