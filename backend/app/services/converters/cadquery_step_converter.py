from __future__ import annotations

from pathlib import Path

import numpy as np
import trimesh

from app.services.converters.base import ConversionArtifact, ConversionResult
from app.services.converters.colors import extract_step_primary_rgb, rgba255


class CadQueryStepConverter:
    name = "cadquery-ocp-step"
    supported_formats = {"step"}

    def convert(self, source: Path, artifact_dir: Path) -> ConversionResult:
        """开发版 STEP -> GLB 转换器。

        CadQuery/OCP 底层使用 OpenCascade，能把 STEP 的 B-Rep 几何三角化。
        这适合本地验证和中小文件 fallback；真正几百 MB / GB 级文件仍建议
        接 CAD Exchanger、HOOPS Exchange 或专门的 3D Tiles 生成服务。
        """

        try:
            from cadquery import importers
        except ImportError:
            return ConversionResult(
                status="blocked",
                message="STEP converter is not installed. Install CadQuery/OCP or configure an external CAD converter.",
                artifacts=[],
            )

        workplane = importers.importStep(str(source))
        vertices: list[list[float]] = []
        faces: list[list[int]] = []

        for shape in workplane.vals():
            shape_vertices, shape_faces = shape.tessellate(0.45, 0.25)
            offset = len(vertices)
            for vertex in shape_vertices:
                vertices.append([float(vertex.x), float(vertex.y), float(vertex.z)])
            for face in shape_faces:
                faces.append([int(face[0] + offset), int(face[1] + offset), int(face[2] + offset)])

        if not vertices or not faces:
            raise RuntimeError("STEP tessellation produced no mesh.")

        rgb = extract_step_primary_rgb(source)
        mesh = trimesh.Trimesh(
            vertices=np.asarray(vertices, dtype=np.float64),
            faces=np.asarray(faces, dtype=np.int64),
            process=True,
        )
        mesh.visual.face_colors = np.tile(np.asarray(rgba255(rgb), dtype=np.uint8), (len(mesh.faces), 1))
        mesh.fix_normals()

        target = artifact_dir / f"{source.stem}.glb"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(trimesh.Scene(mesh).export(file_type="glb"))

        return ConversionResult(
            status="completed",
            message="STEP tessellated with CadQuery/OCP and exported as GLB. Main STEP color was applied when present.",
            artifacts=[
                ConversionArtifact(
                    kind="glb",
                    path=target,
                    metadata={
                        "converter": self.name,
                        "triangleCount": int(len(mesh.faces)),
                        "vertexCount": int(len(mesh.vertices)),
                        "bounds": mesh.bounds.tolist(),
                        "sourceFormat": "step",
                        "materialColor": list(rgb),
                    },
                )
            ],
        )

