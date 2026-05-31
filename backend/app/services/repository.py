from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from app.core.config import settings


SCHEMA = """
CREATE TABLE IF NOT EXISTS assets (
  id TEXT PRIMARY KEY,
  filename TEXT NOT NULL,
  format TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  status TEXT NOT NULL,
  source_path TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  status TEXT NOT NULL,
  progress REAL NOT NULL,
  message TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(asset_id) REFERENCES assets(id)
);

CREATE TABLE IF NOT EXISTS artifacts (
  id TEXT PRIMARY KEY,
  asset_id TEXT NOT NULL,
  kind TEXT NOT NULL,
  filename TEXT NOT NULL,
  path TEXT NOT NULL,
  size_bytes INTEGER NOT NULL,
  metadata_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY(asset_id) REFERENCES assets(id)
);
"""


def init_db() -> None:
    # SQLite 适合本地开发。生产环境建议替换成 PostgreSQL。
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(settings.database_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_asset(
    asset_id: str,
    filename: str,
    file_format: str,
    size_bytes: int,
    status: str,
    source_path: Path,
) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO assets (id, filename, format, size_bytes, status, source_path)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (asset_id, filename, file_format, size_bytes, status, str(source_path)),
        )
    return get_asset(asset_id)


def update_asset_status(asset_id: str, status: str) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE assets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, asset_id),
        )


def get_asset(asset_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not row:
        raise KeyError(asset_id)
    return dict(row)


def insert_job(job_id: str, asset_id: str, status: str, progress: float, message: str) -> dict[str, Any]:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, asset_id, status, progress, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (job_id, asset_id, status, progress, message),
        )
    return get_job(job_id)


def update_job(job_id: str, status: str, progress: float, message: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            UPDATE jobs
            SET status = ?, progress = ?, message = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, progress, message, job_id),
        )


def get_job(job_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if not row:
        raise KeyError(job_id)
    return dict(row)


def insert_artifact(
    artifact_id: str,
    asset_id: str,
    kind: str,
    filename: str,
    path: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    # artifact 是转换后的预览产物，例如 GLB 或 tileset.json。
    # 前端只需要拿 URL 加载产物，不需要知道后端转换细节。
    size_bytes = path.stat().st_size
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO artifacts (id, asset_id, kind, filename, path, size_bytes, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (artifact_id, asset_id, kind, filename, str(path), size_bytes, json.dumps(metadata)),
        )
    return get_artifact(artifact_id)


def get_artifact(artifact_id: str) -> dict[str, Any]:
    with connect() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if not row:
        raise KeyError(artifact_id)
    return hydrate_artifact(dict(row))


def list_artifacts(asset_id: str) -> list[dict[str, Any]]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE asset_id = ? ORDER BY created_at ASC",
            (asset_id,),
        ).fetchall()
    return [hydrate_artifact(dict(row)) for row in rows]


def hydrate_artifact(row: dict[str, Any]) -> dict[str, Any]:
    row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
    return row
