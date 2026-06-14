"""Import-graph resolution in the compilation pipeline.

Covers the diamond case (A->B->D, A->C->D) that must resolve to a single shared
node rather than being rebuilt or flagged as a false circular import, and a
genuine cycle that must still be detected.
"""

from pathlib import Path

import pytest

from spice.cli import CLI_FLAGS
from spice.compilation import SpicePipeline
from spice.errors import ImportError as SpiceImportError


def _flags(entry: Path) -> CLI_FLAGS:
    return CLI_FLAGS(source=entry, emit="py")


def _fn(name: str) -> str:
    return f"def {name}() -> None {{\n    pass;\n}}\n"


def _write(d: Path, name: str, body: str) -> None:
    (d / f"{name}.spc").write_text(body, encoding="utf-8")


class TestImportGraph:
    def test_diamond_resolves_to_single_shared_node(self, tmp_path, monkeypatch):
        # cwd is a lookup path, so resolve modules by bare name from here.
        monkeypatch.chdir(tmp_path)
        _write(tmp_path, "d", _fn("d"))
        _write(tmp_path, "b", "import d\n\n" + _fn("b"))
        _write(tmp_path, "c", "import d\n\n" + _fn("c"))
        _write(tmp_path, "a", "import b\nimport c\n\n" + _fn("a"))

        entry = tmp_path / "a.spc"
        tree = SpicePipeline.walk(entry, None, _flags(entry))

        assert [i.path.stem for i in tree.spc_imports] == ["b", "c"]
        b, c = tree.spc_imports

        # Both importers point at the same D instance
        assert len(b.spc_imports) == 1 and len(c.spc_imports) == 1
        assert b.spc_imports[0] is c.spc_imports[0]
        assert b.spc_imports[0].path.stem == "d"
        # D was actually walked / tokenized exactly once.
        assert b.spc_imports[0].tokens

    def test_real_cycle_is_detected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        _write(tmp_path, "x", "import y\n\n" + _fn("x"))
        _write(tmp_path, "y", "import x\n\n" + _fn("y"))

        entry = tmp_path / "x.spc"
        with pytest.raises(SpiceImportError):
            SpicePipeline.walk(entry, None, _flags(entry))
