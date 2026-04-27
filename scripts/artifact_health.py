from __future__ import annotations

from repo_health import build_parser, main, run_health_checks

__all__ = ["build_parser", "main", "run_health_checks"]


if __name__ == "__main__":
    raise SystemExit(main())
