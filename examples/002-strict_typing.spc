# =============================================================================
# Strict typing and inference
# =============================================================================
#
# Python type hints are optional and ignored at runtime. Spice turns them into a
# real, enforced rule that is checked at *compile time*:
#
#   Every variable's type must be known.
#
# The compiler figures the type out for you in the obvious cases and refuses to
# compile when it can't. There are exactly three ways a variable gets a type.


def main() -> None {

    # 1. Literals infer their type.
    #    The compiler reads the literal and knows the type.

    count = 42            # int
    ratio = 3.14          # float
    name = "Spice"        # str
    ready = True          # bool

    print(f"{count} {ratio} {name} {ready}")


    # 2. Constructor calls infer their type.
    #    `Thing()` is known to produce a `Thing`, so no annotation is needed.

    box = Box(count)      # inferred as Box
    print(box.get())


    # 3. Everything else must be annotated explicitly.
    #    The result of a call or another variable is opaque to the checker, so
    #    you must state the type yourself. These are FINE:

    doubled: int = count * 2
    label: str = describe(box)     # function result -> annotation required
    alias: int = count             # copy of a variable -> annotation required

    print(f"{doubled} {label} {alias}")
}


# A plain class so the constructor-inference case above has something to build.
class Box {
    def Box(value: int) {
        self.value = value
    }

    def get() -> int {
        return self.value
    }
}


def describe(b: Box) -> str {
    return f"Box holding {b.get()}"
}


main()


# -----------------------------------------------------------------------------
# What the compiler REJECTS
#
# The following would each fail at compile time, because the type can't be
# inferred and wasn't declared:
#
#     alias = count                 # copy of a variable, no annotation
#     label = describe(box)         # function result, no annotation
#
# Add an annotation (`alias: int = count`) and they compile. This is the whole
# point of strict typing: no variable is ever left with an unknown type.
# -----------------------------------------------------------------------------
#
# Compile and run:
#
#     spicy 002-strict_typing.spc -o build
#     python build/002-strict_typing.py
# -----------------------------------------------------------------------------
