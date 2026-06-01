from __future__ import annotations

from app.services.converters.base import Converter
from app.services.converters.cadquery_step_converter import CadQueryStepConverter
from app.services.converters.external_cli_converter import ExternalCliConverter
from app.services.converters.passthrough_converter import PassthroughGlbConverter
from app.services.converters.stl_converter import StlConverter


CONVERTERS: list[Converter] = [
    StlConverter(),
    CadQueryStepConverter(),
    PassthroughGlbConverter(),
    ExternalCliConverter(),
]


def find_converter(file_format: str) -> Converter | None:
    """根据源文件格式选择转换器。

    业务流程只调用这个函数，不关心背后是开源库、商业 CLI 还是云服务。
    """

    for converter in CONVERTERS:
        if file_format in converter.supported_formats:
            return converter
    return None


def list_converter_status() -> list[dict]:
    """返回所有转换器状态，供前端和运维确认当前能力。"""

    return [
        {
            "name": converter.name,
            "supported_formats": sorted(converter.supported_formats),
            "available": converter.available(),
            "message": converter.status_message(),
        }
        for converter in CONVERTERS
    ]
