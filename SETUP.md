# Spice Development Setup Guide

Complete setup instructions for the Spice programming language ecosystem.

## Prerequisites

- **Python 3.8+**
- **Node.js 16+** and npm
- **VSCode** (for extension development)
- **Git** (for submodules)

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/ReclipseTheOne/Spice.git
cd Spice
git submodule init
git submodule update
```

This will initialize the `spice-vscode` submodule.

### 2. Install Core Spice Compiler

```bash
cd spice-lang
pip install -e .
cd ..
```

This installs:
- `spicy` - Spice compiler CLI
- `spice` - Spice interpreter CLI

Verify installation:
```bash
spicy --version
```

### 3. Install LSP Server

```bash
cd spice-lsp
pip install -r requirements.txt
pip install -e .
cd ..
```

This installs:
- `spice-lsp` - Language server executable
- `pygls` - Language Server Protocol library

Verify installation:
```bash
which spice-lsp
# Should show the executable path
```

### 4. Install VSCode Extension

```bash
cd spice-vscode
npm install
npm run compile
```

### 5. Launch VSCode Extension (Development)

Option A: **From VSCode**
1. Open `spice-vscode/` in VSCode
2. Press `F5` to launch Extension Development Host
3. Open a `.spc` file in the new window

Option B: **Package and Install**
```bash
cd spice-vscode
npm install -g @vscode/vsce
vsce package
code --install-extension spice-language-0.1.0.vsix
```

## Configuration

### LSP Server Path

If `spice-lsp` is not in your PATH, configure it in VSCode:

**File → Preferences → Settings** → Search "Spice"
- **Spice: Lsp Server Path**: `/path/to/spice-lsp`

Or edit `.vscode/settings.json`:
```json
{
  "spice.lspServerPath": "/absolute/path/to/spice-lsp"
}
```

### Compiler Path

Similarly for the Spice compiler:
```json
{
  "spice.compilerPath": "spicy"
}
```

## Troubleshooting

### LSP Server Not Starting

**Error**: `Failed to start Spice Language Server`

**Solutions**:
1. Verify `spice-lsp` is installed:
   ```bash
   pip show spice-lsp
   ```

2. Check if executable exists:
   ```bash
   which spice-lsp
   ```

3. Set absolute path in VSCode settings

4. Check LSP server logs:
   - **View → Output** → Select "Spice Language Server"

### Import Errors in LSP

**Error**: `ModuleNotFoundError: No module named 'spice'`

**Solution**: The LSP server needs access to the `spice` package. Ensure:
```bash
cd spice-lang
pip install -e .
```

The `-e` flag creates an editable install so changes are reflected immediately.

### VSCode Extension Not Loading

1. Check compilation succeeded:
   ```bash
   cd spice-vscode
   npm run compile
   ```

2. Look for `out/` directory:
   ```bash
   ls out/
   # Should contain extension.js
   ```

3. Check extension host logs:
   - **Help → Toggle Developer Tools** → Console tab

### Syntax Highlighting Not Working

The syntax highlighting is defined in:
- `spice-vscode/syntaxes/spice.tmLanguage.json`

If it's not working:
1. Reload VSCode: `Ctrl+Shift+P` → "Reload Window"
2. Check file association: File should be detected as "Spice"

## Development Workflow

### Making Changes to Core Language

```bash
cd spice-lang
# Make changes to lexer/parser/etc.
pytest  # Run tests
cd ..
```

Changes are immediately available (editable install).

### Making Changes to LSP Server

```bash
cd spice-lsp
# Edit spice_lsp/server.py
# Restart VSCode window to reload LSP
```

### Making Changes to VSCode Extension

```bash
cd spice-vscode
# Edit src/extension.ts
npm run compile
# Press F5 in VSCode to launch new instance
```

## Testing

### Test Core Language
```bash
cd spice-lang
pytest -v
```

### Test LSP Server Manually
```bash
spice-lsp
# Type a JSON-RPC message and press Enter
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"capabilities":{}}}
```

### Test End-to-End
1. Create `test.spc`:
   ```spice
   interface Greeter {
       def greet(name: str) -> None;
   }
   ```
2. Open in VSCode with extension running
3. Should see:
   - Syntax highlighting
   - No red squiggles (valid syntax)
   - Completion for `interface` keyword
   - Hover info on `interface`

## Project Structure Reference

```
Spice/
├── spice-lang/              # Core language
│   ├── spice/
│   │   ├── lexer/           # Tokenizer
│   │   ├── parser/          # Parser
│   │   ├── compilation/     # Type checker
│   │   ├── transformer/     # Code generator
│   │   └── cli/             # CLI handlers
│   ├── tests/               # Unit tests
│   ├── setup.py             # Package definition
│   └── pyproject.toml       # Build config
│
├── spice-lsp/               # LSP server
│   ├── spice_lsp/
│   │   ├── __init__.py
│   │   └── server.py        # LSP implementation
│   ├── requirements.txt     # pygls
│   └── setup.py
│
└── spice-vscode/            # VSCode extension (submodule)
    ├── src/
    │   └── extension.ts     # LSP client
    ├── syntaxes/            # TextMate grammar
    ├── snippets/            # Code snippets
    ├── package.json         # Extension manifest
    └── tsconfig.json        # TypeScript config
```

## Next Steps

1. Try the examples:
   ```bash
   cd examples
   spice shapes.spc
   ```

2. Read the language documentation

3. Contribute! Check `TODO` for planned features
