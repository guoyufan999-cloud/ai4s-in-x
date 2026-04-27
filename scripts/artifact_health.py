from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from repo_health import ARTIFACT_CHECK_NAMES, run_health_checks


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only formal artifact integrity checks.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--allow-missing-source-db",
        action="store_true",
        help="Do not fail provenance when the ignored local SQLite source DB is absent.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_health_checks(
        args.root,
        allow_missing_source_db=args.allow_missing_source_db,
        check_names=ARTIFACT_CHECK_NAMES,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"artifact_health: {result['status']}")
        for name, check in result["checks"].items():
            print(f"- {name}: {check['status']}")
            for failure in check.get("failures", []):
                print(f"  - {failure}")
    return 0 if result["status"] == "ok" else 1


__all__ = ["ARTIFACT_CHECK_NAMES", "build_parser", "main", "run_health_checks"]


if __name__ == "__main__":
    sys.exit(main())
