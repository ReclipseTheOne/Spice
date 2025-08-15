"""Enhanced compiler with optional type checking."""

import click
from pathlib import Path
from typing import Optional

from lexer import Lexer
from parser.parser import Parser
from transformer.transformer import Transformer
from styping.type_system import TypeChecker, TypeEnforcement
from errors import SpiceError


class SpiceCompiler:
    """Enhanced Spice compiler with type checking."""

    def __init__(self, type_enforcement: TypeEnforcement = TypeEnforcement.WARNINGS):
        self.type_enforcement = type_enforcement
        self.type_checker = TypeChecker()

    def compile(self, source_code: str, source_path: Path) -> str:
        """Compile Spice source code to Python."""

        # Lexical analysis
        lexer = Lexer()
        tokens = lexer.tokenize(source_code)

        # Parsing
        parser = Parser()
        ast = parser.parse(tokens)

        # Type checking (optional)
        if self.type_enforcement != TypeEnforcement.NONE:
            self._perform_type_checking(ast, source_path)

        # Code generation
        transformer = Transformer()
        python_code = transformer.transform(ast)

        # Add runtime type checking if requested
        if self.type_enforcement == TypeEnforcement.STRICT:
            python_code = self._add_runtime_checks(python_code)

        return python_code

    def _perform_type_checking(self, ast, source_path):
        """Perform static type checking."""
        # TODO: Walk the AST and check types
        # For now, just validate interfaces are properly implemented

        for error in self.type_checker.errors:
            if self.type_enforcement == TypeEnforcement.STRICT:
                raise SpiceError(f"Type error: {error}")
            else:  # WARNINGS
                click.echo(f"Type warning: {error}", err=True)

        for warning in self.type_checker.warnings:
            click.echo(f"Type hint: {warning}", err=True)

    def _add_runtime_checks(self, python_code: str) -> str:
        """Add runtime type checking to generated Python code."""
        from styping.type_system import create_runtime_type_checker

        runtime_checks = create_runtime_type_checker()

        # Add runtime checking imports and decorators
        enhanced_code = runtime_checks + "\n\n" + python_code

        # TODO: Automatically add @typed decorators to functions
        # This would require AST manipulation of the generated Python

        return enhanced_code


# CLI integration
@click.command()
@click.argument('source', type=click.Path(exists=True))
@click.option('--type-check', type=click.Choice(['none', 'warnings', 'strict']),
              default='warnings', help='Type checking level')
@click.option('-o', '--output', help='Output file')
@click.option('-v', '--verbose', is_flag=True)
def compile_with_types(source: str, type_check: str, output: Optional[str], verbose: bool):
    """Compile Spice files with optional type checking."""

    source_path = Path(source)
    if output:
        output_path = Path(output)
    else:
        output_path = source_path.with_suffix('.py')

    # Read source
    with open(source_path, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Compile with type checking
    enforcement = TypeEnforcement(type_check)
    compiler = SpiceCompiler(enforcement)

    try:
        result = compiler.compile(source_code, source_path)

        # Write output
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(result)

        if verbose:
            click.echo(f"Compiled {source_path} -> {output_path}")
            if enforcement == TypeEnforcement.STRICT:
                click.echo("Strict type checking enabled")
            elif enforcement == TypeEnforcement.WARNINGS:
                click.echo("Type warnings enabled")

    except SpiceError as e:
        click.echo(f"Compilation failed: {e}", err=True)
        return 1

    return 0


if __name__ == '__main__':
    compile_with_types()
