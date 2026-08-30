# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

Fresh `uv init` scaffold for DataAnalysisTool. The only source file is `main.py`;
`pyproject.toml` declares no dependencies yet and there is no test suite, linter,
or CI configuration. Treat the layout below as the intended convention rather
than something already established in the tree.

## Environment

The project is managed by [uv](https://docs.astral.sh/uv/); Python is pinned to
3.11 in `.python-version`. There is no committed `uv.lock` yet — the first
`uv sync` or `uv add` creates it, and it should be committed.

```sh
uv sync                  # create .venv and install from pyproject.toml
uv add <package>         # add a runtime dependency (updates pyproject + lock)
uv add --dev <package>   # add a dev-only dependency
uv run main.py           # run in the project environment
```

Prefer `uv run <cmd>` over activating `.venv` manually — it resolves the
environment and keeps the lockfile honest.

## Tests and linting

Nothing is configured yet. When adding tooling, wire it through uv so commands
stay reproducible:

```sh
uv run pytest                          # full suite
uv run pytest tests/test_x.py::test_y  # single test
uv run ruff check .                    # lint
uv run ruff format .                   # format
```

Add `pytest`/`ruff` with `uv add --dev` before these work.

## Git workflow — git flow

All git operations follow the git flow branching model.

### Branches

| Branch | Role |
| --- | --- |
| `main` | Production-ready history only. Every commit is a release, tagged `vX.Y.Z`. Never commit directly. |
| `develop` | Integration branch. The base for all feature work and the default target of pull requests. |
| `feature/<name>` | Branches from `develop`, merges back into `develop`. |
| `release/<X.Y.Z>` | Branches from `develop`, merges into **both** `main` and `develop`. Only bug fixes, version bumps, and release metadata. |
| `hotfix/<X.Y.Z>` | Branches from `main`, merges into **both** `main` and `develop`. |

Merge topic branches with `--no-ff` so each branch keeps a visible merge commit.
Bump `version` in `pyproject.toml` on the release/hotfix branch, and tag the
merge commit on `main` with the matching `vX.Y.Z`.

### Commands

The `git-flow` extension is not installed in this environment, so use plain git:

```sh
# feature
git checkout -b feature/<name> develop
git checkout develop && git merge --no-ff feature/<name>

# release
git checkout -b release/<X.Y.Z> develop      # bump version in pyproject.toml
git checkout main && git merge --no-ff release/<X.Y.Z>
git tag -a v<X.Y.Z> -m "v<X.Y.Z>"
git checkout develop && git merge --no-ff release/<X.Y.Z>

# hotfix
git checkout -b hotfix/<X.Y.Z> main
git checkout main && git merge --no-ff hotfix/<X.Y.Z> && git tag -a v<X.Y.Z> -m "v<X.Y.Z>"
git checkout develop && git merge --no-ff hotfix/<X.Y.Z>
```

If `git-flow` (AVH edition) is available, `git flow feature start/finish <name>`
and the `release`/`hotfix` equivalents do the same thing.

### Which branch Claude works on

Claude works on `develop`. Never commit or push to `main` — it only receives
release and hotfix merges.

Small, self-contained changes go directly onto `develop`. For anything larger,
branch `feature/<name>` off `develop` and merge it back with `--no-ff`.

If a Claude Code web session is handed a harness-assigned branch
(`claude/<slug>`), treat it as a feature branch off `develop` and open its pull
request against `develop`.