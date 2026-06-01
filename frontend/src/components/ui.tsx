import type { ReactNode } from "react";
import { AlertTriangle, CheckCircle2, Loader2 } from "lucide-react";
import type { Job } from "../api/client";

export function Progress({ label, value }: { label: string; value: number }) {
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

export function Metric({ label, value }: { label: string; value?: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value || "-"}</strong>
    </div>
  );
}

export function StatusPill({ job }: { job?: Job }) {
  if (!job) return <span className="status-pill idle">idle</span>;
  const Icon = job.status === "completed" ? CheckCircle2 : job.status === "processing" ? Loader2 : AlertTriangle;
  return (
    <span className={`status-pill ${job.status}`}>
      <Icon size={16} />
      {job.status} · {Math.round(job.progress * 100)}%
    </span>
  );
}

export function InfoCard({ icon, title, value }: { icon: ReactNode; title: string; value: string }) {
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
