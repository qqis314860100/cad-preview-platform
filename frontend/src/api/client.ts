export type AssetStatus = "uploaded" | "queued" | "processing" | "ready" | "blocked" | "failed";
export type JobStatus = "queued" | "processing" | "completed" | "blocked" | "failed";

// 这些 TypeScript 类型和后端 Pydantic schema 对应。
// 你可以把它理解成“前后端约定好的接口合同”：
// 后端返回这些字段，前端按这些字段渲染页面。
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

    // 后端 FastAPI 的 upload_asset(file: UploadFile) 参数名叫 file，
    // 所以前端 FormData 这里也必须 append("file", file)。
    form.append("file", file);

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded, event.total);
    };
    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        // 后端返回 JSON 字符串，前端需要 parse 成对象。
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
  // 查询后台任务进度。这个接口会被 useCadUpload 定时调用。
  const response = await fetch(`/api/jobs/${jobId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<Job>;
}

export async function getAsset(assetId: string): Promise<Asset> {
  // 查询源文件当前状态，例如 queued / processing / ready。
  const response = await fetch(`/api/assets/${assetId}`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<Asset>;
}

export async function listArtifacts(assetId: string): Promise<Artifact[]> {
  // 查询某个源文件已经生成了哪些产物：metadata.json、GLB、3D Tiles 等。
  const response = await fetch(`/api/assets/${assetId}/artifacts`);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<Artifact[]>;
}

export async function listConverters(): Promise<ConverterInfo[]> {
  // 页面左侧“转换器状态”用这个接口判断当前后端能处理哪些格式。
  const response = await fetch("/api/converters");
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<ConverterInfo[]>;
}

export async function fetchArtifactJson<T>(url: string): Promise<T> {
  // metadata.json 是一个独立文件，不在 artifact 列表接口里直接展开。
  // 用泛型 T 可以让调用方指定返回数据结构，例如 StructuredMetadata。
  const response = await fetch(url);
  if (!response.ok) throw new Error(await response.text());
  return response.json() as Promise<T>;
}

export function artifactUrl(url: string): string {
  // 前端只关心 artifact URL。以后后端把 GLB 换成 3D Tiles，这里仍然是 URL 加载模式。
  return url;
}
