# Spice by example

These are small programs that show what Spice adds **on top of Python**. Spice
is a Python superset, so anything you already know from Python (variables,
`for`/`while`, comprehensions, f-strings, the standard library, ...) works
unchanged. The files here deliberately *skip* that and focus only on the
features Spice introduces.

They are meant to be read, compiled and run, starting from the lowest-numbered
file and going upward. Each file is self-contained and ends with the exact
commands used to build and run it.

```
examples/
  001-syntax_and_blocks.spc
  002-strict_typing.spc
  010-classes_and_constructors.spc
  011-inheritance.spc
  012-interfaces.spc
  013-abstract_classes.spc
  014-final.spc
  015-static_methods.spc
  020-data_classes.spc
  021-enums.spc
  030-generics.spc
  040-switch.spc
  050-annotations.spc
  060-imports_and_modules/
  projects/                     # larger programs, each with a build.spice.py
    shapes_renderer/
    todo_manager/
    bank_ledger/
```

## Building a single file

Spice ships one CLI, `spicy`, which compiles `.spc` to Python:

```bash
spicy 001-syntax_and_blocks.spc -o build
python build/001-syntax_and_blocks.py
```

`spicy` can also take a directory if it contains a `__main__.spc` entry point
(*see `060-imports_and_modules/`).

## Building a project

The `projects/` programs span several modules and are driven by a
`build.spice.py` file.

Spice is intended to be built by either calling `spicy` or
by creating a script file containing the `spice.compilation.pipeline`
toolchain.

It is planned for a plethora of tools to be implemented extending
the current options of `spice.compilation` so a
`build.spice.py` file is the preffered option going forward.

```bash
cd projects/shapes_renderer
python build.spice.py --run
```
