"""Generic bound checker for Spice.

A bounded type parameter (`class Box<T extends C>` / `class Box<T implements C>`)
Whatever concrete type ends up bound to `T` must have `C` somewhere in
its inheritance tree.

The concrete type for `T` is discovered at a constructor call site, where the
type checker-style inference maps a constructor argument back onto the parameter
typed as `T`. This checker validates those inferred bindings.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import Dict, List, Optional

from spice.compilation.checks.compile_time_check import CompileTimeCheck
from spice.compilation.checks.interface_checker import CheckError
from spice.compilation.spicefile import SpiceFile
from spice.parser.ast_nodes import (
    CallExpression,
    FunctionDeclaration,
    IdentifierExpression,
    LiteralExpression,
)


class GenericBoundChecker(CompileTimeCheck):
    """Validate that concrete type arguments satisfy their type parameter bounds."""

    def __init__(self) -> None:
        self.errors: List[CheckError] = []

    def check(self, file: SpiceFile) -> bool:
        self.errors = []
        table = getattr(file, "symbol_table", None)
        if table is None:
            # No symbol table -> nothing resolved; let other checks report that.
            return True

        self.table = table
        self.classes = table.classes
        self.interfaces = table.interfaces

        # Flat map of every known variable's type. Good enough to resolve a bare
        # identifier passed as a constructor argument.
        self.var_types: Dict[str, Optional[str]] = {}
        for scope in table.scopes.values():
            for var in scope.variables.values():
                if var.type_annotation:
                    self.var_types[var.name] = var.type_annotation

        for call in self._iter_calls(file.ast):
            self._check_constructor_call(call)

        return len(self.errors) == 0

    def _iter_calls(self, node):
        """Yield every CallExpression anywhere in the tree."""
        if is_dataclass(node):
            if isinstance(node, CallExpression):
                yield node
            for f in fields(node):
                yield from self._iter_calls(getattr(node, f.name))
        elif isinstance(node, list):
            for item in node:
                yield from self._iter_calls(item)

    def _check_constructor_call(self, call: CallExpression) -> None:
        callee = call.callee
        if not isinstance(callee, IdentifierExpression):
            return

        class_symbol = self.classes.get(callee.name)
        if class_symbol is None:
            return

        # Bounds declared on this class's type parameters: {param_name: bound}.
        bounds = {
            tp.name: tp.bound
            for tp in getattr(class_symbol.node, "type_parameters", [])
            if tp.bound
        }
        if not bounds:
            return

        ctor = self._find_constructor(class_symbol.node, callee.name)
        if ctor is None:
            return

        params = [p for p in ctor.params if p.name != "self"]
        for arg, param in zip(call.arguments, params):
            bound = bounds.get(param.type_annotation)
            if not bound:
                continue  # this parameter isn't a bounded type parameter

            concrete = self._infer_type(arg)
            if concrete is None:
                continue  # can't determine the argument's type -> can't check

            if not self._satisfies(concrete, bound):
                self.errors.append(CheckError(
                    message=(
                        f"Type argument '{concrete}' for "
                        f"'{callee.name}<{param.type_annotation}>' does not have "
                        f"'{bound}' in its inheritance tree"
                    ),
                    line=getattr(call, "line", 0),
                    column=getattr(call, "column", 0),
                ))

    def _find_constructor(self, class_node, class_name: str) -> Optional[FunctionDeclaration]:
        for member in getattr(class_node, "body", []):
            if isinstance(member, FunctionDeclaration) and member.name in (class_name, "__init__"):
                return member
        return None

    def _infer_type(self, expr) -> Optional[str]:
        if isinstance(expr, LiteralExpression):
            if expr.literal_type == "number":
                text = str(expr.value)
                return "float" if any(c in text for c in ".eE") else "int"
            return {"string": "str", "boolean": "bool"}.get(expr.literal_type)
        if isinstance(expr, CallExpression) and isinstance(expr.callee, IdentifierExpression):
            # A constructor call evaluates to an instance of that class.
            if expr.callee.name in self.classes:
                return expr.callee.name
        if isinstance(expr, IdentifierExpression):
            return self.var_types.get(expr.name)
        return None

    def _satisfies(self, concrete: str, bound: str) -> bool:
        return concrete == bound or bound in self.table.ancestors(concrete)
