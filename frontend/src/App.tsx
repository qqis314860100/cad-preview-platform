import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Box,
  Braces,
  CheckCircle2,
  CloudUpload,
  Cpu,
  Database,
  FileArchive,
  Loader2,
} from "lucide-react";
import {
  Artifact,
  Asset,
  ConverterInfo,
  Job,
  StructuredMetadata,
  artifactUrl,
  fetchArtifactJson,
  getAsset,
  getJob,
  listArtifacts,
  listConverters,
  uploadAsset,
} from "./api/client";

type UploadState = {
  asset?: Asset;
  job?: Job;
  artifacts: Artifact[];
  structuredMetadata?: StructuredMetadata;
  uploadProgress: number;
  error?: string;
};

const terminalStates = new Set(["completed", "blocked", "failed"]);

export function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>({ artifacts: [], uploadProgress: 0 });
  const [converters, setConverters] = useState<ConverterInfo[]>([]);
  const primaryArtifact = useMemo(
    () => state.artifacts.find((artifact) => artifact.kind === "glb") ?? state.artifacts[0],
    [state.artifacts]
  );
  const metadataArtifact = useMemo(
    () => state.artifacts.find((artifact) => artifact.kind === "metadata"),
    [state.artifacts]
  );

  useEffect(() => {
    listConverters()
      .then(setConverters)
      .catch((error) => setState((current) => ({ ...current, error: String(error) })));
  }, []);

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

  useEffect(() => {
    if (!metadataArtifact) return;

    // metadata.json 是后端提取出的“明文结构化数据”。
    // 它和 GLB 一样按 URL 加载，避免把所有内容塞进任务状态接口。
    fetchArtifactJson<StructuredMetadata>(metadataArtifact.url)
      .then((structuredMetadata) => setState((current) => ({ ...current, structuredMetadata })))
      .catch((error) =>
        setState((current) => ({ ...current, error: error instanceof Error ? error.message : String(error) }))
      );
  }, [metadataArtifact?.url]);

  async function submitUpload() {
    if (!selectedFile) return;
    setState({ artifacts: [], structuredMetadata: undefined, uploadProgress: 0 });
    try {
      const response = await uploadAsset(selectedFile, (sent, total) => {
        // 大文件上传可能持续很久，进度条能明确告诉用户“文件还在传”。
        setState((current) => ({ ...current, uploadProgress: total ? sent / total : 0 }));
      });
      setState({ asset: response.asset, job: response.job, artifacts: [], structuredMetadata: undefined, uploadProgress: 1 });
    } catch (error) {
      setState({
        artifacts: [],
        structuredMetadata: undefined,
        uploadProgress: 0,
        error: error instanceof Error ? error.message : String(error),
      });
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
          <InfoCard
            icon={<Cpu size={18} />}
            title="外部转换器"
            value="X_T / SolidWorks 通过 CAD_EXTERNAL_CONVERTER_COMMAND 接入商业或内部转换服务。"
          />
        </section>

        <StructuredMetadataPanel metadata={state.structuredMetadata} metadataArtifact={metadataArtifact} />

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

function StructuredMetadataPanel({
  metadata,
  metadataArtifact,
}: {
  metadata?: StructuredMetadata;
  metadataArtifact?: Artifact;
}) {
  const details = metadata?.details ?? {};
  const stl = details.stl as Record<string, unknown> | undefined;
  const step = details.step as Record<string, unknown> | undefined;
  const xt = details.parasolidXt as Record<string, unknown> | undefined;
  const glb = details.glb as Record<string, unknown> | undefined;
  const solidworks = details.solidworks as Record<string, unknown> | undefined;

  return (
    <section className="metadata-panel">
      <div className="section-title">
        <div>
          <Braces size={18} />
          <h3>结构化数据</h3>
        </div>
        {metadataArtifact ? (
          <a href={metadataArtifact.url} target="_blank" rel="noreferrer">
            打开 metadata.json
          </a>
        ) : null}
      </div>

      {!metadata ? (
        <p className="empty-copy">上传并处理后，这里会展示从源文件提取出的明文信息。</p>
      ) : (
        <>
          <div className="metadata-grid">
            <KeyValue title="源文件" rows={metadata.source} />
            <KeyValue title="提取结论" rows={metadata.summary} />
          </div>

          {stl ? <StlDetails data={stl} /> : null}
          {step ? <StepDetails data={step} /> : null}
          {xt ? <XtDetails data={xt} /> : null}
          {glb ? <KeyValue title="GLB 信息" rows={glb} /> : null}
          {solidworks ? <KeyValue title="SolidWorks 信息" rows={solidworks} /> : null}

          {metadata.limitations.length ? (
            <div className="metadata-block">
              <h4>限制说明</h4>
              <ul>
                {metadata.limitations.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}

function StlDetails({ data }: { data: Record<string, unknown> }) {
  return (
    <div className="metadata-block">
      <h4>STL 网格统计</h4>
      <div className="metadata-grid compact">
        <Metric label="编码" value={String(data.encoding ?? "-")} />
        <Metric label="三角面" value={String(data.triangleCount ?? "-")} />
        <Metric label="顶点引用" value={String(data.vertexReferenceCount ?? "-")} />
        <Metric label="包围盒" value={formatValue(data.bounds)} />
      </div>
    </div>
  );
}

function StepDetails({ data }: { data: Record<string, unknown> }) {
  const header = (data.header ?? {}) as Record<string, unknown>;
  const entities = (data.entities ?? {}) as Record<string, unknown>;
  const topTypes = (entities.topTypes ?? []) as Array<Record<string, unknown>>;
  const colors = (data.colors ?? []) as Array<Record<string, unknown>>;
  const products = (data.products ?? []) as string[];

  return (
    <div className="metadata-block">
      <h4>STEP 结构</h4>
      <div className="metadata-grid">
        <KeyValue title="HEADER" rows={header} />
        <KeyValue title="实体总览" rows={{ total: entities.total }} />
      </div>

      {topTypes.length ? (
        <div className="entity-list">
          {topTypes.slice(0, 12).map((item) => (
            <span key={`${item.type}`}>
              {String(item.type)} <b>{String(item.count)}</b>
            </span>
          ))}
        </div>
      ) : null}

      {colors.length ? (
        <div className="color-list">
          {colors.slice(0, 12).map((item, index) => {
            const rgb = Array.isArray(item.rgb) ? (item.rgb as number[]) : [0.8, 0.8, 0.8];
            return (
              <span key={`${item.name}-${index}`}>
                <i style={{ backgroundColor: `rgb(${rgb.map((value) => Math.round(value * 255)).join(",")})` }} />
                {String(item.name || "未命名颜色")}
              </span>
            );
          })}
        </div>
      ) : null}

      {products.length ? <p className="plain-list">产品名：{products.join("、")}</p> : null}
    </div>
  );
}

function XtDetails({ data }: { data: Record<string, unknown> }) {
  const keywords = (data.topKeywords ?? []) as Array<Record<string, unknown>>;
  const preview = (data.textPreview ?? []) as string[];
  return (
    <div className="metadata-block">
      <h4>Parasolid XT 明文片段</h4>
      <div className="metadata-grid compact">
        <Metric label="行数" value={String(data.lineCount ?? "-")} />
        <Metric label="数字 Token" value={String(data.numericTokenEstimate ?? "-")} />
        <Metric label="需要外部转换器" value={String(data.requiresExternalConverter ?? true)} />
      </div>
      {keywords.length ? (
        <div className="entity-list">
          {keywords.slice(0, 12).map((item) => (
            <span key={`${item.keyword}`}>
              {String(item.keyword)} <b>{String(item.count)}</b>
            </span>
          ))}
        </div>
      ) : null}
      {preview.length ? <pre className="text-preview">{preview.slice(0, 20).join("\n")}</pre> : null}
    </div>
  );
}

function KeyValue({ title, rows }: { title: string; rows: Record<string, unknown> }) {
  return (
    <div className="metadata-card">
      <h4>{title}</h4>
      {Object.entries(rows).map(([key, value]) => (
        <div className="kv-row" key={key}>
          <span>{key}</span>
          <strong>{formatValue(value)}</strong>
        </div>
      ))}
    </div>
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

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === "") return "-";
  if (typeof value === "boolean") return value ? "是" : "否";
  if (typeof value === "number") return Number.isInteger(value) ? String(value) : value.toFixed(4);
  if (Array.isArray(value)) {
    if (value.length === 0) return "-";
    return value.map(formatValue).join(" / ");
  }
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
