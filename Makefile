REACHY_HOST  ?= pollen@reachy-mini.local
REMOTE_DIR   ?= /home/pollen/reachy_mini_apps
PROJECT      ?=
ARGS         ?=

EXCLUDES := \
	--exclude .git \
	--exclude .venv \
	--exclude .DS_Store \
	--exclude .env \
	--exclude agents.local.md \
	--exclude __pycache__ \
	--exclude .mypy_cache \
	--exclude .pytest_cache \
	--exclude .ruff_cache \
	--exclude .ipynb_checkpoints

RSYNC := rsync -avz

.PHONY: \
	agent-check \
	app-check \
	check \
	format \
	format-check \
	lint \
	list-apps \
	run \
	run-local \
	sync \
	sync-up \
	sync-down \
	test \
	typecheck \
	kill

agent-check:
	@./scripts/check-agent-scaffold.sh

app-check:
	@./scripts/check-apps.sh

list-apps:
	@./scripts/list-apps.sh

sync:
	uv sync --all-packages --group dev

lint:
	uv run --group dev ruff check apps

format:
	uv run --group dev ruff format apps

format-check:
	uv run --group dev ruff format --check apps

typecheck:
	@./scripts/typecheck-apps.sh

test:
	@./scripts/test-apps.sh

check: agent-check app-check lint format-check typecheck test

run-local:
	@if [ -z "$(PROJECT)" ]; then echo "Usage: make run-local PROJECT=<name> [ARGS='...']"; exit 1; fi
	@test -d "apps/$(PROJECT)" || { echo "Unknown app: $(PROJECT)"; exit 1; }
	@./scripts/run-app.sh "apps/$(PROJECT)" $(ARGS)

sync-up:
	ssh $(REACHY_HOST) "mkdir -p $(REMOTE_DIR)"
	$(RSYNC) --delete $(EXCLUDES) ./ $(REACHY_HOST):$(REMOTE_DIR)/

sync-down:
	$(RSYNC) --delete $(EXCLUDES) $(REACHY_HOST):$(REMOTE_DIR)/ ./

run:
	@if [ -z "$(PROJECT)" ]; then echo "Usage: make run PROJECT=<name>"; exit 1; fi
	@test -d "apps/$(PROJECT)" || { echo "Unknown app: $(PROJECT)"; exit 1; }
	ssh $(REACHY_HOST) "cd $(REMOTE_DIR) && UV=/opt/uv/uv ./scripts/run-app.sh apps/$(PROJECT) $(ARGS)"

kill:
	ssh $(REACHY_HOST) "pkill -f reachy_mini_apps || true"
