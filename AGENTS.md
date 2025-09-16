# Repository Guidelines

## Project Structure & Module Organization
Source modules live in `llean/`; `utils.py` holds Lean REPL helpers and the package exposes its API through `llean/__init__.py`. CLI-style entry points and experiments sit under `scripts/` (for example `Tutorial_L01.py`). Lightweight demos can go at the repo root (e.g., `hello.py`). Keep shared assets inside the package or `scripts/` so they ship with the project. Place any future tests in `tests/` to keep the top level clean.

## Build, Test, and Development Commands
Install or refresh dependencies with `uv sync` (Python 3.12). Run ad‑hoc scripts through `uv run python <script.py>`; fall back to `./.venv/bin/python <script.py>` when sandboxing blocks `uv`. Launch the packaged greeting with `./.venv/bin/python hello.py`. Drive Lean study flows via `./.venv/bin/python scripts/Tutorial_L01.py` or `scripts/getting_help.py`, and try the file-driven loader with `./.venv/bin/python scripts/Tutorial_L01_from_file.py`; all rely on the Lean server utilities in `llean/utils.py`.

## Environment & Lean Setup
Create `.env` from `.env.example` and set `NNG_PATH` to a local clone of the Natural Number Game (`/path/to/NNG4`). Ensure the linked repo is writable because `lean_interact` creates a `<NNG_PATH>.lock` while building the project. Re-run scripts after any mathlib update to rebuild the Lean cache.

## Lean Level Loading Helpers
Use `llean.utils.parse_level_file(path)` to pull metadata (module, namespace, goal) from a Natural Number Game level. Launch a REPL configured for that level with `get_problem_server_from_file(path, verbose=True)`; pass absolute paths under `$NNG_PATH/Game/Levels`. Opening the reported namespace mirrors the original level context so tactics behave as in-game.

## Coding Style & Naming Conventions
Follow standard Python conventions: 4-space indentation, snake_case for functions and variables, PascalCase for classes. Favor explicit imports and type hints (seen in `utils.py`). Keep helper functions pure and document non-obvious behavior with brief comments.

## Testing Guidelines
Automated tests are not yet configured; prefer creating reproducible scripts in `scripts/` that exercise new Lean workflows. Name future test modules `test_<feature>.py` using `pytest` conventions so that `pytest` can be introduced without restructuring. Record expected Lean outputs (e.g., goal states) in docstrings to aid manual verification.

## Commit & Pull Request Guidelines
Existing commits use concise, imperative subjects ("Make setup better", "Load the proper tactics..."). Continue that style, ≤72 characters, with descriptive bodies when necessary. Pull requests should summarise the change, list impacted scripts, include reproduction commands, and note any Lean caches or external repositories that must be refreshed. Link relevant issues and attach output snippets when modifying Lean interactions.
