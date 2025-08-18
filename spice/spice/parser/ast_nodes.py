"""AST node definitions for Spice language."""

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
    """Root node representing a .spc file."""
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_Module(self)


@dataclass
class InterfaceDeclaration(ASTNode):
    """Interface declaration node."""
    name: str
    methods: List['MethodSignature']
    base_interfaces: List[str] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_InterfaceDeclaration(self)


@dataclass
class MethodSignature(ASTNode):
    """Method signature in an interface."""
    name: str
    params: List['Parameter']
    return_type: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_MethodSignature(self)


@dataclass
class Parameter(ASTNode):
    """Function/method parameter."""
    name: str
    type_annotation: Optional[str] = None
    default: Optional[Any] = None

    def accept(self, visitor):
        return visitor.visit_Parameter(self)


@dataclass
class ClassDeclaration(ASTNode):
    """Class declaration with modifiers."""
    name: str
    body: List[ASTNode]
    bases: List[str] = field(default_factory=list)  # Classes extended with 'extends'
    interfaces: List[str] = field(default_factory=list)  # Interfaces implemented with 'implements'
    is_abstract: bool = False
    is_final: bool = False

    def accept(self, visitor):
        return visitor.visit_ClassDeclaration(self)


@dataclass
class FunctionDeclaration(ASTNode):
    """Function/method declaration."""
    name: str
    params: List[Parameter]
    body: Optional[List[ASTNode]] = None
    return_type: Optional[str] = None
    is_static: bool = False
    is_abstract: bool = False
    is_final: bool = False
    decorators: List[str] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_FunctionDeclaration(self)


@dataclass
class BlockStatement(ASTNode):
    """Block statement using curly braces."""
    statements: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_BlockStatement(self)


@dataclass
class ExpressionStatement(ASTNode):
    """Expression statement (possibly with semicolon)."""
    expression: Optional[ASTNode]
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_ExpressionStatement(self)


@dataclass
class PassStatement(ASTNode):
    """Pass statement."""
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_PassStatement(self)


@dataclass
class ReturnStatement(ASTNode):
    """Return statement."""
    value: Optional["Expression"] = None
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_ReturnStatement(self)


@dataclass
class IfStatement(ASTNode):
    """If statement."""
    condition: "Expression"
    then_body: List[ASTNode]
    else_body: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_IfStatement(self)


@dataclass
class ForStatement(ASTNode):
    """For statement."""
    target: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_ForStatement(self)


@dataclass
class WhileStatement(ASTNode):
    """While statement."""
    condition: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_WhileStatement(self)


@dataclass
class SwitchStatement(ASTNode):
    """Switch statement."""
    expression: "Expression"
    cases: List[ASTNode]
    default: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_SwitchStatement(self)


@dataclass
class CaseClause(ASTNode):
    """Case clause in a switch statement."""
    value: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_CaseClause(self)


# Expression nodes
@dataclass
class Expression(ASTNode):
    """Base class for expressions."""
    pass


@dataclass
class AssignmentExpression(Expression):
    """Assignment expression: target = value or target += value, etc."""
    target: Expression
    value: Expression
    operator: str = '='  # '=', '+=', '-=', '*=', '/=', etc.

    def accept(self, visitor):
        return visitor.visit_AssignmentExpression(self)


@dataclass
class IdentifierExpression(Expression):
    """Identifier expression."""
    name: str

    def accept(self, visitor):
        return visitor.visit_IdentifierExpression(self)


@dataclass
class AttributeExpression(Expression):
    """Attribute access: object.attribute."""
    object: Expression
    attribute: str

    def accept(self, visitor):
        return visitor.visit_AttributeExpression(self)


@dataclass
class LiteralExpression(Expression):
    """Literal value (string, number, etc.)."""
    value: Any
    literal_type: str  # 'string', 'number', 'boolean', etc.

    def accept(self, visitor):
        return visitor.visit_LiteralExpression(self)


@dataclass
class CallExpression(Expression):
    """Function or method call: callee(args)."""
    callee: Expression
    arguments: List[Expression]

    def accept(self, visitor):
        return visitor.visit_CallExpression(self)


@dataclass
class ArgumentExpression(Expression):
    """Argument in a function call."""
    name: Optional[str] = None
    value: Optional[Expression] = None

    def accept(self, visitor):
        return visitor.visit_ArgumentExpression(self)


@dataclass
class LogicalExpression(Expression):
    """Logical expression: left and/or right."""
    operator: str  # 'and' or 'or'
    left: Expression
    right: Expression

    def accept(self, visitor):
        return visitor.visit_LogicalExpression(self)


@dataclass
class UnaryExpression(Expression):
    """Unary expression: not operand."""
    operator: str  # 'not'
    operand: Expression

    def accept(self, visitor):
        return visitor.visit_UnaryExpression(self)


@dataclass
class BinaryExpression(Expression):
    """Binary expression: left operator right."""
    operator: str  # '+', '-', '*', '/'...
    left: Expression
    right: Expression

    def accept(self, visitor):
        return visitor.visit_BinaryExpression(self)


@dataclass
class LambdaExpression(Expression):
    """Lambda expression: (params) => body."""
    params: List[Parameter]
    body: Expression
    return_type: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_LambdaExpression(self)


@dataclass
class RaiseStatement(ASTNode):
    """Raise statement for exceptions."""
    exception: Optional["Expression"] = None
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_RaiseStatement(self)


@dataclass
class ImportStatement(ASTNode):
    """Import statement: import module or from module import names."""
    module: str
    names: List[str] = field(default_factory=list)  # Empty for 'import module'
    aliases: List[Optional[str]] = field(default_factory=list)  # For 'as' aliases
    is_from_import: bool = False
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_ImportStatement(self)


@dataclass
class DictEntry(Expression):
    """Dictionary key-value pair."""
    key: Expression
    value: Expression

    def accept(self, visitor):
        return visitor.visit_DictEntry(self)


@dataclass
class SubscriptExpression(Expression):
    """Subscript expression: object[index] or object[slice]."""
    object: Expression
    index: Expression  # Can be a simple expression or SliceExpression

    def accept(self, visitor):
        return visitor.visit_SubscriptExpression(self)


@dataclass
class SliceExpression(Expression):
    """Slice expression: start:stop:step."""
    start: Optional[Expression] = None
    stop: Optional[Expression] = None
    step: Optional[Expression] = None

    def accept(self, visitor):
        return visitor.visit_SliceExpression(self)

@dataclass
class ComprehensionExpression(Expression):
    """Comprehension expression: [expr for target in iter if condition]"""
    element: Expression  # The expression to evaluate for each item
    target: Expression   # The loop variable(s)
    iter: Expression     # The iterable to loop over
    condition: Optional[Expression] = None  # Optional filter condition
    comp_type: str = 'generator'  # 'generator', 'list', 'dict', 'set'
    key: Optional[Expression] = None  # For dict comprehensions: key expression

    def accept(self, visitor):
        return visitor.visit_ComprehensionExpression(self)

@dataclass
class FinalDeclaration(ASTNode):
    """Final variable declaration that cannot be reassigned."""
    target: Expression
    value: Expression
    type_annotation: Optional[str] = None
    
    def accept(self, visitor):
        return visitor.visit_FinalDeclaration(self)