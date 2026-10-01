"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { usePathname } from "next/navigation";

function isModifiedClick(event: MouseEvent) {
  return event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
}

export function NavigationProgress() {
  const pathname = usePathname();
  const [pendingPath, setPendingPath] = useState<string | null>(null);
  const pending = pendingPath !== null && pendingPath !== pathname;

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      if (isModifiedClick(event)) return;
      const target = event.target;
      if (!(target instanceof Element)) return;
      const link = target.closest("a[href]");
      if (!(link instanceof HTMLAnchorElement)) return;
      if (!link.href || link.target === "_blank" || link.hasAttribute("download")) return;
      if (link.origin !== window.location.origin) return;

      const nextUrl = new URL(link.href);
      const currentUrl = new URL(window.location.href);
      if (nextUrl.pathname === currentUrl.pathname && nextUrl.search === currentUrl.search && nextUrl.hash === currentUrl.hash) return;
      if (nextUrl.pathname.startsWith("/api/")) return;

      setPendingPath(`${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`);
    };

    document.addEventListener("click", handleClick, true);
    return () => document.removeEventListener("click", handleClick, true);
  }, []);

  if (!pending) return null;

  return (
    <div className="navigation-progress" role="status" aria-live="polite" aria-label="Loading workspace">
      <div className="navigation-progress-bar" />
      <div className="navigation-progress-card">
        <Loader2 size={15} className="navigation-progress-spinner" aria-hidden="true" />
        <span>Loading workspace</span>
      </div>
    </div>
  );
}

