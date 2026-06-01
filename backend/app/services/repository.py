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
    """初始化本地 SQLite 数据库。

    SQLite 是一个单文件数据库，适合本地开发和原型验证。
    它不像 MySQL/PostgreSQL 那样需要单独启动数据库服务。
    生产环境建议替换成 PostgreSQL，因为它更适合并发、权限和备份。
    """

    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    """创建数据库连接，并在代码块结束后自动提交和关闭。

    Python 的 @contextmanager 可以把函数变成 with 语法可用的上下文管理器：

        with connect() as conn:
            conn.execute(...)

    好处是每次数据库操作都不会忘记 commit 或 close。
    """

    conn = sqlite3.connect(settings.database_path)

    # 默认 sqlite3 返回 tuple，例如 row[0]、row[1]。
    # 设置 row_factory 后可以像字典一样用 row["filename"] 读取字段，更直观。
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
    """新增 asset 记录。

    asset 表保存“用户上传的源文件”的信息，不保存文件内容本身。
    文件内容在磁盘上，数据库里只保存 source_path。
    """

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
    """更新源文件状态，例如 queued -> processing -> ready。"""

    with connect() as conn:
        conn.execute(
            "UPDATE assets SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, asset_id),
        )


def get_asset(asset_id: str) -> dict[str, Any]:
    """按 id 查询单个 asset。

    查不到时抛 KeyError，让 API 层统一转换成 404。
    这样 repository 层不需要知道 HTTP 的存在，职责更单一。
    """

    with connect() as conn:
        row = conn.execute("SELECT * FROM assets WHERE id = ?", (asset_id,)).fetchone()
    if not row:
        raise KeyError(asset_id)
    return dict(row)


def insert_job(job_id: str, asset_id: str, status: str, progress: float, message: str) -> dict[str, Any]:
    """新增后台任务记录。

    job 表不保存文件内容，只记录任务状态和进度。
    前端轮询的就是这张表里的状态。
    """

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
    """更新任务状态和进度。

    progress 是 0 到 1 的小数，前端会显示成百分比。
    message 是给用户看的当前阶段说明。
    """

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
    """按 id 查询后台任务。"""

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
    """新增产物记录。

    artifact 是转换后的预览或数据产物，例如：
    - GLB：浏览器可以直接加载的 3D 模型；
    - tileset.json：3D Tiles 入口文件；
    - metadata.json：结构化数据。

    前端只需要拿 URL 加载产物，不需要知道后端转换细节。
    """

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
    """按 id 查询单个产物。"""

    with connect() as conn:
        row = conn.execute("SELECT * FROM artifacts WHERE id = ?", (artifact_id,)).fetchone()
    if not row:
        raise KeyError(artifact_id)
    return hydrate_artifact(dict(row))


def list_artifacts(asset_id: str) -> list[dict[str, Any]]:
    """列出某个源文件生成的所有产物。"""

    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts WHERE asset_id = ? ORDER BY created_at ASC",
            (asset_id,),
        ).fetchall()
    return [hydrate_artifact(dict(row)) for row in rows]


def hydrate_artifact(row: dict[str, Any]) -> dict[str, Any]:
    """把数据库里的 JSON 字符串还原成 Python dict。

    SQLite 没有像 PostgreSQL 那样强大的 JSONB 类型。
    所以这里把 metadata dict 存成字符串，读取时再 json.loads 回来。
    """

    row["metadata"] = json.loads(row.pop("metadata_json") or "{}")
    return row
