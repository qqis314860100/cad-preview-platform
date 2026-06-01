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
    # 后台线程只拿到 id，不直接拿文件对象。
    # 因为上传请求已经结束，文件已落盘；后台任务需要从数据库重新找到源文件路径。
    asset = repository.get_asset(asset_id)
    source = Path(asset["source_path"])
    file_format = asset["format"]

    # 任务刚开始时，先把 asset 和 job 都标记为 processing。
    # 前端轮询 job 时，就能看到“正在处理”而不是一直停在 queued。
    repository.update_asset_status(asset_id, AssetStatus.processing)
    repository.update_job(job_id, JobStatus.processing, 0.1, "Conversion started.")

    try:
        asset_artifacts_dir = artifacts_dir(asset_id)

        # metadata.json 是轻量结构化数据，通常比几何转换快。
        # 先生成它的好处是：即使后面的 GLB 转换被阻塞，用户也能看到文件里读出了什么。
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

        # 根据格式寻找合适转换器：
        # - stl -> 内置 trimesh 转 GLB；
        # - step -> CadQuery/OCP 开发版转换；
        # - x_t / solidworks -> 外部命令转换器；
        # - glb -> 直接复制为产物。
        converter = find_converter(file_format)
        if converter:
            repository.update_job(job_id, JobStatus.processing, 0.35, f"Running converter: {converter.name}.")
            result = converter.convert(source, asset_artifacts_dir)

            # 一个转换器可能输出多个产物，例如：
            # - metadata.json
            # - model.glb
            # - tileset.json + 多个 b3dm/glb 分块
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
                # completed 表示至少已经生成一个可用预览产物。
                repository.update_asset_status(asset_id, AssetStatus.ready)
                repository.update_job(job_id, JobStatus.completed, 1.0, result.message)
                return

            # blocked 表示“任务逻辑正常，但当前环境缺少条件”。
            # 比如 X_T 文件需要外部 CAD 转换器，但用户还没配置。
            repository.update_asset_status(asset_id, AssetStatus.blocked)
            repository.update_job(job_id, JobStatus.blocked, 1.0, result.message)
            return

        # 没找到转换器，说明当前项目不知道这个格式怎么生成预览产物。
        repository.update_asset_status(asset_id, AssetStatus.blocked)
        repository.update_job(job_id, JobStatus.blocked, 1.0, "Unsupported source format.")
    except Exception as exc:
        # failed 表示真正异常，例如文件损坏、转换库报错、磁盘写入失败。
        # 原型里先把错误信息写入 job.message；生产环境还应写结构化日志。
        repository.update_asset_status(asset_id, AssetStatus.failed)
        repository.update_job(job_id, JobStatus.failed, 1.0, f"Conversion failed: {exc}")
