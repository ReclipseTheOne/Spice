"""Build configuration for the Spice compiler."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional


def _core_field(key: str) -> property:
    """Build a get/set wrapper (property) for a core field backed by `_data`."""
    def getter(self: "BuildFlags") -> Any:
        return self._data.get(key)

    def setter(self: "BuildFlags", value: Any) -> None:
        self._data[key] = value

    getter.__name__ = key
    return property(getter, setter, doc=f"Core build flag '{key}'.")


class BuildFlags:
    """Compiler build options.

    Core fields:
        source: Path to the source .spc file or a directory with __main__.spc
        output: Output directory or file path
        emit: Compilation target ('py', 'pyx', or 'exe')
        keep_intermediates: Keep intermediates generated during exe compilation
        check: Syntax validation without code generation
        watch: File watching mode
        verbose: Detailed logging of pipeline stages
        runtime_checks: Inject runtime type checking decorators

    Extra keys (for plugins/tools) live in the same dict and are reached with
    get()/set(), item access (flags["key"]) or as_dict().
    """

    CORE_DEFAULTS: dict[str, Any] = {
        "source": None,
        "output": None,
        "emit": "py",
        "keep_intermediates": False,
        "check": False,
        "watch": False,
        "verbose": False,
        "runtime_checks": False,
    }

    def __init__(
        self,
        source: Path,
        output: Optional[Path] = None,
        emit: str = "py",
        keep_intermidiates: bool = False,
        check: bool = False,
        watch: bool = False,
        verbose: bool = False,
        runtime_checks: bool = False,
        **extra: Any,
    ) -> None:
        self._data: dict[str, Any] = dict(self.CORE_DEFAULTS)
        self._data.update({
            "source": source,
            "output": output,
            "emit": emit,
            "keep_intermediates": keep_intermidiates,
            "check": check,
            "watch": watch,
            "verbose": verbose,
            "runtime_checks": runtime_checks,
        })

        self._data.update(extra)

    source = _core_field("source")
    output = _core_field("output")
    emit = _core_field("emit")
    keep_intermediates = _core_field("keep_intermediates")
    check = _core_field("check")
    watch = _core_field("watch")
    verbose = _core_field("verbose")
    runtime_checks = _core_field("runtime_checks")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> "BuildFlags":
        self._data[key] = value
        return self

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        return key in self._data

    def as_dict(self) -> dict[str, Any]:
        """A shallow copy of the backing dict (core fields + extras)."""
        return dict(self._data)

    def __repr__(self) -> str:
        return f"BuildFlags({self._data!r})"
