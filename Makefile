.PHONY: install dev test format lint clean build build-all rebuild setup-tools vscode-ext vscode-dev deploy lsp build-lsp install-lsp

# Build wheels using pypa/build
build:
	cd spice-lang && python -m build --wheel --outdir ../dist

build-lsp:
	cd spice-lsp && python -m build --wheel --outdir ../dist

build-all: build build-lsp

# Install wheels using pypa/installer
install: build
	python -m installer $$(ls -t dist/spicy-*.whl | head -1)

install-lsp: build-lsp
	python -m installer $$(ls -t dist/spice_lsp-*.whl | head -1)

# Quick rebuild + reinstall for development
rebuild: clean uninstall build-all install install-lsp

# Uninstall existing packages
uninstall:
	-pip uninstall -y spicy
	-pip uninstall -y spice-lsp

dev-spice:
	pip install -e "./spice-lang[dev]"

dev-lsp:
	pip install -e "./spice-lsp"

dev-all: dev-spice dev-lsp

# Build and install just the LSP server
lsp: install-lsp

# Install build tools
setup-tools:
	pip install build installer

test:
	cd spice-lang && pytest tests/ -v

test-coverage:
	cd spice-lang && pytest tests/ --cov=spice --cov-report=html --cov-report=term

format:
	black spice-lang/spice/ spice-lang/tests/
	isort spice-lang/spice/ spice-lang/tests/

lint:
	flake8 spice-lang/spice/ spice-lang/tests/
	mypy spice-lang/spice/

clean:
	python -c "import shutil, pathlib; [p.unlink() for p in pathlib.Path('.').rglob('*.pyc')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('__pycache__')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p) for p in pathlib.Path('.').rglob('*.egg-info')]"
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path(d) for d in ['build', 'dist', 'htmlcov', '.coverage', 'spice-lang/dist', 'spice-lang/build', 'spice-lsp/dist', 'spice-lsp/build']]]"

run-example:
	spice examples/shapes.spc -v
	python examples/shapes.py

# Build and install VSCode extension
vscode-ext:
	cd spice-vscode && npm install && npm run package
	cd spice-vscode && npx vsce package --allow-missing-repository
	code --install-extension $$(ls -t spice-vscode/*.vsix | head -1) --force

# Launch VSCode in extension development mode
vscode-dev:
	code . --extensionDevelopmentPath="$(CURDIR)/spice-vscode" --disable-extensions

# Full deploy: rebuild spice + vscode extension + launch
deploy: rebuild vscode-ext vscode-dev