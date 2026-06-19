# Reachy Mini Apps — Agent Instructions

This repository consumes the developer-maintained agent guidance from the
sibling Reachy Mini SDK checkout. Do not duplicate that guidance here.

## Required startup sequence

Before inspecting or changing application code:

1. Read `agents.local.md` when it exists. It contains machine and robot context.
2. Run `make agent-check` and stop if the shared SDK checkout is unavailable.
3. Read [`../reachy_mini/AGENTS.md`](../reachy_mini/AGENTS.md) in full.
4. Read the task-specific playbooks exposed through [`skills/`](skills).
5. Inspect the target app's `README.md`, `pyproject.toml`, and existing patterns.

If `agents.local.md` is absent, follow the shared `skills/setup-environment.md`
procedure. `agents.local.md.example` documents the expected local format.

## Path semantics

- `skills` is a relative symlink to `../reachy_mini/skills`.
- Relative `docs/`, `examples/`, `src/`, and `ts/` references in the shared
  guide resolve from `../reachy_mini`, not this repository.
- Paths under `apps/` resolve from this repository.

The sibling checkout must therefore be named `reachy_mini` and sit beside this
repository:

```text
parent/
├── reachy_mini/
└── reachy_mini_apps/
```

## Local workflow

- **Python is the required default for all applications.** This overrides the
  shared guide's JS-first recommendation. Use JS only when a concrete
  requirement cannot reasonably be implemented in Python, and document that
  constraint before choosing JS. A browser UI alone is not sufficient reason:
  prefer a Python app with a frontend in its `static/` directory.
- Existing apps may be edited in place. Use the shared app-creation playbook
  and its required scaffolder only when creating a new app.
- Follow the most task-specific shared playbook when it refines the general
  guide.
- Keep app plans in the app directory as `plan.md` when required by the shared
  guide or playbook.
- Use `uv` for Python environments and commands.
- Before handing off Python changes, run the applicable Ruff, mypy, and pytest
  checks, then follow `skills/testing-apps.md` for simulation or robot testing.
- Do not run hardware tests or publish/deploy without the user-provided robot,
  authentication, and target context.

Update shared SDK knowledge in `../reachy_mini`; keep this file limited to
repository integration and local workflow.
