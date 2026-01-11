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

    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class Module(ASTNode):
    """Root node representing a .spc file."""
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_Module(self)

    def __str__(self) -> str:
        ret = "Module: "
        for stmt in self.body:
            ret += f"\n  {stmt}"
        return ret


@dataclass
class InterfaceDeclaration(ASTNode):
    """Interface declaration node."""
    name: str
    methods: List['MethodSignature']
    base_interfaces: List[str] = field(default_factory=list)
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_InterfaceDeclaration(self)

    def __str__(self) -> str:
        ret = f"InterfaceDeclaration(name={self.name}, methods=["
        ret += ", ".join(f"{method}" for method in self.methods)
        ret += f"], base_interfaces={self.base_interfaces})"
        return ret


@dataclass
class MethodSignature(ASTNode):
    """Method signature in an interface."""
    name: str
    params: List['Parameter']
    return_type: Optional[str] = None
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_MethodSignature(self)

    def __str__(self) -> str:
        ret = f"MethodSignature(name={self.name}, params=["
        ret += ", ".join(f"{param}" for param in self.params)
        ret += f"], return_type={self.return_type})"
        return ret


@dataclass
class Parameter(ASTNode):
    """Function/method parameter."""
    name: str
    type_annotation: Optional[str] = None
    default: Optional[Any] = None
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_Parameter(self)

    def __str__(self) -> str:
        return f"Parameter(name={self.name}, type_annotation={self.type_annotation}, default={self.default})"


@dataclass
class TypeParameter(ASTNode):
    """Type parameter for generics: <T extends Bound>."""
    name: str
    bound: Optional[str] = None  # Upper bound constraint
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_TypeParameter(self)

    def __str__(self) -> str:
        bound_str = f" extends {self.bound}" if self.bound else ""
        return f"TypeParameter(name={self.name}{bound_str})"


@dataclass
class ClassDeclaration(ASTNode):
    """Class declaration with modifiers."""
    name: str
    body: List[ASTNode]
    type_parameters: List[TypeParameter] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    is_abstract: bool = False
    is_final: bool = False
    compiler_flags: List[str] = field(default_factory=list)
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_ClassDeclaration(self)

    def __str__(self) -> str:
        ret = f"ClassDeclaration(name={self.name}, bases={self.bases}, interfaces={self.interfaces}, "
        ret += f"is_abstract={self.is_abstract}, is_final={self.is_final}, compiler_flags={self.compiler_flags})"
        return ret


@dataclass
class FunctionDeclaration(ASTNode):
    """Function/method declaration."""
    name: str
    params: List[Parameter]
    body: Optional[List[ASTNode]] = None
    return_type: Optional[str] = None
    type_parameters: List[TypeParameter] = field(default_factory=list)
    is_static: bool = False
    is_abstract: bool = False
    is_final: bool = False
    decorators: List[str] = field(default_factory=list)
    compiler_flags: List[str] = field(default_factory=list)
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_FunctionDeclaration(self)

    def __str__(self) -> str:
        ret = f"FunctionDeclaration(name={self.name}, params=["
        ret += ", ".join(f"{param}" for param in self.params)
        ret += f"], body={self.body}, return_type={self.return_type}, "
        ret += f"is_static={self.is_static}, is_abstract={self.is_abstract}, is_final={self.is_final}, "
        ret += f"decorators={self.decorators}, compiler_flags={self.compiler_flags})"
        return ret


@dataclass
class BlockStatement(ASTNode):
    """Block statement using curly braces."""
    statements: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_BlockStatement(self)

    def __str__(self) -> str:
        ret = "BlockStatement: "
        for stmt in self.statements:
            ret += f"\n  {stmt}"
        return ret


@dataclass
class ExpressionStatement(ASTNode):
    """Expression statement (possibly with semicolon)."""
    expression: Optional[ASTNode]
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_ExpressionStatement(self)

    def __str__(self) -> str:
        return f"ExpressionStatement(expression={self.expression}, has_semicolon={self.has_semicolon})"


@dataclass
class PassStatement(ASTNode):
    """Pass statement."""
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_PassStatement(self)

    def __str__(self) -> str:
        return f"PassStatement(has_semicolon={self.has_semicolon})"


@dataclass
class ReturnStatement(ASTNode):
    """Return statement."""
    value: Optional["Expression"] = None
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_ReturnStatement(self)

    def __str__(self) -> str:
        return f"ReturnStatement(value={self.value}, has_semicolon={self.has_semicolon})"


@dataclass
class IfStatement(ASTNode):
    """If statement."""
    condition: "Expression"
    then_body: List[ASTNode]
    else_body: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_IfStatement(self)

    def __str__(self) -> str:
        return f"IfStatement(condition={self.condition}, then_body={self.then_body}, else_body={self.else_body})"


