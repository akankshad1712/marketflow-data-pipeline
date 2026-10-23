.PHONY: install test lint run sample
install:
	python -m pip install -e '.[dev]'
test:
	pytest
lint:
	ruff check src tests
run:
	uvicorn marketflow.api:app --reload
sample:
	python scripts/generate_sample.py --count 100
