from typing import final, Optional
from pathlib import Path

@final
class CLI_FLAGS:
    """
    CLI flags for the Spice compiler.

    Attributes:
        source: Path to the source .spc file
        output: Output directory or file path
        emit: Compilation target ('py', 'pyx', or 'exe')
        check: Syntax validation without code generation
        watch: File watching mode
        verbose: Detailed logging of pipeline stages
        no_final_check: Skip final variable reassignment checks
        runtime_checks: Inject runtime type checking decorators
    """
    def __init__(
        self,
        source: Path,
        # temp: bool = False, TODO: Implement temp running and .spice caching
        output: Optional[Path] = None,
        emit: str = "py",
        keep_intermidiates: bool = False,
        check: bool = False,
        watch: bool = False,
        verbose: bool = False,
        no_final_check: bool = False,
        runtime_checks: bool = False,
    ):
        # self.temp = temp, TODO: ^
        self.source = source
        self.output = output
        self.emit = emit
        self.keep_intermediates = keep_intermidiates
        self.check = check
        self.watch = watch
        self.verbose = verbose
        self.no_final_check = no_final_check
        self.runtime_checks = runtime_checks
