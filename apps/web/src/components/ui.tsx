import { ReactNode, type ButtonHTMLAttributes } from "react";
import { LucideIcon, AlertCircle, AlertTriangle, BarChart3, CalendarDays, CheckCircle2, ClipboardCheck, Clock3, Info, Layers3, Loader2, SearchX, ShieldCheck, Target, UsersRound, Video, Webhook } from "lucide-react";

export function PageHeader({ eyebrow, title, description, actions }: { eyebrow?: string; title: string; description?: string; actions?: ReactNode }) {
  return <div className="page-heading"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2>{description && <p>{description}</p>}</div>{actions && <div className="page-heading-actions">{actions}</div>}</div>;
}

type MetricIconName = "alert" | "calendar" | "chart" | "check" | "clipboard" | "clock" | "layers" | "shield" | "target" | "users" | "video" | "webhook";

const metricIcons: Record<MetricIconName, LucideIcon> = {
  alert: AlertTriangle,
  calendar: CalendarDays,
  chart: BarChart3,
  check: CheckCircle2,
  clipboard: ClipboardCheck,
  clock: Clock3,
  layers: Layers3,
  shield: ShieldCheck,
  target: Target,
  users: UsersRound,
  video: Video,
  webhook: Webhook,
};

export function MetricCard({ label, value, detail, hint, icon }: { label: string; value: ReactNode; detail?: string; hint?: string; icon?: MetricIconName | LucideIcon }) {
  const Icon = typeof icon === "string" ? metricIcons[icon] : icon;
  return <div className="stat-card metric-card"><div className="metric-card-top"><span>{label}</span>{Icon ? <Icon size={16} aria-hidden="true"/> : null}</div><strong>{value}</strong><small>{detail ?? hint}</small></div>;
}

export function StatusBadge({ status, tone }: { status: string; tone?: "success" | "warning" | "danger" | "muted" }) {
  const normalized = status.toLowerCase();
  const inferred = tone ?? (["inactive", "disabled", "unverified"].includes(normalized) ? "muted" : normalized.includes("complete") || normalized.includes("active") || normalized.includes("valid") || normalized.includes("passed") || normalized.includes("published") || normalized.includes("connected") || normalized === "approved" || normalized === "excepted" ? "success" : normalized.includes("overdue") || normalized.includes("expired") || normalized.includes("failed") || normalized.includes("revoked") || normalized.includes("error") || normalized === "rejected" ? "danger" : normalized.includes("assigned") || normalized.includes("progress") || normalized.includes("warning") || normalized.includes("draft") || normalized.includes("planned") || normalized.includes("requested") || normalized.includes("submitted") || normalized.includes("pending") ? "warning" : "muted");
  return <span className={"status-badge "+inferred}>{status.replaceAll("_"," ")}</span>;
}

export function EmptyState({ title = "Nothing to display", description, message, icon }: { title?: string; description?: string; message?: string; icon?: MetricIconName | LucideIcon }) {
  const Icon = typeof icon === "string" ? metricIcons[icon] : icon ?? SearchX;
  return <div className="empty-state"><div className="empty-state-icon"><Icon size={26} aria-hidden="true"/></div><h3>{title}</h3>{(description || message) && <p>{description || message}</p>}</div>;
}

export function Section({ eyebrow, title, action, children }: { eyebrow?: string; title: string; action?: ReactNode; children: ReactNode }) {
  return <section className="data-panel"><div className="section-heading compact"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{action && <div>{action}</div>}</div>{children}</section>;
}

export function SectionCard({ eyebrow, title, meta, actions, children }: { eyebrow?: string; title: string; meta?: ReactNode; actions?: ReactNode; children: ReactNode }) {
  return <section className="data-panel"><div className="section-heading compact"><div>{eyebrow && <span className="eyebrow">{eyebrow}</span>}<h2>{title}</h2></div><div className="section-actions">{meta && <span className="section-meta">{meta}</span>}{actions}</div></div>{children}</section>;
}

export function Notice({ kind="info", children }: { kind?: "info"|"success"|"error"; children: ReactNode }) {
  const Icon = kind==="success" ? CheckCircle2 : kind==="error" ? AlertCircle : Info;
  const tone = kind === "error" ? "danger" : kind;
  return <div className={`ds-state ds-state-${tone}`} role={kind === "error" ? "alert" : "status"}><Icon size={17} aria-hidden="true"/><div>{children}</div></div>;
}

export function Button({ variant="primary", children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary"|"secondary"|"ghost" }) {
  return <button {...props} className={`ds-button ds-button-${variant} ${props.className ?? ""}`.trim()}>{children}</button>;
}

export function IconButton({ label, children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <button {...props} className={`header-icon-button ${props.className ?? ""}`.trim()} aria-label={label} title={props.title ?? label}>{children}</button>;
}

export function StateMessage({ tone="info", title, children }: { tone?: "info"|"success"|"warning"|"danger"; title: string; children?: ReactNode }) {
  return <div className={`ds-state ds-state-${tone}`} role={tone === "danger" ? "alert" : "status"}><div><strong className="ds-state-title">{title}</strong>{children && <span className="ds-state-copy">{children}</span>}</div></div>;
}

export function LoadingState({ message="Loading workspace…" }: { message?: string }) {
  return <div className="loading-state"><Loader2 size={20} className="spin"/><span>{message}</span></div>;
}

export function DataTable({ columns, rows, empty, rowKey }: { columns: ReactNode[]; rows: ReactNode[][]; empty: ReactNode; rowKey?: (row: ReactNode[], index: number) => React.Key }) {
  return rows.length ? <div className="table-wrap"><table className="data-table"><thead><tr>{columns.map((column,index)=><th key={index}>{column}</th>)}</tr></thead><tbody>{rows.map((row,index)=><tr key={rowKey?rowKey(row,index):index}>{row.map((cell,cellIndex)=><td key={cellIndex}>{cell}</td>)}</tr>)}</tbody></table></div> : <>{empty}</>;
}

export function FormField({ label, children, hint }: { label: string; children: ReactNode; hint?: string }) {
  return <label className="form-field"><span>{label}</span>{children}{hint&&<small>{hint}</small>}</label>;
}
