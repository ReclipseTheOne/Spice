.PHONY: install dev test format lint clean build

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	cd ./spice
	pytest tests/ -v

test-coverage:
	pytest tests/ --cov=spice --cov-report=html --cov-report=term

format:
	black src/ tests/
	isort src/ tests/

lint:
	flake8 src/ tests/
	mypy src/

clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage

build:
	python -m build

run-example:
	spicy examples/shapes.spc -v
	python examples/example.py