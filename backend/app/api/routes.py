from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.models.schemas import ArtifactOut, AssetOut, AssetStatus, ConverterOut, JobOut, JobStatus, UploadResponse
from app.services import repository
from app.services.converters.registry import list_converter_status
from app.services.storage import detect_format, new_id, persist_upload
from app.workers.queue import enqueue_conversion


router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/converters", response_model=list[ConverterOut])
def list_converters() -> list[ConverterOut]:
    """查看当前后端支持哪些转换器，以及它们是否可用。"""

    return [ConverterOut(**item) for item in list_converter_status()]


@router.post("/assets", response_model=UploadResponse)
async def upload_asset(file: UploadFile) -> UploadResponse:
    """上传源文件并创建转换任务。

    注意：这里不会同步转换 CAD 文件。接口只做三件事：
    1. 分块保存源文件；
    2. 写入 asset/job 记录；
    3. 把 job 丢给后台 worker。
    """
    asset_id = new_id()
    job_id = new_id()

    try:
        source_path, size_bytes, filename = await persist_upload(file, asset_id)
    except ValueError as exc:
        raise HTTPException(status_code=413, detail=str(exc)) from exc

    file_format = detect_format(filename)
    asset = repository.insert_asset(
        asset_id=asset_id,
        filename=filename,
        file_format=file_format,
        size_bytes=size_bytes,
        status=AssetStatus.queued,
        source_path=source_path,
    )
    job = repository.insert_job(
        job_id=job_id,
        asset_id=asset_id,
        status=JobStatus.queued,
        progress=0.0,
        message="Queued for conversion.",
    )
    # 真正的转换在后台执行，前端通过 /jobs/{job_id} 轮询状态。
    enqueue_conversion(job_id, asset_id)
    return UploadResponse(asset=AssetOut(**asset), job=JobOut(**job))


@router.get("/assets/{asset_id}", response_model=AssetOut)
def get_asset(asset_id: str) -> AssetOut:
    try:
        return AssetOut(**repository.get_asset(asset_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc


@router.get("/jobs/{job_id}", response_model=JobOut)
def get_job(job_id: str) -> JobOut:
    try:
        return JobOut(**repository.get_job(job_id))
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Job not found") from exc


@router.get("/assets/{asset_id}/artifacts", response_model=list[ArtifactOut])
def list_artifacts(asset_id: str) -> list[ArtifactOut]:
    try:
        repository.get_asset(asset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Asset not found") from exc
    return [artifact_out(row) for row in repository.list_artifacts(asset_id)]


@router.get("/artifacts/{asset_id}/{filename}")
def get_artifact_file(asset_id: str, filename: str) -> FileResponse:
    artifacts = repository.list_artifacts(asset_id)
    for artifact in artifacts:
        if artifact["filename"] == filename:
            path = Path(artifact["path"])
            if path.exists():
                return FileResponse(path)
    raise HTTPException(status_code=404, detail="Artifact not found")


def artifact_out(row: dict) -> ArtifactOut:
    # 前端拿到的是产物 URL。大模型不能通过 API JSON 内联返回。
    return ArtifactOut(
        id=row["id"],
        asset_id=row["asset_id"],
        kind=row["kind"],
        filename=row["filename"],
        url=f"/api/artifacts/{row['asset_id']}/{row['filename']}",
        size_bytes=row["size_bytes"],
        metadata=row["metadata"],
    )
