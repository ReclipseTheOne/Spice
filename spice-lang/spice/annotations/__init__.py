"""Spice annotation framework: compile-time processors and their registry.

`@name` annotations are runtime (emitted as Python decorators by the transformer);
`@!name` annotations are compile-time and handled here by registered processors.
"""

from spice.annotations.base import AnnotationProcessor
from spice.annotations.registry import register, get_processor, all_processors

__all__ = [
    "AnnotationProcessor",
    "register",
    "get_processor",
    "all_processors",
]
