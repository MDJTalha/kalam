from __future__ import annotations

import re
from dataclasses import dataclass

_INJECTION_PATTERNS = (
    re.compile(r"ignore (all|any|the|previous|prior) instructions", re.IGNORECASE),
    re.compile(r"(reveal|show|print|return).{0,30}(system prompt|hidden prompt|secret|api key)", re.IGNORECASE),
    re.compile(r"(you are now|act as|roleplay as).{0,40}(admin|system|developer|root)", re.IGNORECASE),
    re.compile(r"(bypass|disable|override).{0,30}(policy|guardrail|permission|authorization)", re.IGNORECASE),
)


@dataclass(frozen=True)
class EvaluationResult:
    passed: bool
    score: float
    reasons: tuple[str, ...]


def detect_prompt_injection(text: str) -> tuple[str, ...]:
    findings: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            findings.append(pattern.pattern)
    return tuple(findings)


def evaluate_grounded_response(answer: str, valid_citations: set[str]) -> EvaluationResult:
    reasons: list[str] = []
    citations = set(re.findall(r"\[(S\d+)\]", answer))
    if not answer.strip():
        reasons.append("empty_response")
    if not citations:
        reasons.append("missing_citation")
    elif citations - valid_citations:
        reasons.append("invalid_citation")
    score = 1.0
    if reasons:
        score -= min(1.0, 0.4 * len(reasons))
    return EvaluationResult(not reasons, round(max(score, 0.0), 3), tuple(reasons))
