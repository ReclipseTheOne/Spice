.PHONY: install dev test format lint clean build rebuild setup-tools vscode-ext vscode-dev deploy

# Build wheel using pypa/build
build:
	cd spice-lang && python -m build --wheel --outdir ../dist

# Install wheel using pypa/installer
install: build
	python -m installer $$(ls -t dist/*.whl | head -1)

# Quick rebuild + reinstall for development
rebuild: clean uninstall build install

# Uninstall existing package
uninstall:
	-pip uninstall -y spicy

# Editable install for development
dev:
	pip install -e "./spice-lang[dev]"

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
	python -c "import shutil, pathlib; [shutil.rmtree(p, ignore_errors=True) for p in [pathlib.Path(d) for d in ['build', 'dist', 'htmlcov', '.coverage', 'spice-lang/dist', 'spice-lang/build']]]"

run-example:
	spice examples/shapes.spc -v
	python examples/shapes.py

# Build and install VSCode extension
vscode-ext:
	cd spice-vscode && npm install && npm run compile
	cd spice-vscode && npx vsce package --allow-missing-repository
	code --install-extension $$(ls -t spice-vscode/*.vsix | head -1) --force

# Launch VSCode in extension development mode
vscode-dev:
	code . --extensionDevelopmentPath="$(CURDIR)/spice-vscode" --disable-extensions

# Full deploy: rebuild spice + vscode extension + launch
deploy: rebuild vscode-ext vscode-dev