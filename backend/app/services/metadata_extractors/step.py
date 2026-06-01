from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any

from app.services.metadata_extractors.common import compact_text, read_text_prefix


STEP_ENTITY_RE = re.compile(r"#\d+\s*=\s*([A-Z0-9_]+)\s*\(", re.IGNORECASE)
STEP_COLOUR_RE = re.compile(
    r"COLOUR_RGB\s*\(\s*'((?:''|[^'])*)'\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*,\s*([-+0-9.Ee]+)\s*\)",
    re.IGNORECASE,
)
STEP_PRODUCT_RE = re.compile(r"PRODUCT\s*\(\s*'((?:''|[^'])*)'", re.IGNORECASE)
STEP_STRING_RE = re.compile(r"'((?:''|[^'])*)'")


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
