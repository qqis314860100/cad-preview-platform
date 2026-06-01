from __future__ import annotations

import re
from pathlib import Path


DEFAULT_RGB = (0.72, 0.74, 0.72)


def extract_step_primary_rgb(path: Path) -> tuple[float, float, float]:
    """从 STEP 文本里提取主颜色。

    很多 STEP 文件会把外观颜色写在 COLOUR_RGB / FILL_AREA_STYLE_COLOUR
    这一类 presentation 实体里。这里先做“主色恢复”，后续如果要做到
    每个零件/每个面的颜色，需要进一步建立 face -> style 的映射。
    """

    text = path.read_text(encoding="utf-8", errors="replace")
    rgb_by_id: dict[str, tuple[float, float, float]] = {}
    for match in re.finditer(
        r"#(\d+)\s*=\s*COLOUR_RGB\s*\([^,]*,\s*([0-9.+\-Ee]+)\s*,\s*([0-9.+\-Ee]+)\s*,\s*([0-9.+\-Ee]+)\s*\)",
        text,
        re.I | re.S,
    ):
        rgb_by_id[match.group(1)] = (
            float(match.group(2)),
            float(match.group(3)),
            float(match.group(4)),
        )

    if not rgb_by_id:
        return DEFAULT_RGB

    usage = {ident: 0 for ident in rgb_by_id}
    for match in re.finditer(r"FILL_AREA_STYLE_COLOUR\s*\([^)]*#(\d+)\s*\)", text, re.I | re.S):
        ident = match.group(1)
        if ident in usage:
            usage[ident] += 1

    best_id = max(rgb_by_id, key=lambda ident: (usage[ident], sum(rgb_by_id[ident])))
    return rgb_by_id[best_id]


def rgba255(rgb: tuple[float, float, float], alpha: int = 255) -> list[int]:
    return [max(0, min(255, round(channel * 255))) for channel in rgb] + [alpha]

