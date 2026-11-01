"use client";

import { useMemo, useState } from "react";
import { Activity, UsersRound } from "lucide-react";

type TrendPoint = { date: string; enrollments: number; completions: number };
type OrgUnit = { org_unit_id: string; org_unit: string; people: number; completion_rate: number };

const formatNumber = (value: number) => new Intl.NumberFormat().format(value);
const formatDate = (value: string, options?: Intl.DateTimeFormatOptions) =>
  new Date(value).toLocaleDateString(undefined, options);

export function LearningMomentumChart({ points }: { points: TrendPoint[] }) {
  const [range, setRange] = useState<7 | 14 | 30>(30);
  const [activeIndex, setActiveIndex] = useState<number | null>(null);
  const visible = points.slice(-range);
  const maxValue = Math.max(1, ...visible.flatMap(point => [point.enrollments, point.completions]));
  const totals = useMemo(() => visible.reduce(
    (acc, point) => ({
      enrollments: acc.enrollments + point.enrollments,
      completions: acc.completions + point.completions,
    }),
    { enrollments: 0, completions: 0 },
  ), [visible]);
  const peak = visible.length
    ? visible.reduce((best, point) =>
        point.enrollments + point.completions > best.enrollments + best.completions ? point : best,
      visible[0])
    : null;

  if (!points.length) {
    return <div className="dashboard-chart-empty">No learning activity is available for this period.</div>;
  }

  const active = activeIndex === null ? visible.length - 1 : activeIndex;
  const selected = visible[active] ?? visible[visible.length - 1];
  const chartHeight = 190;
  const chartWidth = 840;
  const xStep = visible.length > 1 ? chartWidth / (visible.length - 1) : chartWidth;
  const enrollmentPath = visible.map((point, index) => {
    const x = index * xStep;
    const y = chartHeight - (point.enrollments / maxValue) * (chartHeight - 18);
    return (index === 0 ? "M" : "L") + " " + x.toFixed(1) + " " + y.toFixed(1);
  }).join(" ");
  const completionPath = visible.map((point, index) => {
    const x = index * xStep;
    const y = chartHeight - (point.completions / maxValue) * (chartHeight - 18);
    return (index === 0 ? "M" : "L") + " " + x.toFixed(1) + " " + y.toFixed(1);
  }).join(" ");

  return (
    <div className="dashboard-chart-shell">
      <div className="dashboard-chart-toolbar">
        <div className="dashboard-chart-summary">
          <span><b>{formatNumber(totals.enrollments)}</b> enrollments</span>
          <span><b>{formatNumber(totals.completions)}</b> completions</span>
          <span>{peak ? <>Peak <b>{formatDate(peak.date, { month: "short", day: "numeric" })}</b></> : "Peak —"}</span>
        </div>
        <div className="dashboard-chart-ranges" role="group" aria-label="Learning trend range">
          {[7, 14, 30].map(value => (
            <button key={value} type="button" className={range === value ? "active" : ""} aria-pressed={range === value} onClick={() => {
              setRange(value as 7 | 14 | 30);
              setActiveIndex(null);
            }}>{value}d</button>
          ))}
        </div>
      </div>

      <div className="dashboard-chart-plot" role="region" aria-label="Learning activity trend with daily enrollments and completions">
        <svg viewBox={"0 0 " + chartWidth + " " + chartHeight} preserveAspectRatio="none" aria-hidden="true">
          {[0.25, 0.5, 0.75].map(level => (
            <line key={level} x1="0" x2={chartWidth} y1={chartHeight - (chartHeight * level)} y2={chartHeight - (chartHeight * level)} className="chart-grid-line" />
          ))}
          <path d={enrollmentPath} className="chart-line chart-line-enrollment" />
          <path d={completionPath} className="chart-line chart-line-completion" />
          {visible.map((point, index) => {
            const x = index * xStep;
            const enrollmentY = chartHeight - (point.enrollments / maxValue) * (chartHeight - 18);
            const completionY = chartHeight - (point.completions / maxValue) * (chartHeight - 18);
            return (
              <g key={point.date} onMouseEnter={() => setActiveIndex(index)} onClick={() => setActiveIndex(index)} className="chart-point-group">
                <rect x={Math.max(0, x - Math.max(9, xStep / 2))} y="0" width={Math.min(chartWidth, Math.max(18, xStep))} height={chartHeight} fill="transparent" />
                <circle cx={x} cy={enrollmentY} r={index === active ? 5 : 3.5} className="chart-dot chart-dot-enrollment" />
                <circle cx={x} cy={completionY} r={index === active ? 5 : 3.5} className="chart-dot chart-dot-completion" />
              </g>
            );
          })}
        </svg>
        <div className="dashboard-chart-labels" role="group" aria-label="Select a day to inspect learning activity">
          {visible.map((point, index) => (
            <button key={point.date} type="button" className={index === active ? "active" : ""} aria-label={formatDate(point.date, { weekday: "long", month: "long", day: "numeric", year: "numeric" })} title={formatDate(point.date, { month: "long", day: "numeric", year: "numeric" })} aria-pressed={index === active} onClick={() => setActiveIndex(index)}>
              {formatDate(point.date, { day: "numeric" })}
            </button>
          ))}
        </div>
        <div className="dashboard-chart-detail">
          <div><span>{formatDate(selected.date, { weekday: "short", month: "long", day: "numeric" })}</span><strong>{formatNumber(selected.enrollments + selected.completions)} learning events</strong></div>
          <div><span>Enrollments</span><b>{formatNumber(selected.enrollments)}</b></div>
          <div><span>Completions</span><b>{formatNumber(selected.completions)}</b></div>
          <div><span>Completion conversion</span><b>{selected.enrollments ? Math.round(selected.completions / selected.enrollments * 100) : 0}%</b></div>
        </div>
      </div>
      <div className="dashboard-chart-legend">
        <span><i className="enrollment" /> Enrollments</span>
        <span><i className="completion" /> Completions</span>
        <span className="dashboard-chart-hint"><Activity size={12} /> Hover or select a day for detail</span>
      </div>
    </div>
  );
}

