from __future__ import annotations

import math
import struct
from pathlib import Path
from typing import Any

from app.services.metadata_extractors.common import bounds_dict


def extract_stl_metadata(source: Path) -> dict[str, Any]:
    """提取 STL 网格统计信息。

    STL 有两种常见形式：
    - binary：二进制，更常见、更小；
    - ascii：纯文本，可直接打开看。

    两种格式都只描述三角网格，不包含 STEP 那种精确曲面/B-Rep 拓扑。
    """

    encoding = detect_stl_encoding(source)
    if encoding == "binary":
        return extract_binary_stl_metadata(source)
    return extract_ascii_stl_metadata(source)


def detect_stl_encoding(source: Path) -> str:
    """判断 STL 是二进制还是 ASCII。

    二进制 STL 的文件大小有固定公式：
        80 字节头 + 4 字节三角面数量 + 三角面数量 * 50 字节

    如果文件大小刚好匹配，就基本可以认为它是 binary STL。
    """

    size = source.stat().st_size
    with source.open("rb") as file:
        header = file.read(84)
    if len(header) >= 84:
        triangle_count = struct.unpack("<I", header[80:84])[0]
        if 84 + triangle_count * 50 == size:
            return "binary"
    return "ascii"


def extract_binary_stl_metadata(source: Path) -> dict[str, Any]:
    """读取二进制 STL。

    struct.unpack 是 Python 读取二进制结构的常用工具。
    "<I" 表示小端序 unsigned int，用来读三角面数量。
    "<12fH" 表示 12 个 float + 1 个 unsigned short，对应一个三角面记录。
    """

    with source.open("rb") as file:
        header = file.read(80)
        triangle_count = struct.unpack("<I", file.read(4))[0]
        min_point = [math.inf, math.inf, math.inf]
        max_point = [-math.inf, -math.inf, -math.inf]

        # 二进制 STL 每个三角面固定 50 字节，适合流式统计，不需要一次性读入内存。
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
    """读取 ASCII STL。

    ASCII STL 类似：
        facet normal ...
          vertex x y z
          vertex x y z
          vertex x y z
        endfacet

    所以这里通过 facet normal 统计三角面，通过 vertex 统计顶点引用和包围盒。
    """

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
