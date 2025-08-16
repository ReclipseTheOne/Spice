"""Parser module for Spice language."""

from spice.parser.parser import Parser

# The only place where I'll actaully use *
from spice.parser.ast_nodes import *

__all__ = ['Parser']