export function WorkforceUnitChart({ units }: { units: OrgUnit[] }) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const ordered = [...units].sort((a, b) => b.completion_rate - a.completion_rate);
  const active = ordered.find(unit => unit.org_unit_id === activeId) ?? ordered[0];

  if (!ordered.length) {
    return <div className="dashboard-chart-empty">Organization performance is unavailable.</div>;
  }

  return (
    <div className="dashboard-unit-chart">
      <div className="dashboard-unit-summary">
        <span><b>{formatNumber(ordered.reduce((total, unit) => total + unit.people, 0))}</b> people across {ordered.length} displayed units</span>
        {active && <span>Selected <b>{active.org_unit}</b> · <b>{active.completion_rate}%</b> completion</span>}
      </div>
      <div className="dashboard-unit-bars">
        {ordered.map(unit => (
          <button
            key={unit.org_unit_id}
            type="button"
            className={"dashboard-unit-row" + (active?.org_unit_id === unit.org_unit_id ? " active" : "")}
            onMouseEnter={() => setActiveId(unit.org_unit_id)}
            onFocus={() => setActiveId(unit.org_unit_id)}
            onClick={() => setActiveId(unit.org_unit_id)}
          >
            <span className="dashboard-unit-label"><b>{unit.org_unit}</b><small>{formatNumber(unit.people)} people</small></span>
            <span className="dashboard-unit-track"><span style={{ width: Math.max(0, Math.min(100, unit.completion_rate)) + "%" }} /></span>
            <strong>{unit.completion_rate}%</strong>
          </button>
        ))}
      </div>
      {active && (
        <div className="dashboard-unit-detail">
          <div><UsersRound size={14} /><span>{active.org_unit}</span><b>{active.completion_rate}%</b></div>
          <p>{formatNumber(active.people)} people are represented in this workforce unit. Completion rate is calculated from persisted enrollment and completion records for the unit.</p>
        </div>
      )}
    </div>
  );
}
