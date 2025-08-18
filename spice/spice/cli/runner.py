#!/usr/bin/env python3
"""Spice CLI - Spice runner."""

import click
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import Optional

from spice.lexer import Lexer
from spice.parser.parser import Parser
from spice.transformer.transformer import Transformer
from spice.errors import SpiceError

from spice.printils import spice_runner_log


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('-t', '--type-check', type=click.Choice(['none', 'warnings', 'strict'], case_sensitive=False), help='Type checking level - none, warnings (default), strict'),
@click.option('-nf', '--no-final-check', is_flag=True, help='Skip final type checks at compilation')
@click.option('-kt', '--keep-temp', is_flag=True, help='Keep temporary Python file for debugging')
def run(source: str, verbose: bool, keep_temp: bool, type_check: Optional[str], no_final_check: bool):
    """Run a .spc file directly without creating permanent Python files."""
    source_path = Path(source)

    if not source_path.suffix == '.spc':
        click.echo(f"Expected .spc file, got {source_path.suffix}", err=True)
        sys.exit(1)

    try:        # Create temporary Python file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as temp_file:
            temp_path = Path(temp_file.name)

            if verbose:
                spice_runner_log.info(f"Running {source_path}...")
                spice_runner_log.info(f"Temporary Python file: {temp_path}")

            # Compile Spice to python
            compile_Spice_file(source_path, temp_path, verbose)

            # Execute the Python file
            if verbose:
                spice_runner_log.info(f"Executing compiled Python...")

            result = subprocess.run([sys.executable, str(temp_path)],
                                  capture_output=False, text=True)

            # Clean up temporary file unless keeping it
            if not keep_temp:
                try:
                    temp_path.unlink()
                except:
                    pass  # Ignore cleanup errors
            else:
                spice_runner_log.info(f"Temporary file kept at: {temp_path}")

            sys.exit(result.returncode)

    except SpiceError as e:
        spice_runner_log.error(f"Compilation error: {e}")
        sys.exit(1)
    except Exception as e:
        spice_runner_log.error(f"Runtime error: {e}")
        sys.exit(1)


def compile_Spice_file(source_path: Path, output_path: Path, verbose: bool):
    """Compile a .spc file to Python."""
    # Read source
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Compilation pipeline
    lexer = Lexer(verbose=verbose)
    tokens = lexer.tokenize(source_code)

    parser = Parser(verbose=verbose)
    ast = parser.parse(tokens)

    transformer = Transformer(verbose=verbose)
    python_code = transformer.transform(ast)

    # Write compiled Python
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(python_code)
