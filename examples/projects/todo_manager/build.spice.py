"""

build.spice.py - build script for a Spice project

    python build.spice.py          # compile this folder -> build/
    python build.spice.py --run    # compile, then run the program

"""

from pathlib import Path
import subprocess
import sys

from spice.compilation import BuildFlags, SpicePipeline
from spice.compilation.spicefile import SpiceFile

"""
Compiler flags and settings
"""

ROOT = Path(__file__).resolve().parent

# Entry point for the compiler
ENTRY_FILE = ROOT / "src/__main__.spc"

# Output directory for compiled files, defaults to the place where the compiled file stands
OUT = ROOT / "build"

# "py", "pyx", or "exe"
EMIT = "py"

# Only does something when EMIT is 'exe' | If true, it will keep the .pyx files used for compilation, if false, it will delete them
KEEP_INTERMEDIATES = False

# Enable for debugging / console output of the *complete* compilation pipeline
VERBOSE = False

"""
Compiler pipeline
"""


def build() -> Path:
    OUT.mkdir(exist_ok=True)

    # A dict for all build flags that are passed down along the compilation pipeline
    flags = BuildFlags(source=ENTRY_FILE, output=OUT, emit=EMIT, keep_intermediates=KEEP_INTERMEDIATES, verbose=VERBOSE)

    # Your source of truth.
    # Plugins and tools should be attached to this single SpiceFile instance
    sf: SpiceFile = SpicePipeline.walk(flags.source, None, flags)

    # The last step of the compilation pipeline.
    # This should be the last call before running the output
    SpicePipeline.verify_and_write(sf, flags)
    return OUT / "__main__.py"


"""
Entry point
"""

if __name__ == "__main__":
    entry = build()
    print(f"Built {entry.relative_to(ROOT)}")
    if "--run" in sys.argv:
        raise SystemExit(subprocess.run([sys.executable, str(entry)]).returncode)
