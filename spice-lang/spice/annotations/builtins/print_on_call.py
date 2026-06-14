"""Built-in `@!print_on_call` compile-time annotation.

Injects a timestamped log line at the top of the annotated function's body:

    @!print_on_call(time_format="%H:%M:%S")
    def greet(name: str) -> None { ... }

becomes (roughly):

    import datetime

    def greet(name: str) -> None:
        print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] greet called")
        ...
"""

from spice.annotations import AnnotationProcessor, register
from spice.parser.ast_nodes import FunctionDeclaration


@register
class PrintOnCall(AnnotationProcessor):
    name = "print_on_call"
    targets = (FunctionDeclaration,)

    def process(self, node, file, *, time_format: str = "%H:%M:%S") -> None:
        if node.body is None:
            node.body = []

        file.ensure_import("datetime")

        timestamp = f"datetime.datetime.now().strftime({time_format!r})"
        code = f'print(f"[{{{timestamp}}}] {node.name} called")'
        node.body.insert(0, file.raw_python(code))
