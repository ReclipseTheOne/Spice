# Spice Programming Language

A Python superset with static typing features including interfaces, abstract classes, final modifiers, and more.

## Project Structure

```
Spice/
├── spice-lang/          # Core language implementation (Python package)
│   ├── spice/           # Main package
│   │   ├── lexer/       # Tokenization
│   │   ├── parser/      # AST generation
│   │   ├── compilation/ # Type checking & compilation pipeline
│   │   ├── transformer/ # Spice → Python transformation
│   │   └── cli/         # Command Line handling
│   └── tests/           # Unit tests
├── spice-lsp/           # Language Server Protocol Impl
│   └── spice_lsp/       # LSP server using pygls
├── spice-vscode/        # VSCode extension
│   └── src/             # LSP client + commands
└── examples/            # Example .spc files
```

## Architecture

### 1. Core Language (`spice/`)
The main compiler implementation:
- **Lexer**: Tokenizes `.spc` source files
- **Parser**: Generates Abstract Syntax Trees (AST)
- **Type System**: Static type checking with interfaces
- **Transformer**: Converts Spice code to Python

### 2. Language Server (`spice-lsp/`)
LSP server that provides IDE features:
- Real-time diagnostics (syntax/type errors)
- Code completion
- Hover information
- Uses the core Spice Lexer/Parser

### 3. VSCode Extension (`spice-vscode/`)
Minimal extension that:
- Starts the LSP server
- Provides syntax highlighting
- Registers compile/run commands

## Installation

### 1. Install Core Language
```bash
cd spice-lang
pip install -e .
```

### 2. Install LSP Server
```bash
cd spice-lsp
pip install -e .
```

### 3. Install VSCode Extension
```bash
cd spice-vscode
npm install
npm run compile
```

Then press F5 in VSCode to launch the extension development host.

## Usage

### Compile Spice to Python
```bash
spicy input.spc -o output.py
```

### Run Spice file
```bash
spice input.spc
```

### VSCode Integration
1. Open a `.spc` file
2. LSP provides:
   - Syntax checking (red squiggles)
   - Auto-completion (Ctrl+Space)
   - Hover info (hover over keywords)
3. Commands:
   - `Ctrl+Shift+B`: Compile to Python
   - `Ctrl+Shift+R`: Run file

## Language Features

```spice
// Interfaces
interface Drawable {
    def draw() -> None;
}

// Abstract classes
abstract class Shape {
    abstract def area() -> float;
}

// Final classes (cannot be inherited)
final class Circle extends Shape implements Drawable {
    def __init__(self, radius: float) -> None {
        self.radius = radius;
    }

    def area() -> float {
        return 3.14 * self.radius ** 2;
    }

    def draw() -> None {
        print(f"Drawing circle with radius {self.radius}");
    }
}

// Strict Typing - Anything not directly made with a constructor / primitive requires type inference
myVar = A(); // Will automatically get the A type infered on Transform
or
myVar = 100; // Will automatically be set as int

myNotSetVar = aRandomMethod(); // Will crash at compile time
mySetVar: B = aRandomMethod(); // Will not crash

// And many more planned <3
```

## Development

### Testing
```bash
cd spice-lang
pytest
```

### LSP Server Debug
```bash
spice-lsp
# Then connect VSCode to stdio
```

## Contributing

1. Core language changes → `spice-lang/`
2. IDE features → `spice-lsp/`
3. VSCode UI → `spice-vscode/`
