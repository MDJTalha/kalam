import httpx
from datetime import datetime, timezone

BASE = "http://127.0.0.1:8000"
TENANT = "demo-corporation"
ADMIN = {"email": "admin@demo.corp", "password": "DemoOnly!1234"}
LEARNER = {"email": "learner@demo.corp", "password": "DemoOnly!1234"}

def login(client, credentials):
    r = client.post("/api/v1/auth/login", json={"tenant_slug": TENANT, **credentials})
    r.raise_for_status()

def gap_for(client, user_id, gap_id=None):
    rows = client.get("/api/v1/capability-gaps", params={"user_id": user_id}).json()
    return next((x for x in rows if gap_id is None or x["role_requirement_id"] == gap_id), None)

with httpx.Client(base_url=BASE, timeout=20) as c:
    login(c, ADMIN)
    people = c.get("/api/v1/people").json()
    learner = next(x for x in people if x["email"] == LEARNER["email"])
    learner_id = learner["id"]
    gaps = c.get("/api/v1/capability-gaps", params={"user_id": learner_id}).json()
    if not gaps:
        raise RuntimeError("No governed capability gap exists for the controlled learner.")
    initial = gaps[0]
    print("CONTROLLED_USER", learner_id)
    print("INITIAL_GAP", initial["role_requirement_id"], initial["gap"], initial["severity"])
    c.post("/api/v1/capability-gaps/recalculate", params={"user_id": learner_id}).raise_for_status()
    recs = c.get("/api/v1/development/recommendations", params={"user_id": learner_id, "limit": 50})
    recs.raise_for_status()
    candidates = [x for x in recs.json() if x["intervention_type"] in {"coaching", "mentoring", "experiential", "evidence_building"}]
    if not candidates:
        raise RuntimeError("No controlled non-learning recommendation was generated.")
    recommendation = candidates[0]
    accepted = c.post(f"/api/v1/development/recommendations/{recommendation['id']}/accept")
    accepted.raise_for_status()
    interventions = c.get("/api/v1/development/interventions", params={"user_id": learner_id})
    interventions.raise_for_status()
    intervention = next(x for x in interventions.json() if x["recommendation_id"] == recommendation["id"])
    print("RECOMMENDATION_ACCEPTED", recommendation["id"], recommendation["intervention_type"])
    started = c.patch(f"/api/v1/development/interventions/{intervention['id']}", json={"status": "in_progress"})
    started.raise_for_status()
    interaction = c.post(
        f"/api/v1/development/interventions/{intervention['id']}/interactions",
        json={"interaction_type": "practice_review", "occurred_at": datetime.now(timezone.utc).isoformat(),
              "duration_minutes": 45, "summary": "Controlled Phase 7 practice review completed.",
              "action_items": [{"action": "repeat observed task with feedback"}]},
    )
    interaction.raise_for_status()
    evidence = c.post(
        f"/api/v1/development/interventions/{intervention['id']}/evidence",
        json={"evidence_type": "practical_demonstration", "description": "Controlled Phase 7 demonstration evidence.",
              "observed_at": datetime.now(timezone.utc).isoformat(), "demonstrated_level": 3.2},
    )
    evidence.raise_for_status()
    verified = c.post(f"/api/v1/development/interventions/{intervention['id']}/evidence/{evidence.json()['id']}/verify")
    verified.raise_for_status()
    after_evidence = gap_for(c, learner_id, initial["role_requirement_id"])
    print("EVIDENCE_VERIFIED", evidence.json()["id"], verified.status_code)
    print("POST_EVIDENCE_GAP", after_evidence["gap"], after_evidence["severity"], after_evidence["evidence_count"])
    # Create a governed assessment against the same target and prove baseline -> reassessment.
    assessment = c.post("/api/v1/assessments", json={
        "title": "Phase 7 Live Loop Controlled Assessment",
        "passing_score": 70, "assessment_type": "practical",
        "measurement_method": "level_based", "validity_days": 30,
        "reassessment_interval_days": 90,
    })
    assessment.raise_for_status()
    assessment_id = assessment.json()["id"]
    target = c.post(f"/api/v1/capability-assessments/assessments/{assessment_id}/targets", json={
        "target_type": initial["target_type"], "target_id": initial["target_id"],
        "target_level": initial["required_level"], "weight": 1,
    })
    target.raise_for_status()
    cycle = c.post(f"/api/v1/capability-assessments/assessments/{assessment_id}/cycles", json={
        "user_id": learner_id, "target_type": initial["target_type"],
        "target_id": initial["target_id"], "required_level": initial["required_level"],
    })
    cycle.raise_for_status()
    cycle_id = cycle.json()["id"]
    baseline = c.post(f"/api/v1/capability-assessments/cycles/{cycle_id}/attempts", params={"stage": "baseline"})
    baseline.raise_for_status()
    baseline_id = baseline.json()["id"]
    out = c.post(f"/api/v1/capability-assessments/attempts/{baseline_id}/outcomes", json={
        "target_type": initial["target_type"], "target_id": initial["target_id"],
        "demonstrated_level": 2.4, "confidence": 85,
    })
    out.raise_for_status()
    done = c.post(f"/api/v1/capability-assessments/attempts/{baseline_id}/complete")
    done.raise_for_status()
    baseline_gap = gap_for(c, learner_id, initial["role_requirement_id"])
    print("POST_BASELINE_GAP", baseline_gap["gap"], baseline_gap["severity"], baseline_gap["demonstrated_level"])
    c.post(f"/api/v1/capability-assessments/cycles/{cycle_id}/mark-reassessment-due").raise_for_status()
    reassess = c.post(f"/api/v1/capability-assessments/cycles/{cycle_id}/reassessment")
    reassess.raise_for_status()
    reassess_id = reassess.json()["id"]
    out2 = c.post(f"/api/v1/capability-assessments/attempts/{reassess_id}/outcomes", json={
        "target_type": initial["target_type"], "target_id": initial["target_id"],
        "demonstrated_level": 4.0, "confidence": 93,
    })
    out2.raise_for_status()
    final = c.post(f"/api/v1/capability-assessments/attempts/{reassess_id}/complete")
    final.raise_for_status()
    final_gap = gap_for(c, learner_id, initial["role_requirement_id"])
    cycle_view = c.get(f"/api/v1/capability-assessments/cycles/{cycle_id}")
    cycle_view.raise_for_status()
    print("REASSESSMENT_COMPLETE", reassess_id, "IMPROVEMENT", final.json()["cycle"]["improvement"])
    print("POST_REASSESSMENT_GAP", final_gap["gap"], final_gap["severity"], final_gap["demonstrated_level"])
    print("LIVE_LOOP_PASS", baseline_gap["gap"] == 1.6 and final.json()["cycle"]["improvement"] == 1.6 and final_gap["gap"] == 0.0 and final_gap["demonstrated_level"] == 4.0)
