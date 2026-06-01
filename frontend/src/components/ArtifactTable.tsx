import type { Artifact } from "../api/client";
import { formatBytes } from "../utils/format";

export function ArtifactTable({ artifacts }: { artifacts: Artifact[] }) {
  return (
    <section className="artifact-table">
      <div className="table-head">
        <span>类型</span>
        <span>文件</span>
        <span>大小</span>
        <span>元数据</span>
      </div>
      {artifacts.map((artifact) => (
        <div className="table-row" key={artifact.id}>
          <span>{artifact.kind}</span>
          <a href={artifact.url} target="_blank" rel="noreferrer">
            {artifact.filename}
          </a>
          <span>{formatBytes(artifact.size_bytes)}</span>
          <code>{JSON.stringify(artifact.metadata)}</code>
        </div>
      ))}
    </section>
  );
}
