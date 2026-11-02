import { LoaderCircle } from "lucide-react";

export default function RootLoading() {
  return (
    <main className="auth-shell" aria-busy="true" aria-live="polite">
      <section className="auth-panel">
        <div className="auth-card">
          <div className="auth-card-heading">
            <span className="eyebrow">Kalam</span>
            <h1>Preparing your experience</h1>
            <p>Your workspace and the information you are authorized to access are loading.</p>
          </div>
          <div className="loading-state" role="status">
            <LoaderCircle size={20} className="spin" aria-hidden="true" />
            <span>Loading Kalam…</span>
          </div>
        </div>
      </section>
    </main>
  );
}
