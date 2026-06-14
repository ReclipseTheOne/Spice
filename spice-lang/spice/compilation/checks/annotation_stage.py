"""Annotation lowering stage.

Runs compile-time (`@!`) annotation processors over the AST, strips the
processed annotations, and leaves runtime (`@`) annotations in place for the
transformer to emit as decorators. Implemented as a `CompileTimeCheck` so it
plugs into the pipeline and reports fatal errors the usual way.
"""

import inspect

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.parser.ast_nodes import LiteralExpression
from spice.annotations import get_processor
import spice.annotations.builtins


class AnnotationStage(CompileTimeCheck):
    def __init__(self):
        self.errors = []

    def check(self, file) -> bool:
        self.errors = []

        # Comp time processors are able to modify the code so we need to materialize nodes first
        for node in list(file.walk()):
            if getattr(node, "annotations", None):
                self._process_node(node, file)

        self.errors.extend(getattr(file, "diagnostics", []))
        return not self.errors

    def _process_node(self, node, file) -> None:
        remaining = []
        for ann in node.annotations:
            if ann.retention != "compile_time":
                remaining.append(ann)  # runtime: left for the transformer
                continue
            self._apply(ann, node, file)  # compile-time: applied, then stripped
        node.annotations = remaining

    def _apply(self, ann, node, file) -> None:
        proc = get_processor(ann.name)
        if proc is None:
            self.errors.append(f"Unknown compile-time annotation '@!{ann.name}' (line {ann.line})")
            return

        if proc.targets and not isinstance(node, proc.targets):
            allowed = ", ".join(t.__name__ for t in proc.targets)
            self.errors.append(
                f"'@!{ann.name}' cannot annotate {type(node).__name__}; allowed: {allowed} (line {ann.line})"
            )
            return

        try:
            values = [self._literal(a) for a in ann.args]
            kwargs = {key: self._literal(value) for key, value in ann.kwargs.items()}
        except TypeError as exc:
            self.errors.append(f"'@!{ann.name}': {exc} (line {ann.line})")
            return

        # Validate arity / names against process(node, file, **bound) before any side effects.
        try:
            inspect.signature(proc.process).bind(node, file, *values, **kwargs)
        except TypeError as exc:
            self.errors.append(f"'@!{ann.name}': {exc} (line {ann.line})")
            return

        proc.process(node, file, *values, **kwargs)

    def _literal(self, expr):
        """Evaluate a compile-time-literal argument expression to a Python value."""
        if not isinstance(expr, LiteralExpression):
            raise TypeError(f"argument must be a compile-time literal, got {type(expr).__name__}")

        lt = expr.literal_type
        value = expr.value
        if lt == "number":
            text = str(value)
            return float(text) if ("." in text or "e" in text.lower()) else int(text)
        if lt in ("string", "fstring"):
            s = str(value)
            if len(s) >= 2 and s[0] == s[-1] and s[0] in "\"'":
                s = s[1:-1]
            return s
        if lt == "boolean":
            return bool(value)
        return value
