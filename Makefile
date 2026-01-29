REACHY_HOST  ?= pollen@reachy-mini.local
REMOTE_DIR   ?= /home/pollen/reachy_mini_apps

EXCLUDES := \
	--exclude .git \
	--exclude .venv \
	--exclude __pycache__ \
	--exclude .pytest_cache \
	--exclude .ipynb_checkpoints

RSYNC := rsync -avz

.PHONY: sync-up sync-down run kill

sync-up:
	ssh $(REACHY_HOST) "mkdir -p $(REMOTE_DIR)"
	$(RSYNC) --delete $(EXCLUDES) ./ $(REACHY_HOST):$(REMOTE_DIR)/

sync-down:
	$(RSYNC) --delete $(EXCLUDES) $(REACHY_HOST):$(REMOTE_DIR)/ ./

run:
	@if [ -z "$(PROJECT)" ]; then echo "Usage: make run PROJECT=<name>"; exit 1; fi
	ssh $(REACHY_HOST) "cd $(REMOTE_DIR)/apps/$(PROJECT) && /opt/uv/uv run python main.py"

kill:
	ssh $(REACHY_HOST) "pkill -f reachy_mini_apps || true"
