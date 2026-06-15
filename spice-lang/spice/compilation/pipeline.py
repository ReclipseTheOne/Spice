from spice.compilation import SpiceFile
from spice.lexer import Lexer
from spice.parser import Parser, ImportStatement
from spice.transformer import Transformer
from spice.errors import ImportError, SpiceCompileTimeError

from pathlib import Path
from spice.compilation.build_flags import BuildFlags

from spice.printils import pipeline_log

from typing import Optional

import sys
import sysconfig
import site

# Per-build state. Reset at each top-level walk() so repeated builds in one
# process (e.g. a build script compiling several targets) don't leak state.
LOOKUP_PATHS: list[Path] = []
RESOLVED_FILES: dict[Path, SpiceFile] = {}   # resolved .spc path -> shared SpiceFile (one node per module)


def _reset_build_state():
    """Clear the per-build import caches. Called at the root of walk()."""
    LOOKUP_PATHS.clear()
    RESOLVED_FILES.clear()


def add_and_check_lookup_path(path: Path):
    global LOOKUP_PATHS

    if path.resolve() in LOOKUP_PATHS or not path.exists():
        return

    LOOKUP_PATHS.append(path.resolve())



class SpicePipeline:
    @staticmethod
    def tokenize(file: SpiceFile, flags: BuildFlags):
        """Tokenize and verify lexically the current Spice File"""

        pipeline_log.custom("pipeline", f"Tokenizing file: {file.path.resolve().as_posix()}")

        lexer: Lexer = Lexer()
        file.tokens = lexer.tokenize(file.source)

    @staticmethod
    def parse(file: SpiceFile, flags: BuildFlags):
        """Parse and verify syntactically the current Spice File, generating the file's AST"""

        pipeline_log.custom("pipeline", f"Parsing file: {file.path.resolve().as_posix()}")

        parser: Parser = Parser()
        file.ast = parser.parse(file.tokens)

    @staticmethod
    def resolve_imports(file: SpiceFile, lookup: list[Path], flags: BuildFlags):
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
                # Snapshot: the body removes resolved statements from
                # left_to_resolve, so iterating it directly would skip every
                # second import found under the same lookup path.
                for stmt in list(left_to_resolve):
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
                            left_to_resolve.remove(stmt)

                            # Share one SpiceFile per module so diamond imports
                            # (A->B->D, A->C->D) resolve to the same node instead
                            # of being rebuilt or flagged as a false cycle.
                            resolved = possible_spc_path.resolve()
                            imported_file = RESOLVED_FILES.get(resolved)
                            if imported_file is None:
                                imported_file = SpiceFile(possible_spc_path)
                                RESOLVED_FILES[resolved] = imported_file
                            file.spc_imports.append(imported_file)

                            found = True
                            break

                    for possible_py_path in possible_py_paths:
                        if (flags.verbose):
                            pipeline_log.custom("pipeline", f"Checking possible .py path: {possible_py_path.resolve().as_posix()}")
                        if found:
                            break

                        if possible_py_path.is_file():
                            resolved = possible_py_path.resolve()
                            if resolved not in (p.resolve() for p in file.py_imports):
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
    def transform_and_write(file: SpiceFile, flags: BuildFlags):
        """Transform the AST of the current Spice File into target code and write it to disk."""
        target = "Cython" if flags.emit in ("pyx", "exe") else "Python"
        pipeline_log.custom("pipeline", f"Transforming file to {target}: {file.path.resolve().as_posix()}")

        transformer: Transformer = Transformer(
            emit=flags.emit,
            enable_runtime_final_checks=flags.runtime_checks
        )
        output_code = transformer.transform(file.ast, extra_imports=file.extra_imports)

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
    def walk(root: Path, spc_file: Optional[SpiceFile], flags: BuildFlags, _stack: Optional[list[Path]] = None) -> SpiceFile:
        """Recursively populate the import graph for the current Spice File."""

        if spc_file is None:
            # Top-level entry: start from a clean per-build state.
            _reset_build_state()
            spc_file = SpiceFile(root)
            RESOLVED_FILES[spc_file.path.resolve()] = spc_file

        if _stack is None:
            _stack = []

        add_and_check_lookup_path(root)
        add_and_check_lookup_path(spc_file.path.parent)
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

        here = spc_file.path.resolve()
        _stack.append(here)

        for imported in spc_file.spc_imports:
            target = imported.path.resolve()

            if target in _stack:
                # `target` is an ancestor on the current path -> cycle.
                cycle = _stack[_stack.index(target):] + [target]
                raise ImportError(
                    "Circular import detected:\n" + " ->\n".join(f" - {p.as_posix()}" for p in cycle)
                )

            if imported.tokens:
                # Already walked -> don't rebuild it.
                continue

            pipeline_log.custom("pipeline", f"Walking imported file: {target.as_posix()}")
            SpicePipeline.walk(root, imported, flags, _stack)

        _stack.pop()
        return spc_file

    @staticmethod
    def _run_analysis(file: SpiceFile, flags: BuildFlags, fatal: bool):
        """Run symbol-table build + all checks over the current tree.

        When `fatal` is False diagnostics are collected but never abort,
        so annotation processors / mutators get a fully-analyzed tree and a
        chance to fix would-be errors. When True the checks are authoritative
        and gate compilation.
        """
        from spice.compilation.checks import (
            FinalChecker,
            GenericBoundChecker,
            InterfaceChecker,
            MethodOverloadResolver,
            SymbolTableBuilder,
            TypeChecker,
        )

        SymbolTableBuilder().check(file)

        overload_resolver = MethodOverloadResolver()
        if not overload_resolver.check(file) and fatal:
            exception = "Invalid method overloads detected:\n"
            for error in overload_resolver.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)

        type_checker = TypeChecker()
        if not type_checker.check(file) and fatal:
            exception = "Type checking failed:\n"
            for error in type_checker.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)

        interface_checker = InterfaceChecker()
        if not interface_checker.check(file) and fatal:
            exception = "Interface implementation errors:\n"
            for error in interface_checker.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)

        bound_checker = GenericBoundChecker()
        if not bound_checker.check(file) and fatal:
            exception = "Generic bound errors:\n"
            for error in bound_checker.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)

        final_checker = FinalChecker()
        if not final_checker.check(file) and fatal:
            exception = "Instance(s) declared final found reassigned: \n"
            for error in final_checker.errors:
                exception += f" - {error}"
            raise SpiceCompileTimeError(exception)

    @staticmethod
    def verify_and_write(file: SpiceFile, flags: BuildFlags, _done: Optional[set] = None):
        """Build -> Lower (annotations/tools) -> Rebuild -> transform, for the whole tree.

        `_done` tracks already-processed files
        """

        if _done is None:
            _done = set()

        here = file.path.resolve()
        if here in _done:
            return
        _done.add(here)

        pipeline_log.custom("pipeline", f"Verifying file: {here.as_posix()}")

        from spice.compilation.checks import AnnotationStage

        # Build pass: full analysis, non-fatal. Gives tools a resolved tree + early diagnostics.
        SpicePipeline._run_analysis(file, flags, fatal=False)

        # Lower pass: run compile-time annotation processors / mutators (fatal on misuse).
        annotation_stage = AnnotationStage()
        if not annotation_stage.check(file):
            exception = "Annotation processing failed:\n"
            for error in annotation_stage.errors:
                exception += f" - {error}\n"
            raise SpiceCompileTimeError(exception)
        else:
            pipeline_log.custom("pipeline", "Annotations processed successfully.")

        # Rebuild pass: authoritative analysis on the lowered tree (gates compilation).
        SpicePipeline._run_analysis(file, flags, fatal=True)
        pipeline_log.custom("pipeline", "All compile-time checks passed.")

        SpicePipeline.transform_and_write(file, flags)

        for imported in file.spc_imports:
            SpicePipeline.verify_and_write(imported, flags, _done)
