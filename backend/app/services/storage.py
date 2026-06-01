from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile

from app.core.config import settings


# 每次只读 1MB，避免几百 MB / GB 文件一次性进入内存。
CHUNK_SIZE = 1024 * 1024


def asset_root(asset_id: str) -> Path:
    # 每个上传文件都有自己的目录，避免不同用户/不同文件的源文件和产物混在一起。
    # 目录结构大致是：backend/storage/assets/{asset_id}/...
    return settings.storage_dir / "assets" / asset_id


def source_dir(asset_id: str) -> Path:
    # source 目录只放用户上传的原始文件。
    return asset_root(asset_id) / "source"


def artifacts_dir(asset_id: str) -> Path:
    # artifacts 目录只放后端生成的结果，例如 GLB、tileset.json、metadata.json。
    return asset_root(asset_id) / "artifacts"


def safe_filename(filename: str) -> str:
    """把用户上传的文件名清理成相对安全的文件名。

    用户传来的文件名不能直接信任，例如可能包含路径分隔符。
    Path(filename).name 会去掉路径，只保留最后的文件名；
    正则会把奇怪字符替换成下划线，降低落盘风险。
    """

    clean = Path(filename).name.strip() or "upload.bin"
    return re.sub(r"[^\w.\-]+", "_", clean, flags=re.UNICODE)


def detect_format(filename: str) -> str:
    """根据文件后缀识别格式。

    这是轻量识别，不是严格魔数检测。它的作用是选择转换器和 metadata 提取器。
    如果未来要做生产级校验，可以在这里增加文件头检查和 MIME 白名单。
    """

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
        # await upload.read(...) 说明这里是异步读取上传流。
        # FastAPI 可以在等待 I/O 时处理其他请求，比同步阻塞更适合 Web 服务。
        while chunk := await upload.read(CHUNK_SIZE):
            size += len(chunk)
            if size > settings.max_upload_bytes:
                raise ValueError("Upload exceeds configured maximum size.")
            # 分块写入：上传 1GB 文件时，内存里也只保留当前 chunk。
            output.write(chunk)

    return target, size, filename


def new_id() -> str:
    # uuid4 基本可以理解成“生成一个足够随机的字符串 id”。
    # hex 去掉了横线，更适合作为目录名、数据库主键、URL 参数。
    return uuid4().hex
