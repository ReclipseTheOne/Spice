"""Holder for a Spice source file and its data"""

from pathlib import Path
from spice.lexer import Token
from spice.parser import Module
from spice.utils import generate_spc_stub


class SpiceFile:
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
