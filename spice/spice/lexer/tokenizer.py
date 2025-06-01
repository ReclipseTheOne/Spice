"""Tokenizer for Spy (Static Python) language."""

import re
from typing import List
from lexer.tokens import Token, TokenType


class Lexer:
    """Tokenizes Spy source code."""

    # Keywords mapping
    KEYWORDS = {
        # Python keywords
        'def': TokenType.DEF,
        'class': TokenType.CLASS,
        'if': TokenType.IF,
        'elif': TokenType.ELIF,
        'else': TokenType.ELSE,
        'for': TokenType.FOR,
        'while': TokenType.WHILE,
        'return': TokenType.RETURN,
        'import': TokenType.IMPORT,
        'from': TokenType.FROM,
        'as': TokenType.AS,
        'with': TokenType.WITH,
        'try': TokenType.TRY,
        'except': TokenType.EXCEPT,
        'finally': TokenType.FINALLY,
        'raise': TokenType.RAISE,
        'pass': TokenType.PASS,
        'break': TokenType.BREAK,
        'continue': TokenType.CONTINUE,
        'True': TokenType.TRUE,
        'False': TokenType.FALSE,
        'None': TokenType.NONE,
        'and': TokenType.AND,
        'or': TokenType.OR,
        'not': TokenType.NOT,
        'in': TokenType.IN,
        'is': TokenType.IS,
        'lambda': TokenType.LAMBDA,

        # Spice keywords
        'interface': TokenType.INTERFACE,
        'abstract': TokenType.ABSTRACT,
        'final': TokenType.FINAL,
        'static': TokenType.STATIC,
    }

    # Token patterns
    TOKEN_PATTERNS = [
        # Comments
        (r'#.*$', TokenType.COMMENT),

        # Numbers
        (r'\d+\.\d+', TokenType.NUMBER),
        (r'\d+', TokenType.NUMBER),

        # Strings
        (r'""".*?"""', TokenType.STRING),
        (r"'''.*?'''", TokenType.STRING),
        (r'".*?"', TokenType.STRING),
        (r"'.*?'", TokenType.STRING),

        # Operators (order matters!)
        (r'==', TokenType.EQUAL),
        (r'!=', TokenType.NOTEQUAL),
        (r'<=', TokenType.LESSEQUAL),
        (r'>=', TokenType.GREATEREQUAL),
        (r'<', TokenType.LESS),
        (r'>', TokenType.GREATER),
        (r'\+=', TokenType.PLUSASSIGN),
        (r'-=', TokenType.MINUSASSIGN),
        (r'\*=', TokenType.STARASSIGN),
        (r'/=', TokenType.SLASHASSIGN),
        (r'\*\*', TokenType.DOUBLESTAR),
        (r'//', TokenType.DOUBLESLASH),
        (r'->', TokenType.ARROW),
        (r'\+', TokenType.PLUS),
        (r'-', TokenType.MINUS),
        (r'\*', TokenType.STAR),
        (r'/', TokenType.SLASH),
        (r'%', TokenType.PERCENT),
        (r'=', TokenType.ASSIGN),

        # Delimiters
        (r'\(', TokenType.LPAREN),
        (r'\)', TokenType.RPAREN),
        (r'\[', TokenType.LBRACKET),
        (r'\]', TokenType.RBRACKET),
        (r'\{', TokenType.LBRACE),
        (r'\}', TokenType.RBRACE),
        (r',', TokenType.COMMA),
        (r':', TokenType.COLON),
        (r';', TokenType.SEMICOLON),
        (r'\.', TokenType.DOT),

        # Identifiers (must come after keywords)
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
    ]

    def __init__(self):
        self.patterns = [(re.compile(pattern, re.MULTILINE), token_type) for pattern, token_type in self.TOKEN_PATTERNS]

    def tokenize(self, source: str) -> List[Token]:
        """Tokenize source code into a list of tokens."""
        tokens = []
        lines = source.split('\n')

        for line_num, line in enumerate(lines, 1):
            self._tokenize_line(line, line_num, tokens)

        # Add EOF token
        tokens.append(Token(TokenType.EOF, None, len(lines), 0))
        return tokens

    def _tokenize_line(self, line: str, line_num: int, tokens: List[Token]):
        """Tokenize a single line."""
        column = 0

        # Handle indentation
        indent_match = re.match(r'^(\s*)', line)
        if indent_match:
            indent = indent_match.group(1)
            if indent:
                # TODO: Proper indent/dedent handling
                column = len(indent)

        # Skip empty lines
        if not line.strip():
            tokens.append(Token(TokenType.NEWLINE, '\\n', line_num, column))
            return

        # Tokenize the rest of the line
        pos = column
        while pos < len(line):
            # Skip whitespace
            if line[pos].isspace():
                pos += 1
                continue

            # Try to match patterns
            matched = False
            for pattern, token_type in self.patterns:
                match = pattern.match(line, pos)
                if match:
                    value = match.group(0)

                    # Handle keywords vs identifiers
                    if token_type == TokenType.IDENTIFIER and value in self.KEYWORDS:
                        token_type = self.KEYWORDS[value]

                    # Skip comments
                    if token_type != TokenType.COMMENT:
                        tokens.append(Token(token_type, value, line_num, pos))

                    pos = match.end()
                    matched = True
                    break

            if not matched:
                raise SyntaxError(f"Invalid character '{line[pos]}' at line {line_num}, column {pos}")

        # Add newline token at end of non-empty lines
        tokens.append(Token(TokenType.NEWLINE, '\\n', line_num, len(line)))
