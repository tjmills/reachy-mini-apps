# Applications

Each direct child of this directory is an independent Python Reachy Mini app
and a member of the root `uv` workspace.

## Required app contract

Every app directory must contain:

- `pyproject.toml` with unique project metadata, Python 3.10 compatibility, and
  a `reachy-mini` runtime dependency
- `README.md` describing purpose, prerequisites, and run instructions
- `index.html` and `style.css` for its Hugging Face landing page
- `<package>/__init__.py` and `<package>/main.py`
- a `ReachyMiniApp` subclass registered under
  `[project.entry-points."reachy_mini_apps"]`
- README frontmatter containing `reachy_mini` and `reachy_mini_python_app`
- hardware-independent tests for configuration and pure behavior where possible

Optional app-owned content includes:

- `static/` for a browser UI served by the Python app
- `assets/` for audio, images, motion files, or models
- `tests/` or `test_*.py` for automated tests
- `.env.example` containing documented variable names without secrets
- `plan.md` for active implementation planning

Do not commit `.env`, virtual environments, generated media, caches, or an
app-local `uv.lock`. Shared dependencies are resolved by the root lockfile.

## Create and validate

Use the developer-supplied workflow in `../skills/create-app.md`; do not create
new app directories manually.

From the repository root:

```bash
make app-check
make run-local PROJECT=<directory-name>
make check
```

Hardware and media behavior must also be tested according to
`../skills/testing-apps.md` before an app is considered complete.
