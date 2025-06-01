"""AST node definitions for Spy language."""

from dataclasses import dataclass, field
from typing import List, Optional, Any
from abc import ABC, abstractmethod


class ASTNode(ABC):
    """Base class for all AST nodes."""

    @abstractmethod
    def accept(self, visitor):
        """Accept a visitor for traversal."""
        pass


@dataclass
class Module(ASTNode):
    """Root node representing a .spy file."""
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_module(self)


@dataclass
class InterfaceDeclaration(ASTNode):
    """Interface declaration node."""
    name: str
    methods: List['MethodSignature']
    base_interfaces: List[str] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_interface(self)


@dataclass
class MethodSignature(ASTNode):
    """Method signature in an interface."""
    name: str
    params: List['Parameter']
    return_type: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_method_signature(self)


@dataclass
class Parameter(ASTNode):
    """Function/method parameter."""
    name: str
    type_annotation: Optional[str] = None
    default: Optional[Any] = None

    def accept(self, visitor):
        return visitor.visit_parameter(self)


@dataclass
class ClassDeclaration(ASTNode):
    """Class declaration with modifiers."""
    name: str
    body: List[ASTNode]
    bases: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_final: bool = False

    def accept(self, visitor):
        return visitor.visit_class(self)


@dataclass
class FunctionDeclaration(ASTNode):
    """Function/method declaration."""
    name: str
    params: List[Parameter]
    body: List[ASTNode]
    return_type: Optional[str] = None
    is_static: bool = False
    is_abstract: bool = False
    is_final: bool = False
    decorators: List[str] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_function(self)


@dataclass
class BlockStatement(ASTNode):
    """Block statement using curly braces."""
    statements: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_block(self)


@dataclass
class ExpressionStatement(ASTNode):
    """Expression statement (possibly with semicolon)."""
    expression: ASTNode
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_expression_statement(self)
