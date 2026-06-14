"""Holder for a Spice source file and its data"""

from pathlib import Path
from typing import Optional, List
from spice.lexer import Token
from spice.parser import Module
from spice.parser.ast_nodes import ASTNode, RawCode
from spice.utils import generate_spc_stub


class SpiceFile:
    """
    Holder for a Spice source file and its compilation data.

    Manages the source file path, generated output paths, tokens, AST,
    and import tracking throughout the compilation pipeline.
    """

    # Extension mapping for different emit modes
    EMIT_EXTENSIONS = {
        "py": ".py",
        "pyx": ".pyx",
        "exe": ".pyx"
    }

    def __init__(self, path: Path) -> None:
        self.is_directory: bool = path.is_dir()

        if self.is_directory:
            main_file = path / '__main__.spc'
            if not main_file.is_file():
                raise FileNotFoundError(f"Directory '{path}' does not contain '__main__.spc'")
            path = main_file
        elif not path.is_file():
            raise FileNotFoundError(f"Expected a .spc file or a directory containing '__main__.spc', got: {path}")

        self.path: Path = path
        self.py_path: Path = self.path.with_suffix('.py')
        self.temp_path: Path = Path.home().joinpath('.spice', 'cache', generate_spc_stub(self.path))
        self.source: str = Path(self.path).read_text(encoding='utf-8')

        self._init_defaults()

    def get_output_path(self, emit: str = "py") -> Path:
        """Get the output path for the given emit mode."""
        ext = self.EMIT_EXTENSIONS.get(emit, ".py")
        return self.path.with_suffix(ext)

    def _init_defaults(self) -> None:
        """Initialize default values for all mutable attributes."""
        self.tokens: list[Token] = []
        self.ast: Module = Module(body=[])
        self.py_code: str = ""

        self.import_paths: list[Path] = []
        self.spc_imports: list[SpiceFile] = []
        self.py_imports: list[Path] = []
        self.method_overload_table: dict[str, dict[str, str]] = {}
        self.symbol_table = None

        # Imports not introduced by parsed code
        self.extra_imports: set[str] = set()

        # Fatal errors
        self.diagnostics: List[str] = []

        # Non-fatal errors
        self.warnings: List[str] = []

    # Utils #

    def ensure_import(self, module: str, names: Optional[List[str]] = None) -> None:
        """Record a top-level import to emit in the generated file (deduped by line)."""
        if names:
            self.extra_imports.add(f"from {module} import {', '.join(names)}")
        else:
            self.extra_imports.add(f"import {module}")

    def parse_stmts(self, source: str) -> List[ASTNode]:
        """Parse Spice source into a list of AST statement nodes (quasiquote)."""
        from spice.lexer import Lexer
        from spice.parser import Parser
        tokens = Lexer().tokenize(source)
        return Parser().parse(tokens).body

    def parse_expr(self, source: str):
        """Parse a single Spice expression into an AST node."""
        snippet = source if source.rstrip().endswith(';') else source + ';'
        stmts = self.parse_stmts(snippet)
        if not stmts:
            return None
        first = stmts[0]
        return getattr(first, 'expression', first)

    def raw_python(self, code: str) -> RawCode:
        """Wrap verbatim Python source as an injectable AST node (escape hatch)."""
        return RawCode(code=code)

    def walk(self, root: Optional[ASTNode] = None):
        """Yield every AST node under `root` (defaults to the module root)."""
        root = root if root is not None else self.ast
        stack = [root]
        while stack:
            node = stack.pop()
            yield node
            stack.extend(_iter_child_nodes(node))

    def find(self, node_type, root: Optional[ASTNode] = None) -> List[ASTNode]:
        """All nodes of `node_type` under `root`."""
        return [n for n in self.walk(root) if isinstance(n, node_type)]

    def parent_of(self, target: ASTNode, root: Optional[ASTNode] = None):
        """The parent of `target`, or None. The AST only links parent->child, so this walks."""
        root = root if root is not None else self.ast
        for node in self.walk(root):
            for child in _iter_child_nodes(node):
                if child is target:
                    return node
        return None

    def error(self, node, message: str) -> None:
        """Record a fatal diagnostic (gates compilation at the owning stage)."""
        self.diagnostics.append(f"{message} (line {getattr(node, 'line', 0)})")

    def warn(self, node, message: str) -> None:
        """Record a non-fatal diagnostic."""
        self.warnings.append(f"{message} (line {getattr(node, 'line', 0)})")

    @classmethod
    def empty(cls, source: str = "") -> "SpiceFile":
        """Create an empty SpiceFile for in-memory use (e.g., LSP)."""
        instance = object.__new__(cls)
        instance.is_directory = False
        instance.path = Path("<memory>")
        instance.py_path = Path("<memory>.py")
        instance.temp_path = Path("<memory>")
        instance.source = source
        instance._init_defaults()
        return instance


def _iter_child_nodes(node):
    """Yield the immediate AST-node children of `node` (through lists and dicts)."""
    for value in vars(node).values():
        if isinstance(value, ASTNode):
            yield value
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, ASTNode):
                    yield item
        elif isinstance(value, dict):
            for item in value.values():
                if isinstance(item, ASTNode):
                    yield item
