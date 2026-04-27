from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ai4s_legitimacy.utils.db import connect_sqlite_readonly


def test_connect_sqlite_readonly_requires_existing_file_and_creates_no_parent_dirs(
    tmp_path: Path,
) -> None:
    missing_db = tmp_path / "missing" / "research.sqlite3"
    with pytest.raises(FileNotFoundError):
        connect_sqlite_readonly(missing_db)
    assert not missing_db.parent.exists()


def test_connect_sqlite_readonly_does_not_create_wal_or_shm_files(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "readonly.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO sample (value) VALUES ('ok')")
        connection.commit()

    with connect_sqlite_readonly(db_path) as connection:
        row = connection.execute("SELECT value FROM sample").fetchone()
        assert row["value"] == "ok"

    assert db_path.exists()
    assert not db_path.with_suffix(".sqlite3-wal").exists()
    assert not db_path.with_suffix(".sqlite3-shm").exists()


def test_connect_sqlite_readonly_accepts_immutable_mode(tmp_path: Path) -> None:
    db_path = tmp_path / "readonly.sqlite3"
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY, value TEXT)")
        connection.execute("INSERT INTO sample (value) VALUES ('ok')")
        connection.commit()

    with connect_sqlite_readonly(db_path, immutable=True) as connection:
        row = connection.execute("SELECT value FROM sample").fetchone()
        assert row["value"] == "ok"

    assert not db_path.with_suffix(".sqlite3-wal").exists()
    assert not db_path.with_suffix(".sqlite3-shm").exists()
