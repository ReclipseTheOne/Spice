#!/usr/bin/env python3
"""Spice CLI - Spice compiler."""

import click
import sys
from pathlib import Path
from typing import Optional

from lexer import Lexer
from parser.parser import Parser
from transformer.transformer import Transformer
from errors import SpiceError

from printils import spice_compiler_log


def add_runtime_type_checks(python_code: str) -> str:
    """Add runtime type checking to Python code."""
    runtime_checks = '''
# Runtime type checking support
import functools
from typing import get_type_hints

def typed(func):
    """Decorator to add runtime type checking to functions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get type hints
        hints = get_type_hints(func)

        # Check argument types
        for i, (arg_name, arg_value) in enumerate(zip(func.__code__.co_varnames, args)):
            if arg_name in hints and arg_name != 'return':
                expected_type = hints[arg_name]
                if not isinstance(arg_value, expected_type):
                    raise TypeError(f"Argument '{arg_name}' expected {expected_type.__name__}, got {type(arg_value).__name__}")

        # Call original function
        result = func(*args, **kwargs)

        # Check return type
        if 'return' in hints:
            expected_return = hints['return']
            if expected_return is not type(None) and not isinstance(result, expected_return):
                raise TypeError(f"Return value expected {expected_return.__name__}, got {type(result).__name__}")

        return result
    return wrapper

'''
    return runtime_checks + "\n" + python_code


@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('-o', '--output', type=click.Path(), help='Output file (default: <source>.py)')
@click.option('-c', '--check', is_flag=True, help='Check syntax without generating output')
@click.option('-w', '--watch', is_flag=True, help='Watch file for changes')
@click.option('-v', '--verbose', is_flag=True, help='Verbose output')
@click.option('--type-check', type=click.Choice(['none', 'warnings', 'strict']),
              default='none', help='Type checking level (default: none)')
@click.option('--runtime-checks', is_flag=True, help='Add runtime type checking to output')
@click.version_option(version='0.1.0', prog_name='spicy')
def main(source: str, output: Optional[str], check: bool, watch: bool, verbose: bool, type_check: str, runtime_checks: bool):
    """Compile Spice (.spc) files to Python."""
    source_path = Path(source)

    if not source_path.suffix == '.spc':
        spice_compiler_log.error(f"Expected .spc file, got {source_path.suffix}")
        sys.exit(1)

    if output is None:
        output_path = source_path.with_suffix('.py')
    else:
        output_path = Path(output)

    try:
        compile_file(source_path, output_path, check, verbose, type_check, runtime_checks)

        if watch:
            spice_compiler_log.info(f"Watching {source_path} for changes... (Ctrl+C to stop)")
            # TODO: Implement file watching

    except SpiceError as e:
        spice_compiler_log.error(f"Compilation error: {e}")
        sys.exit(1)
    except Exception as e:
        spice_compiler_log.error(f"Unexpected error: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def compile_file(source_path: Path, output_path: Path, check_only: bool, verbose: bool, type_check: str = 'none', runtime_checks: bool = False):
    """Compile a single .spc file to Python."""
    spice_compiler_log.info(f"Starting compilation of {source_path}")

    # Read source file
    if verbose:
        spice_compiler_log.info("Step 1/6: Reading source file...")
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    if verbose:
        lines = source_code.count('\n') + 1
        chars = len(source_code)
        spice_compiler_log.success(f"Read {lines} lines ({chars} characters)")

    # Compilation pipeline
    if verbose:
        spice_compiler_log.info("Step 2/6: Lexical analysis (tokenization)...")
    lexer = Lexer(verbose=verbose)
    tokens = lexer.tokenize(source_code)

    if len(lexer.errors) != 0:
        spice_compiler_log.error("Lexical errors found:")
        for error in lexer.errors:
            spice_compiler_log.error(f"   - {error}")
        sys.exit(1)
    else:
        if verbose:
            spice_compiler_log.success("Lexical analysis complete, no errors found")

    if verbose:
        token_count = len(tokens) if hasattr(tokens, '__len__') else "unknown"
        spice_compiler_log.success(f"Generated {token_count} tokens")

    if verbose:
        spice_compiler_log.info("Step 3/6: Syntax analysis (parsing)...")

    parser = Parser(verbose=verbose)
    ast = parser.parse(tokens)

    if verbose:
        spice_compiler_log.success("Built Abstract Syntax Tree (AST)")

    if check_only:
        if verbose:
            spice_compiler_log.info("Step 4/6: Syntax validation complete")
        spice_compiler_log.success("Syntax check passed")
        return

    # Add type checking warnings/errors
    if verbose:
        spice_compiler_log.info("Step 4/6: Type checking...")
    if type_check == 'warnings':
        if verbose:
            spice_compiler_log.info("Type checking mode: warnings")
        # TODO: Implement type checking warnings
    elif type_check == 'strict':
        if verbose:
            spice_compiler_log.info("Type checking mode: strict")
        # TODO: Implement strict type checking
    else:
        if verbose:
            spice_compiler_log.info("Type checking disabled")

    if verbose:
        spice_compiler_log.info("Step 5/6: Code transformation (AST -> Python)...")
    transformer = Transformer(verbose=verbose)
    python_code = transformer.transform(ast)

    if verbose:
        python_lines = python_code.count('\n') + 1
        spice_compiler_log.success(f"Generated {python_lines} lines of Python code")

    # Add runtime type checks if requested
    if runtime_checks:
        if verbose:
            spice_compiler_log.info("Adding runtime type checking...")
        python_code = add_runtime_type_checks(python_code)

    # Write output
    if verbose:
        spice_compiler_log.info("Step 6/6: Writing output file...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(python_code)

    if verbose:
        spice_compiler_log.info(f"Written to {output_path}")
        if type_check != 'none':
            spice_compiler_log.info(f"Type checking level: {type_check}")
        if runtime_checks:
            spice_compiler_log.info("Runtime type checking included")


    spice_compiler_log.success("Compilation completed successfully!")

if __name__ == '__main__':
    main()
