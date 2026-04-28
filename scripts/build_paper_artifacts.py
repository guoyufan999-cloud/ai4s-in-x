#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "ai4s_legitimacy.cli.build_artifacts", *sys.argv[1:]],
        check=False,
        cwd=PROJECT_ROOT,
    )
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
