from __future__ import annotations

from pathlib import Path

from app.models.schemas import AssetStatus, ArtifactKind, JobStatus
from app.services import repository
from app.services.stl_to_glb import convert_stl_to_glb
from app.services.storage import artifacts_dir, new_id


def run_conversion(job_id: str, asset_id: str) -> None:
    """执行单个转换任务。

    当前版本先实现 STL -> GLB，用来验证“后台转换 + 产物分发”的主链路。
    STEP、X_T、SolidWorks 会进入 blocked 状态，表示需要外部 CAD 转换器接入。
    """
    asset = repository.get_asset(asset_id)
    source = Path(asset["source_path"])
    file_format = asset["format"]

    repository.update_asset_status(asset_id, AssetStatus.processing)
    repository.update_job(job_id, JobStatus.processing, 0.1, "Conversion started.")

    try:
        if file_format == "stl":
            repository.update_job(job_id, JobStatus.processing, 0.35, "Converting STL to GLB artifact.")
            target = artifacts_dir(asset_id) / f"{source.stem}.glb"
            # GLB 是浏览器友好的二进制 3D 格式，比把 mesh JSON 发给前端更适合大文件。
            metadata = convert_stl_to_glb(source, target)
            repository.insert_artifact(
                artifact_id=new_id(),
                asset_id=asset_id,
                kind=ArtifactKind.glb,
                filename=target.name,
                path=target,
                metadata=metadata,
            )
            repository.update_asset_status(asset_id, AssetStatus.ready)
            repository.update_job(job_id, JobStatus.completed, 1.0, "Preview artifact is ready.")
            return

        if file_format in {"step", "parasolid_xt", "solidworks"}:
            # 这些格式需要 CAD 内核或商业转换器。这里明确告诉前端“已接收，但缺转换器”。
            repository.update_asset_status(asset_id, AssetStatus.blocked)
            repository.update_job(
                job_id,
                JobStatus.blocked,
                1.0,
                f"{file_format} requires an external CAD converter to generate GLB or 3D Tiles.",
            )
            return

        if file_format in {"glb", "gltf"}:
            target = artifacts_dir(asset_id) / source.name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
            repository.insert_artifact(
                artifact_id=new_id(),
                asset_id=asset_id,
                kind=ArtifactKind.glb if file_format == "glb" else ArtifactKind.metadata,
                filename=target.name,
                path=target,
                metadata={"sourceFormat": file_format},
            )
            repository.update_asset_status(asset_id, AssetStatus.ready)
            repository.update_job(job_id, JobStatus.completed, 1.0, "Preview artifact is ready.")
            return

        repository.update_asset_status(asset_id, AssetStatus.blocked)
        repository.update_job(job_id, JobStatus.blocked, 1.0, "Unsupported source format.")
    except Exception as exc:
        repository.update_asset_status(asset_id, AssetStatus.failed)
        repository.update_job(job_id, JobStatus.failed, 1.0, f"Conversion failed: {exc}")
