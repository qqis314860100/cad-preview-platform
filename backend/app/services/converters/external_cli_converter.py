from __future__ import annotations

from pathlib import Path

from app.services.converters.base import ConversionResult


class ExternalCliConverter:
    """商业/外部转换器的占位适配器。

    后续接 CAD Exchanger、HOOPS Exchange、Autodesk APS 或内部转换服务时，
    可以在这里封装命令行调用、鉴权、重试和日志采集。
    """

    name = "external-cli"
    supported_formats = {"parasolid_xt", "solidworks"}

    def convert(self, source: Path, artifact_dir: Path) -> ConversionResult:
        return ConversionResult(
            status="blocked",
            message=(
                f"{source.suffix or 'source'} requires an external CAD converter "
                "to generate GLB or 3D Tiles."
            ),
        )

