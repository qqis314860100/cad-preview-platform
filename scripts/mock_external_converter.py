#!/usr/bin/env python3.11
"""外部 CAD 转换器 mock。

这个脚本不做真实 CAD 解析，只生成一个简单 GLB。
用途：在没有 CAD Exchanger / HOOPS / APS 时，验证外部转换器命令链路是否打通。
"""

from __future__ import annotations

import argparse
from pathlib import Path

import trimesh


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="源 CAD 文件路径。mock 不会真正解析它。")
    parser.add_argument("--output", required=True, help="输出 GLB 路径。")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # 用一个盒子代表“转换成功的预览产物”。
    # 真实转换器应该在这里输出源 CAD 对应的 GLB 或 3D Tiles。
    mesh = trimesh.creation.box(extents=(20, 12, 8))
    mesh.visual.face_colors = [80, 120, 220, 255]
    output.write_bytes(trimesh.Scene(mesh).export(file_type="glb"))


if __name__ == "__main__":
    main()

