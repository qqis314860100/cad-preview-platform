from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from app.services.converters.base import ConversionArtifact, ConversionResult


class StlConverter:
    name = "stl-trimesh"
    supported_formats = {"stl"}

    def convert(self, source: Path, artifact_dir: Path) -> ConversionResult:
        """把 STL 网格转换成 GLB。

        STL 已经是三角网格，所以不需要 CAD 内核，只需要把它包装成
        浏览器更友好的 GLB 产物。
        """

        mesh = trimesh.load_mesh(source, force="mesh")
        if mesh.is_empty:
            raise RuntimeError("STL did not produce a mesh.")

        if not isinstance(mesh, trimesh.Trimesh):
            mesh = trimesh.util.concatenate(tuple(mesh.geometry.values()))

        mesh.remove_duplicate_faces()
        mesh.remove_unreferenced_vertices()
        mesh.fix_normals()

        target = artifact_dir / f"{source.stem}.glb"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(trimesh.Scene(mesh).export(file_type="glb"))

        bounds = mesh.bounds.tolist() if isinstance(mesh.bounds, np.ndarray) else mesh.bounds
        return ConversionResult(
            status="completed",
            message="STL converted to GLB preview artifact.",
            artifacts=[
                ConversionArtifact(
                    kind="glb",
                    path=target,
                    metadata={
                        "converter": self.name,
                        "triangleCount": int(len(mesh.faces)),
                        "vertexCount": int(len(mesh.vertices)),
                        "bounds": bounds,
                        "sourceFormat": "stl",
                    },
                )
            ],
        )

