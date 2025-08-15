"""Error classes for Spice compiler."""


class SpiceError(Exception):
    """Base class for all Spice compiler errors."""
    pass


class LexerError(SpiceError):
    """Lexer error."""
    pass


class ParserError(SpiceError):
    """Parser error."""
    pass


class SemanticError(SpiceError):
    """Semantic analysis error."""
    pass


class TransformError(SpiceError):
    """Transformation error."""
    pass
