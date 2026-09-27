"use client";

import { useEffect, useState } from "react";
import { Bell, Check, X } from "lucide-react";

type NotificationItem = { id: string; type: string; title: string; body: string; read_at?: string | null; created_at: string };

export function NotificationCenter() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<NotificationItem[]>([]);

  useEffect(() => {
    let active = true;
    void fetch("/api/lms/notifications", { cache: "no-store" })
      .then((response) => response.ok ? response.json() : [])
      .then((data: unknown) => {
        if (active && Array.isArray(data)) setItems(data as NotificationItem[]);
      })
      .catch(() => undefined);
    return () => { active = false; };
  }, []);

  const unread = items.filter((item) => !item.read_at).length;
  async function markRead(id: string) {
    await fetch(`/api/lms/notifications/${id}/read`, { method: "POST" });
    setItems((current) => current.map((item) => item.id === id ? { ...item, read_at: new Date().toISOString() } : item));
  }

  return <div className="notification-wrap">
    <button className="header-icon-button" onClick={() => setOpen((v) => !v)} aria-label="Notifications"><Bell size={18}/>{unread > 0 && <span className="notification-count">{unread > 9 ? "9+" : unread}</span>}</button>
    {open && <div className="notification-popover">
      <div className="notification-head"><div><strong>Notifications</strong><small>{unread ? `${unread} unread` : "All caught up"}</small></div><button className="icon-button" onClick={() => setOpen(false)} aria-label="Close notifications"><X size={16}/></button></div>
      <div className="notification-list">
        {items.length ? items.slice(0, 12).map((item) => <div className={`notification-item ${item.read_at ? "read" : "unread"}`} key={item.id}><div><strong>{item.title}</strong><p>{item.body}</p><small>{new Date(item.created_at).toLocaleString()}</small></div>{!item.read_at && <button className="notification-read" onClick={() => markRead(item.id)} aria-label="Mark as read"><Check size={15}/></button>}</div>) : <div className="notification-empty">No notifications yet.</div>}
      </div>
    </div>}
  </div>;
}
