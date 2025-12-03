"""Spice compiler - A Python superset with static typing features."""
from spice import cli, lexer, parser, styping, transformer, errors, printils, compilation, version

__version__ = version.version

__all__ = ["cli", "lexer", "parser", "styping", "transformer", "compilation", "errors", "printils", "version"]