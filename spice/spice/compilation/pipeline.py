from spice.compilation import SpiceFile
from spice.lexer import Lexer
from spice.parser import Parser, ImportStatement
from spice.transformer import Transformer
from spice.errors import ImportError

from pathlib import Path
from spice.cli import CLI_FLAGS

from spice.printils import pipeline_log

ALL_IMPORTED_PATHS: list[Path] = []

def add_and_check_import_path(path: Path):
    global ALL_IMPORTED_PATHS

    if path.resolve() in ALL_IMPORTED_PATHS:
        exception: str = "Circular Import.\nAll current file paths: \n"
        for path in ALL_IMPORTED_PATHS:
            exception += (f" - {path}")

        raise ImportError(exception)

    ALL_IMPORTED_PATHS.append(path.resolve())


class SpicePipeline:
    @staticmethod
    def tokenize(file: SpiceFile, flags: CLI_FLAGS):
        pipeline_log.custom("pipeline", f"Tokenizing file: {file.path.resolve().as_posix()}")

        lexer: Lexer = Lexer()
        file.tokens = lexer.tokenize(file.source)

    @staticmethod
    def parse(file: SpiceFile, flags: CLI_FLAGS):
        pipeline_log.custom("pipeline", f"Parsing file: {file.path.resolve().as_posix()}")
        
        parser: Parser = Parser()
        file.ast = parser.parse(file.tokens)

    @staticmethod
    def resolve_imports(file: SpiceFile, lookup: list[Path], flags: CLI_FLAGS):
        pipeline_log.custom("pipeline", f"Resolving imports for file: {file.path.resolve().as_posix()}")

        left_to_resolve: list[ImportStatement] = []
        for stmt in file.ast.body:
            if isinstance(stmt, ImportStatement):
                left_to_resolve.append(stmt)
        
        for path in lookup:
            if path.exists():
                for stmt in left_to_resolve:
                    module_path = Path(stmt.module.replace('.', '/'))
                    possible_spc_paths = [
                        path / (str(module_path) + ".spc"),
                        path / module_path / "__init__.spc"
                    ]
                    possible_py_paths = [
                        path / (str(module_path) + ".py"),
                        path / module_path / "__init__.py"
                    ]

                    for possible_spc_path in possible_spc_paths:
                        if possible_spc_path.exists():
                            add_and_check_import_path(possible_spc_path)
                            left_to_resolve.remove(stmt)

                            imported_file = SpiceFile(possible_spc_path)
                            file.spc_imports.append(imported_file)
                            break
                    
                    for possible_py_path in possible_py_paths:
                        if possible_py_path.exists():
                            add_and_check_import_path(possible_py_path)

                            file.py_imports.append(possible_py_path)
                            left_to_resolve.remove(stmt)
                            break

        if len(left_to_resolve) > 0:
            exception = "Unresolved imports found: "
            for stmt in left_to_resolve:
                exception += f"{stmt.module}\n"
            raise ImportError(exception)
        
        if flags.verbose and len(file.spc_imports) > 0:
            msg = f"Added pipeline divergence from file {file.path.resolve().as_posix()} to:\n"
            for spc in file.spc_imports:
                msg += f" - {spc.path.resolve().as_posix()}\n"
            pipeline_log.custom("pipeline", msg)

    @staticmethod
    def transform_and_write(file: SpiceFile, flags: CLI_FLAGS):
        pipeline_log.custom("pipeline", f"Writing python for file: {file.path.resolve().as_posix()}")

        transformer: Transformer = Transformer()
        file.py_code = transformer.transform(file.ast)

        if isinstance(flags.output, Path):
            file.py_path = flags.output.resolve() / file.py_path

        with open(file.py_path, 'w', encoding='utf-8') as f:
            f.write(file.py_code)

    @staticmethod
    def walk(path: Path, flags: CLI_FLAGS):
        spc_file = SpiceFile(path)
        SpicePipeline.tokenize(spc_file, flags)
        SpicePipeline.parse(spc_file, flags)
        SpicePipeline.resolve_imports(spc_file, [path.parent], flags)

        for imported in spc_file.spc_imports:
            pipeline_log.custom("pipeline", f"Walking imported file: {imported.path.resolve().as_posix()}")
            SpicePipeline.walk(imported.path, flags)
        
        SpicePipeline.transform_and_write(spc_file, flags)
