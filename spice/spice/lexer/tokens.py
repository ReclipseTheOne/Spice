"""Token definitions for Spice language."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional, Union


class TokenType(Enum):
    """Token types for Spice language."""

    # Literals
    NUMBER = auto()
    STRING = auto()
    FSTRING = auto() # Treated the same way as a STRING
    RSTRING = auto() # Treated the same way as a STRING
    FRSTRING = auto() # Treated the same way as a STRING
    REGEX = auto()
    IDENTIFIER = auto()

    # Keywords (Python)
    DEF = auto()
    CLASS = auto()
    IF = auto()
    ELIF = auto()
    ELSE = auto()
    FOR = auto()
    WHILE = auto()
    RETURN = auto()
    IMPORT = auto()
    FROM = auto()
    AS = auto()
    WITH = auto()
    TRY = auto()
    EXCEPT = auto()
    FINALLY = auto()
    RAISE = auto()
    PASS = auto()
    BREAK = auto()
    CONTINUE = auto()
    TRUE = auto()
    FALSE = auto()
    NONE = auto()
    AND = auto()
    OR = auto()
    NOT = auto()
    IN = auto()
    IS = auto()
    LAMBDA = auto()

    # New Keywords (Spice)
    INTERFACE = auto()
    ABSTRACT = auto()
    FINAL = auto()
    STATIC = auto()
    EXTENDS = auto()
    IMPLEMENTS = auto()

    # Operators
    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()
    DOUBLESTAR = auto()
    DOUBLESLASH = auto()
    EQUAL = auto()
    NOTEQUAL = auto()
    LESS = auto()
    GREATER = auto()
    LESSEQUAL = auto()
    GREATEREQUAL = auto()
    ASSIGN = auto()
    PLUSASSIGN = auto()
    MINUSASSIGN = auto()
    STARASSIGN = auto()
    SLASHASSIGN = auto()
    PERCENTASSIGN = auto()
    DOUBLESTARASSIGN = auto()
    DOUBLESLASHASSIGN = auto()

    # Delimiters
    LPAREN = auto()
    RPAREN = auto()
    LBRACKET = auto()
    RBRACKET = auto()
    LBRACE = auto()
    RBRACE = auto()
    COMMA = auto()
    COLON = auto()
    SEMICOLON = auto()
    DOT = auto()
    ARROW = auto()

    # Special
    NEWLINE = auto()
    INDENT = auto()
    DEDENT = auto()
    EOF = auto()

    # Comments
    COMMENT = auto()

    # Control flow
    SWITCH = auto()
    CASE = auto()
    DEFAULT = auto()

    # Groups (not used in the lexer, just for utility in the follow set)
    BOOLEAN = auto()


@dataclass
class Token:
    """Represents a token in the source code."""
    type: TokenType
    value: Any
    line: int
    column: int
    filename: Optional[str] = None

    def __repr__(self):
        return f"Token({self.type.name}, {self.value!r}, {self.line}, {self.column})"


# Util methods
def isBoolean(token: Union[Token, TokenType]) -> bool:
    """Check if the token can be used in a logic statement"""
    if isinstance(token, Token):
        return token.type in (TokenType.TRUE, TokenType.FALSE, TokenType.IDENTIFIER, TokenType.STRING, TokenType.NUMBER, TokenType.NONE)
    else:
        return token in (TokenType.TRUE, TokenType.FALSE, TokenType.IDENTIFIER, TokenType.STRING, TokenType.NUMBER, TokenType.NONE)

def isLogicToken(token: Union[Token, TokenType]) -> bool:
    """Check if the token is a logic operator"""
    if isinstance(token, Token):
        return token.type in (TokenType.AND, TokenType.OR, TokenType.NOT, TokenType.IN, TokenType.IS)
    else:
        return token in (TokenType.AND, TokenType.OR, TokenType.NOT, TokenType.IN, TokenType.IS)

def isValidFirstLogicToken(token: Union[Token, TokenType]) -> bool:
    """Check if the token is a valid first logic token"""
    if isinstance(token, Token):
        return token.type in (TokenType.TRUE, TokenType.FALSE, TokenType.IDENTIFIER, TokenType.STRING, TokenType.NUMBER, TokenType.NONE, TokenType.NOT)
    else:
        return token in (TokenType.TRUE, TokenType.FALSE, TokenType.IDENTIFIER, TokenType.STRING, TokenType.NUMBER, TokenType.NONE, TokenType.NOT)