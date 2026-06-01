from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any


def extract_xt_metadata(source: Path) -> dict[str, Any]:
    """提取 Parasolid XT 的可读片段和粗略统计。

    重点提醒：
    X_T 是 Parasolid 的专有格式。这里不是完整解析器，只做“能明文看到什么”的
    辅助提取。完整几何重建仍需要 Parasolid 兼容内核或商业转换器。
    """

    preview = []
    line_count = 0
    numeric_token_count = 0
    keyword_counts: Counter[str] = Counter()

    # keyword_pattern 用来抓像 transmit、unknown、body 这类英文关键词。
    # number_pattern 用来粗略估计文件里有多少数字 token，帮助判断几何数据规模。
    keyword_pattern = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{2,}\b")
    number_pattern = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[Ee][-+]?\d+)?")

    with source.open("rt", encoding="utf-8", errors="replace") as file:
        for line in file:
            line_count += 1
            if len(preview) < 80:
                # 只保留前 80 行给前端展示，避免把大文件内容塞进 metadata.json。
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
