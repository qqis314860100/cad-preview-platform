from __future__ import annotations

import math
import re
from pathlib import Path


def read_text_prefix(source: Path, max_bytes: int) -> str:
    with source.open("rb") as file:
        return file.read(max_bytes).decode("utf-8", errors="replace")


def bounds_dict(min_point: list[float], max_point: list[float]) -> dict[str, list[float]] | None:
    if any(math.isinf(value) for value in min_point + max_point):
        return None
    return {"min": min_point, "max": max_point}


def compact_text(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit]
