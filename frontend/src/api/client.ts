export type AssetStatus = "uploaded" | "queued" | "processing" | "ready" | "blocked" | "failed";
export type JobStatus = "queued" | "processing" | "completed" | "blocked" | "failed";

export interface Asset {
  id: string;
  filename: string;
  format: string;
  size_bytes: number;
  status: AssetStatus;
  created_at: string;
  updated_at: string;
}

export interface Job {
  id: string;
  asset_id: string;
  status: JobStatus;
  progress: number;
  message: string;
  created_at: string;
  updated_at: string;
}

export interface Artifact {
  id: string;
  asset_id: string;
  kind: "glb" | "tileset" | "metadata";
  filename: string;
  url: string;
  size_bytes: number;
  metadata: Record<string, unknown>;
}

export interface UploadResponse {
  asset: Asset;
  job: Job;
}

export interface ConverterInfo {
  name: string;
  supported_formats: string[];
  available: boolean;
  message: string;
}

export interface StructuredMetadata {
  schemaVersion: string;
  source: Record<string, unknown>;
  summary: Record<string, unknown>;
  details: Record<string, unknown>;
  limitations: string[];
}

export async function uploadAsset(file: File, onProgress?: (sent: number, total: number) => void): Promise<UploadResponse> {
  // 使用 XMLHttpRequest 是为了拿到上传进度。
  // fetch 原生不方便汇报“已上传多少字节”，大文件上传时用户会没有反馈。
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const form = new FormData();
    form.append("file", file);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded, event.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText) as UploadResponse);
      } else {
        reject(new Error(xhr.responseText || xhr.statusText));
      }
    };
    xhr.onerror = () => reject(new Error("Upload failed."));
    xhr.open("POST", "/api/assets");
    xhr.send(form);
  });
}

export async function getJob(jobId: string): Promise<Job> {
  const response = await fetch(`/api/jobs/${jobId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<Job>;
}

export async function getAsset(assetId: string): Promise<Asset> {
  const response = await fetch(`/api/assets/${assetId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<Asset>;
}

export async function listArtifacts(assetId: string): Promise<Artifact[]> {
  const response = await fetch(`/api/assets/${assetId}/artifacts`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<Artifact[]>;
}

export async function listConverters(): Promise<ConverterInfo[]> {
  const response = await fetch("/api/converters");
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<ConverterInfo[]>;
}

export async function fetchArtifactJson<T>(url: string): Promise<T> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export function artifactUrl(url: string): string {
  // 前端只关心 artifact URL。以后后端把 GLB 换成 3D Tiles，这里仍然是 URL 加载模式。
  return url;
}
