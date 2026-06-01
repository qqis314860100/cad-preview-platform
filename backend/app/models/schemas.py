from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class AssetStatus(StrEnum):
    """源文件状态。

    Asset 可以理解成“用户上传的原始 CAD 文件记录”。它描述文件本身现在处于
    什么阶段，类似前端状态机里的 status 字段。
    """

    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    ready = "ready"
    blocked = "blocked"
    failed = "failed"


class JobStatus(StrEnum):
    """后台任务状态。

    Job 描述“某个处理任务”的进度。一个 asset 可以对应一个转换 job。
    前端上传后不会一直等转换完成，而是拿 job_id 轮询这个状态。
    """

    queued = "queued"
    processing = "processing"
    completed = "completed"
    blocked = "blocked"
    failed = "failed"


class ArtifactKind(StrEnum):
    """转换或提取后生成的产物类型。

    这里的 artifact 类似前端构建后的 dist 文件：
    它不是源文件，而是浏览器或业务系统真正要消费的结果。
    """

    glb = "glb"
    tileset = "tileset"
    metadata = "metadata"


class AssetOut(BaseModel):
    """返回给前端的源文件信息。

    Pydantic BaseModel 很像 TypeScript interface + runtime 校验：
    它既声明字段类型，也会在 FastAPI 返回响应前帮我们做结构校验。
    """

    id: str
    filename: str
    format: str
    size_bytes: int
    status: AssetStatus
    created_at: str
    updated_at: str


class JobOut(BaseModel):
    """返回给前端的后台任务信息。"""

    id: str
    asset_id: str
    status: JobStatus
    progress: float
    message: str
    created_at: str
    updated_at: str


class ArtifactOut(BaseModel):
    """返回给前端的产物信息。

    注意这里给的是 url，不直接把 GLB 或 metadata 内容塞进接口响应。
    这样大文件预览可以走浏览器的文件加载能力，也方便以后接 CDN/对象存储。
    """

    id: str
    asset_id: str
    kind: ArtifactKind
    filename: str
    url: str
    size_bytes: int
    metadata: dict[str, Any]


class UploadResponse(BaseModel):
    """上传接口的返回值：同时告诉前端源文件记录和后台任务记录。"""

    asset: AssetOut
    job: JobOut


class ConverterOut(BaseModel):
    """转换器状态，用于前端展示当前环境能处理哪些格式。"""

    name: str
    supported_formats: list[str]
    available: bool
    message: str
