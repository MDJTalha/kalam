"use client";

import { FormEvent, useState } from "react";
import { CheckCircle2, Send } from "lucide-react";

type Question = {
  id: string;
  question_type: string;
  prompt: string;
  options: string[];
  points: number;
  position: number;
};

type Assessment = {
  id: string;
  title: string;
  passing_score: number;
  max_attempts?: number | null;
  time_limit_minutes?: number | null;
  questions: Question[];
};

export function AssessmentRunner({ assessment }: { assessment: Assessment }) {
  const [answers, setAnswers] = useState<Record<string, unknown>>({});
  const [result, setResult] = useState<{ score: number; passed: boolean; certificate_id?: string | null } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  function setSingle(id: string, value: string) {
    setAnswers((current) => ({ ...current, [id]: value }));
  }

  function setMultiple(id: string, value: string, checked: boolean) {
    const current = Array.isArray(answers[id]) ? [...(answers[id] as string[])] : [];
    const next = checked ? [...current, value] : current.filter((item) => item !== value);
    setAnswers((state) => ({ ...state, [id]: next }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const origin = process.env.NEXT_PUBLIC_API_ORIGIN || "http://localhost:8000";
      const response = await fetch(`${origin}/api/v1/assessments/${assessment.id}/submit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ answers }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || "Submission failed");
      setResult(data);
    } catch (error) {
      setError(error instanceof Error ? error.message : "Submission failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="data-panel">
      <div className="player-toolbar">
        <div><span className="eyebrow">Assessment</span><h2>{assessment.title}</h2></div>
        <span className="status-badge warning">Pass: {assessment.passing_score}%</span>
      </div>
      {result ? (
        <div className="assessment-result">
          <CheckCircle2 size={42}/>
          <h2>{result.passed ? "Assessment passed" : "Assessment not passed"}</h2>
          <strong>{result.score}%</strong>
          <p>{result.passed ? (result.certificate_id ? "Your learning record is complete and a credential was issued where applicable." : "Your score passed the threshold.") : "Review the learning material and use another allowed attempt."}</p>
        </div>
      ) : (
        <form className="assessment-form" onSubmit={submit}>
          {assessment.questions.map((question, index) => (
            <fieldset className="question-card" key={question.id}>
              <legend><span>{index + 1}</span>{question.prompt}</legend>
              <div className="option-list">
                {question.options.map((option) => question.question_type === "multiple_choice" ? (
                  <label key={option}><input type="checkbox" checked={Array.isArray(answers[question.id]) && (answers[question.id] as string[]).includes(option)} onChange={(event) => setMultiple(question.id, option, event.target.checked)} />{option}</label>
                ) : (
                  <label key={option}><input type="radio" name={question.id} checked={answers[question.id] === option} onChange={() => setSingle(question.id, option)} />{option}</label>
                ))}
              </div>
            </fieldset>
          ))}
          {error && <div className="form-error" role="alert">{error}</div>}
          <button className="button button-primary button-large" disabled={busy}><Send size={16}/>{busy ? "Submitting…" : "Submit assessment"}</button>
        </form>
      )}
    </div>
  );
}
