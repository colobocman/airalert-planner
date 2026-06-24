.PHONY: run test lint clean

run:
	python -m airalert_planner.cli analyze --input data/sample_alerts.csv --out outputs

test:
	pytest -q

lint:
	ruff check src tests

clean:
	rm -rf outputs/*.csv outputs/*.md outputs/figures .pytest_cache .ruff_cache
