# ---- Config ----
REACHY_HOST ?= pollen@reachy-mini.local
REMOTE_BASE ?= /home/pollen/projects
PY_CMD ?= /opt/uv/uv run python
PROJECT ?= hello_vision
# ---- Targets ----
.PHONY: run sync logs

## Run main.py on the robot for the given project
run:
	ssh $(REACHY_HOST) "cd $(REMOTE_BASE)/$(PROJECT) && $(PY_CMD) main.py"

## Sync current workspace folder to the robot (optional convenience)
## Usage: make sync PROJECT=hello_motion
sync:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make sync PROJECT=<project_name>"; \
		exit 1; \
	fi
	rsync -az --delete \
		--exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache --exclude .ipynb_checkpoints \
		./ $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/

## Tail a log file if you have one (optional; adjust path)
logs:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make logs PROJECT=<project_name>"; \
		exit 1; \
	fi
	ssh $(REACHY_HOST) "tail -n 200 -f $(REMOTE_BASE)/$(PROJECT)/run.log"
