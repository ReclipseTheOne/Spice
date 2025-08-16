"""
Follow set definitions for Spice parser.

This file should be extended per every change in Spice grammar.
The FOLLOW_SET should NOT be used as a final check for syntax.
This is just filter for broad verification
"""

from spice.lexer.tokens import TokenType
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
    # ... alpha, beta]
    # alpha is None
    # alpha not in list
    # alpha if condition
    # alpha for item
    TokenType.IDENTIFIER: {
        TokenType.SEMICOLON, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.DOUBLESTAR, TokenType.DOUBLESLASH, TokenType.PLUS, TokenType.MINUS,
        TokenType.LESS, TokenType.GREATER, TokenType.LESSEQUAL, TokenType.GREATEREQUAL,
        TokenType.EQUAL, TokenType.NOTEQUAL, TokenType.ASSIGN, TokenType.PLUSASSIGN,
        TokenType.MINUSASSIGN, TokenType.STARASSIGN, TokenType.SLASHASSIGN,
        TokenType.PERCENTASSIGN, TokenType.DOUBLESTARASSIGN, TokenType.DOUBLESLASHASSIGN,
        TokenType.AND, TokenType.OR, TokenType.IN, TokenType.RPAREN, TokenType.LPAREN,
        TokenType.COLON, TokenType.DOT, TokenType.COMMA, TokenType.LBRACE, TokenType.RBRACKET,
        TokenType.EXTENDS, TokenType.IMPLEMENTS, TokenType.LBRACKET,
        TokenType.IS, TokenType.NOT, TokenType.IF, TokenType.FOR
    },

    # alpha = "alpha";
    # alpha("beta");
    # alpha, beta
    # ..., "gamma"]
    # == "alpha" {
    # ..., "alpha" }
    # "key": value (dictionary literals)
    TokenType.STRING: {
        TokenType.SEMICOLON, TokenType.RPAREN, TokenType.COMMA, TokenType.LBRACE,
        TokenType.RBRACKET, TokenType.RBRACE, TokenType.COLON
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
    # 1, 2
    # ...1, 2]
    # a == 1 {
    # 1 for i (list comprehensions)
    # 1 if condition
    # 1 else value
    # 1: value
    TokenType.NUMBER: {
        TokenType.SEMICOLON, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.DOUBLESTAR, TokenType.DOUBLESLASH, TokenType.PLUS, TokenType.MINUS,
        TokenType.LESS, TokenType.GREATER, TokenType.LESSEQUAL, TokenType.GREATEREQUAL,
        TokenType.EQUAL, TokenType.NOTEQUAL, TokenType.AND, TokenType.OR, TokenType.IN,
        TokenType.RPAREN, TokenType.COMMA, TokenType.RBRACKET, TokenType.LBRACE,
        TokenType.FOR, TokenType.IF, TokenType.ELSE, TokenType.RBRACE, TokenType.COLON
    },


    # alpha: beta
    # -> type:
    # :] (empty collections)
    # "key": value
    TokenType.COLON: {
        TokenType.IDENTIFIER, TokenType.NONE, TokenType.RBRACKET, TokenType.STRING, TokenType.NUMBER,
        TokenType.TRUE, TokenType.FALSE, TokenType.LBRACKET, TokenType.LBRACE
    },
    #
    TokenType.SEMICOLON: {
        TokenType.DEF, TokenType.PASS, TokenType.RETURN, TokenType.IF, TokenType.FOR, TokenType.WHILE, TokenType.SWITCH,
        TokenType.IDENTIFIER, TokenType.RBRACE, TokenType.NEWLINE, TokenType.COMMENT, TokenType.EOF
    },


    #
    TokenType.NEWLINE: {
        TokenType.ABSTRACT, TokenType.CLASS, TokenType.DEF, TokenType.FINAL, TokenType.INTERFACE,
        TokenType.IDENTIFIER, TokenType.PASS, TokenType.RETURN, TokenType.IF, TokenType.FOR, TokenType.WHILE,
        TokenType.SWITCH, TokenType.RBRACE, TokenType.COMMENT, TokenType.EOF, TokenType.NEWLINE, TokenType.STATIC,
        TokenType.RAISE, TokenType.IMPORT, TokenType.STRING
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
    # True, False
    # [list], (tuple)
    TokenType.COMMA: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.TRUE, TokenType.FALSE,
        TokenType.LBRACKET, TokenType.LPAREN
    },

    # alpha.beta
    TokenType.DOT: {
        TokenType.IDENTIFIER
    },

    # alpha = beta; / alpha = gamma(...);
    # alpha = 1;
    # alpha = "string";
    # alpha = (alpha, beta);
    # alpha = [alpha, beta];
    # alpha = {alpha: beta, gamma: delta};
    TokenType.ASSIGN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING,
        TokenType.FRSTRING, TokenType.REGEX, TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE,
        TokenType.TRUE, TokenType.FALSE, TokenType.NONE
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
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.FRSTRING,
        TokenType.REGEX, TokenType.LPAREN, TokenType.LBRACKET, TokenType.LBRACE
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
    # -> "string" (for return type annotations)
    # -> [list] (for complex return types)
    TokenType.ARROW: {
        TokenType.NONE, TokenType.IDENTIFIER, TokenType.STRING, TokenType.LBRACKET
    },

    # raise ValueError
    # raise Exception("message")
    TokenType.RAISE: {
        TokenType.IDENTIFIER, TokenType.STRING
    },

    # import module
    # import package.module
    TokenType.IMPORT: {
        TokenType.IDENTIFIER
    },

    # return alpha;
    # return 1;
    # return "string";
    # return;
    # return (alpha, beta);
    # return not ...
    # return True/False
    # return {dict}
    TokenType.RETURN: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING,
        TokenType.SEMICOLON, TokenType.LPAREN, TokenType.NOT, TokenType.TRUE, TokenType.FALSE,
        TokenType.LBRACE
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
    # else 0 (ternary-like)
    TokenType.ELSE: {
        TokenType.LBRACE, TokenType.COLON, TokenType.NUMBER, TokenType.IDENTIFIER, TokenType.STRING
    },

    #
    TokenType.ELIF: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING, TokenType.LPAREN, TokenType.NOT
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

    # x is None
    # obj is not None
    TokenType.IS: {
        TokenType.NONE, TokenType.IDENTIFIER, TokenType.NOT
    },

    TokenType.AND: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.TRUE, TokenType.FALSE,
        TokenType.LPAREN, TokenType.NOT
    },

    TokenType.OR: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.TRUE, TokenType.FALSE,
        TokenType.LPAREN, TokenType.NOT
    },

    # ... not alpha:
    # ... not 1 ...
    # ... not "string" ...
    # ... (...)
    # ... not ...
    # obj not in list
    TokenType.NOT: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING, TokenType.RSTRING,
        TokenType.LPAREN, TokenType.IN
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
    # [item] { body }
    TokenType.RBRACKET: {
        TokenType.COLON, TokenType.COMMA, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.RPAREN,
        TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT,
        TokenType.DOUBLESTAR, TokenType.DOUBLESLASH, TokenType.LESS, TokenType.GREATER,
        TokenType.LESSEQUAL, TokenType.GREATEREQUAL, TokenType.EQUAL, TokenType.NOTEQUAL,
        TokenType.AND, TokenType.OR, TokenType.IN, TokenType.DOT, TokenType.RBRACKET,
        TokenType.LBRACE
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

    # class body {
    # method body {
    # { dict literal }
    # { comprehension }
    TokenType.LBRACE: {
        TokenType.DEF, TokenType.PASS, TokenType.RETURN, TokenType.IF, TokenType.FOR, TokenType.WHILE,
        TokenType.SWITCH, TokenType.IDENTIFIER, TokenType.RBRACE, TokenType.NEWLINE, TokenType.COMMENT,
        TokenType.STRING, TokenType.NUMBER
    },

    #
    TokenType.RBRACE: {
        TokenType.ELSE, TokenType.EOF, TokenType.NEWLINE, TokenType.SEMICOLON, TokenType.RBRACE, TokenType.CASE, TokenType.DEFAULT,
        TokenType.ELIF
    },

    # True;
    # ...True, False)
    # True, False
    # True, False]
    TokenType.BOOLEAN: {
        TokenType.SEMICOLON, TokenType.RPAREN, TokenType.COMMA, TokenType.RBRACKET
    },

    # pass;
    TokenType.PASS: {
        TokenType.SEMICOLON
    },

    # alpha < beta;
    # alpha < 1;
    # alpha < "string";
    # alpha < (expr);
    # alpha < [list];
    # alpha < {set};
    # alpha < func();
    # alpha < obj.attr;
    # alpha < True/False/None;
    TokenType.LESS: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING,
        TokenType.RSTRING, TokenType.FRSTRING, TokenType.LPAREN, TokenType.LBRACKET,
        TokenType.LBRACE, TokenType.TRUE, TokenType.FALSE, TokenType.NONE, TokenType.MINUS
    },

    # alpha > beta;
    # alpha > 1;
    # alpha > "string";
    # alpha > (expr);
    # alpha > [list];
    # alpha > {set};
    # alpha > func();
    # alpha > obj.attr;
    # alpha > True/False/None;
    TokenType.GREATER: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING,
        TokenType.RSTRING, TokenType.FRSTRING, TokenType.LPAREN, TokenType.LBRACKET,
        TokenType.LBRACE, TokenType.TRUE, TokenType.FALSE, TokenType.NONE, TokenType.MINUS
    },

    # alpha <= beta;
    # alpha <= 1;
    # alpha <= "string";
    # alpha <= (expr);
    # alpha <= [list];
    # alpha <= {set};
    # alpha <= func();
    # alpha <= obj.attr;
    # alpha <= True/False/None;
    TokenType.LESSEQUAL: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING,
        TokenType.RSTRING, TokenType.FRSTRING, TokenType.LPAREN, TokenType.LBRACKET,
        TokenType.LBRACE, TokenType.TRUE, TokenType.FALSE, TokenType.NONE, TokenType.MINUS
    },

    # alpha >= beta;
    # alpha >= 1;
    # alpha >= "string";
    # alpha >= (expr);
    # alpha >= [list];
    # alpha >= {set};
    # alpha >= func();
    # alpha >= obj.attr;
    # alpha >= True/False/None;
    TokenType.GREATEREQUAL: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING,
        TokenType.RSTRING, TokenType.FRSTRING, TokenType.LPAREN, TokenType.LBRACKET,
        TokenType.LBRACE, TokenType.TRUE, TokenType.FALSE, TokenType.NONE, TokenType.MINUS
    },

    # alpha == beta;
    # alpha == 1;
    # alpha == "string";
    # alpha == (expr);
    # alpha == [list];
    # alpha == {set};
    # alpha == func();
    # alpha == obj.attr;
    # alpha == True/False/None;
    TokenType.EQUAL: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING,
        TokenType.RSTRING, TokenType.FRSTRING, TokenType.LPAREN, TokenType.LBRACKET,
        TokenType.LBRACE, TokenType.TRUE, TokenType.FALSE, TokenType.NONE, TokenType.MINUS
    },

    # alpha != beta;
    # alpha != 1;
    # alpha != "string";
    # alpha != (expr);
    # alpha != [list];
    # alpha != {set};
    # alpha != func();
    # alpha != obj.attr;
    # alpha != True/False/None;
    TokenType.NOTEQUAL: {
        TokenType.IDENTIFIER, TokenType.NUMBER, TokenType.STRING, TokenType.FSTRING,
        TokenType.RSTRING, TokenType.FRSTRING, TokenType.LPAREN, TokenType.LBRACKET,
        TokenType.LBRACE, TokenType.TRUE, TokenType.FALSE, TokenType.NONE, TokenType.MINUS
    }
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

    if token_type in [TokenType.STARASSIGN, TokenType.SLASHASSIGN, TokenType.PERCENTASSIGN,
                      TokenType.DOUBLESTARASSIGN, TokenType.DOUBLESLASHASSIGN, TokenType.PLUSASSIGN,
                      TokenType.MINUSASSIGN]:
        token_type = TokenType.ASSIGN

    if token_type in [TokenType.TRUE, TokenType.FALSE]:
        token_type = TokenType.BOOLEAN

    return FOLLOW_SET.get(token_type, set())

def check(token, next_token, line, col) -> Optional[IllegalFollow]:
    if (next_token in get_follow_set(token)):
        return None
    else:
        return IllegalFollow(token, next_token, line, col)
