import { ArtifactTable } from "./components/ArtifactTable";
import { Dashboard } from "./components/Dashboard";
import { MetadataPanel } from "./components/MetadataPanel";
import { Sidebar } from "./components/Sidebar";
import { StatusPill } from "./components/ui";
import { ViewerPanel } from "./components/ViewerPanel";
import { useCadUpload } from "./hooks/useCadUpload";

export function App() {
  // App 现在只负责“页面组装”。
  // 数据加载、上传、轮询这些逻辑都放在 useCadUpload，避免主组件越来越难读。
  const {
    converters,
    metadataArtifact,
    primaryArtifact,
    selectedFile,
    setSelectedFile,
    state,
    submitUpload,
  } = useCadUpload();

  return (
    <main className="app-shell">
      {/* 左侧栏：上传入口、文件状态、转换器状态。 */}
      <Sidebar
        asset={state.asset}
        converters={converters}
        job={state.job}
        selectedFile={selectedFile}
        uploadProgress={state.uploadProgress}
        onFileChange={setSelectedFile}
        onUpload={submitUpload}
      />

      <section className="stage">
        {/* 右侧主区域：当前文件标题、任务状态、3D 预览、metadata、产物列表。 */}
        <header className="stage-header">
          <div>
            <span className="eyebrow">产物优先预览</span>
            <h2>{state.asset?.filename ?? "上传一个 CAD 文件"}</h2>
          </div>
          <StatusPill job={state.job} />
        </header>

        <ViewerPanel artifact={primaryArtifact} job={state.job} />

        {/* error 是给用户看的轻量错误提示。更完整的错误日志应在后端记录。 */}
        {state.error ? <p className="error-line">{state.error}</p> : null}

        <Dashboard artifacts={state.artifacts} job={state.job} />
        <MetadataPanel metadata={state.structuredMetadata} metadataArtifact={metadataArtifact} />
        <ArtifactTable artifacts={state.artifacts} />
      </section>
    </main>
  );
}
