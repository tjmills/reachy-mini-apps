# Reachy Mini Apps

Tutorial and demo applications for Reachy Mini.

## Agent development setup

Agent instructions are rooted at [`AGENTS.md`](AGENTS.md). The repository uses
the developer-maintained guide and playbooks from a sibling `reachy_mini`
checkout rather than copying them:

```text
parent/
├── reachy_mini/
└── reachy_mini_apps/
```

Validate the integration with:

```bash
make agent-check
```

Copy `agents.local.md.example` to the ignored `agents.local.md` only when local
machine or robot context needs to be initialized manually. Otherwise follow the
setup procedure referenced by `AGENTS.md`.

Application code lives under `apps/`. Use `uv` for Python environment and
dependency management.

## Monorepo commands

```bash
make list-apps                         # Discover workspace apps
make sync                              # Sync every app and development tools
make app-check                         # Validate app directory contracts
make check                             # Lint, format-check, type-check, and test
make run-local PROJECT=hello_motion    # Run locally or against a local daemon
make run PROJECT=hello_motion          # Run on the configured Wireless robot
```

Pass application arguments with `ARGS`, for example:

```bash
make run-local PROJECT=hello_emotion ARGS="--list"
```

The root `uv.lock` is authoritative for the whole workspace. Do not create or
commit lockfiles inside individual app directories.

## Adding an app

Python is the default. Follow [`skills/create-app.md`](skills/create-app.md)
and use `reachy-mini-app-assistant`; do not hand-create an app directory. New
directories under `apps/` are picked up automatically by the `uv` workspace.
Run `make app-check` immediately after scaffolding, then `make check` before
handoff.
