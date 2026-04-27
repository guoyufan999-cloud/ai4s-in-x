from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, TypedDict

FORMAL_STAGE = "quality_v5"
FORMAL_POSTS = 514
FORMAL_COMMENTS = 0
SUMMARY_PATH = Path("outputs/reports/freeze_checkpoints/research_db_summary.json")
CONSISTENCY_PATH = Path("outputs/reports/freeze_checkpoints/quality_v5_consistency_report.json")
PROVENANCE_PATH = Path("outputs/reports/freeze_checkpoints/quality_v5_artifact_provenance.json")
SMOKE_RESIDUE_MANIFEST_PATH = Path("outputs/reports/review_v2/smoke_residue_manifest.json")
PRUNE_DIR_NAMES = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".ruff_cache"}


class IgnoredEntry(TypedDict):
    path: str
    bytes: int


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _line in handle)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _project_path(root: Path, relative_path: str | Path) -> Path:
    return root / Path(relative_path)


def _git_ls_files(root: Path) -> list[Path]:
    process = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    return [Path(item.decode()) for item in process.stdout.split(b"\0") if item]


def _git_ignored_entries(root: Path) -> list[Path]:
    process = subprocess.run(
        ["git", "-C", str(root), "status", "--ignored", "--short", "-z"],
        check=True,
        capture_output=True,
    )
    entries: list[Path] = []
    for raw_entry in process.stdout.split(b"\0"):
        if not raw_entry:
            continue
        entry = raw_entry.decode("utf-8", "ignore")
        if entry.startswith("!! "):
            entries.append(Path(entry[3:]))
    return entries


def _path_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    total = 0
    for child in path.rglob("*"):
        if child.is_file():
            total += child.stat().st_size
    return total


def _allowed_zero_byte_paths(root: Path) -> set[Path]:
    manifest_path = _project_path(root, SMOKE_RESIDUE_MANIFEST_PATH)
    if not manifest_path.exists():
        return set()
    manifest = _load_json(manifest_path)
    allowed: set[Path] = set()
    for item in manifest.get("files", []):
        if int(item.get("bytes", -1)) == 0:
            allowed.add(Path(str(item["path"])))
    return allowed


def _check_formal_counts(root: Path) -> dict[str, Any]:
    summary = _load_json(_project_path(root, SUMMARY_PATH))
    consistency = _load_json(_project_path(root, CONSISTENCY_PATH))
    paper_summary = summary[f"paper_{FORMAL_STAGE}"]
    failures: list[str] = []

    if int(paper_summary["formal_posts"]) != FORMAL_POSTS:
        failures.append(f"summary formal_posts={paper_summary['formal_posts']}")
    if int(paper_summary["formal_comments"]) != FORMAL_COMMENTS:
        failures.append(f"summary formal_comments={paper_summary['formal_comments']}")
    if consistency.get("status") != "aligned":
        failures.append(f"consistency status={consistency.get('status')!r}")
    delta = consistency.get("delta", {})
    if int(delta.get("paper_posts_minus_checkpoint", 999999)) != 0:
        failures.append(f"posts_delta={delta.get('paper_posts_minus_checkpoint')}")
    if int(delta.get("paper_comments_minus_checkpoint", 999999)) != 0:
        failures.append(f"comments_delta={delta.get('paper_comments_minus_checkpoint')}")

    return {
        "status": "ok" if not failures else "fail",
        "formal_posts": int(paper_summary["formal_posts"]),
        "formal_comments": int(paper_summary["formal_comments"]),
        "consistency_status": consistency.get("status"),
        "posts_delta": delta.get("paper_posts_minus_checkpoint"),
        "comments_delta": delta.get("paper_comments_minus_checkpoint"),
        "failures": failures,
    }


def _check_file_record(root: Path, record: dict[str, Any]) -> list[str]:
    relative_path = Path(str(record["path"]))
    path = _project_path(root, relative_path)
    failures: list[str] = []
    if bool(record.get("exists")) != path.exists():
        failures.append(f"{relative_path}: exists mismatch")
        return failures
    if not path.exists():
        return failures
    if record.get("sha256") != _sha256(path):
        failures.append(f"{relative_path}: sha256 mismatch")
    if int(record.get("bytes", -1)) != path.stat().st_size:
        failures.append(f"{relative_path}: byte size mismatch")
    if int(record.get("line_count", -1)) != _line_count(path):
        failures.append(f"{relative_path}: line count mismatch")
    return failures


