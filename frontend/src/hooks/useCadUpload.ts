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
  // selectedFile 只存在浏览器内存里，还没有上传到后端。
  // 真正上传成功后，后端会返回 asset/job，才进入下面的 state。
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // 把上传、任务、产物、metadata、错误放在一个状态里，
  // 页面组件只负责展示，不需要知道这些数据是怎么加载来的。
  const [state, setState] = useState<UploadState>({ artifacts: [], uploadProgress: 0 });
  const [converters, setConverters] = useState<ConverterInfo[]>([]);

  // primaryArtifact 是当前最适合拿来预览的产物。
  // 现在优先找 GLB；以后如果加 3D Tiles，可以在这里调整优先级。
  const primaryArtifact = useMemo(
    () => state.artifacts.find((artifact) => artifact.kind === "glb") ?? state.artifacts[0],
    [state.artifacts]
  );
  const metadataArtifact = useMemo(
    () => state.artifacts.find((artifact) => artifact.kind === "metadata"),
    [state.artifacts]
  );

  useEffect(() => {
    // 页面首次加载时查询转换器状态。
    // 空依赖数组 [] 表示这个 effect 只在组件挂载时执行一次。
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

        // 只有任务结束后才拉取 artifacts。
        // 处理中一直拉 artifact 没意义，还会增加后端请求压力。
        const artifacts = terminalStates.has(job.status) ? await listArtifacts(job.asset_id) : undefined;
        setState((current) => ({ ...current, job, asset, artifacts: artifacts ?? current.artifacts }));
      } catch (error) {
        setState((current) => ({ ...current, error: error instanceof Error ? error.message : String(error) }));
      }
    }, 1200);

    // React 组件卸载或 job 变化时，要清掉旧定时器。
    // 否则会出现多个轮询同时跑，页面状态被旧请求覆盖。
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

    // 开始新上传前清空旧文件的结果，避免页面短时间显示上一个文件的数据。
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
