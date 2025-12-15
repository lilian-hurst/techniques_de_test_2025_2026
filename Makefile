.PHONY: test run unit_test perf_test coverage lint doc

test:
	pytest tests/



unit_test:
	pytest tests/ -m "not performance"

perf_test:
	pytest tests/ -m performance

coverage:
	coverage run -m pytest tests/ -m "not performance"
	coverage report -m
	coverage html

lint:
	ruff check src/ tests/
	ruff check --fix src/ tests/

doc:
	pdoc --html src/triangulator --output-dir docs