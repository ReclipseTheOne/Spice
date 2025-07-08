"""Tokenizer for Spy (Static Python) language."""

import re
from typing import List
from lexer.follow_set import check, IllegalFollow
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
        'extends': TokenType.EXTENDS,
        'implements': TokenType.IMPLEMENTS,
        'switch': TokenType.SWITCH,
        'case': TokenType.CASE,
        'default': TokenType.DEFAULT,
    }

    # Token patterns
    TOKEN_PATTERNS = [
        # Comments
        (r'#.*$', TokenType.COMMENT),

        # Numbers
        (r'\d+\.\d+', TokenType.NUMBER),
        (r'\d+', TokenType.NUMBER),

        # Strings
        (r'f""".*?"""|f\'\'\'.*?\'\'\'|f".*?"|f\'.*?\'', TokenType.FSTRING),
        (r'r""".*?"""|r\'\'\'.*?\'\'\'|r".*?"|r\'.*?\'', TokenType.RSTRING),
        (r'fr""".*?"""|fr\'\'\'.*?\'\'\'|fr".*?"|fr\'.*?\'|rf""".*?"""|rf\'\'\'.*?\'\'\'|rf".*?"|rf\'.*?\'', TokenType.FRSTRING),
        (r'REGEX".*?"|REGEX\'.*?\'', TokenType.REGEX),
        (r'""".*?"""|\'\'\'.*?\'\'\'|".*?"|\'.*?\'', TokenType.STRING),

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
        # Note: Identifiers and function/method calls are always valid operands in logical/boolean expressions (see parser).
        (r'[a-zA-Z_][a-zA-Z0-9_]*', TokenType.IDENTIFIER),
    ]

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.patterns = [(re.compile(pattern, re.MULTILINE), token_type) for pattern, token_type in self.TOKEN_PATTERNS]
        self.errors: list[IllegalFollow] = []

    def tokenize(self, source: str) -> List[Token]:
        """Tokenize source code into a list of tokens."""
        if self.verbose:
            print(f"Starting tokenization of source code ({len(source)} characters)")
            print(source)

        tokens = []
        lines = source.split('\n')

        if self.verbose:
            print(f"Processing {len(lines)} lines of code")

        for line_num, line in enumerate(lines, 1):
            if self.verbose and (line_num == 1 or line_num % 100 == 0 or line_num == len(lines)):
                print(f"Tokenizing line {line_num}/{len(lines)}")
            self._tokenize_line(line, line_num, tokens)

        # Add EOF token
        tokens.append(Token(TokenType.EOF, None, len(lines), 0))

        if self.verbose:
            token_types = {}
            for token in tokens:
                if token.type != TokenType.COMMENT and token.type != TokenType.NEWLINE:
                    token_types[token.type.name] = token_types.get(token.type.name, 0) + 1

            print(f"Tokenization complete: {len(tokens)} tokens generated")
            print(f"Token type distribution: {token_types}")

            # Print first few tokens for debugging
            if len(tokens) > 10:
                print("First 10 tokens: " + ', '.join(f"{token.type.name}({token.value})" for token in tokens[:10] if token.type != TokenType.COMMENT))
            else:
                print("All tokens: " + ', '.join(f"{token.type.name}({token.value})" for token in tokens if token.type != TokenType.COMMENT))

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
                if self.verbose and len(indent) > 0:
                    print(f"Line {line_num}: Found indentation of {len(indent)} spaces")

        # Skip empty lines
        if not line.strip():
            tokens.append(Token(TokenType.NEWLINE, '\\\\n', line_num, column))
            if self.verbose:
                print(f"Line {line_num}: Empty line, added NEWLINE token")
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
                        if self.verbose:
                            print(f"Line {line_num}, Column {pos}: Identified keyword '{value}' as {token_type.name}")
                    elif self.verbose and token_type != TokenType.COMMENT:
                        print(f"Line {line_num}, Column {pos}: Matched '{value}' as {token_type.name}")

                    # Skip comments
                    if token_type != TokenType.COMMENT:
                        tokens.append(Token(token_type, value, line_num, pos))
                    elif self.verbose:
                        print(f"Line {line_num}, Column {pos}: Skipping comment")

                    # Check for illegal follows
                    if len(tokens) >= 2:
                        err = check(tokens[-2].type, tokens[-1].type, line_num, pos)
                        if err is not None:
                            self.errors.append(err)

                    pos = match.end()
                    matched = True
                    break

            if not matched:
                error_msg = f"Invalid character '{line[pos]}' at line {line_num}, column {pos}"
                if self.verbose:
                    print(f"ERROR: {error_msg}")
                raise SyntaxError(error_msg)

        # Add newline token at end of non-empty lines
        tokens.append(Token(TokenType.NEWLINE, '\\\\n', line_num, len(line)))
        if self.verbose and len(tokens) > 1 and tokens[-2].type != TokenType.NEWLINE:
            print(f"Line {line_num}: Added NEWLINE token at end of line")
