"use client";

import Link from "next/link";
import { ChevronDown, CircleHelp, KeyRound, LogOut, Settings2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

type Props = { displayName: string; email: string; role: string; initials: string };

export function AccountMenu({ displayName, email, role, initials }: Props) {
  const [open, setOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!open) return;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!menuRef.current?.contains(event.target as Node)) setOpen(false);
    };
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutsideClick);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return <div className="account-menu" ref={menuRef}>
    <button className="profile-chip account-menu-trigger" type="button" onClick={() => setOpen((value) => !value)}
      aria-label={`Open account menu for ${displayName}`} aria-haspopup="menu" aria-expanded={open} aria-controls="account-menu-panel">
      <span>{initials}</span>
      <div><strong>{displayName}</strong><small>{role}</small></div>
      <ChevronDown size={14} aria-hidden="true" />
    </button>
    {open && <div className="account-popover" id="account-menu-panel" role="menu" aria-label="Account menu">
      <div className="account-popover-heading"><strong>{displayName}</strong><small>{email}</small></div>
      <Link role="menuitem" href="/dashboard/settings" onClick={() => setOpen(false)}><Settings2 size={15} aria-hidden="true" />Settings</Link>
      <Link role="menuitem" href="/dashboard/settings/sessions" onClick={() => setOpen(false)}><KeyRound size={15} aria-hidden="true" />Active sessions</Link>
      <Link role="menuitem" href="/dashboard/help" onClick={() => setOpen(false)}><CircleHelp size={15} aria-hidden="true" />Help & support</Link>
      <form action="/api/auth/logout" method="post">
        <button role="menuitem" type="submit"><LogOut size={15} aria-hidden="true" />Sign out</button>
      </form>
    </div>}
  </div>;
}
