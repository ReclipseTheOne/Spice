"""Tests for the Spy lexer."""

import pytest
from lexer import Lexer, TokenType
from testutils import (
    assert_contains_all, assert_count, log_test_start, 
    log_test_result, safe_assert
)


class TestLexer:
    """Test lexer functionality."""
    
    def test_keywords(self):
        """Test tokenization of Spy keywords."""
        source = "interface abstract final static class def"
        
        log_test_start("test_keywords", source)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        expected_types = [
            TokenType.INTERFACE,
            TokenType.ABSTRACT,
            TokenType.FINAL,
            TokenType.STATIC,
            TokenType.CLASS,
            TokenType.DEF,
            TokenType.NEWLINE,
            TokenType.EOF
        ]

        # Log token information
        token_info = "\n".join([f"   {i}: {token.type.name} = '{token.value}'" for i, token in enumerate(tokens)])
        print(f"✅ Tokenized {len(tokens)} tokens:")
        print(token_info, flush=True)

        safe_assert(
            len(tokens) == len(expected_types),
            f"Expected {len(expected_types)} tokens, got {len(tokens)}",
            f"Tokens: {[t.type.name for t in tokens]}"
        )
        
        for i, (token, expected_type) in enumerate(zip(tokens, expected_types)):
            safe_assert(
                token.type == expected_type,
                f"Token {i}: expected {expected_type.name}, got {token.type.name}",
                f"Token value: '{token.value}'"
            )

    def test_interface_declaration(self):
        """Test interface declaration tokenization."""
        source = """interface Drawable {
    def draw() -> None;
}"""
        
        log_test_start("test_interface_declaration", source)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        # Log token information
        token_info = "\n".join([f"   {i}: {token.type.name} = '{token.value}'" for i, token in enumerate(tokens)])
        print(f"✅ Tokenized {len(tokens)} tokens:")
        print(token_info, flush=True)

        # Check key tokens with enhanced assertions
        safe_assert(tokens[0].type == TokenType.INTERFACE, "First token should be INTERFACE")
        safe_assert(tokens[1].type == TokenType.IDENTIFIER, "Second token should be IDENTIFIER")
        safe_assert(tokens[1].value == "Drawable", f"Identifier should be 'Drawable', got '{tokens[1].value}'")
        safe_assert(tokens[2].type == TokenType.LBRACE, "Third token should be LBRACE")

        # Find semicolon with enhanced checking
        semicolon_tokens = [t for t in tokens if t.type == TokenType.SEMICOLON]
        safe_assert(
            len(semicolon_tokens) > 0,
            "Should find at least one semicolon token",
            f"Token types found: {[t.type.name for t in tokens]}"
        )

    def test_numbers_and_strings(self):
        """Test number and string tokenization."""
        source = '42 3.14 "hello" \'world\''
        
        log_test_start("test_numbers_and_strings", source)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        # Log token information
        token_info = "\n".join([f"   {i}: {token.type.name} = '{token.value}'" for i, token in enumerate(tokens)])
        print(f"✅ Tokenized {len(tokens)} tokens:")
        print(token_info, flush=True)

        safe_assert(tokens[0].type == TokenType.NUMBER, "First token should be NUMBER")
        safe_assert(tokens[0].value == "42", f"First number should be '42', got '{tokens[0].value}'")
        safe_assert(tokens[1].type == TokenType.NUMBER, "Second token should be NUMBER")
        safe_assert(tokens[1].value == "3.14", f"Second number should be '3.14', got '{tokens[1].value}'")
        safe_assert(tokens[2].type == TokenType.STRING, "Third token should be STRING")
        safe_assert(tokens[3].type == TokenType.STRING, "Fourth token should be STRING")

    def test_operators(self):
        """Test operator tokenization."""
        source = "+ - * / == != <= >= = += -="
        
        log_test_start("test_operators", source)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        expected_types = [
            TokenType.PLUS,
            TokenType.MINUS,
            TokenType.STAR,
            TokenType.SLASH,
            TokenType.EQUAL,
            TokenType.NOTEQUAL,
            TokenType.LESSEQUAL,
            TokenType.GREATEREQUAL,
            TokenType.ASSIGN,
            TokenType.PLUSASSIGN,
            TokenType.MINUSASSIGN,
        ]

        # Log token information
        token_info = "\n".join([f"   {i}: {token.type.name} = '{token.value}'" for i, token in enumerate(tokens)])
        print(f"✅ Tokenized {len(tokens)} tokens:")
        print(token_info, flush=True)

        # Check each expected operator type
        for i, expected_type in enumerate(expected_types):
            safe_assert(
                i < len(tokens),
                f"Expected token {i} to exist",
                f"Only {len(tokens)} tokens found"
            )
            safe_assert(
                tokens[i].type == expected_type,
                f"Token {i}: expected {expected_type.name}, got {tokens[i].type.name}",
                f"Token value: '{tokens[i].value}'"
            )

    def test_comments(self):
        """Test comment handling."""
        source = """# This is a comment
x = 5  # inline comment"""
        
        log_test_start("test_comments", source)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        # Log token information
        token_info = "\n".join([f"   {i}: {token.type.name} = '{token.value}'" for i, token in enumerate(tokens)])
        print(f"✅ Tokenized {len(tokens)} tokens:")
        print(token_info, flush=True)

        # Comments should be tokenized but can be filtered later
        # Check that identifier 'x' is present
        identifier_tokens = [t for t in tokens if t.type == TokenType.IDENTIFIER]
        safe_assert(
            len(identifier_tokens) == 1,
            f"Expected 1 identifier token, found {len(identifier_tokens)}",
            f"Identifier tokens: {[t.value for t in identifier_tokens]}"
        )
        safe_assert(
            identifier_tokens[0].value == "x",
            f"Expected identifier 'x', got '{identifier_tokens[0].value}'"
        )

    def test_multiline_code(self):
        """Test multiline code tokenization."""
        source = """class Example:
    def method(self):
        return 42"""
        
        log_test_start("test_multiline_code", source)
        lexer = Lexer()
        tokens = lexer.tokenize(source)

        # Log token information
        token_info = "\n".join([f"   {i}: {token.type.name} = '{token.value}'" for i, token in enumerate(tokens)])
        print(f"✅ Tokenized {len(tokens)} tokens:")
        print(token_info, flush=True)

        # Verify structure
        safe_assert(tokens[0].type == TokenType.CLASS, "First token should be CLASS")
        safe_assert(tokens[1].type == TokenType.IDENTIFIER, "Second token should be IDENTIFIER")
        safe_assert(tokens[1].value == "Example", f"Class name should be 'Example', got '{tokens[1].value}'")
        safe_assert(tokens[2].type == TokenType.COLON, "Third token should be COLON")

        # Find 'def' token
        def_tokens = [t for t in tokens if t.type == TokenType.DEF]
        safe_assert(
            len(def_tokens) == 1,
            f"Expected 1 'def' token, found {len(def_tokens)}",
            f"All token types: {[t.type.name for t in tokens]}"
        )

    def test_error_on_invalid_character(self):
        """Test error handling for invalid characters."""
        source = "valid @ invalid"
        
        log_test_start("test_error_on_invalid_character", source)
        lexer = Lexer()

        # This should raise a SyntaxError
        try:
            tokens = lexer.tokenize(source)
            safe_assert(False, "Expected SyntaxError for invalid character '@'")
        except SyntaxError as e:
            print(f"✅ Correctly caught SyntaxError: {e}", flush=True)
            # Test passes if we get here
            assert True