@dataclass
class ForStatement(ASTNode):
    """For statement."""
    target: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_ForStatement(self)

    def __str__(self) -> str:
        return f"ForStatement(target={self.target}, body={self.body})"


@dataclass
class WhileStatement(ASTNode):
    """While statement."""
    condition: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_WhileStatement(self)

    def __str__(self) -> str:
        return f"WhileStatement(condition={self.condition}, body={self.body})"


@dataclass
class SwitchStatement(ASTNode):
    """Switch statement."""
    expression: "Expression"
    cases: List[ASTNode]
    default: List[ASTNode] = field(default_factory=list)

    def accept(self, visitor):
        return visitor.visit_SwitchStatement(self)

    def __str__(self) -> str:
        return f"SwitchStatement(expression={self.expression}, cases={self.cases}, default={self.default})"


@dataclass
class CaseClause(ASTNode):
    """Case clause in a switch statement."""
    value: "Expression"
    body: List[ASTNode]

    def accept(self, visitor):
        return visitor.visit_CaseClause(self)

    def __str__(self) -> str:
        return f"CaseClause(value={self.value}, body={self.body})"


# Expression nodes
@dataclass
class Expression(ASTNode):
    """Base class for expressions."""
    pass


@dataclass
class AssignmentExpression(Expression):
    """
    Unified assignment expression supporting:
    - Simple assignment: target = value
    - Compound assignment: target += value, target -= value, etc.
    - Type declaration: target: type
    - Typed assignment: target: type = value
    """
    target: Expression
    value: Optional[Expression] = None
    operator: Optional[str] = None  # '=', '+=', '-=', '*=', '/=', etc. None for declarations
    type_annotation: Optional[str] = None
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_AssignmentExpression(self)

    def __str__(self) -> str:
        return (
            f"AssignmentExpression(target={self.target}, value={self.value}, "
            f"operator={self.operator}, type_annotation={self.type_annotation})"
        )


@dataclass
class IdentifierExpression(Expression):
    """Identifier expression."""
    name: str

    def accept(self, visitor):
        return visitor.visit_IdentifierExpression(self)

    def __str__(self) -> str:
        return f"IdentifierExpression(name={self.name})"


@dataclass
class AttributeExpression(Expression):
    """Attribute access: object.attribute."""
    object: Expression
    attribute: str

    def accept(self, visitor):
        return visitor.visit_AttributeExpression(self)

    def __str__(self) -> str:
        return f"AttributeExpression(object={self.object}, attribute={self.attribute})"


@dataclass
class LiteralExpression(Expression):
    """Literal value (string, number, etc.)."""
    value: Any
    literal_type: str  # 'string', 'number', 'boolean', etc.

    def accept(self, visitor):
        return visitor.visit_LiteralExpression(self)

    def __str__(self) -> str:
        return f"LiteralExpression(value={self.value}, literal_type={self.literal_type})"


@dataclass
class CallExpression(Expression):
    """Function or method call: callee(args)."""
    callee: Expression
    arguments: List[Expression]

    def accept(self, visitor):
        return visitor.visit_CallExpression(self)

    def __str__(self) -> str:
        return f"CallExpression(callee={self.callee}, arguments={self.arguments})"


@dataclass
class ArgumentExpression(Expression):
    """Argument in a function call."""
    name: Optional[str] = None
    value: Optional[Expression] = None

    def accept(self, visitor):
        return visitor.visit_ArgumentExpression(self)

    def __str__(self) -> str:
        return f"ArgumentExpression(name={self.name}, value={self.value})"


@dataclass
class LogicalExpression(Expression):
    """Logical expression: left and/or right."""
    operator: str  # 'and' or 'or'
    left: Expression
    right: Expression

    def accept(self, visitor):
        return visitor.visit_LogicalExpression(self)

    def __str__(self) -> str:
        return f"LogicalExpression(operator={self.operator}, left={self.left}, right={self.right})"


@dataclass
class UnaryExpression(Expression):
    """Unary expression: not operand."""
    operator: str  # 'not'
    operand: Expression

    def accept(self, visitor):
        return visitor.visit_UnaryExpression(self)

    def __str__(self) -> str:
        return f"UnaryExpression(operator={self.operator}, operand={self.operand})"


@dataclass
class BinaryExpression(Expression):
    """Binary expression: left operator right."""
    operator: str  # '+', '-', '*', '/'...
    left: Expression
    right: Expression

    def accept(self, visitor):
        return visitor.visit_BinaryExpression(self)

    def __str__(self) -> str:
        return f"BinaryExpression(operator={self.operator}, left={self.left}, right={self.right})"


