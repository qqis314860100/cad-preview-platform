from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

from app.core.config import settings
from app.services.converters.base import ConversionArtifact, ConversionResult


class ExternalCliConverter:
    """商业/外部转换器的占位适配器。

    后续接 CAD Exchanger、HOOPS Exchange、Autodesk APS 或内部转换服务时，
    可以在这里封装命令行调用、鉴权、重试和日志采集。
    """

    name = "external-cli"
    supported_formats = {"parasolid_xt", "solidworks"}
    production_ready = True

    def available(self) -> bool:
        return bool(settings.external_converter_command.strip())

    def status_message(self) -> str:
        if self.available():
            return "外部 CAD 转换器命令已配置，可处理 X_T / SolidWorks 等专有格式。"
        return "未配置 CAD_EXTERNAL_CONVERTER_COMMAND，X_T / SolidWorks 暂不能自动转换。"

    def convert(self, source: Path, artifact_dir: Path) -> ConversionResult:
        """调用外部转换器生成预览产物。

        命令通过环境变量配置，而不是写死在代码里。原因很简单：
        不同团队可能用 CAD Exchanger、HOOPS、APS 本地代理或自研服务，
        但它们对平台来说都只是“输入源文件，输出 GLB/3D Tiles”。
        """

        if not self.available():
            return ConversionResult(
                status="blocked",
                message=(
                    f"{source.suffix or 'source'} requires an external CAD converter. "
                    "Set CAD_EXTERNAL_CONVERTER_COMMAND to enable this path."
                ),
            )

        artifact_dir.mkdir(parents=True, exist_ok=True)
        output_glb = artifact_dir / f"{source.stem}.glb"
        command = format_command(
            settings.external_converter_command,
            source=source,
            artifact_dir=artifact_dir,
            output_glb=output_glb,
        )

        completed = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True,
            timeout=settings.external_converter_timeout_seconds,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                "External CAD converter failed: "
                f"{completed.stderr[-2000:] or completed.stdout[-2000:] or completed.returncode}"
            )

        artifacts = collect_external_artifacts(artifact_dir, source.stem)
        if not artifacts:
            raise RuntimeError("External CAD converter finished but produced no GLB or 3D Tiles artifact.")

        return ConversionResult(
            status="completed",
            message="External CAD converter produced preview artifacts.",
            artifacts=artifacts,
        )


def format_command(template: str, *, source: Path, artifact_dir: Path, output_glb: Path) -> str:
    """把命令模板里的占位符替换成 shell 安全路径。"""

    values = {
        "source": shlex.quote(str(source)),
        "artifact_dir": shlex.quote(str(artifact_dir)),
        "output_glb": shlex.quote(str(output_glb)),
    }
    return template.format(**values)


def collect_external_artifacts(artifact_dir: Path, stem: str) -> list[ConversionArtifact]:
    artifacts: list[ConversionArtifact] = []
    glb = artifact_dir / f"{stem}.glb"
    if glb.exists():
        artifacts.append(
            ConversionArtifact(
                kind="glb",
                path=glb,
                metadata={"converter": "external-cli", "sourceFormat": "external"},
            )
        )

    for tileset in artifact_dir.rglob("tileset.json"):
        artifacts.append(
            ConversionArtifact(
                kind="tileset",
                path=tileset,
                metadata={"converter": "external-cli", "sourceFormat": "external"},
            )
        )
    return artifacts
