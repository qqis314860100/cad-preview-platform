from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import trimesh


def convert_stl_to_glb(source: Path, target: Path) -> dict[str, Any]:
    """把 STL 网格转换成 GLB 预览文件。

    STL 已经是三角网格，所以可以本地转换。
    STEP/X_T/SolidWorks 不是简单网格，不能复用这个函数。
    """
    mesh = trimesh.load_mesh(source, force="mesh")
    if mesh.is_empty:
        raise RuntimeError("STL did not produce a mesh.")

    if not isinstance(mesh, trimesh.Trimesh):
        mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))

    mesh.remove_duplicate_faces()
    mesh.remove_unreferenced_vertices()
    mesh.fix_normals()

    scene = trimesh.Scene(mesh)
    target.parent.mkdir(parents=True, exist_ok=True)
    data = scene.export(file_type="glb")
    target.write_bytes(data)

    bounds = mesh.bounds.tolist() if isinstance(mesh.bounds, np.ndarray) else mesh.bounds
    return {
        "triangleCount": int(len(mesh.faces)),
        "vertexCount": int(len(mesh.vertices)),
        "bounds": bounds,
        "sourceFormat": "stl",
    }
