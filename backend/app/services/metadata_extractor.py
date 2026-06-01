from __future__ import annotations

import json
import math
import re
import struct
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


STEP_ENTITY_RE = re.compile(r"#\d+\s*=\s*([A-Z0-9_]+)\s*\(", re.IGNORECASE)
STEP_COLOUR_RE = re.compile(
    r"COLOUR_RGB\s*\(\s*'((?:''|[^'])*)'\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)",
    re.IGNORECASE,
)
STEP_PRODUCT_RE = re.compile(r"PRODUCT\s*\(\s*'((?:''|[^'])*)'", re.IGNORECASE)
STEP_STRING_RE = re.compile(r"'((?:''|[^'])*)'")


def extract_structured_metadata(asset: dict[str, Any], source: Path) -> dict[str, Any]:
    """提取源 CAD 文件的结构化信息。

    这一步只做“读懂文件里容易安全读取的信息”，不会尝试重建完整 B-Rep。
    预览几何仍然交给转换器；这里生成的是给业务、搜索、排查问题看的 metadata.json。
    """

    base: dict[str, Any] = {
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

    file_format = str(asset["format"])
    try:
        if file_format == "stl":
            base["details"]["stl"] = extract_stl_metadata(source)
            base["summary"]["geometryKind"] = "mesh"
            base["summary"]["note"] = "STL 本身就是三角网格，可直接统计网格结构并转换为 GLB。"
        elif file_format == "step":
            base["details"]["step"] = extract_step_metadata(source)
            base["summary"]["geometryKind"] = "brep_source"
            base["limitations"].append("STEP 的 B-Rep 拓扑和精确曲面没有在 metadata.json 中完整展开。")
        elif file_format == "parasolid_xt":
            base["details"]["parasolidXt"] = extract_xt_metadata(source)
            base["limitations"].append("Parasolid XT 是专有 CAD 内核格式，完整几何需要 Parasolid 兼容转换器。")
        elif file_format == "glb":
            base["details"]["glb"] = extract_glb_metadata(source)
            base["summary"]["geometryKind"] = "mesh_scene"
            base["summary"]["note"] = "GLB 已经是浏览器可加载的图形产物。"
        elif file_format == "solidworks":
            base["details"]["solidworks"] = {
                "filenameSuffix": source.suffix.lower(),
                "requiresExternalConverter": True,
            }
            base["limitations"].append("SolidWorks 源文件需要商业转换器或 SolidWorks 自动化服务才能提取几何。")
        else:
            base["summary"]["readable"] = False
            base["limitations"].append("当前版本还没有该格式的结构化提取规则。")
    except Exception as exc:  # 提取失败不能阻断上传链路，错误也写进 JSON 方便排查。
        base["summary"]["readable"] = False
        base["details"]["error"] = {"message": str(exc)}
        base["limitations"].append("结构化提取失败，但源文件仍已保存，可继续尝试外部转换。")

    return base


def write_metadata_artifact(asset: dict[str, Any], source: Path, artifact_dir: Path) -> Path:
    """生成 metadata.json 文件，并返回它在 artifacts 目录里的路径。"""

    artifact_dir.mkdir(parents=True, exist_ok=True)
    target = artifact_dir / "metadata.json"
    data = extract_structured_metadata(asset, source)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def extract_stl_metadata(source: Path) -> dict[str, Any]:
    encoding = detect_stl_encoding(source)
    if encoding == "binary":
        return extract_binary_stl_metadata(source)
    return extract_ascii_stl_metadata(source)


def detect_stl_encoding(source: Path) -> str:
    size = source.stat().st_size
    with source.open("rb") as file:
        header = file.read(84)
    if len(header) >= 84:
        triangle_count = struct.unpack("<I", header[80:84])[0]
        if 84 + triangle_count * 50 == size:
            return "binary"
    return "ascii"


def extract_binary_stl_metadata(source: Path) -> dict[str, Any]:
    with source.open("rb") as file:
        header = file.read(80)
        triangle_count = struct.unpack("<I", file.read(4))[0]
        min_point = [math.inf, math.inf, math.inf]
        max_point = [-math.inf, -math.inf, -math.inf]

        # 二进制 STL 每个三角面固定 50 字节：法线 12 + 三个顶点 36 + 属性 2。
        for _ in range(triangle_count):
            record = file.read(50)
            if len(record) < 50:
                break
            values = struct.unpack("<12fH", record)
            for offset in (3, 6, 9):
                point = values[offset : offset + 3]
                for axis, value in enumerate(point):
                    min_point[axis] = min(min_point[axis], float(value))
                    max_point[axis] = max(max_point[axis], float(value))

    return {
        "encoding": "binary",
        "headerText": header.decode("utf-8", errors="replace").strip("\x00 ").strip(),
        "triangleCount": int(triangle_count),
        "vertexReferenceCount": int(triangle_count * 3),
        "bounds": bounds_dict(min_point, max_point),
    }


def extract_ascii_stl_metadata(source: Path) -> dict[str, Any]:
    triangle_count = 0
    vertex_reference_count = 0
    solid_name = ""
    min_point = [math.inf, math.inf, math.inf]
    max_point = [-math.inf, -math.inf, -math.inf]

    with source.open("rt", encoding="utf-8", errors="replace") as file:
        for line in file:
            stripped = line.strip()
            if stripped.startswith("solid ") and not solid_name:
                solid_name = stripped.removeprefix("solid ").strip()
            if stripped.startswith("facet normal"):
                triangle_count += 1
            if stripped.startswith("vertex "):
                parts = stripped.split()
                if len(parts) >= 4:
                    vertex_reference_count += 1
                    point = [float(parts[1]), float(parts[2]), float(parts[3])]
                    for axis, value in enumerate(point):
                        min_point[axis] = min(min_point[axis], value)
                        max_point[axis] = max(max_point[axis], value)

    return {
        "encoding": "ascii",
        "solidName": solid_name,
        "triangleCount": triangle_count,
        "vertexReferenceCount": vertex_reference_count,
        "bounds": bounds_dict(min_point, max_point),
    }


def extract_step_metadata(source: Path) -> dict[str, Any]:
    text_prefix = read_text_prefix(source, 4 * 1024 * 1024)
    header_text = extract_step_header_text(text_prefix)
    entities, colors, products = scan_step_entities(source)
    return {
        "header": {
            "fileDescription": extract_step_strings(header_text, "FILE_DESCRIPTION"),
            "fileName": extract_step_strings(header_text, "FILE_NAME"),
            "fileSchema": extract_step_strings(header_text, "FILE_SCHEMA"),
            "rawPreview": compact_text(header_text, 4000),
        },
        "entities": {
            "total": sum(entities.values()),
            "topTypes": [{"type": name, "count": count} for name, count in entities.most_common(20)],
        },
        "colors": colors[:50],
        "products": products[:50],
    }


def read_text_prefix(source: Path, max_bytes: int) -> str:
    with source.open("rb") as file:
        return file.read(max_bytes).decode("utf-8", errors="replace")


def extract_step_header_text(text: str) -> str:
    match = re.search(r"HEADER\s*;(.*?)ENDSEC\s*;", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_step_strings(header_text: str, call_name: str) -> list[str]:
    pattern = re.compile(rf"{re.escape(call_name)}\s*\((.*?)\)\s*;", re.IGNORECASE | re.DOTALL)
    match = pattern.search(header_text)
    if not match:
        return []
    return [decode_step_string(item) for item in STEP_STRING_RE.findall(match.group(1))]


def scan_step_entities(source: Path) -> tuple[Counter[str], list[dict[str, Any]], list[str]]:
    entities: Counter[str] = Counter()
    colors: list[dict[str, Any]] = []
    products: list[str] = []
    statement = ""

    with source.open("rt", encoding="utf-8", errors="replace") as file:
        for line in file:
            statement += line.strip()
            if ";" not in statement:
                continue

            for entity_name in STEP_ENTITY_RE.findall(statement):
                entities[entity_name.upper()] += 1

            color_match = STEP_COLOUR_RE.search(statement)
            if color_match:
                colors.append(
                    {
                        "name": decode_step_string(color_match.group(1)),
                        "rgb": [float(color_match.group(index)) for index in (2, 3, 4)],
                    }
                )

            product_match = STEP_PRODUCT_RE.search(statement)
            if product_match:
                products.append(decode_step_string(product_match.group(1)))

            statement = ""

    return entities, colors, sorted(set(products))


def decode_step_string(value: str) -> str:
    return value.replace("''", "'")


def extract_xt_metadata(source: Path) -> dict[str, Any]:
    preview = []
    line_count = 0
    numeric_token_count = 0
    keyword_counts: Counter[str] = Counter()
    keyword_pattern = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b")
    number_pattern = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?")

    with source.open("rt", encoding="utf-8", errors="replace") as file:
        for line in file:
            line_count += 1
            if len(preview) < 80:
                preview.append(line.rstrip("\n"))
            numeric_token_count += len(number_pattern.findall(line))
            keyword_counts.update(match.group(0).lower() for match in keyword_pattern.finditer(line))

    return {
        "textPreview": preview,
        "lineCount": line_count,
        "numericTokenEstimate": numeric_token_count,
        "topKeywords": [{"keyword": name, "count": count} for name, count in keyword_counts.most_common(20)],
        "requiresExternalConverter": True,
    }


def extract_glb_metadata(source: Path) -> dict[str, Any]:
    with source.open("rb") as file:
        header = file.read(12)
        if len(header) < 12:
            raise ValueError("GLB 文件头不完整。")
        magic, version, declared_length = struct.unpack("<4sII", header)
        if magic != b"glTF":
            raise ValueError("不是合法 GLB 文件。")

        chunk_headers = []
        first_json: dict[str, Any] | None = None
        while True:
            chunk_header = file.read(8)
            if not chunk_header:
                break
            if len(chunk_header) < 8:
                break
            chunk_length, chunk_type = struct.unpack("<II", chunk_header)
            chunk_type_text = chunk_type.to_bytes(4, "little").decode("ascii", errors="replace").strip()
            chunk_headers.append({"type": chunk_type_text, "length": chunk_length})
            payload = file.read(chunk_length)
            if first_json is None and chunk_type_text == "JSON":
                first_json = json.loads(payload.decode("utf-8").rstrip("\x00 "))

    return {
        "version": version,
        "declaredLength": declared_length,
        "chunks": chunk_headers,
        "sceneCount": len(first_json.get("scenes", [])) if first_json else None,
        "meshCount": len(first_json.get("meshes", [])) if first_json else None,
        "materialCount": len(first_json.get("materials", [])) if first_json else None,
    }


def bounds_dict(min_point: list[float], max_point: list[float]) -> dict[str, list[float]] | None:
    if any(math.isinf(value) for value in min_point + max_point):
        return None
    return {"min": min_point, "max": max_point}


def compact_text(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]
