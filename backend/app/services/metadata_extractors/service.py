from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.services.metadata_extractors.glb import extract_glb_metadata
from app.services.metadata_extractors.step import extract_step_metadata
from app.services.metadata_extractors.stl import extract_stl_metadata
from app.services.metadata_extractors.xt import extract_xt_metadata


def extract_structured_metadata(asset: dict[str, Any], source: Path) -> dict[str, Any]:
    """提取源 CAD 文件的结构化信息。

    这一步只做“读懂文件里容易安全读取的信息”，不会尝试重建完整 B-Rep。
    预览几何仍然交给转换器；这里生成的是给业务、搜索、排查问题看的 metadata.json。
    """

    metadata = base_metadata(asset)
    file_format = str(asset["format"])

    try:
        fill_format_details(metadata, file_format, source)
    except Exception as exc:  # 提取失败不能阻断上传链路，错误也写进 JSON 方便排查。
        metadata["summary"]["readable"] = False
        metadata["details"]["error"] = {"message": str(exc)}
        metadata["limitations"].append("结构化提取失败，但源文件仍已保存，可继续尝试外部转换。")

    return metadata


def write_metadata_artifact(asset: dict[str, Any], source: Path, artifact_dir: Path) -> Path:
    """生成 metadata.json 文件，并返回它在 artifacts 目录里的路径。"""

    artifact_dir.mkdir(parents=True, exist_ok=True)
    target = artifact_dir / "metadata.json"
    data = extract_structured_metadata(asset, source)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def base_metadata(asset: dict[str, Any]) -> dict[str, Any]:
    return {
        "schemaVersion": "1.0",
        "source": {
            "assetId": asset["id"],
            "filename": asset["filename"],
            "format": asset["format"],
            "sizeBytes": int(asset["size_bytes"]),
            "extractedAt": datetime.now(UTC).isoformat(),
        },
        "summary": {
            "readable": True,
            "fullBrepGeometryExtracted": False,
            "geometryKind": "unknown",
            "note": "结构化数据用于识别文件内容；完整几何预览仍依赖 GLB 或 3D Tiles 转换产物。",
        },
        "details": {},
        "limitations": [],
    }


def fill_format_details(metadata: dict[str, Any], file_format: str, source: Path) -> None:
    # 各格式的读取规则放在独立模块里，新增格式时只需要补一个 extractor。
    if file_format == "stl":
        metadata["details"]["stl"] = extract_stl_metadata(source)
        metadata["summary"]["geometryKind"] = "mesh"
        metadata["summary"]["note"] = "STL 本身就是三角网格，可直接统计网格结构并转换为 GLB。"
        return

    if file_format == "step":
        metadata["details"]["step"] = extract_step_metadata(source)
        metadata["summary"]["geometryKind"] = "brep_source"
        metadata["limitations"].append("STEP 的 B-Rep 拓扑和精确曲面没有在 metadata.json 中完整展开。")
        return

    if file_format == "parasolid_xt":
        metadata["details"]["parasolidXt"] = extract_xt_metadata(source)
        metadata["limitations"].append("Parasolid XT 是专有 CAD 内核格式，完整几何需要 Parasolid 兼容转换器。")
        return

    if file_format == "glb":
        metadata["details"]["glb"] = extract_glb_metadata(source)
        metadata["summary"]["geometryKind"] = "mesh_scene"
        metadata["summary"]["note"] = "GLB 已经是浏览器可加载的图形产物。"
        return

    if file_format == "solidworks":
        metadata["details"]["solidworks"] = {
            "filenameSuffix": source.suffix.lower(),
            "requiresExternalConverter": True,
        }
        metadata["limitations"].append("SolidWorks 源文件需要商业转换器或 SolidWorks 自动化服务才能提取几何。")
        return

    metadata["summary"]["readable"] = False
    metadata["limitations"].append("当前版本还没有该格式的结构化提取规则。")
