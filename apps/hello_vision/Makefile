# ---- Config ----
REACHY_HOST  ?= pollen@reachy-mini.local
REMOTE_BASE  ?= /home/pollen/projects
PY_CMD       ?= /opt/uv/uv run python
PROJECT      ?= hello_vision

# ---- Rsync options ----
EXCLUDES := \
	--exclude .git \
	--exclude .venv \
	--exclude __pycache__ \
	--exclude .pytest_cache \
	--exclude .ipynb_checkpoints

RSYNC := rsync -az

# ---- Targets ----
.PHONY: run sync-up sync-down sync-up-dry sync-down-dry logs

## Run main.py on the robot for the given project
run:
	ssh $(REACHY_HOST) "cd $(REMOTE_BASE)/$(PROJECT) && $(PY_CMD) main.py"

## Sync *everything in the current folder* up to the robot (mirror local -> remote)
sync-up:
	ssh $(REACHY_HOST) "mkdir -p $(REMOTE_BASE)/$(PROJECT)"
	$(RSYNC) --delete $(EXCLUDES) ./ $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/

## Dry-run for sync-up (shows what would change, including deletes)
sync-up-dry:
	ssh $(REACHY_HOST) "mkdir -p $(REMOTE_BASE)/$(PROJECT)"
	$(RSYNC) --delete --dry-run $(EXCLUDES) ./ $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/

## Sync *everything from the robot* down to the current folder (mirror remote -> local)
sync-down:
	$(RSYNC) --delete $(EXCLUDES) $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/ ./

## Dry-run for sync-down
sync-down-dry:
	$(RSYNC) --delete --dry-run $(EXCLUDES) $(REACHY_HOST):$(REMOTE_BASE)/$(PROJECT)/ ./

## Tail a log file if you have one (optional; adjust path)
logs:
	ssh $(REACHY_HOST) "tail -n 200 -f $(REMOTE_BASE)/$(PROJECT)/run.log"
