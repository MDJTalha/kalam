"use client";

import { Bell, Check, ChevronDown } from "lucide-react";
import { useEffect, useMemo, useState } from "react";

type Notice = { id: string; type: string; title: string; body: string; read_at?: string | null; created_at: string };

export function NotificationsCenter() {
  const [items, setItems] = useState<Notice[]>([]);
  const [open, setOpen] = useState(false);
  const unread = useMemo(() => items.filter((item) => !item.read_at).length, [items]);

  useEffect(() => {
    let active = true;
    void fetch("/api/lms/notifications", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then((data: unknown) => {
        if (active && Array.isArray(data)) setItems(data as Notice[]);
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  async function markRead(id: string) {
    const response = await fetch(`/api/lms/notifications/${id}/read`, { method: "POST" });
    if (response.ok) setItems((current) => current.map((item) => item.id === id ? { ...item, read_at: new Date().toISOString() } : item));
  }

  return <div className="header-action-wrap">
    <button className="header-icon-button" onClick={() => setOpen((value) => !value)} aria-label={`Notifications${unread ? `, ${unread} unread` : ""}`} aria-expanded={open}>
      <Bell size={18}/>{unread > 0 && <span className="notification-count">{unread > 9 ? "9+" : unread}</span>}
    </button>
    {open && <div className="notification-popover">
      <div className="popover-heading"><div><strong>Notifications</strong><small>{unread ? `${unread} unread` : "All caught up"}</small></div><ChevronDown size={16}/></div>
      {items.length ? items.slice(0, 8).map((item) => <button key={item.id} className={`notification-row ${item.read_at ? "read" : "unread"}`} onClick={() => void markRead(item.id)}>
        <div><strong>{item.title}</strong><small>{item.body}</small><em>{new Date(item.created_at).toLocaleString()}</em></div>{item.read_at ? <Check size={14}/> : <i/>}
      </button>) : <div className="popover-empty"><Bell size={20}/><span>No notifications yet.</span></div>}
    </div>}
  </div>;
}
