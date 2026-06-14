"""Built-in compile-time annotation processors.

Importing this package registers all built-ins as a side effect.
"""

from spice.annotations.builtins import print_on_call  # noqa: F401  (registers @!print_on_call)