def _check_provenance(root: Path, *, allow_missing_source_db: bool) -> dict[str, Any]:
    provenance = _load_json(_project_path(root, PROVENANCE_PATH))
    failures: list[str] = []

    if provenance.get("formal_stage") != FORMAL_STAGE:
        failures.append(f"formal_stage={provenance.get('formal_stage')!r}")
    if int(provenance.get("formal_posts", -1)) != FORMAL_POSTS:
        failures.append(f"provenance formal_posts={provenance.get('formal_posts')}")
    if int(provenance.get("formal_comments", -1)) != FORMAL_COMMENTS:
        failures.append(f"provenance formal_comments={provenance.get('formal_comments')}")
    if "generated_at" in json.dumps(provenance, ensure_ascii=False):
        failures.append("provenance contains generated_at")

    source_db = provenance["source_db"]
    source_db_path = _project_path(root, source_db["path"])
    if source_db_path.exists():
        if source_db.get("sha256") != _sha256(source_db_path):
            failures.append(f"{source_db['path']}: source DB sha256 mismatch")
        if int(source_db.get("bytes", -1)) != source_db_path.stat().st_size:
            failures.append(f"{source_db['path']}: source DB byte size mismatch")
    elif not allow_missing_source_db:
        failures.append(f"{source_db['path']}: source DB missing")

    for record in provenance.get("files", {}).values():
        failures.extend(_check_file_record(root, record))

    return {
        "status": "ok" if not failures else "fail",
        "schema_version": provenance.get("schema_version"),
        "formal_stage": provenance.get("formal_stage"),
        "file_count": len(provenance.get("files", {})),
        "failures": failures,
    }


def _check_zero_byte_tracked_files(root: Path) -> dict[str, Any]:
    tracked_files = _git_ls_files(root)
    allowed = _allowed_zero_byte_paths(root)
    zero_byte_files = [
        path
        for path in tracked_files
        if _project_path(root, path).is_file() and _project_path(root, path).stat().st_size == 0
    ]
    unexpected = [str(path) for path in zero_byte_files if path not in allowed]
    return {
        "status": "ok" if not unexpected else "fail",
        "zero_byte_tracked_count": len(zero_byte_files),
        "allowed_zero_byte_tracked": [str(path) for path in sorted(allowed)],
        "unexpected_zero_byte_tracked": unexpected,
        "failures": unexpected,
    }


def _check_wal_shm(root: Path) -> dict[str, Any]:
    found: list[str] = []
    for path in root.rglob("*"):
        if any(part in PRUNE_DIR_NAMES for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.name.endswith((".sqlite3-wal", ".sqlite3-shm")):
            found.append(str(path.relative_to(root)))
    return {
        "status": "ok" if not found else "fail",
        "files": sorted(found),
        "failures": sorted(found),
    }


def _check_ignored_cache_size(
    root: Path,
    *,
    max_ignored_cache_mib: float | None,
) -> dict[str, Any]:
    entries = _git_ignored_entries(root)
    sizes: list[IgnoredEntry] = [
        {"path": str(path), "bytes": _path_size(_project_path(root, path))}
        for path in entries
    ]
    total = sum(item["bytes"] for item in sizes)
    failures: list[str] = []
    if max_ignored_cache_mib is not None and total > max_ignored_cache_mib * 1024 * 1024:
        failures.append(
            f"ignored cache size {total / 1024 / 1024:.1f} MiB exceeds {max_ignored_cache_mib:.1f} MiB"
        )
    return {
        "status": "ok" if not failures else "fail",
        "ignored_entry_count": len(sizes),
        "ignored_total_bytes": total,
        "largest_entries": sorted(sizes, key=lambda item: item["bytes"], reverse=True)[:10],
        "failures": failures,
    }


def run_health_checks(
    root: Path,
    *,
    allow_missing_source_db: bool = False,
    max_ignored_cache_mib: float | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    checks = {
        "formal_counts": _check_formal_counts(root),
        "provenance": _check_provenance(root, allow_missing_source_db=allow_missing_source_db),
        "zero_byte_tracked_files": _check_zero_byte_tracked_files(root),
        "wal_shm": _check_wal_shm(root),
        "ignored_cache_size": _check_ignored_cache_size(
            root,
            max_ignored_cache_mib=max_ignored_cache_mib,
        ),
    }
    failures = {
        name: check["failures"]
        for name, check in checks.items()
        if check.get("failures")
    }
    return {
        "status": "ok" if not failures else "fail",
        "root": str(root),
        "checks": checks,
        "failures": failures,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run read-only repository and artifact health checks.")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument(
        "--allow-missing-source-db",
        action="store_true",
        help="Do not fail provenance when the ignored local SQLite source DB is absent.",
    )
    parser.add_argument(
        "--max-ignored-cache-mib",
        type=float,
        default=None,
        help="Optional threshold for ignored local cache size.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = run_health_checks(
        args.root,
        allow_missing_source_db=args.allow_missing_source_db,
        max_ignored_cache_mib=args.max_ignored_cache_mib,
    )
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"repo_health: {result['status']}")
        for name, check in result["checks"].items():
            print(f"- {name}: {check['status']}")
            for failure in check.get("failures", []):
                print(f"  - {failure}")
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
