"""Spice compiler - A Python superset with static typing features."""
from importlib.metadata import version

from spice import cli, lexer, parser, transformer, errors, printils, compilation

__version__ = version("spice-lang")

__all__ = ["cli", "lexer", "parser", "transformer", "compilation", "errors", "printils"]