@dataclass
class LambdaExpression(Expression):
    """Lambda expression: (params) => body."""
    params: List[Parameter]
    body: Expression
    return_type: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_LambdaExpression(self)

    def __str__(self) -> str:
        return f"LambdaExpression(params={self.params}, body={self.body}, return_type={self.return_type})"


@dataclass
class RaiseStatement(ASTNode):
    """Raise statement for exceptions."""
    exception: Optional["Expression"] = None
    has_semicolon: bool = False

    def accept(self, visitor):
        return visitor.visit_RaiseStatement(self)

    def __str__(self) -> str:
        return f"RaiseStatement(exception={self.exception}, has_semicolon={self.has_semicolon})"


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

    def __str__(self) -> str:
        ret = (
            "ImportStatement: \n"
            f"    module: {self.module},\n"
            f"    names: {self.names},\n"
            f"    aliases: {self.aliases},\n"
            f"    is_from_import: {self.is_from_import}"
        )
        return ret


@dataclass
class DictEntry(Expression):
    """Dictionary key-value pair."""
    key: Expression
    value: Expression

    def accept(self, visitor):
        return visitor.visit_DictEntry(self)

    def __str__(self) -> str:
        return f"DictEntry(key={self.key}, value={self.value})"


@dataclass
class SubscriptExpression(Expression):
    """Subscript expression: object[index] or object[slice]."""
    object: Expression
    index: Expression  # Can be a simple expression or SliceExpression

    def accept(self, visitor):
        return visitor.visit_SubscriptExpression(self)

    def __str__(self) -> str:
        return f"SubscriptExpression(object={self.object}, index={self.index})"


@dataclass
class SliceExpression(Expression):
    """Slice expression: start:stop:step."""
    start: Optional[Expression] = None
    stop: Optional[Expression] = None
    step: Optional[Expression] = None

    def accept(self, visitor):
        return visitor.visit_SliceExpression(self)

    def __str__(self) -> str:
        return f"SliceExpression(start={self.start}, stop={self.stop}, step={self.step})"


@dataclass
class ComprehensionExpression(Expression):
    """Comprehension expression: [expr for target in iter if condition]"""
    element: Expression
    target: Expression
    iter: Expression
    condition: Optional[Expression] = None
    comp_type: str = 'generator'
    key: Optional[Expression] = None

    def accept(self, visitor):
        return visitor.visit_ComprehensionExpression(self)

    def __str__(self) -> str:
        return (f"ComprehensionExpression(element={self.element}, target={self.target}, "
                f"iter={self.iter}, condition={self.condition}, comp_type={self.comp_type}, "
                f"key={self.key})")


@dataclass
class FinalDeclaration(ASTNode):
    """Final variable declaration that cannot be reassigned."""
    target: Expression
    value: Expression
    type_annotation: Optional[str] = None

    def accept(self, visitor):
        return visitor.visit_FinalDeclaration(self)

    def __str__(self) -> str:
        return (f"FinalDeclaration(target={self.target}, value={self.value}, "
                f"type_annotation={self.type_annotation})")


@dataclass
class DataClassDeclaration(ASTNode):
    """Data class declaration: data class Point(x: int, y: int);"""
    name: str
    fields: List[Parameter]  # Fields defined in parentheses
    body: List[ASTNode] = field(default_factory=list)  # Optional methods
    type_parameters: List['TypeParameter'] = field(default_factory=list)
    bases: List[str] = field(default_factory=list)
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_DataClassDeclaration(self)

    def __str__(self) -> str:
        type_params = f"<{', '.join(tp.name for tp in self.type_parameters)}>" if self.type_parameters else ""
        fields_str = ", ".join(str(f) for f in self.fields)
        return f"DataClassDeclaration(name={self.name}{type_params}, fields=[{fields_str}], body={len(self.body)} members)"


@dataclass
class EnumMember(ASTNode):
    """Enum member: RED or EARTH(a, b)"""
    name: str
    args: List[Expression] = field(default_factory=list)  # Constructor arguments
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_EnumMember(self)

    def __str__(self) -> str:
        args_str = f"({', '.join(str(a) for a in self.args)})" if self.args else ""
        return f"EnumMember(name={self.name}{args_str})"


@dataclass
class EnumDeclaration(ASTNode):
    """Enum declaration: enum Color { RED, GREEN, BLUE }"""
    name: str
    members: List[EnumMember]
    body: List[ASTNode] = field(default_factory=list)  # Constructor and methods after semicolon
    compile_time_annotations: List[str] = field(default_factory=list)
    runtime_annotations: List[str] = field(default_factory=list)
    line: int = 0
    column: int = 0

    def accept(self, visitor):
        return visitor.visit_EnumDeclaration(self)

    def __str__(self) -> str:
        members_str = ", ".join(m.name for m in self.members)
        return f"EnumDeclaration(name={self.name}, members=[{members_str}], body={len(self.body)} members)"
