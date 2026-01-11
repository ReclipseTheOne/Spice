from spice.compilation import SpiceFile
from spice.lexer import Lexer
from spice.parser import Parser, ImportStatement
from spice.transformer import Transformer
from spice.errors import ImportError, SpiceCompileTimeError

from pathlib import Path
from spice.cli import CLI_FLAGS

from spice.printils import pipeline_log

from typing import Optional

import sys
import sysconfig
import site

ALL_IMPORTED_PATHS: list[Path] = []
LOOKUP_PATHS: list[Path] = []


def add_and_check_import_path(path: Path):
    global ALL_IMPORTED_PATHS

    if path.resolve() in ALL_IMPORTED_PATHS:
        exception: str = "Circular Import.\nAll current file paths: \n"
        for path in ALL_IMPORTED_PATHS:
            exception += (f" - {path}")

        raise ImportError(exception)

    ALL_IMPORTED_PATHS.append(path.resolve())


def add_and_check_lookup_path(path: Path):
    global LOOKUP_PATHS

    if path.resolve() in LOOKUP_PATHS or not path.exists():
        return

    LOOKUP_PATHS.append(path.resolve())



class SpicePipeline:
    @staticmethod
    def tokenize(file: SpiceFile, flags: CLI_FLAGS):
        """Tokenize and verify lexically the current Spice File"""

        pipeline_log.custom("pipeline", f"Tokenizing file: {file.path.resolve().as_posix()}")

        lexer: Lexer = Lexer()
        file.tokens = lexer.tokenize(file.source)

    @staticmethod
    def parse(file: SpiceFile, flags: CLI_FLAGS):
        """Parse and verify syntactically the current Spice File, generating the file's AST"""

        pipeline_log.custom("pipeline", f"Parsing file: {file.path.resolve().as_posix()}")

        parser: Parser = Parser()
        file.ast = parser.parse(file.tokens)

    @staticmethod
    def resolve_imports(file: SpiceFile, lookup: list[Path], flags: CLI_FLAGS):
        """Resolve the imports for the current Spice File"""

        pipeline_log.custom("pipeline", f"Resolving imports for file: {file.path.resolve().as_posix()}")

        left_to_resolve: list[ImportStatement] = []
        for stmt in file.ast.body:
            if isinstance(stmt, ImportStatement):
                if stmt.module in sys.builtin_module_names:
                    continue

                left_to_resolve.append(stmt)
                if flags.verbose:
                    pipeline_log.custom("pipeline", f"Added import statement: {stmt.module}")

        for path in lookup:
            if path.exists():
                for stmt in left_to_resolve:
                    found: bool = False
                    relative_path: str = path.resolve().as_posix()

                    if flags.verbose:
                        pipeline_log.custom("pipeline", f"Searching for import statement '{stmt.module}' against path {relative_path}")

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
                        if (flags.verbose):
                            pipeline_log.custom("pipeline", f"Checking possible .spc path: {possible_spc_path.resolve().as_posix()}")
                        if possible_spc_path.is_file() or (possible_spc_path / "__main__.spc").is_file():
                            add_and_check_import_path(possible_spc_path)
                            left_to_resolve.remove(stmt)

                            imported_file = SpiceFile(possible_spc_path)
                            file.spc_imports.append(imported_file)

                            found = True
                            break

                    for possible_py_path in possible_py_paths:
                        if (flags.verbose):
                            pipeline_log.custom("pipeline", f"Checking possible .py path: {possible_py_path.resolve().as_posix()}")
                        if found:
                            break

                        if possible_py_path.is_file():
                            add_and_check_import_path(possible_py_path)

                            file.py_imports.append(possible_py_path)
                            left_to_resolve.remove(stmt)
                            break

        if len(left_to_resolve) > 0:
            exception = "\nUnresolved imports found: \n"
            for stmt in left_to_resolve:
                exception += f" - {stmt.module}\n"
            exception += "All available source sets: \n"
            for path in LOOKUP_PATHS:
                exception += f" - {path.resolve().as_posix()}\n"
            raise ImportError(exception)

        if flags.verbose and len(file.spc_imports) > 0:
            msg = f"Added pipeline divergence from file {file.path.resolve().as_posix()} to:\n"
            for spc in file.spc_imports:
                msg += f" - {spc.path.resolve().as_posix()}\n"
            pipeline_log.custom("pipeline", msg)

    @staticmethod
    def transform_and_write(file: SpiceFile, flags: CLI_FLAGS):
        """Transform the AST of the current Spice File into target code and write it to disk."""
        target = "Cython" if flags.emit in ("pyx", "exe") else "Python"
        pipeline_log.custom("pipeline", f"Transforming file to {target}: {file.path.resolve().as_posix()}")

        transformer: Transformer = Transformer(
            emit=flags.emit,
            enable_runtime_final_checks=flags.runtime_checks
        )
        output_code = transformer.transform(file.ast)

        # Determine output path based on emit mode
        output_path = file.get_output_path(flags.emit)
        if isinstance(flags.output, Path):
            output_path = flags.output.resolve() / output_path.name

        with open(output_path, 'w', encoding='utf-8') as f:
            pipeline_log.custom("pipeline", f"Writing to {output_path}...")
            f.write(output_code)

        # For exe mode, compile the generated .pyx to binary
        if flags.emit == "exe":
            from spice.compilation.cython_compiler import compile_to_executable
            compile_to_executable(output_path, flags)

    @staticmethod
    def walk(root: Path, spc_file: Optional[SpiceFile], flags: CLI_FLAGS) -> SpiceFile:
        """Recursively populate and transform the import tree for the current Spice File"""

        if spc_file is None:
            spc_file = SpiceFile(root)

        add_and_check_lookup_path(root)
        add_and_check_lookup_path(Path.cwd())
        add_and_check_lookup_path(Path(sysconfig.get_path('purelib')))
        add_and_check_lookup_path(Path(sysconfig.get_path('platlib')))
        add_and_check_lookup_path(Path(site.getusersitepackages()))
        add_and_check_lookup_path(Path(sysconfig.get_path('stdlib')))

        global_sites = site.getsitepackages()
        for site_path_str in global_sites:
            add_and_check_lookup_path(Path(site_path_str))


        SpicePipeline.tokenize(spc_file, flags)
        SpicePipeline.parse(spc_file, flags)
        SpicePipeline.resolve_imports(spc_file, LOOKUP_PATHS, flags)

        for imported in spc_file.spc_imports:
            pipeline_log.custom("pipeline", f"Walking imported file: {imported.path.resolve().as_posix()}")
            SpicePipeline.walk(root, imported, flags)

        return spc_file

    @staticmethod
    def verify_and_write(file: SpiceFile, flags: CLI_FLAGS):
        """Run compile time checks on all the Spice File Tree and write the tree to disk"""

        pipeline_log.custom("pipeline", f"Verifying file: {file.path.resolve().as_posix()}")

        from spice.compilation.checks import (
            FinalChecker,
            InterfaceChecker,
            MethodOverloadResolver,
            SymbolTableBuilder,
            TypeChecker,
        )

        symbol_builder = SymbolTableBuilder()
        symbol_builder.check(file)

        overload_resolver = MethodOverloadResolver()
        if not overload_resolver.check(file):
            exception = "Invalid method overloads detected:\n"
            for error in overload_resolver.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)
        else:
            pipeline_log.custom("pipeline", "No invalid method overloads present. Overloads added successfully.")

        type_checker = TypeChecker()
        if not type_checker.check(file):
            exception = "Type checking failed:\n"
            for error in type_checker.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)
        else:
            pipeline_log.custom("pipeline", "No type errors present.")

        interface_checker = InterfaceChecker()
        if not interface_checker.check(file):
            exception = "Interface implementation errors:\n"
            for error in interface_checker.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)
        else:
            pipeline_log.custom("pipeline", "All interfaces implemented correctly.")

        final_checker = FinalChecker()
        if (not final_checker.check(file) and not flags.no_final_check):
            exception = "Instance(s) declared final found reassigned: \n"
            for error in final_checker.errors:
                exception += f" - {error}"
            raise SpiceCompileTimeError(exception)
        else:
            pipeline_log.custom("pipeline", "No final violations found.")

        SpicePipeline.transform_and_write(file, flags)

        for imported in file.spc_imports:
            SpicePipeline.verify_and_write(imported, flags)
