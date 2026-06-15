"""
Mostly utility file.
Will be used mostly as a better access point for checks / compiled code parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from spice.parser.ast_nodes import ClassDeclaration, FunctionDeclaration, InterfaceDeclaration, Parameter, ASTNode, TypeParameter


@dataclass
class VariableSymbol:
    name: str
    type_annotation: Optional[str]
    node: ASTNode

    # For generic types: maps type parameter names to concrete types
    # e.g., {"T": "int"} for Stack<int>
    generic_bindings: Dict[str, str] = field(default_factory=dict)


@dataclass
class FunctionSymbol:
    name: str
    params: List[Parameter]
    return_type: Optional[str]
    node: FunctionDeclaration
    scope: str


@dataclass
class ScopeSymbol:
    name: str
    parent: Optional[str]
    variables: Dict[str, VariableSymbol] = field(default_factory=dict)
    functions: Dict[str, List[FunctionSymbol]] = field(default_factory=dict)


@dataclass
class ClassSymbol:
    name: str
    node: ClassDeclaration
    methods: Dict[str, List[FunctionSymbol]] = field(default_factory=dict)
    scope: str = "global"
    # Generics
    type_parameters: List[str] = field(default_factory=list)

    def is_generic(self) -> bool:
        """Check if this class has generic type parameters."""
        return len(self.type_parameters) > 0


@dataclass
class InterfaceSymbol:
    name: str
    node: InterfaceDeclaration
    scope: str = "global"


class SymbolTable:
    """Represents declarations discovered during parsing."""

    def __init__(self) -> None:
        self.scopes: Dict[str, ScopeSymbol] = {
            "global": ScopeSymbol(name="global", parent=None)
        }
        self.classes: Dict[str, ClassSymbol] = {}
        self.interfaces: Dict[str, InterfaceSymbol] = {}

    def ensure_scope(self, name: str, parent: Optional[str]) -> ScopeSymbol:
        scope = self.scopes.get(name)
        if scope is None:
            scope = ScopeSymbol(name=name, parent=parent)
            self.scopes[name] = scope
        return scope

    def ancestors(self, name: str, _seen: Optional[set] = None) -> set:
        """All type names reachable from `name` via extends/implements links.

        Walks class bases + implemented interfaces and interface base interfaces
        transitively. Does not include `name` itself.
        """
        if _seen is None:
            _seen = set()

        class_symbol = self.classes.get(name)
        if class_symbol is not None:
            node = class_symbol.node
            for base in list(getattr(node, "bases", [])) + list(getattr(node, "interfaces", [])):
                if base not in _seen:
                    _seen.add(base)
                    self.ancestors(base, _seen)

        interface_symbol = self.interfaces.get(name)
        if interface_symbol is not None:
            for base in getattr(interface_symbol.node, "base_interfaces", []):
                if base not in _seen:
                    _seen.add(base)
                    self.ancestors(base, _seen)

        return _seen
