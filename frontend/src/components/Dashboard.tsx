import { AlertTriangle, Cpu, Database, FileArchive } from "lucide-react";
import type { Artifact, Job } from "../api/client";
import { InfoCard } from "./ui";

export function Dashboard({ artifacts, job }: { artifacts: Artifact[]; job?: Job }) {
  return (
    <section className="dashboard-grid">
      <InfoCard icon={<Database size={18} />} title="任务说明" value={job?.message ?? "等待上传。"} />
      <InfoCard
        icon={<FileArchive size={18} />}
        title="预览产物"
        value={artifacts.length ? artifacts.map((item) => item.filename).join(", ") : "暂无"}
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
  );
}
