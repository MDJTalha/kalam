import { Activity, AlertTriangle, ArrowUpRight, BadgeCheck, BarChart3, BookOpenCheck, ShieldCheck, Target, UsersRound } from "lucide-react";
import styles from "@/app/landing.module.css";

export function CapabilityCommandCenter() {
  return (
    <div className={styles.commandVisual} aria-label="Illustrative Kalam capability command center">
      <div className={styles.commandTop}>
        <div>
          <span className={styles.commandKicker}>KALAM COMMAND CENTER</span>
          <strong>Workforce capability</strong>
        </div>
        <span className={styles.commandLive}><i /> ILLUSTRATIVE VIEW</span>
      </div>

      <div className={styles.commandShell}>
        <aside className={styles.commandRail} aria-hidden="true">
          <span className={styles.commandRailMark} aria-hidden="true"><svg className={styles.commandRailIcon} viewBox="0 0 192 192" focusable="false"><g transform="translate(16 16)"><path fill="#092844" d="M24 12 H43 Q50 12 50 19 V141 Q50 148 43 148 H24 Q17 148 17 141 V19 Q17 12 24 12 Z"/><path fill="#147AC5" d="M51 77 L104 16 Q108 12 115 12 H148 Q155 12 150 18 L87 87 H51 Z"/><path fill="#63BDE8" d="M51 86 H87 L150 142 Q155 148 148 148 H115 Q108 148 104 144 L51 95 Z"/></g></svg></span>
          <span className={styles.commandRailItem}><BarChart3 size={16}/></span>
          <span className={styles.commandRailItem}><UsersRound size={16}/></span>
          <span className={styles.commandRailItem}><Target size={16}/></span>
          <span className={styles.commandRailItem}><ShieldCheck size={16}/></span>
        </aside>

        <div className={styles.commandMain}>
          <div className={styles.commandHeader}>
            <div>
              <span>EXECUTIVE VIEW</span>
              <h3>Capability & readiness overview</h3>
              <p>Signals from learning, skills, evidence and compliance.</p>
            </div>
            <span className={styles.commandPeriod}>Q3 · GLOBAL</span>
          </div>

          <div className={styles.commandMetrics}>
            <article><span><UsersRound size={15}/> Workforce mapped</span><strong>84%</strong><small>Role expectations connected</small></article>
            <article><span><Target size={15}/> Capability coverage</span><strong>72%</strong><small>Priority skills evidenced</small></article>
            <article><span><ShieldCheck size={15}/> Readiness evidence</span><strong>91%</strong><small>Current required records</small></article>
          </div>

          <div className={styles.commandBody}>
            <section className={styles.commandChart}>
              <div className={styles.commandSectionHead}><span>READINESS TREND</span><strong>Capability evidence is moving forward</strong></div>
              <div className={styles.commandChartCanvas}>
                <div className={styles.commandGridLines}><i/><i/><i/><i/></div>
                <svg viewBox="0 0 420 138" role="img" aria-label="Illustrative upward readiness trend">
                  <defs>
                    <linearGradient id="kalamArea" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="#1f76d2" stopOpacity=".24"/>
                      <stop offset="100%" stopColor="#1f76d2" stopOpacity=".015"/>
                    </linearGradient>
                  </defs>
                  <path d="M6 112 C42 106,57 98,88 100 S142 82,176 86 S228 67,266 71 S318 46,355 53 S390 31,414 24 L414 136 L6 136 Z" fill="url(#kalamArea)"/>
                  <path d="M6 112 C42 106,57 98,88 100 S142 82,176 86 S228 67,266 71 S318 46,355 53 S390 31,414 24" fill="none" stroke="#1f76d2" strokeWidth="4" strokeLinecap="round"/>
                  <circle cx="414" cy="24" r="5.5" fill="#fff" stroke="#1f76d2" strokeWidth="4"/>
                </svg>
              </div>
              <div className={styles.commandLegend}><span><i/> Learning evidence</span><span><i/> Skills evidence</span><span><i/> Compliance evidence</span></div>
            </section>

            <section className={styles.commandQueue}>
              <div className={styles.commandSectionHead}><span>ACTION QUEUE</span><strong>What needs attention</strong></div>
              <div className={styles.commandAction}><span className={styles.commandActionIcon}><AlertTriangle size={16}/></span><span><strong>Critical role gaps</strong><small>12 people · 3 roles</small></span><ArrowUpRight size={15}/></div>
              <div className={styles.commandAction}><span className={styles.commandActionIcon}><BookOpenCheck size={16}/></span><span><strong>Development due</strong><small>28 actions this month</small></span><ArrowUpRight size={15}/></div>
              <div className={styles.commandAction}><span className={styles.commandActionIcon}><BadgeCheck size={16}/></span><span><strong>Evidence expiring</strong><small>9 records need review</small></span><ArrowUpRight size={15}/></div>
            </section>
          </div>

          <div className={styles.commandFooter}>
            <span><Activity size={15}/> Connected operating signal</span>
            <span>Role → Learn → Assess → Evidence → Act</span>
          </div>
        </div>
      </div>
    </div>
  );
}
