from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.services.metadata_extractors.common import compact_text, read_text_prefix


# STEP 文件是一种文本格式，里面常见语句长这样：
#   #123 = CARTESIAN_POINT('', (1.0, 2.0, 3.0));
# 下面这些正则只做“轻量统计”，不是完整 STEP 解析器。
STEP_ENTITY_RE = re.compile(r"#\d+\s*=\s*([A-Z0-9_]+)\s*\(", re.IGNORECASE)
STEP_COLOUR_RE = re.compile(
    r"COLOUR_RGB\s*\(\s*'((?:''|[^'])*)'\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)",
    re.IGNORECASE,
)
STEP_PRODUCT_RE = re.compile(r"PRODUCT\s*\(\s*'((?:''|[^'])*)'", re.IGNORECASE)
STEP_STRING_RE = re.compile(r"'((?:''|[^'])*)'")


def extract_step_metadata(source: Path) -> dict[str, Any]:
    """提取 STEP 文件里的可读结构化信息。

    注意：这里不重建 B-Rep 几何，只读取文本里容易安全提取的信息。
    真正把 STEP 曲面三角化成 GLB，是 converter 的职责。
    """

    # HEADER 通常在文件开头，所以只读前 4MB 就够了，避免大文件全部进内存。
    text_prefix = read_text_prefix(source, 4 * 1024 * 1024)
    header_text = extract_step_header_text(text_prefix)

    # DATA 区里的实体可能分布在整个文件，所以这里用逐行扫描。
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


def extract_step_header_text(text: str) -> str:
    """从 STEP 文本里截取 HEADER 段。"""

    match = re.search(r"HEADER\s*;(.*?)ENDSEC\s*;", text, flags=re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else ""


def extract_step_strings(header_text: str, call_name: str) -> list[str]:
    """提取 HEADER 函数调用里的字符串参数。

    例如 FILE_SCHEMA(('AP242...')) 会被提取成 AP242...。
    STEP 字符串里两个单引号代表一个真实单引号，所以后面会 decode。
    """

    pattern = re.compile(rf"{re.escape(call_name)}\s*\((.*?)\)\s*;", re.IGNORECASE | re.DOTALL)
    match = pattern.search(header_text)
    if not match:
        return []
    return [decode_step_string(item) for item in STEP_STRING_RE.findall(match.group(1))]


def scan_step_entities(source: Path) -> tuple[Counter[str], list[dict[str, Any]], list[str]]:
    """扫描 STEP DATA 区的常见信息。

    Counter 类似一个专门计数的 dict：
        entities["CARTESIAN_POINT"] += 1

    返回三类数据：
    - 实体类型统计；
    - COLOUR_RGB 颜色；
    - PRODUCT 产品名。
    """

    entities: Counter[str] = Counter()
    colors: list[dict[str, Any]] = []
    products: list[str] = []
    statement = ""

    with source.open("rt", encoding="utf-8", errors="replace") as file:
        for line in file:
            # STEP 的一条语句可能跨多行，这里先把行拼成 statement，
            # 直到看到分号 ; 才当作一条完整语句处理。
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
    """还原 STEP 字符串里的转义单引号。"""

    return value.replace("''", "'")
