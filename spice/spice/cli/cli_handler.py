from spice.cli import CLI_FLAGS
from spice.printils import spice_compiler_log, pipeline_log, spam_console
from spice.compilation import SpiceFile, SpicePipeline

from typing import Optional
from pathlib import Path

import click

@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file (default: <source>.py)')
@click.option('-c', '--check', is_flag=True, help='Check syntax without generating output')
@click.option('-w', '--watch', is_flag=True, help='Watch file for changes. This option disables verbosity.')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-nf', '--no-final-check', is_flag=True, help='Skip final type checks at compilation')
@click.option('--runtime-checks', is_flag=True, help='Add runtime type checking to output')
@click.version_option(version='0.1.0', prog_name='spicy')
def from_cli(source: str, output: Optional[str], check: bool, watch: bool, verbose: bool, no_final_check: bool, runtime_checks: bool):
    """Compile Spice (.spc) files to Python."""
    flags: CLI_FLAGS = CLI_FLAGS(
        source=Path(source),
        output=Path(output) if output else None,
        check=check,
        watch=watch,
        verbose=verbose,
        no_final_check=no_final_check,
        runtime_checks=runtime_checks
    )
    spam_console(flags.verbose)

    spice_compiler_log.custom("spice", f"Compiling from entry point: {flags.source.resolve().as_posix()}")

    spice_tree: SpiceFile = SpicePipeline.walk(flags.source, None, flags)
    SpicePipeline.verify_and_write(spice_tree, flags)

    spice_compiler_log.custom("spice", "Compilation finished successfully.")
