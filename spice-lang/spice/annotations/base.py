"""Base class for compile-time annotation processors."""

from abc import ABC, abstractmethod


class AnnotationProcessor(ABC):
    """A compile-time annotation handler.

    Subclasses set `name` (matched against `@!name`) and optionally `targets`
    (a tuple of AST node types it may annotate; empty means any declaration).
    Annotation arguments bind to `process`'s keyword parameters, decorator-factory
    style: `@!print_on_call(time_format="%H:%M:%S")` -> `process(..., time_format=...)`.

    `process` mutates `node` in place (and may edit AST fields directly). The
    annotation stage strips the annotation afterward.
    """

    name: str = ""
    targets: tuple = ()  # allowed node types; () = any

    @abstractmethod
    def process(self, node, file, **kwargs) -> None:
        """Apply this annotation to `node`. `file` is the SpiceFile (utilities live there)."""
        raise NotImplementedError
