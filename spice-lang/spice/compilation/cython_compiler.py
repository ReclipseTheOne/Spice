"""Cython compilation module for Spice exe mode."""

import subprocess
import sys
import sysconfig
import tempfile
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from spice.printils import pipeline_log

if TYPE_CHECKING:
    from spice.cli import CLI_FLAGS


def compile_to_executable(pyx_path: Path, flags: "CLI_FLAGS") -> Path:
    """
    Compile a .pyx file to a standalone executable using Cython --embed.

    Uses distutils/setuptools to handle compiler setup automatically,
    which properly configures MSVC on Windows.

    Args:
        pyx_path: Path to the .pyx file to compile
        flags: CLI flags for compilation options

    Returns:
        Path to the generated executable

    Raises:
        RuntimeError: If compilation fails at any stage
    """
    pipeline_log.custom("cython", f"Compiling {pyx_path} to executable...")

    # Determine output paths
    c_path = pyx_path.with_suffix('.c')
    if sys.platform == 'win32':
        exe_path = pyx_path.with_suffix('.exe')
    else:
        exe_path = pyx_path.with_suffix('')

    # Step 1: Cython .pyx -> .c with --embed for standalone executable
    pipeline_log.custom("cython", "Step 1: Generating C code with embedded main()...")
    cython_cmd = [
        sys.executable, '-m', 'cython',
        '--embed',  # Generate main() function for standalone executable
        '-3',       # Python 3 mode
        '-o', str(c_path),
        str(pyx_path)
    ]

    try:
        result = subprocess.run(cython_cmd, capture_output=True, text=True, check=True)
        if flags.verbose and result.stdout:
            pipeline_log.info(result.stdout)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Cython compilation failed:\n{e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError(
            "Cython not found. Install it with: pip install cython"
        )

    pipeline_log.custom("cython", f"Generated C code: {c_path}")

    # Step 2: Compile C -> executable using distutils (handles MSVC setup)
    pipeline_log.custom("cython", "Step 2: Compiling C to executable...")

    _compile_c_to_exe(c_path, exe_path, flags)

    # Cleanup intermediate files for AOT compilation (unless --keep_intermediates)
    if not flags.keep_intermediates:
        pipeline_log.custom("cython", "Cleaning up intermediate files...")
        if c_path.exists():
            c_path.unlink()
        if pyx_path.exists():
            pyx_path.unlink()
        # Also clean up MSVC artifacts
        for ext in ['.lib', '.exp', '.obj']:
            artifact = pyx_path.with_suffix(ext)
            if artifact.exists():
                artifact.unlink()
    else:
        pipeline_log.custom("cython", "Keeping intermediate files (.pyx, .c)")

    pipeline_log.success(f"Generated executable: {exe_path}")
    return exe_path


def _compile_c_to_exe(c_path: Path, exe_path: Path, flags: "CLI_FLAGS"):
    """Compile C file to executable using distutils for proper compiler setup."""
    import distutils.ccompiler
    from distutils.errors import CompileError, LinkError

    # Create a temporary build directory
    build_dir = c_path.parent / '.spice_build'
    build_dir.mkdir(exist_ok=True)

    try:
        # Get a compiler instance - this handles MSVC env setup on Windows
        compiler = distutils.ccompiler.new_compiler()

        # Add Python include directory
        compiler.add_include_dir(sysconfig.get_path('include'))

        # Add Python library directory
        lib_dir = sysconfig.get_config_var('LIBDIR')
        if lib_dir:
            compiler.add_library_dir(lib_dir)

        # On Windows, also add the libs folder
        if sys.platform == 'win32':
            python_lib_dir = Path(sys.executable).parent / 'libs'
            if python_lib_dir.exists():
                compiler.add_library_dir(str(python_lib_dir))

            # Link against pythonXY.lib
            python_lib = f'python{sys.version_info.major}{sys.version_info.minor}'
            compiler.add_library(python_lib)
        else:
            # Unix - link against libpythonX.Y
            python_lib = f'python{sys.version_info.major}.{sys.version_info.minor}'
            compiler.add_library(python_lib)

        # Compile
        objects = compiler.compile(
            [str(c_path)],
            output_dir=str(build_dir),
        )

        # Link to executable
        compiler.link_executable(
            objects,
            str(exe_path.stem),
            output_dir=str(exe_path.parent),
        )

    except (CompileError, LinkError) as e:
        raise RuntimeError(f"C compilation failed: {e}") from e
    finally:
        # Cleanup build directory
        if build_dir.exists():
            shutil.rmtree(build_dir, ignore_errors=True)
