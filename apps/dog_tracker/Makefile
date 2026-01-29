# ---- Config ----
REACHY_HOST ?= pollen@reachy-mini.local
REMOTE_BASE ?= /home/pollen/projects
PY_CMD ?= /opt/uv/uv run python
PROJECT ?= dog_tracker
# ---- Targets ----
.PHONY: run sync logs verify-sync kill

## Run main.py on the robot for the given project
run:
	ssh $(REACHY_HOST) "cd $(REMOTE_BASE)/$(PROJECT) && set -a && . ./.env && set +a && $(PY_CMD) main.py"

sync-up:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make sync-up PROJECT=<project_name>"; \
		exit 1; \
	fi
	rsync -avz --delete \
		--exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache --exclude .ipynb_checkpoints \
		./ $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/
	@echo "--- Verifying sync (first 5 lines of remote main.py) ---"
	@ssh $(REACHY_HOST) "head -5 $(REMOTE_BASE)/$(PROJECT)/main.py"

verify-sync:
	@echo "=== LOCAL main.py (line 75-80) ==="
	@sed -n '75,80p' main.py
	@echo ""
	@echo "=== REMOTE main.py (line 75-80) ==="
	@ssh $(REACHY_HOST) "sed -n '75,80p' $(REMOTE_BASE)/$(PROJECT)/main.py"

sync-down:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make sync-down PROJECT=<project_name>"; \
		exit 1; \
	fi
	rsync -az --ignore-existing \
		--exclude .git --exclude .venv --exclude __pycache__ --exclude .pytest_cache --exclude .ipynb_checkpoints \
		$(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/ ./

## Kill the running main.py process on the robot (puts it to sleep)
kill:
	ssh $(REACHY_HOST) "pkill -f '$(REMOTE_BASE)/$(PROJECT)/main.py' || true"

## Tail a log file if you have one (optional; adjust path)
logs:
	@if [ -z "$(PROJECT)" ]; then \
		echo "Usage: make logs PROJECT=<project_name>"; \
		exit 1; \
	fi
	ssh $(REACHY_HOST) "tail -n 200 -f $(REMOTE_BASE)/$(PROJECT)/run.log"
