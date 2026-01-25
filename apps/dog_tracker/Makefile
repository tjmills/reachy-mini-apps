# ---- Config ----
REACHY_HOST ?= pollen@reachy-mini.local
REMOTE_BASE ?= /home/pollen/projects
PY_CMD ?= /opt/uv/uv run python
PROJECT ?= dog_tracker
# ---- Targets ----
.PHONY: run sync logs

## Run main.py on the robot for the given project
run:
	ssh $(REACHY_HOST) "cd $(REMOTE_BASE)/$(PROJECT) && set -a && . ./.env && set +a && $(PY_CMD) main.py"

sync-up:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make sync-up PROJECT=<project_name>"; \
		exit 1; \
	fi
	rsync -az --delete \
		--exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache --exclude .ipynb_checkpoints \
		./ $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/

sync-down:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make sync-down PROJECT=<project_name>"; \
		exit 1; \
	fi
	rsync -az --ignore-existing \
		--exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache --exclude .ipynb_checkpoints \
		$(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/ ./

## Tail a log file if you have one (optional; adjust path)
logs:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make logs PROJECT=<project_name>"; \
		exit 1; \
	fi
	ssh $(REACHY_HOST) "tail -n 200 -f $(REMOTE_BASE)/$(PROJECT)/run.log"
