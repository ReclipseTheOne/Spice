"""Type system design for Spy language."""

from typing import Dict, List, Any, Optional, Union
from enum import Enum


class TypeKind(Enum):
    """Built-in type kinds."""
    ANY = "any"
    NONE = "None"
    BOOL = "bool"
    INT = "int"
    FLOAT = "float"
    STR = "str"
    LIST = "list"
    DICT = "dict"
    TUPLE = "tuple"
    CALLABLE = "callable"
    PROTOCOL = "protocol"
    CLASS = "class"


class SpyType:
    """Represents a type in the Spy type system."""

    def __init__(self, kind: TypeKind, name: str, params: List['SpyType'] = []):
        self.kind = kind
        self.name = name
        self.params = params or []
        self.fields: Dict[str, 'SpyType'] = {}  # Field name to type
        self.methods: Dict[str, 'SpyType'] = {}  # Method name to type (could be signature type)

    def __str__(self):
        if self.params:
            param_str = ", ".join(str(p) for p in self.params)
            return f"{self.name}[{param_str}]"
        return self.name

    def is_assignable_to(self, other: 'SpyType') -> bool:
        """Check if this type can be assigned to other type."""
        # any can be assigned to anything
        if self.kind == TypeKind.ANY:
            return True

        # anything can be assigned to any
        if other.kind == TypeKind.ANY:
            return True

        # exact match
        if self.kind == other.kind and self.name == other.name:
            return True

        # TODO: Implement inheritance, protocol compatibility, etc.
        return False

    def add_field(self, name: str, field_type: 'SpyType'):
        """Add a field to the type."""
        self.fields[name] = field_type

    def add_method(self, name: str, method_type: 'SpyType'):
        """Add a method to the type."""
        self.methods[name] = method_type

    def get_field(self, name: str) -> Optional['SpyType']:
        """Get the type of a field."""
        return self.fields.get(name)

    def get_method(self, name: str) -> Optional['SpyType']:
        """Get the type of a method."""
        return self.methods.get(name)


class TypeChecker:
    """Type checker for Spy language."""

    def __init__(self):
        self.symbol_table: Dict[str, SpyType] = {}
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def check_assignment(self, target: SpyType, value: SpyType, location: str = ""):
        """Check if assignment is type-safe."""
        if not value.is_assignable_to(target):
            self.errors.append(
                f"Type mismatch{' at ' + location if location else ''}: "
                f"Cannot assign {value} to {target}"
            )

    def infer_type(self, expression) -> SpyType:
        """Infer the type of an expression."""
        # TODO: Implement type inference
        return SpyType(TypeKind.ANY, "any")

    def validate_interface_implementation(self, class_name: str, interface_name: str):
        """Validate that a class properly implements an interface."""
        # TODO: Check that all interface methods are implemented
        pass

    def resolve_attribute(self, obj_type: SpyType, attr: str, location: str = "") -> Optional[SpyType]:
        """Resolve the type of an attribute or method on an object type."""
        field_type = obj_type.get_field(attr)
        if field_type:
            return field_type
        method_type = obj_type.get_method(attr)
        if method_type:
            return method_type
        self.errors.append(
            f"Attribute '{attr}' not found on type {obj_type}{' at ' + location if location else ''}"
        )
        return None


# Type enforcement levels
class TypeEnforcement(Enum):
    """Levels of type enforcement."""
    NONE = "none"          # No type checking (like Python)
    WARNINGS = "warnings"  # Type errors as warnings
    STRICT = "strict"      # Type errors as compilation errors


def create_runtime_type_checker():
    """Create runtime type checking decorators."""
    return """
# Runtime type checking decorators
def typed(func):
    '''Decorator to add runtime type checking to functions.'''
    import functools
    from typing import get_type_hints

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints
        hints = get_type_hints(func)

        # Check argument types
        for i, (arg_name, arg_value) in enumerate(zip(func.__code__.co_varnames, args)):
            if arg_name in hints:
                expected_type = hints[arg_name]
                if not isinstance(arg_value, expected_type):
                    raise TypeError(f"Argument '{arg_name}' expected {expected_type.__name__}, got {type(arg_value).__name__}")

        # Call original function
        result = func(*args, **kwargs)

        # Check return type
        if 'return' in hints:
            expected_return = hints['return']
            if not isinstance(result, expected_return):
                raise TypeError(f"Return value expected {expected_return.__name__}, got {type(result).__name__}")

        return result

    return wrapper


def cast(target_type, value):
    '''Runtime casting with validation.'''
    try:
        if target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == str:
            return str(value)
        elif target_type == bool:
            return bool(value)
        else:
            # For complex types, just return the value (duck typing)
            return value
    except (ValueError, TypeError) as e:
        raise TypeError(f"Cannot cast {type(value).__name__} to {target_type.__name__}: {e}")
"""
