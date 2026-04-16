from __future__ import annotations

import sqlite3
from pathlib import Path


def _configure_connection(connection: sqlite3.Connection) -> sqlite3.Connection:
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def connect_sqlite_readonly(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite DB not found for readonly access: {db_path}")
    uri = f"{db_path.absolute().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    _configure_connection(connection)
    connection.execute("PRAGMA query_only = ON")
    return connection


def connect_sqlite_writable(
    db_path: Path,
    *,
    create_parents: bool = True,
    enable_wal: bool = True,
) -> sqlite3.Connection:
    db_path = Path(db_path)
    if create_parents:
        db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(str(db_path))
    _configure_connection(connection)
    if enable_wal:
        connection.execute("PRAGMA journal_mode = WAL")
        connection.execute("PRAGMA synchronous = NORMAL")
    return connection


def init_sqlite_db(
    db_path: Path,
    schema_path: Path,
    views_path: Path | None = None,
    *,
    views_sql: str | None = None,
) -> None:
    with connect_sqlite_writable(db_path) as connection:
        connection.executescript(schema_path.read_text(encoding="utf-8"))
        if views_sql is not None:
            connection.executescript(views_sql)
        elif views_path and views_path.exists():
            connection.executescript(views_path.read_text(encoding="utf-8"))
        connection.commit()
