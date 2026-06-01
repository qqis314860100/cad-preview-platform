#!/usr/bin/env python3.11
"""项目烟雾检查。

这个脚本给非开发同学一个简单判断：
只要它通过，说明项目结构、关键文件和 Python 代码语法基本正常。
它不替代完整测试，但适合每次改完项目后快速跑一下。
"""

from __future__ import annotations

import py_compile
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FILES = [
    "README.md",
    "AGENTS.md",
    "docs/ARCHITECTURE.md",
    "docs/METADATA.md",
    "backend/app/main.py",
    "backend/app/api/routes.py",
    "frontend/src/App.tsx",
    "frontend/package.json",
]


def main() -> int:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).exists()]
    if missing:
        print("缺少关键文件：")
        for path in missing:
            print(f"  - {path}")
        return 1

    for path in sorted((ROOT / "backend" / "app").rglob("*.py")):
        py_compile.compile(str(path), doraise=True)

    print("烟雾检查通过：项目结构完整，后端 Python 语法正常。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
