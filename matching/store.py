"""
SQLite store for the shared value graph.

Tables:
  canonical_values — deduplicated values (the graph nodes)
  user_values      — which users hold which canonical values (the links)
"""

from __future__ import annotations

import json
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

DEFAULT_DB = Path.home() / ".hermes" / "matching" / "values.db"


class Store:
    """Thin wrapper around SQLite for the shared value graph."""

    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self) -> None:
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS canonical_values (
                id          TEXT PRIMARY KEY,
                title       TEXT NOT NULL,
                policies    TEXT NOT NULL,
                created_at  REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_values (
                user_id       TEXT NOT NULL,
                canonical_id  TEXT NOT NULL REFERENCES canonical_values(id),
                original_title TEXT NOT NULL,
                contributed_at REAL NOT NULL,
                PRIMARY KEY (user_id, canonical_id)
            );
        """)

    # -- Canonical values --

    def add_canonical(self, title: str, policies: list[str]) -> str:
        """Insert a new canonical value. Returns its ID."""
        vid = str(uuid.uuid4())[:8]
        self.conn.execute(
            "INSERT INTO canonical_values (id, title, policies, created_at) "
            "VALUES (?, ?, ?, ?)",
            (vid, title, json.dumps(policies), time.time()),
        )
        self.conn.commit()
        return vid

    def get_canonical(self, vid: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM canonical_values WHERE id = ?", (vid,)
        ).fetchone()
        return _row_to_value(row) if row else None

    def all_canonicals(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM canonical_values ORDER BY created_at"
        ).fetchall()
        return [_row_to_value(r) for r in rows]

    # -- User-value links --

    def link_user(self, user_id: str, canonical_id: str,
                  original_title: str) -> None:
        """Link a user to a canonical value (idempotent)."""
        self.conn.execute(
            "INSERT OR IGNORE INTO user_values "
            "(user_id, canonical_id, original_title, contributed_at) "
            "VALUES (?, ?, ?, ?)",
            (user_id, canonical_id, original_title, time.time()),
        )
        self.conn.commit()

    def user_values(self, user_id: str) -> list[dict]:
        """Get all canonical values for a user."""
        rows = self.conn.execute(
            "SELECT cv.* FROM canonical_values cv "
            "JOIN user_values uv ON cv.id = uv.canonical_id "
            "WHERE uv.user_id = ? ORDER BY cv.created_at",
            (user_id,),
        ).fetchall()
        return [_row_to_value(r) for r in rows]

    def users_for_value(self, canonical_id: str) -> list[str]:
        """Get all user IDs linked to a canonical value."""
        rows = self.conn.execute(
            "SELECT user_id FROM user_values WHERE canonical_id = ?",
            (canonical_id,),
        ).fetchall()
        return [r["user_id"] for r in rows]

    def all_user_ids(self) -> list[str]:
        rows = self.conn.execute(
            "SELECT DISTINCT user_id FROM user_values"
        ).fetchall()
        return [r["user_id"] for r in rows]

    def close(self) -> None:
        self.conn.close()


def _row_to_value(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "policies": json.loads(row["policies"]),
        "created_at": row["created_at"],
    }
