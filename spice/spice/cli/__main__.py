#!/usr/bin/env python3
"""Spice CLI - SPy compiler."""

import click
import sys
from pathlib import Path
from typing import Optional

from lexer import Lexer
from parser.parser import Parser
from transformer.transformer import Transformer
from errors import SpiceError


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file (default: <source>.py)')
@click.option('-c', '--check', is_flag=True, help='Check syntax without generating output')
@click.option('-w', '--watch', is_flag=True, help='Watch file for changes')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.version_option(version='0.1.0', prog_name='spyc')
def main(source: str, output: Optional[str], check: bool, watch: bool, verbose: bool):
    """Compile Spice (.spy) files to Python."""
    source_path = Path(source)

    if not source_path.suffix == '.spy':
        click.echo(f"Error: Expected .spy file, got {source_path.suffix}", err=True)
        sys.exit(1)

    if output is None:
        output_path = source_path.with_suffix('.py')
    else:
        output_path = Path(output)

    try:
        compile_file(source_path, output_path, check, verbose)

        if watch:
            click.echo(f"Watching {source_path} for changes... (Ctrl+C to stop)")
            # TODO: Implement file watching

    except SpiceError as e:
        click.echo(f"Compilation error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def compile_file(source_path: Path, output_path: Path, check_only: bool, verbose: bool):
    """Compile a single .spy file to Python."""
    if verbose:
        click.echo(f"Compiling {source_path}...")

    # Read source file
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Compilation pipeline
    lexer = Lexer()
    tokens = lexer.tokenize(source_code)

    parser = Parser()
    ast = parser.parse(tokens)

    if check_only:
        click.echo("✓ Syntax check passed")
        return

    transformer = Transformer()
    python_code = transformer.transform(ast)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(python_code)

    if verbose:
        click.echo(f"✓ Generated {output_path}")


if __name__ == '__main__':
    main()
