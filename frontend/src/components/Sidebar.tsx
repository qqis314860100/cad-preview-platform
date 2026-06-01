import { CloudUpload } from "lucide-react";
import type { Asset, ConverterInfo, Job } from "../api/client";
import { formatBytes } from "../utils/format";
import { Metric, Progress } from "./ui";

interface SidebarProps {
  asset?: Asset;
  converters: ConverterInfo[];
  job?: Job;
  selectedFile: File | null;
  uploadProgress: number;
  onFileChange: (file: File | null) => void;
  onUpload: () => void;
}

export function Sidebar({
  asset,
  converters,
  job,
  selectedFile,
  uploadProgress,
  onFileChange,
  onUpload,
}: SidebarProps) {
  return (
    <aside className="rail">
      <div className="brand-lockup">
        <div className="brand-mark">CAD</div>
        <div>
          <h1>CAD 在线预览平台</h1>
          <p>大文件上传、后台转换、预览产物分发。</p>
        </div>
      </div>

      <section className="upload-panel">
        <label className="file-drop">
          <CloudUpload size={24} />
          <span>{selectedFile ? selectedFile.name : "选择 CAD 源文件"}</span>
          <input
            type="file"
            accept=".stl,.step,.stp,.x_t,.xmt_txt,.sldprt,.sldasm,.glb,.gltf"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          />
        </label>
        <button className="primary-action" disabled={!selectedFile} onClick={onUpload}>
          上传并创建任务
        </button>
        <Progress label="上传进度" value={uploadProgress} />
      </section>

      <section className="stat-stack">
        <Metric label="文件" value={asset?.filename ?? "-"} />
        <Metric label="格式" value={asset?.format ?? "-"} />
        <Metric label="大小" value={formatBytes(asset?.size_bytes)} />
        <Metric label="任务" value={job?.status ?? "idle"} />
      </section>

      <section className="converter-stack">
        <h3>转换器状态</h3>
        {converters.map((converter) => (
          <div className="converter-line" key={converter.name}>
            <span className={converter.available ? "dot ok" : "dot off"} />
            <div>
              <strong>{converter.name}</strong>
              <small>{converter.supported_formats.join(" / ")}</small>
              <p>{converter.message}</p>
            </div>
          </div>
        ))}
      </section>
    </aside>
  );
}
