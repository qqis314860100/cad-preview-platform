import { Braces } from "lucide-react";
import type { Artifact, StructuredMetadata } from "../api/client";
import { formatValue } from "../utils/format";
import { Metric } from "./ui";

export function MetadataPanel({
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
