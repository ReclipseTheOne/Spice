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
    bases: List[str] = field(default_factory=list)  # Classes extended with 'extends'
    interfaces: List[str] = field(default_factory=list)  # Interfaces implemented with 'implements'
    is_abstract: bool = False
    is_final: bool = False

    def accept(self, visitor):
        return visitor.visit_class(self)


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
    expression: Optional[ASTNode]
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_expression_statement(self)


@dataclass
class PassStatement(ASTNode):
    """Pass statement."""
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_pass_statement(self)


@dataclass
class ReturnStatement(ASTNode):
    """Return statement."""
    value: Optional["Expression"] = None
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_return_statement(self)


@dataclass
class IfStatement(ASTNode):
    """If statement."""
    condition: "Expression"
    then_body: List[ASTNode]
    else_body: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_if_statement(self)


@dataclass
class ForStatement(ASTNode):
    """For statement."""
    target: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_for_statement(self)


@dataclass
class WhileStatement(ASTNode):
    """While statement."""
    condition: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_while_statement(self)


@dataclass
class SwitchStatement(ASTNode):
    """Switch statement."""
    expression: "Expression"
    cases: List[ASTNode]
    default: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_switch_statement(self)


@dataclass
class CaseClause(ASTNode):
    """Case clause in a switch statement."""
    value: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_case_clause(self)


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
        return visitor.visit_assignment(self)


@dataclass
class IdentifierExpression(Expression):
    """Identifier expression."""
    name: str

    def accept(self, visitor):
        return visitor.visit_identifier(self)


@dataclass
class AttributeExpression(Expression):
    """Attribute access: object.attribute."""
    object: Expression
    attribute: str

    def accept(self, visitor):
        return visitor.visit_attribute(self)


@dataclass
class LiteralExpression(Expression):
    """Literal value (string, number, etc.)."""
    value: Any
    literal_type: str  # 'string', 'number', 'boolean', etc.

    def accept(self, visitor):
        return visitor.visit_literal(self)


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
        return visitor.visit_logical_expression(self)


@dataclass
class UnaryExpression(Expression):
    """Unary expression: not operand."""
    operator: str  # 'not'
    operand: Expression

    def accept(self, visitor):
        return visitor.visit_unary_expression(self)


@dataclass
class BinaryExpression(Expression):
    """Binary expression: left operator right."""
    operator: str  # '+', '-', '*', '/'...
    left: Expression
    right: Expression

    def accept(self, visitor):
        return visitor.visit_binary_expression(self)


@dataclass
class LambdaExpression(Expression):
    """Lambda expression: (params) => body."""
    params: List[Parameter]
    body: Expression
    return_type: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_lambda_expression(self)


@dataclass
class RaiseStatement(ASTNode):
    """Raise statement for exceptions."""
    exception: Optional["Expression"] = None
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_raise_statement(self)


@dataclass
class ImportStatement(ASTNode):
    """Import statement: import module or from module import names."""
    module: str
    names: List[str] = field(default_factory=list)  # Empty for 'import module'
    aliases: List[Optional[str]] = field(default_factory=list)  # For 'as' aliases
    is_from_import: bool = False
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_import_statement(self)


@dataclass
class DictEntry(Expression):
    """Dictionary key-value pair."""
    key: Expression
    value: Expression

    def accept(self, visitor):
        return visitor.visit_dict_entry(self)
