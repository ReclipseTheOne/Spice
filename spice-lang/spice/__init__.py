"""Spice compiler - A Python superset with static typing features."""
from importlib.metadata import version

from spice import cli, lexer, parser, styping, transformer, errors, printils, compilation

__version__ = version("spicy")

__all__ = ["cli", "lexer", "parser", "styping", "transformer", "compilation", "errors", "printils"]