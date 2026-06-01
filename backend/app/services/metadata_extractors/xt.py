from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


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
