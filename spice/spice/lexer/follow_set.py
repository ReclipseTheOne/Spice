"""
Follow set definitions for Spy parser.

This file should be extended per every change in Spy grammar.
The FOLLOW_SET should NOT be used as a final check for syntax.
This is just filter for broad verification
"""

from lexer.tokens import TokenType
from typing import Optional

FOLLOW_SET = {

    # alpha;
    # alpha *
    # alpha /
    # alpha %
    # alpha **
    # alpha // 
    # alpha +
    # alpha -
    # alpha <
    # alpha >
    # alpha <=
    # alpha >=
    # alpha ==
    # alpha !=
    # alpha =
    # alpha +=
    # alpha -=
    # alpha *=
    # alpha /=
    # alpha %=
    # alpha **=
    # alpha //=
    # ... alpha and
    # ... alpha or
    # ... alpha in
    # alpha(beta) (for alpha and beta)
    # alpha : 
    # alpha.beta
    # alpha, beta
    # (class) alpha {
    # alpha = [beta]
    # alpha extends beta
    # alpha implements beta
    TokenType.IDENTIFIER: {
        TokenType.SEMICOLON, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.DOUBLESTAR, TokenType.DOUBLESLASH, TokenType.PLUS, TokenType.MINUS,
        TokenType.LESS, TokenType.GREATER, TokenType.LESSEQUAL, TokenType.GREATEREQUAL,
        TokenType.EQUAL, TokenType.NOTEQUAL, TokenType.ASSIGN, TokenType.PLUSASSIGN,
        TokenType.MINUSASSIGN, TokenType.STARASSIGN, TokenType.SLASHASSIGN,
        TokenType.PERCENTASSIGN, TokenType.DOUBLESTARASSIGN, TokenType.DOUBLESLASHASSIGN,
        TokenType.AND, TokenType.OR, TokenType.IN, TokenType.RPAREN, TokenType.LPAREN,
        TokenType.COLON, TokenType.DOT, TokenType.COMMA, TokenType.LBRACE, TokenType.RBRACKET,
        TokenType.EXTENDS, TokenType.IMPLEMENTS
    },

    # alpha = "alpha";
    # alpha("beta");
    # alpha, beta
    TokenType.STRING: {
        TokenType.SEMICOLON, TokenType.RPAREN, TokenType.COMMA
    },


    # = 1;
    # 1 *
    # 1 /
    # 1 %
    # 1 **
    # 1 // 
    # 1 +
    # 1 -
    # 1 <
    # 1 >
    # 1 <=
    # 1 >=
    # 1 ==
    # 1 !=
    # ... 1 and
    # ... 1 or
    # ... 1 in
    # alpha(1)
    TokenType.NUMBER: {
        TokenType.SEMICOLON, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.DOUBLESTAR, TokenType.DOUBLESLASH, TokenType.PLUS, TokenType.MINUS,
        TokenType.LESS, TokenType.GREATER, TokenType.LESSEQUAL, TokenType.GREATEREQUAL,
        TokenType.EQUAL, TokenType.NOTEQUAL, TokenType.AND, TokenType.OR, TokenType.IN,
        TokenType.RPAREN
    },


    #
    TokenType.COLON: {
        TokenType.IDENTIFIER, TokenType.NONE
    },

    #
    TokenType.SEMICOLON: {
        TokenType.DEF, TokenType.PASS, TokenType.RETURN, TokenType.IF, TokenType.FOR, TokenType.WHILE, TokenType.SWITCH,
        TokenType.IDENTIFIER, TokenType.RBRACE, TokenType.NEWLINE, TokenType.COMMENT, TokenType.EOF
    },


    # Any start of a new line
    TokenType.NEWLINE: {
        TokenType.ABSTRACT, TokenType.CLASS, TokenType.DEF, TokenType.FINAL, TokenType.INTERFACE,
        TokenType.IDENTIFIER, TokenType.PASS, TokenType.RETURN, TokenType.IF, TokenType.FOR, TokenType.WHILE,
        TokenType.SWITCH, TokenType.RBRACE, TokenType.COMMENT, TokenType.EOF, TokenType.NEWLINE, TokenType.STATIC
    },

    # -> None:
    # -> None {
    # def alpha() -> None; (abstract def)
    TokenType.NONE: {
        TokenType.COLON, TokenType.LBRACE, TokenType.SEMICOLON
    },
    

    # alpha implements beta:
    TokenType.IMPLEMENTS: {
        TokenType.IDENTIFIER
    },

    # alpha extends beta:
    TokenType.EXTENDS: {
        TokenType.IDENTIFIER
    },

    # abstract class alpha:
    # abstract def alpha():
    TokenType.ABSTRACT: {
        TokenType.CLASS, TokenType.DEF
    },

    # interface alpha:
    TokenType.INTERFACE: {
        TokenType.IDENTIFIER
    },

    # class alpha:
    TokenType.CLASS: {
        TokenType.IDENTIFIER
    },

    # static alpha
    # static def alpha():
    TokenType.STATIC: {
        TokenType.IDENTIFIER, TokenType.DEF
    },

    # final alpha
    # final class Alpha:
    # final def alpha():
    TokenType.FINAL: {
        TokenType.CLASS, TokenType.IDENTIFIER, TokenType.DEF
    },


    # alpha, beta, gamma
    # 1, 2, 3
    # "string1", "string2", "string3"
    TokenType.COMMA: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha.beta
    TokenType.DOT: {
        TokenType.IDENTIFIER
    },

    # alpha = beta; / alpha = gamma(...);
    # alpha = 1;
    # alpha = "string";
    TokenType.ASSIGN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING,
        TokenType.FRSTRING, TokenType.REGEX, TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE
    },

    # alpha += beta;
    # alpha += 1;
    # alpha += "string";
    TokenType.PLUSASSIGN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },
    
    # alpha -= beta;
    # alpha -= 1;
    # alpha -= "string";
    TokenType.MINUSASSIGN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha *= beta;
    # alpha *= 1;
    # alpha *= "string";
    TokenType.STARASSIGN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha /= beta;
    # alpha /= 1;
    # alpha /= "string";
    TokenType.SLASHASSIGN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha * beta;
    # alpha * 1;
    # alpha * "string";
    TokenType.STAR: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING,
    },

    # alpha / beta;
    # alpha / 1;
    # alpha / "string";
    TokenType.SLASH: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha % beta;
    # alpha % 1;
    # alpha % "string";
    TokenType.PERCENT: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha ** beta;
    # alpha ** 1;
    # alpha ** "string";
    TokenType.DOUBLESTAR: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha // beta;
    # alpha // 1;
    # alpha // "string";
    TokenType.DOUBLESLASH: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha + beta;
    # alpha + 1;
    # alpha + "string";
    TokenType.PLUS: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },

    # alpha - beta;
    # alpha - 1;
    # alpha - "string";
    TokenType.MINUS: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING
    },


    # def alpha():
    TokenType.DEF: {
        TokenType.IDENTIFIER
    },

    # -> None
    # -> alpha
    TokenType.ARROW: {
        TokenType.NONE, TokenType.IDENTIFIER
    },

    # return alpha;
    # return 1;
    # return "string";
    # return;
    TokenType.RETURN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.SEMICOLON
    },


    # if alpha:
    # if 1 ...
    # if "string" ...
    # if (...) 
    # if not ...
    TokenType.IF: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.LPAREN, TokenType.NOT
    },

    # else:
    # else {
    TokenType.ELSE: {
        TokenType.LBRACE, TokenType.COLON
    },

    # for alpha ...
    TokenType.FOR: {
        TokenType.IDENTIFIER
    },

    # alpha in beta
    # alpha in 1
    # alpha in "string"
    # alpha in (alpha, beta)
    # alpha in [alpha, beta]
    TokenType.IN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, 
        TokenType.RSTRING, TokenType.LPAREN, TokenType.LBRACKET
    },

    # ... not alpha:
    # ... not 1 ...
    # ... not "string" ...
    # ... (...) 
    # ... not ...
    TokenType.NOT: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.LPAREN
    },


    # [alpha]
    # [1]
    # ["str"]
    # [-alpha]
    # [(alpha, beta)]
    # [[]]
    TokenType.LBRACKET: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING,
        TokenType.FRSTRING, TokenType.MINUS, TokenType.LPAREN, TokenType.LBRACKET, TokenType.RBRACKET, 
    },

    # for a in [alpha]:
    # [[alpha], beta]
    # a = [alpha];
    # [[alpha]]
    # alpha([beta])
    TokenType.RBRACKET: {
        TokenType.COLON, TokenType.COMMA, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.RPAREN
    },

    # (alpha, beta)
    # (1, 2)
    # ("alpha", "beta")
    # (True, False)
    # (-alpha)
    # ()
    # (alpha())
    TokenType.LPAREN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.TRUE, TokenType.FALSE, TokenType.NONE,
        TokenType.LPAREN, TokenType.MINUS, TokenType.RPAREN
    },

    #
    TokenType.RPAREN: {
        TokenType.COLON, TokenType.LBRACE, TokenType.COMMA, TokenType.SEMICOLON, TokenType.NEWLINE, TokenType.ARROW,
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.DOUBLESTAR, TokenType.DOUBLESLASH, TokenType.LESS, TokenType.GREATER,
        TokenType.LESSEQUAL, TokenType.GREATEREQUAL, TokenType.EQUAL, TokenType.NOTEQUAL,
        TokenType.AND, TokenType.OR, TokenType.RBRACE, TokenType.IN, TokenType.DOT, TokenType.RPAREN
    },

    #
    TokenType.LBRACE: {
        TokenType.DEF, TokenType.PASS, TokenType.RETURN, TokenType.IF, TokenType.FOR, TokenType.WHILE, TokenType.SWITCH,
        TokenType.IDENTIFIER, TokenType.RBRACE, TokenType.NEWLINE, TokenType.COMMENT
    },

    #
    TokenType.RBRACE: {
        TokenType.ELSE, TokenType.EOF, TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.CASE, TokenType.DEFAULT
    },
}


class IllegalFollow:
    def __init__(self, token, next_token, line, column):
        self.token = token
        self.next_token = next_token
        self.line = line
        self.column = column

    def __str__(self):
        return f"Illegal follow: {self.token} followed by {self.next_token} at line {self.line}, column {self.column}"


def get_follow_set(token_type):
    """Return the set of token types that can follow the given token type."""
    
    # All string types follow the same rules
    if token_type in [TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.FRSTRING, TokenType.REGEX]:
        token_type = TokenType.STRING

    return FOLLOW_SET.get(token_type, set())

def check(token, next_token, line, col) -> Optional[IllegalFollow]:
    if (next_token in get_follow_set(token)):
        return None
    else:
        return IllegalFollow(token, next_token, line, col)
