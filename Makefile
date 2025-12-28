.PHONY: build-spice build-lsp build-all install-spice install-lsp install-all \
	rebuild-lsp rebuild-spice rebuild uninstall-all uninstall-lsp uninstall-spice \
	dev-spice dev-lsp dev-all setup-tools test test-coverage format lint clean \
	vscode-ext vscode-dev deploy

build-spice:
	cd spice-lang && python -m build --wheel --outdir ../dist

build-lsp:
	cd spice-lsp && python -m build --wheel --outdir ../dist

build-all: build-spice build-lsp

install-spice: build-spice
	python -m installer $$(ls -t dist/spicy-*.whl | head -1)

install-lsp: build-lsp
	python -m installer $$(ls -t dist/spice_lsp-*.whl | head -1)

install-all: install-spice install-lsp

rebuild-lsp: clean uninstall-lsp build-lsp install-lsp

rebuild-spice: clean uninstall-spice build-spice install-spice

rebuild: clean uninstall-all build-all install-all

uninstall-all: uninstall-spice uninstall-lsp

uninstall-lsp:
	-pip uninstall -y spice-lsp

uninstall-spice:
	-pip uninstall -y spicy

dev-spice:
	pip install -e "./spice-lang[dev]"

dev-lsp:
	pip install -e "./spice-lsp"

dev-all: dev-spice dev-lsp

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

vscode-ext:
	cd spice-vscode && npm install && npm run package
	cd spice-vscode && npx vsce package --allow-missing-repository
	code --install-extension $$(ls -t spice-vscode/*.vsix | head -1) --force

vscode-dev:
	code . --extensionDevelopmentPath="$(CURDIR)/spice-vscode" --disable-extensions

deploy: rebuild vscode-ext vscode-dev