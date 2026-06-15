# =============================================================================
# Final: classes, methods and variables
# =============================================================================
#
# Python has no way to say "this can't be changed" and have it enforced - `Final`
# from typing is a hint a checker might honour. Spice makes `final` a keyword the
# compiler enforces, in three places:
#
#   final class C { ... }      # C cannot be subclassed
#   final def m() -> T { ... } # m cannot be overridden by a subclass
#   final x: int = 1           # x cannot be reassigned
#
# Violations are caught at compile time.


# A final variable: a real constant. Reassigning `MAX_RETRIES` later would fail
# to compile.
final MAX_RETRIES: int = 3


class Connection {
    def Connection(host: str) {
        self.host = host
    }

    # A final method: subclasses inherit it but may not override it.
    final def fingerprint() -> str {
        return f"conn:{self.host}"
    }

    def greet() -> str {
        return f"connected to {self.host}"
    }
}


# A final class: nothing may `extend` SecureConnection.
final class SecureConnection extends Connection {
    def SecureConnection(host: str) {
        super(host)
    }

    def greet() -> str {
        return f"securely connected to {self.host}"
    }
}


def main() -> None {
    c: SecureConnection = SecureConnection("example.com")
    print(c.greet())
    print(c.fingerprint())
    print(f"retry budget: {MAX_RETRIES}")
}

main()


# -----------------------------------------------------------------------------
# Each of these would be rejected at compile time:
#
#     MAX_RETRIES = 5                          # reassigning a final variable
#     class Faster extends SecureConnection    # extending a final class
#     overriding fingerprint() in a subclass
#
# -----------------------------------------------------------------------------
#
# Compile and run:
#
#     spicy 014-final.spc -o build
#     python build/014-final.py
# -----------------------------------------------------------------------------
