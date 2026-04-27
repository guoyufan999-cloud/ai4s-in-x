# Runtime Environment Snapshot

- Snapshot date: 2026-04-27
- Purpose: lock the environment used to validate the `quality_v5` post-only formal baseline
- Python: `3.11.9`
- Platform: `macOS-26.4.1-arm64-arm-64bit`
- Kernel: `Darwin 25.4.0 RELEASE_ARM64_T8132 arm64`
- SQLite runtime: `3.45.1`
- pip: `26.0.1`
- Project install mode: editable package from this repository

## Locked Package Set

The pinned package set is versioned in `requirements.lock.txt`. It was captured with:

```bash
./.venv/bin/python -m pip freeze --exclude-editable
```

The local editable package `ai4s-legitimacy` is excluded from the lock because the package source is this repository. For a strict replay of the current environment, install the lock first and then install the editable project against the same constraint set:

```bash
./.venv/bin/python -m pip install -r requirements.lock.txt
./.venv/bin/python -m pip install -e '.[dev]' -c requirements.lock.txt
./.venv/bin/python -m pip check
```

## Verified Toolchain

- `pandas==3.0.2`
- `matplotlib==3.10.8`
- `numpy==2.4.4`
- `certifi==2026.2.25`
- `pytest==9.0.3`
- `ruff==0.15.10`
- `mypy==1.20.2`

## Baseline Verification Commands

The current snapshot was verified with:

```bash
./.venv/bin/python -B -m pytest -q
./.venv/bin/ruff check .
./.venv/bin/python -m mypy
./.venv/bin/python -B scripts/repo_health.py --json --allow-missing-source-db
./.venv/bin/pip check
```

Current expected result: `113 passed`, Ruff clean, mypy clean, repo_health ok, and no broken requirements.
