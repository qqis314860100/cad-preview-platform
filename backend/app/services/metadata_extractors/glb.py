from __future__ import annotations

import json
import struct
from pathlib import Path
from typing import Any


def extract_glb_metadata(source: Path) -> dict[str, Any]:
    with source.open("rb") as file:
        header = file.read(12)
        if len(header) < 12:
            raise ValueError("GLB 文件头不完整。")
        magic, version, declared_length = struct.unpack("<4sII", header)
        if magic != b"glTF":
            raise ValueError("不是合法 GLB 文件。")

        chunk_headers = []
        first_json: dict[str, Any] | None = None
        while True:
            chunk_header = file.read(8)
            if not chunk_header:
                break
            if len(chunk_header) < 8:
                break
            chunk_length, chunk_type = struct.unpack("<II", chunk_header)
            chunk_type_text = chunk_type.to_bytes(4, "little").decode("ascii", errors="replace").strip()
            chunk_headers.append({"type": chunk_type_text, "length": chunk_length})
            payload = file.read(chunk_length)
            if first_json is None and chunk_type_text == "JSON":
                first_json = json.loads(payload.decode("utf-8").rstrip("\x00 "))

    return {
        "version": version,
        "declaredLength": declared_length,
        "chunks": chunk_headers,
        "sceneCount": len(first_json.get("scenes", [])) if first_json else None,
        "meshCount": len(first_json.get("meshes", [])) if first_json else None,
        "materialCount": len(first_json.get("materials", [])) if first_json else None,
    }
