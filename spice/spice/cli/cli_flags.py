from typing import final, Optional
from pathlib import Path

@final
class CLI_FLAGS:
    def __init__(
        self,
        source: Path,
        # temp: bool = False, TODO: Implement temp running and .spice caching
        output: Optional[Path] = None,
        check: bool = False,
        watch: bool = False,
        verbose: bool = False,
        type_check: bool = False,
        no_final_check: bool = False,
        runtime_checks: bool = False,
    ):  
        # self.temp = temp, TODO: ^
        self.source = source
        self.output = output
        self.check = check
        self.watch = watch
        self.verbose = verbose
        self.type_check = type_check
        self.no_final_check = no_final_check
        self.runtime_checks = runtime_checks
