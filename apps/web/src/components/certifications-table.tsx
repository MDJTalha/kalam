"use client";

import { useMemo, useState } from "react";
import { ExternalLink, Search } from "lucide-react";
import { DataTable, EmptyState, StatusBadge } from "./ui";
import { CertificationQuickActions } from "./saas-crm-forms";

export type SaaSCertification = {
  id: string;
  title: string;
  issuer: string;
  registration_number?: string | null;
  status: string;
  public_visible: boolean;
  issued_at?: string | null;
  expires_at?: string | null;
  verification_url?: string | null;
};

function formatDate(value?: string | null) {
  return value ? new Date(value).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" }) : "—";
}

function daysUntil(value?: string | null) {
  if (!value) return null;
  return Math.ceil((new Date(value).getTime() - Date.now()) / 86400000);
}

export function CertificationsTable({ certifications }: { certifications: SaaSCertification[] }) {
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return certifications.filter((item) => {
      const matchesQuery = !needle || [item.title, item.issuer, item.registration_number ?? ""].some((value) => value.toLowerCase().includes(needle));
      return matchesQuery && (status === "all" || item.status === status);
    });
  }, [certifications, query, status]);

  return <>
    <div className="certification-toolbar" aria-label="Certification filters">
      <label className="certification-search"><Search size={15} aria-hidden="true" /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search certification, issuer or registration…" aria-label="Search certifications" /></label>
      <label className="certification-filter"><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value)} aria-label="Filter by status"><option value="all">All statuses</option><option value="planned">Planned</option><option value="registered">Registered</option><option value="active">Active</option><option value="expired">Expired</option></select></label>
    </div>
    <DataTable caption="Corporate certifications" columns={["Certification", "Issuer & verification", "Validity", "Status", "Public", "Actions"]} empty={<EmptyState title={certifications.length ? "No matching certifications" : "No certification records yet"} description={certifications.length ? "Try a different search or status filter." : "Register certifications only when there is an authoritative issuer and evidence trail."} />} rows={visible.map((c) => {
      const remaining = daysUntil(c.expires_at);
      const validityNote = remaining !== null && remaining >= 0 && remaining <= 90 ? (remaining === 0 ? "Expires today" : `Expires in ${remaining} days`) : remaining !== null && remaining < 0 ? "Expired" : null;
      return [
        <span key="title"><strong>{c.title}</strong><small>{c.registration_number || "Registration number not recorded"}</small></span>,
        <span key="issuer"><strong>{c.issuer}</strong>{c.verification_url ? <a className="certification-verification-link" href={c.verification_url} target="_blank" rel="noreferrer">Open verification <ExternalLink size={12} aria-hidden="true" /></a> : <small>Verification URL not recorded</small>}</span>,
        <span key="validity"><strong>{formatDate(c.issued_at)} → {formatDate(c.expires_at)}</strong>{validityNote && <small className={remaining !== null && remaining < 0 ? "certification-expiry danger" : "certification-expiry"}>{validityNote}</small>}</span>,
        <StatusBadge key="status" status={c.status} />,
        <StatusBadge key="public" status={c.public_visible ? "published" : "private"} />,
        <CertificationQuickActions key="actions" id={c.id} status={c.status} publicVisible={c.public_visible} />,
      ];
    })} />
  </>;
}