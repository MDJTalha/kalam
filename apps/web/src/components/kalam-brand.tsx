import Link from "next/link";

type Props = {
  href?: string;
  dark?: boolean;
  descriptor?: string;
  className?: string;
  compact?: boolean;
};

/** Canonical Kalam brand lockup. Keep logo geometry and wordmark spacing centralized here. */
export function KalamBrand({ href = "/", dark = false, descriptor, className = "", compact = false }: Props) {
  return (
    <Link href={href} className={`kalam-logo ${dark ? "kalam-logo-dark" : ""} ${className}`} aria-label="Kalam home">
      <span className="kalam-logo-asset" aria-hidden="true">
        <svg className="kalam-logo-icon" viewBox="0 0 192 192" focusable="false">
          <g transform="translate(16 16)">
            <path fill={dark ? "#F4FAFF" : "#08243D"} d="M24 12 H43 Q50 12 50 19 V141 Q50 148 43 148 H24 Q17 148 17 141 V19 Q17 12 24 12 Z"/>
            <path fill="#0878C9" d="M51 77 L104 16 Q108 12 115 12 H148 Q155 12 150 18 L87 87 H51 Z"/>
            <path fill="#3EA9DD" d="M51 86 H87 L150 142 Q155 148 148 148 H115 Q108 148 104 144 L51 95 Z"/>
          </g>
        </svg>
        <span className="kalam-logo-wordmark">alam</span>
      </span>
      {!compact && descriptor && <small className="kalam-logo-descriptor">{descriptor}</small>}
    </Link>
  );
}
