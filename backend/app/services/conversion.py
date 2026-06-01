from __future__ import annotations

from pathlib import Path

from app.models.schemas import AssetStatus, ArtifactKind, JobStatus
from app.services import repository
from app.services.converters.registry import find_converter
from app.services.metadata_extractor import write_metadata_artifact
from app.services.storage import artifacts_dir, new_id


def run_conversion(job_id: str, asset_id: str) -> None:
    """执行单个转换任务。

    这里不直接写具体格式的转换细节，而是交给 converter registry。
    这样后续接商业 CAD 转换器时，不需要改 HTTP 接口和 job 主流程。
    """
    asset = repository.get_asset(asset_id)
    source = Path(asset["source_path"])
    file_format = asset["format"]

    repository.update_asset_status(asset_id, AssetStatus.processing)
    repository.update_job(job_id, JobStatus.processing, 0.1, "Conversion started.")

    try:
        asset_artifacts_dir = artifacts_dir(asset_id)
        metadata_path = write_metadata_artifact(asset, source, asset_artifacts_dir)
        repository.insert_artifact(
            artifact_id=new_id(),
            asset_id=asset_id,
            kind=ArtifactKind.metadata,
            filename=metadata_path.name,
            path=metadata_path,
            metadata={
                "extractor": "built-in",
                "sourceFormat": file_format,
                "description": "上传源文件的结构化数据，供前端展示和业务检索使用。",
            },
        )
        repository.update_job(job_id, JobStatus.processing, 0.22, "结构化数据已提取。")

        converter = find_converter(file_format)
        if converter:
            repository.update_job(job_id, JobStatus.processing, 0.35, f"Running converter: {converter.name}.")
            result = converter.convert(source, asset_artifacts_dir)
            for artifact in result.artifacts:
                repository.insert_artifact(
                    artifact_id=new_id(),
                    asset_id=asset_id,
                    kind=ArtifactKind(artifact.kind),
                    filename=artifact.path.name,
                    path=artifact.path,
                    metadata=artifact.metadata,
                )

            if result.status == "completed":
                repository.update_asset_status(asset_id, AssetStatus.ready)
                repository.update_job(job_id, JobStatus.completed, 1.0, result.message)
                return

            repository.update_asset_status(asset_id, AssetStatus.blocked)
            repository.update_job(job_id, JobStatus.blocked, 1.0, result.message)
            return

        repository.update_asset_status(asset_id, AssetStatus.blocked)
        repository.update_job(job_id, JobStatus.blocked, 1.0, "Unsupported source format.")
    except Exception as exc:
        repository.update_asset_status(asset_id, AssetStatus.failed)
        repository.update_job(job_id, JobStatus.failed, 1.0, f"Conversion failed: {exc}")
