from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass(frozen=True)
class ConversionArtifact:
    """转换器生成的单个预览产物，例如 GLB 或 tileset.json。"""

    kind: str
    path: Path
    metadata: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ConversionResult:
    """转换结果。

    completed 表示已生成可预览产物。
    blocked 表示源文件已接收，但当前环境缺少合适的 CAD 转换器。
    """

    status: str
    message: str
    artifacts: list[ConversionArtifact] = field(default_factory=list)


class Converter(Protocol):
    """所有 CAD 转换器都遵守这个最小接口。"""

    name: str
    supported_formats: set[str]

    def convert(self, source: Path, artifact_dir: Path) -> ConversionResult:
        """把源文件转换成浏览器可加载的预览产物。"""

