import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Box, CheckCircle2, CloudUpload, Database, FileArchive, Loader2 } from "lucide-react";
import { Artifact, Asset, Job, artifactUrl, getAsset, getJob, listArtifacts, uploadAsset } from "./api/client";

type UploadState = {
  asset?: Asset;
  job?: Job;
  artifacts: Artifact[];
  uploadProgress: number;
  error?: string;
};

const terminalStates = new Set(["completed", "blocked", "failed"]);

export function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>({ artifacts: [], uploadProgress: 0 });
  const primaryArtifact = useMemo(
    () => state.artifacts.find((artifact) => artifact.kind === "glb") ?? state.artifacts[0],
    [state.artifacts]
  );

  useEffect(() => {
    if (!state.job || terminalStates.has(state.job.status)) return;

    // 转换是后台任务，不会在上传请求里立刻完成。
    // 前端定时查询 job 状态，完成后再拉取预览产物列表。
    const timer = window.setInterval(async () => {
      try {
        const job = await getJob(state.job!.id);
        const asset = await getAsset(job.asset_id);
        const artifacts = terminalStates.has(job.status) ? await listArtifacts(job.asset_id) : state.artifacts;
        setState((current) => ({ ...current, job, asset, artifacts }));
      } catch (error) {
        setState((current) => ({ ...current, error: error instanceof Error ? error.message : String(error) }));
      }
    }, 1200);

    return () => window.clearInterval(timer);
  }, [state.job, state.artifacts]);

  async function submitUpload() {
    if (!selectedFile) return;
    setState({ artifacts: [], uploadProgress: 0 });
    try {
      const response = await uploadAsset(selectedFile, (sent, total) => {
        // 大文件上传可能持续很久，进度条能明确告诉用户“文件还在传”。
        setState((current) => ({ ...current, uploadProgress: total ? sent / total : 0 }));
      });
      setState({ asset: response.asset, job: response.job, artifacts: [], uploadProgress: 1 });
    } catch (error) {
      setState({ artifacts: [], uploadProgress: 0, error: error instanceof Error ? error.message : String(error) });
    }
  }

  return (
    <main className="app-shell">
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
              onChange={(event) => setSelectedFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <button className="primary-action" disabled={!selectedFile} onClick={submitUpload}>
            上传并创建任务
          </button>
          <Progress label="上传进度" value={state.uploadProgress} />
        </section>

        <section className="stat-stack">
          <Metric label="文件" value={state.asset?.filename ?? "-"} />
          <Metric label="格式" value={state.asset?.format ?? "-"} />
          <Metric label="大小" value={formatBytes(state.asset?.size_bytes)} />
          <Metric label="任务" value={state.job?.status ?? "idle"} />
        </section>
      </aside>

      <section className="stage">
        <header className="stage-header">
          <div>
            <span className="eyebrow">产物优先预览</span>
            <h2>{state.asset?.filename ?? "上传一个 CAD 文件"}</h2>
          </div>
          <StatusPill job={state.job} />
        </header>

        <section className="viewer-panel">
          {primaryArtifact?.kind === "glb" ? (
            <model-viewer
              src={artifactUrl(primaryArtifact.url)}
              camera-controls
              auto-rotate
              shadow-intensity="0.85"
              exposure="0.95"
            />
          ) : (
            <div className="viewer-empty">
              <Box size={42} />
              <p>{state.job?.message ?? "转换完成后，GLB 或 3D Tiles 预览产物会显示在这里。"}</p>
            </div>
          )}
        </section>

        {state.error ? <p className="error-line">{state.error}</p> : null}

        <section className="dashboard-grid">
          <InfoCard
            icon={<Database size={18} />}
            title="任务说明"
            value={state.job?.message ?? "等待上传。"}
          />
          <InfoCard
            icon={<FileArchive size={18} />}
            title="预览产物"
            value={state.artifacts.length ? state.artifacts.map((item) => item.filename).join(", ") : "暂无"}
          />
          <InfoCard
            icon={<AlertTriangle size={18} />}
            title="大文件规则"
            value="请求只保存文件；转换、切片、压缩都在后台任务里执行。"
          />
        </section>

        <section className="artifact-table">
          <div className="table-head">
            <span>类型</span>
            <span>文件</span>
            <span>大小</span>
            <span>元数据</span>
          </div>
          {state.artifacts.map((artifact) => (
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
      </section>
    </main>
  );
}

function Progress({ label, value }: { label: string; value: number }) {
  return (
    <div className="progress-block">
      <div>
        <span>{label}</span>
        <strong>{Math.round(value * 100)}%</strong>
      </div>
      <div className="progress-track">
        <i style={{ width: `${Math.round(value * 100)}%` }} />
      </div>
    </div>
  );
}

function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

function StatusPill({ job }: { job?: Job }) {
  if (!job) return <span className="status-pill idle">idle</span>;
  const Icon = job.status === "completed" ? CheckCircle2 : job.status === "processing" ? Loader2 : AlertTriangle;
  return (
    <span className={`status-pill ${job.status}`}>
      <Icon size={16} />
      {job.status} · {Math.round(job.progress * 100)}%
    </span>
  );
}

function InfoCard({ icon, title, value }: { icon: React.ReactNode; title: string; value: string }) {
  return (
    <article className="info-card">
      <div>
        {icon}
        <span>{title}</span>
      </div>
      <p>{value}</p>
    </article>
  );
}

function formatBytes(size?: number) {
  if (!size) return "-";
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  if (size < 1024 * 1024 * 1024) return `${(size / 1024 / 1024).toFixed(1)} MB`;
  return `${(size / 1024 / 1024 / 1024).toFixed(2)} GB`;
}
