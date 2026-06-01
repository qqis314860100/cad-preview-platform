from __future__ import annotations

from pathlib import Path
from shutil import copy2

from app.services.converters.base import ConversionArtifact, ConversionResult


class PassthroughGlbConverter:
    name = "passthrough-glb"
    supported_formats = {"glb"}

    def convert(self, source: Path, artifact_dir: Path) -> ConversionResult:
        """GLB 本来就是浏览器可预览产物，直接复制到 artifacts 目录。"""

        target = artifact_dir / source.name
        target.parent.mkdir(parents=True, exist_ok=True)
        copy2(source, target)
        return ConversionResult(
            status="completed",
            message="GLB source copied as preview artifact.",
            artifacts=[
                ConversionArtifact(
                    kind="glb",
                    path=target,
                    metadata={"converter": self.name, "sourceFormat": "glb"},
                )
            ],
        )

