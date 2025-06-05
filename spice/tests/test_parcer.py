"""Tests for the Spy parser."""

import pytest
from lexer import Lexer
from parser import Parser
from parser.ast_nodes import InterfaceDeclaration
from testutils import (
    assert_contains_all, assert_count, log_test_start, 
    log_test_result, safe_assert
)


class TestParser:
    """Test parser functionality."""

    def parse_source(self, source: str):
        """Helper to parse source code."""
        lexer = Lexer()
        tokens = lexer.tokenize(source)
        parser = Parser()
        return parser.parse(tokens)

    def test_interface_declaration(self):
        """Test parsing interface declaration."""
        source = """interface Drawable {
    def draw(x: int, y: int) -> None;
    def get_bounds() -> tuple;
}"""

        log_test_start("test_interface_declaration", source)
        ast = self.parse_source(source)

        # Log parsing result
        print(f"✅ Parsed AST with {len(ast.body)} top-level nodes", flush=True)
        print(f"   First node type: {type(ast.body[0]).__name__}", flush=True)

        safe_assert(len(ast.body) == 1, f"Expected 1 AST node, got {len(ast.body)}")
        interface = ast.body[0]

        safe_assert(isinstance(interface, InterfaceDeclaration), 
                   f"Expected InterfaceDeclaration, got {type(interface).__name__}")
        safe_assert(interface.name == "Drawable", 
                   f"Expected interface name 'Drawable', got '{interface.name}'")
        safe_assert(len(interface.methods) == 2, 
                   f"Expected 2 methods, got {len(interface.methods)}")

        # Check first method
        draw_method = interface.methods[0]
        safe_assert(draw_method.name == "draw", 
                   f"Expected first method name 'draw', got '{draw_method.name}'")
        safe_assert(len(draw_method.params) == 2, 
                   f"Expected 2 parameters for draw method, got {len(draw_method.params)}")
        safe_assert(draw_method.params[0].name == "x", 
                   f"Expected first param 'x', got '{draw_method.params[0].name}'")
        safe_assert(draw_method.params[0].type_annotation == "int", 
                   f"Expected first param type 'int', got '{draw_method.params[0].type_annotation}'")
        safe_assert(draw_method.return_type == "None", 
                   f"Expected return type 'None', got '{draw_method.return_type}'")

        # Check second method
        bounds_method = interface.methods[1]
        safe_assert(bounds_method.name == "get_bounds", 
                   f"Expected second method name 'get_bounds', got '{bounds_method.name}'")
        safe_assert(len(bounds_method.params) == 0, 
                   f"Expected 0 parameters for get_bounds method, got {len(bounds_method.params)}")
        safe_assert(bounds_method.return_type == "tuple", 
                   f"Expected return type 'tuple', got '{bounds_method.return_type}'")

    def test_interface_with_inheritance(self):
        """Test interface with base interfaces."""
        source = """interface Colorable extends Drawable {
    def set_color(color: str) -> None;
}"""

        log_test_start("test_interface_with_inheritance", source)
        ast = self.parse_source(source)
        interface = ast.body[0]

        # Log parsing result
        print(f"✅ Parsed interface with inheritance", flush=True)
        print(f"   Interface name: {interface.name}", flush=True)
        print(f"   Base interfaces: {interface.base_interfaces}", flush=True)

        safe_assert(isinstance(interface, InterfaceDeclaration),
                   f"Expected InterfaceDeclaration, got {type(interface).__name__}")
        safe_assert(interface.name == "Colorable",
                   f"Expected interface name 'Colorable', got '{interface.name}'")
        safe_assert(interface.base_interfaces == ["Drawable"],
                   f"Expected base interfaces ['Drawable'], got {interface.base_interfaces}")
        safe_assert(len(interface.methods) == 1,
                   f"Expected 1 method, got {len(interface.methods)}")

    def test_empty_interface(self):
        """Test empty interface parsing."""
        source = """interface Empty {
}"""

        log_test_start("test_empty_interface", source)
        ast = self.parse_source(source)
        interface = ast.body[0]

        # Log parsing result
        print(f"✅ Parsed empty interface", flush=True)
        print(f"   Interface name: {interface.name}", flush=True)
        print(f"   Methods count: {len(interface.methods)}", flush=True)

        safe_assert(isinstance(interface, InterfaceDeclaration),
                   f"Expected InterfaceDeclaration, got {type(interface).__name__}")
        safe_assert(interface.name == "Empty",
                   f"Expected interface name 'Empty', got '{interface.name}'")
        safe_assert(len(interface.methods) == 0,
                   f"Expected 0 methods, got {len(interface.methods)}")

    def test_method_with_default_param(self):
        """Test method with default parameter."""
        source = """interface Example {
    def method(x: int, y: int = 0) -> int;
}"""

        log_test_start("test_method_with_default_param", source)
        ast = self.parse_source(source)
        interface = ast.body[0]
        method = interface.methods[0]

        # Log parsing result
        print(f"✅ Parsed method with default parameter", flush=True)
        print(f"   Method name: {method.name}", flush=True)
        print(f"   Parameters count: {len(method.params)}", flush=True)
        print(f"   Second param default: {method.params[1].default}", flush=True)

        safe_assert(len(method.params) == 2,
                   f"Expected 2 parameters, got {len(method.params)}")
        safe_assert(method.params[1].name == "y",
                   f"Expected second param name 'y', got '{method.params[1].name}'")
        safe_assert(method.params[1].default == "0",
                   f"Expected default value '0', got '{method.params[1].default}'")

    @pytest.mark.skip(reason="Python-style parsing not yet implemented")
    def test_python_style_interface(self):
        """Test Python-style interface declaration."""
        source = """interface Drawable:
    def draw(x: int, y: int) -> None
    def get_bounds() -> tuple"""

        log_test_start("test_python_style_interface", source)
        ast = self.parse_source(source)
        interface = ast.body[0]

        safe_assert(isinstance(interface, InterfaceDeclaration),
                   f"Expected InterfaceDeclaration, got {type(interface).__name__}")
        safe_assert(interface.name == "Drawable",
                   f"Expected interface name 'Drawable', got '{interface.name}'")
        safe_assert(len(interface.methods) == 2,
                   f"Expected 2 methods, got {len(interface.methods)}")
