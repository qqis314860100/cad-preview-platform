import { useEffect, useMemo, useState } from "react";
import type { Artifact, Asset, ConverterInfo, Job, JobStatus, StructuredMetadata } from "../api/client";
import {
  fetchArtifactJson,
  getAsset,
  getJob,
  listArtifacts,
  listConverters,
  uploadAsset,
} from "../api/client";

export type UploadState = {
  asset?: Asset;
  job?: Job;
  artifacts: Artifact[];
  structuredMetadata?: StructuredMetadata;
  uploadProgress: number;
  error?: string;
};

const terminalStates = new Set<JobStatus>(["completed", "blocked", "failed"]);

export function useCadUpload() {
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
    const jobId = state.job.id;

    // 转换是后台任务，不会在上传请求里立刻完成；前端定时查询 job 状态。
    const timer = window.setInterval(async () => {
      try {
        const job = await getJob(jobId);
        const asset = await getAsset(job.asset_id);
        const artifacts = terminalStates.has(job.status) ? await listArtifacts(job.asset_id) : undefined;
        setState((current) => ({ ...current, job, asset, artifacts: artifacts ?? current.artifacts }));
      } catch (error) {
        setState((current) => ({ ...current, error: error instanceof Error ? error.message : String(error) }));
      }
    }, 1200);

    return () => window.clearInterval(timer);
  }, [state.job?.id, state.job?.status]);

  useEffect(() => {
    if (!metadataArtifact) return;

    // metadata.json 是独立 artifact，按 URL 加载，避免任务接口越来越重。
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
      setState({
        asset: response.asset,
        job: response.job,
        artifacts: [],
        structuredMetadata: undefined,
        uploadProgress: 1,
      });
    } catch (error) {
      setState({
        artifacts: [],
        structuredMetadata: undefined,
        uploadProgress: 0,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  return {
    converters,
    metadataArtifact,
    primaryArtifact,
    selectedFile,
    setSelectedFile,
    state,
    submitUpload,
  };
}
