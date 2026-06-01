import { Box } from "lucide-react";
import type { Artifact, Job } from "../api/client";
import { artifactUrl } from "../api/client";

export function ViewerPanel({ artifact, job }: { artifact?: Artifact; job?: Job }) {
  return (
    <section className="viewer-panel">
      {artifact?.kind === "glb" ? (
        <model-viewer
          src={artifactUrl(artifact.url)}
          camera-controls
          auto-rotate
          shadow-intensity="0.85"
          exposure="0.95"
        />
      ) : (
        <div className="viewer-empty">
          <Box size={42} />
          <p>{job?.message ?? "转换完成后，GLB 或 3D Tiles 预览产物会显示在这里。"}</p>
        </div>
      )}
    </section>
  );
}
