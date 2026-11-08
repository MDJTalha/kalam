"use client";

import Link from "next/link";

export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <html lang="en">
      <body>
        <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "24px", background: "#F4F8FC", color: "#08243D", fontFamily: "Arial, sans-serif" }}>
          <section style={{ width: "100%", maxWidth: "520px", padding: "32px", border: "1px solid #DCE6F0", borderRadius: "16px", background: "#FFFFFF" }} aria-labelledby="global-error-title">
            <p style={{ margin: "0 0 10px", color: "#0878C9", fontSize: "12px", fontWeight: 700, letterSpacing: ".08em", textTransform: "uppercase" }}>Kalam · Service recovery</p>
            <h1 id="global-error-title" style={{ margin: "0 0 12px", fontSize: "26px", lineHeight: 1.2 }}>Kalam is temporarily unavailable.</h1>
            <p style={{ margin: "0 0 24px", color: "#63738A", lineHeight: 1.6 }}>An unexpected application error interrupted this page. Retry the request, or return to the home page.</p>
            <button type="button" onClick={() => reset()} style={{ minHeight: "44px", padding: "0 18px", border: 0, borderRadius: "8px", background: "#0878C9", color: "#FFFFFF", fontWeight: 700, cursor: "pointer" }}>Try again</button>
            <Link href="/" style={{ display: "inline-block", marginLeft: "16px", color: "#0878C9", fontWeight: 700 }}>Kalam home</Link>
          </section>
        </main>
      </body>
    </html>
  );
}
