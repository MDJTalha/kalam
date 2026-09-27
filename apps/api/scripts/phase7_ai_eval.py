from __future__ import annotations

import json
from pathlib import Path

from app.services.ai_evaluation import detect_prompt_injection, evaluate_grounded_response

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "tests" / "ai" / "phase7_eval_cases.json"


def main() -> int:
    cases = json.loads(DATASET.read_text(encoding="utf-8"))
    passed = 0
    results: list[dict] = []
    for case in cases:
        if case["kind"] == "request":
            actual = bool(detect_prompt_injection(case["text"]))
            ok = actual == bool(case["expect_injection"])
        else:
            result = evaluate_grounded_response(case["text"], set(case["valid_citations"]))
            actual = result.passed
            ok = actual == bool(case["expect_pass"])
        passed += int(ok)
        results.append({"id": case["id"], "passed": ok, "actual": actual})
    score = round((passed / len(cases)) * 100, 2) if cases else 0.0
    print(json.dumps({"cases": len(cases), "passed": passed, "score_percent": score, "results": results}, indent=2))
    return 0 if passed == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
