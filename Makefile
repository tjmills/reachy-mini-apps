.PHONY: setup sync run-hello clone-vendor lint typecheck

setup:
	uv venv
	uv sync

sync:
	uv sync

run-hello:
	uv run python apps/hello_motion/main.py

clone-vendor:
	uv run python scripts/clone_vendor.py

lint:
	uv run ruff check .

typecheck:
	uv run mypy apps scripts || true
