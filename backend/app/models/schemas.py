from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel


class AssetStatus(StrEnum):
    uploaded = "uploaded"
    queued = "queued"
    processing = "processing"
    ready = "ready"
    blocked = "blocked"
    failed = "failed"


class JobStatus(StrEnum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    blocked = "blocked"
    failed = "failed"


class ArtifactKind(StrEnum):
    glb = "glb"
    tileset = "tileset"
    metadata = "metadata"


class AssetOut(BaseModel):
    id: str
    filename: str
    format: str
    size_bytes: int
    status: AssetStatus
    created_at: str
    updated_at: str


class JobOut(BaseModel):
    id: str
    asset_id: str
    status: JobStatus
    progress: float
    message: str
    created_at: str
    updated_at: str


class ArtifactOut(BaseModel):
    id: str
    asset_id: str
    kind: ArtifactKind
    filename: str
    url: str
    size_bytes: int
    metadata: dict[str, Any]


class UploadResponse(BaseModel):
    asset: AssetOut
    job: JobOut


class ConverterOut(BaseModel):
    name: str
    supported_formats: list[str]
    available: bool
    message: str
