from pathlib import Path
from spice.lexer import Token
from spice.parser import Module
from spice.utils import generate_spc_stub


class SpiceFile:
    def __init__(self, path: Path) -> None:
        NOT_SPC_FILE = path.suffix != '.spc'
        NO_MAIN_SPC = not (path / '__main__.spc').exists()

        if NOT_SPC_FILE and NO_MAIN_SPC:
            raise FileNotFoundError(f"Expected a .spc file or a directory containing '__main__.spc', got: {path}")
        else:
            path = path / '__main__.spc'

        self.path: Path = path
        self.py_path: Path = self.path.with_suffix('.py')
        self.temp_path: Path = Path.home().joinpath('.spice', 'cache', generate_spc_stub(self.path))
        self.source: str = Path(self.path).read_text(encoding='utf-8')

        self.tokens: list[Token] = []
        self.ast: Module = Module(body=[])
        self.py_code: str = ""

        self.import_paths: list[Path] = []
        self.spc_imports: list[SpiceFile] = []
        self.py_imports: list[Path] = []
        self.method_overload_table: dict[str, dict[str, str]] = {}
