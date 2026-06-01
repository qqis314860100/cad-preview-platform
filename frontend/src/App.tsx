import { ArtifactTable } from "./components/ArtifactTable";
import { Dashboard } from "./components/Dashboard";
import { MetadataPanel } from "./components/MetadataPanel";
import { Sidebar } from "./components/Sidebar";
import { StatusPill } from "./components/ui";
import { ViewerPanel } from "./components/ViewerPanel";
import { useCadUpload } from "./hooks/useCadUpload";

export function App() {
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
        <header className="stage-header">
          <div>
            <span className="eyebrow">产物优先预览</span>
            <h2>{state.asset?.filename ?? "上传一个 CAD 文件"}</h2>
          </div>
          <StatusPill job={state.job} />
        </header>

        <ViewerPanel artifact={primaryArtifact} job={state.job} />
        {state.error ? <p className="error-line">{state.error}</p> : null}

        <Dashboard artifacts={state.artifacts} job={state.job} />
        <MetadataPanel metadata={state.structuredMetadata} metadataArtifact={metadataArtifact} />
        <ArtifactTable artifacts={state.artifacts} />
      </section>
    </main>
  );
}
