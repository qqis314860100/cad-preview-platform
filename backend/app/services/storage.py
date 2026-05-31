from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


# 每次只读 1MB，避免几百 MB / GB 文件一次性进入内存。
CHUNK_SIZE = 1024 * 1024


def asset_root(asset_id: str) -> Path:
    return settings.storage_dir / "assets" / asset_id


def source_dir(asset_id: str) -> Path:
    return asset_root(asset_id) / "source"


def artifacts_dir(asset_id: str) -> Path:
    return asset_root(asset_id) / "artifacts"


def safe_filename(filename: str) -> str:
    clean = Path(filename).name.strip() or "upload.bin"
    return re.sub(r"[^\w.\-]+", "_", clean, flags=re.UNICODE)


def detect_format(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in {".step", ".stp"}:
        return "step"
    if suffix in {".x_t", ".xmt_txt"}:
        return "parasolid_xt"
    if suffix == ".stl":
        return "stl"
    if suffix in {".glb", ".gltf"}:
        return suffix.removeprefix(".")
    if suffix in {".sldprt", ".sldasm"}:
        return "solidworks"
    return "unknown"


async def persist_upload(upload: UploadFile, asset_id: str) -> tuple[Path, int, str]:
    """把上传文件分块保存到磁盘。

    这一层只负责“接收并保存源文件”，不做 CAD 解析或转换。
    大文件转换耗时很长，必须交给后台 job，否则 HTTP 请求会超时。
    """
    filename = safe_filename(upload.filename or "upload.bin")
    target_dir = source_dir(asset_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / filename
    size = 0

    with target.open("wb") as output:
        while chunk := await upload.read(CHUNK_SIZE):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                raise ValueError("Upload exceeds configured maximum size.")
            # 分块写入：上传 1GB 文件时，内存里也只保留当前 chunk。
            output.write(chunk)

    return target, size, filename


def new_id() -> str:
    return uuid4().hex
