# =============================================================================
# switch / case
# =============================================================================
#
# Spice has a C-style `switch`:
#
#   switch (expr) {
#       case value: ...
#       default:    ...
#   }
#
# It compiles to a plain `if` / `elif` / `else` chain, so there is NO fall-through
# and you never write `break` - each `case` is its own block. The switched value
# and the case values are ordinary expressions, compared with `==`.


def describe_status(code: int) -> str {
    switch (code) {
        case 200:
            return "OK"
        case 404:
            return "Not Found"
        case 500:
            return "Server Error"
        default:
            return "Unknown"
    }
}


def vowel_or_consonant(letter: str) -> str {
    result: str = ""
    switch (letter) {
        case "a":
            result = "vowel"
        case "e":
            result = "vowel"
        case "i":
            result = "vowel"
        default:
            result = "consonant"
    }
    return result
}


def main() -> None {
    for code in [200, 404, 500, 418] {
        print(f"{code} -> {describe_status(code)}")
    }

    for letter in ["a", "b", "e", "z"] {
        print(f"{letter} is a {vowel_or_consonant(letter)}")
    }
}

main()


# -----------------------------------------------------------------------------
# Compile and run:
#
#     spicy 040-switch.spc -o build
#     python build/040-switch.py
# -----------------------------------------------------------------------------
