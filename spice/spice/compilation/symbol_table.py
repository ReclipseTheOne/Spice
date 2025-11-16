"""
Mostly utility file.
Will be used mostly as a better access point for checks / compiled code parsing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from spice.parser.ast_nodes import ClassDeclaration, FunctionDeclaration, Parameter, ASTNode


@dataclass
class VariableSymbol:
    name: str
    type_annotation: Optional[str]
    node: ASTNode


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


class SymbolTable:
    """Represents declarations discovered during parsing."""

    def __init__(self) -> None:
        self.scopes: Dict[str, ScopeSymbol] = {
            "global": ScopeSymbol(name="global", parent=None)
        }
        self.classes: Dict[str, ClassSymbol] = {}

    def ensure_scope(self, name: str, parent: Optional[str]) -> ScopeSymbol:
        scope = self.scopes.get(name)
        if scope is None:
            scope = ScopeSymbol(name=name, parent=parent)
            self.scopes[name] = scope
        return scope
