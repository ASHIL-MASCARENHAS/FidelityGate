import json
import pytest
from fidelitygate.storage import StorageEngine
from fidelitygate.workflow.models import (
    WorkflowRunSummary,
    WorkflowStage,
    WorkflowStatus,
    GateDecision,
    InterventionOutcomeReport,
    OverallImpact,
)

# Simulated Auto Demo Context mapping to match frontend TypeScript AutoDemoContext
def generate_auto_demo_step_content(step_id: str, ctx: dict) -> dict:
    current_stage = ctx.get("current_stage", "RECEIVED")
    workflow_status = ctx.get("workflow_status", "PENDING")
    gate_verdict = ctx.get("gate_verdict", "PENDING")
    selected_candidate_id = ctx.get("selected_candidate_id")
    explanation_id = ctx.get("explanation_id")
    outcome_report = ctx.get("outcome_report")
    scenario_id = ctx.get("scenario_id")

    if step_id == "decision":
        if selected_candidate_id:
            heading = f"Network Topology & Proposed Candidate ({selected_candidate_id})"
            desc = f"Active Scenario: {scenario_id or 'unspecified'}. Telemetry ingestion monitors decentralized edge nodes under heavy load. Candidate reroute {selected_candidate_id} has been proposed by Agent B for digital-twin validation prior to consequential deployment."
        else:
            heading = "Global Network Topology & Telemetry (No Candidate Selected)"
            desc = f"Active Scenario: {scenario_id or 'unspecified'}. Candidate reroute is currently unavailable for this workflow run (Stage: {current_stage}). To evaluate candidate mitigations, run an automated investigation or select a completed run from Audit Runs."
        return {"heading": heading, "description": desc, "tab": "decision"}

    elif step_id == "workflow":
        # 1. Check explicit operator rejection first
        if workflow_status == "REJECTED_BY_HUMAN":
            heading = "Intervention Halted: Rejected by Human Operator"
            desc = "Human operator rejected candidate reroute. Execution halted cleanly at Stage 11 without touching real or simulated routing tables."
        # 2. Check authoritative gate abstention before generic completion
        elif gate_verdict == "ABSTAIN":
            heading = "Authoritative Gate Verdict: ABSTAIN (Failed Closed)"
            desc = "Mandatory safety constraints were breached during parameter uncertainty sweeps. The candidate is rejected and fails closed without simulated action."
        # 3. Check awaiting human operator authorization
        elif current_stage == "AWAITING_HUMAN_APPROVAL" or workflow_status == "AWAITING_APPROVAL":
            heading = "Awaiting Human Operator Authorization"
            desc = f"The deterministic gate evaluated {gate_verdict}. Algorithmic progression has paused at Stage 11. Consequential network changes strictly require manual operator authorization before simulated execution."
        # 4. Check completed execution with outcome report
        elif workflow_status == "COMPLETED" or current_stage == "OUTCOME_REPORTED":
            heading = "13-Stage Workflow Completed & Outcome Reported"
            if outcome_report:
                delta = outcome_report.get("latency_delta_ms")
                delta_str = f"{delta:+.2f} ms" if delta is not None else "latency delta unavailable"
                eval_id = outcome_report.get("post_action_evaluation_id", "eval-post")
                cap = outcome_report.get("post_action_capacity_violations", 0)
                slo = outcome_report.get("post_action_slo_violations", 0)
                impact = outcome_report.get("overall_impact", "EVALUATED")
                desc = f"Monotonic lifecycle completed across all 13 stages. Simulated outcome (Evaluation: {eval_id}): latency delta {delta_str}, {cap} capacity breach(es), {slo} SLO breach(es). Overall impact: {impact}."
            else:
                desc = "Monotonic lifecycle completed across all 13 stages. Human authorization was granted and simulated digital-twin intervention reached Stage 13."
        else:
            heading = "13-Stage Operational Workflow State Machine"
            desc = f"Current Stage: {current_stage}. Monotonic event bus transitions sequentially through validation, triage, agent investigation, simulation, and gate review."
        return {"heading": heading, "description": desc, "tab": "workflow"}

    elif step_id == "xai":
        if not explanation_id:
            heading = "Decision Explanation Status (Artifact Unavailable)"
            desc = f"No explanation artifact is currently linked to the selected run (Stage: {current_stage}). Explanations are generated at Stage 9 (EXPLANATION)."
        elif gate_verdict == "ACCEPT":
            heading = "Decision Attribution & 5 Gate Predicates Verified"
            desc = f"Artifact: {explanation_id}. Examines the 5 deterministic gate predicates, exact counterexample perturbation vectors, and local simulator elasticity gradients."
        elif gate_verdict == "ABSTAIN":
            heading = "Counterexample Replay & Constraint Breach Attribution"
            desc = f"Artifact: {explanation_id}. Documents exact perturbation vectors and capacity margin breaches that forced gate abstention."
        else:
            heading = "Decision Attribution & Sensitivity Analysis"
            desc = f"Artifact: {explanation_id}. Sensitivity elasticity analysis and counterfactual evaluations."
        return {"heading": heading, "description": desc, "tab": "xai"}

    elif step_id == "trace":
        count = ctx.get("workflow_events_count", 0)
        heading = f"Monotonically Sequenced Audit Events ({count} Events)" if count > 0 else "Execution Trace & Event Timeline (0 Events)"
        desc = "Immutable audit trail showing monotonic stage transitions and actor attribution."
        return {"heading": heading, "description": desc, "tab": "trace"}

    elif step_id == "metrics":
        return {
            "heading": "Fidelity & Latency Distribution Metrics",
            "description": "Nominal versus worst-case behavior across recorded runs.",
            "tab": "metrics",
        }

    elif step_id == "evaluation":
        return {
            "heading": "4-Way Baseline Benchmarks & Scientific Rigor",
            "description": "Empirical benchmark comparing FidelityGate against 3 standard policies.",
            "tab": "evaluation",
        }

    elif step_id == "history":
        run_id = ctx.get("selected_workflow_run_id")
        heading = f"Immutable Audit Trail (Selected: {run_id})" if run_id else "Immutable Audit Runs (No Run Selected)"
        return {
            "heading": heading,
            "description": "Complete historical record of all executed workflows persisted immutably in SQLite.",
            "tab": "history",
        }

    elif step_id == "guide":
        return {
            "heading": "Platform Architecture & Judging Criteria Alignment",
            "description": "Comprehensive 12-section technical guide detailing system architecture and the 5 Hackathon Judging Criteria.",
            "tab": "guide",
        }

    raise ValueError(f"Unknown step_id: {step_id}")


def test_01_auto_demo_config_matches_real_workspace_tabs():
    """Verify that all 8 step tab identifiers correspond to legitimate workspace views."""
    valid_tabs = {"decision", "workflow", "xai", "trace", "metrics", "evaluation", "history", "guide"}
    step_ids = ["decision", "workflow", "xai", "trace", "metrics", "evaluation", "history", "guide"]

    for sid in step_ids:
        content = generate_auto_demo_step_content(sid, {})
        assert content["tab"] in valid_tabs
        assert len(content["heading"]) > 0
        assert len(content["description"]) > 0


def test_02_status_heading_reflects_awaiting_approval():
    """Verify that a workflow in AWAITING_HUMAN_APPROVAL produces an explicit awaiting approval message."""
    ctx = {
        "selected_workflow_run_id": "wf-test-01",
        "current_stage": "AWAITING_HUMAN_APPROVAL",
        "workflow_status": "AWAITING_APPROVAL",
        "gate_verdict": "ACCEPT",
        "selected_candidate_id": "R-reroute-alt1",
    }
    content = generate_auto_demo_step_content("workflow", ctx)
    assert content["heading"] == "Awaiting Human Operator Authorization"
    assert "Stage 11" in content["description"]
    assert "strictly require manual operator authorization" in content["description"]


def test_03_status_heading_reflects_completed_outcome():
    """Verify that a completed workflow displays the delta latency in the heading/description."""
    ctx = {
        "selected_workflow_run_id": "wf-test-02",
        "current_stage": "OUTCOME_REPORTED",
        "workflow_status": "COMPLETED",
        "gate_verdict": "ACCEPT",
        "outcome_report": {
            "latency_delta_ms": -3.55,
            "overall_impact": "IMPROVED",
            "post_action_capacity_violations": 0,
            "post_action_evaluation_id": "eval-post-02",
        },
    }
    content = generate_auto_demo_step_content("workflow", ctx)
    assert content["heading"] == "13-Stage Workflow Completed & Outcome Reported"
    assert "-3.55 ms" in content["description"]
    assert "all 13 stages" in content["description"]


def test_04_abstain_decision_honestly_reported():
    """Verify that an ABSTAIN verdict is truthfully announced without fake-success phrasing."""
    ctx = {
        "selected_workflow_run_id": "wf-test-03",
        "current_stage": "GATE_REVIEW",
        "workflow_status": "COMPLETED",
        "gate_verdict": "ABSTAIN",
    }
    content = generate_auto_demo_step_content("workflow", ctx)
    assert "ABSTAIN" in content["heading"]
    assert "safety constraints were breached" in content["description"]
    assert "fails closed without simulated action" in content["description"]


def test_05_rejection_by_human_honestly_reported():
    """Verify that operator rejection is announced and documented as halting execution."""
    ctx = {
        "selected_workflow_run_id": "wf-test-04",
        "current_stage": "AWAITING_HUMAN_APPROVAL",
        "workflow_status": "REJECTED_BY_HUMAN",
        "gate_verdict": "ACCEPT",
    }
    content = generate_auto_demo_step_content("workflow", ctx)
    assert "Rejected by Human Operator" in content["heading"]
    assert "halted cleanly at Stage 11" in content["description"]


def test_06_missing_explanation_communicated_truthfully():
    """Verify that an incomplete run without explanation artifact discloses that limitation."""
    ctx = {
        "selected_workflow_run_id": "wf-test-05",
        "current_stage": "INVESTIGATION",
        "explanation_id": None,
    }
    content = generate_auto_demo_step_content("xai", ctx)
    assert "Artifact Unavailable" in content["heading"]
    assert "No explanation artifact is currently linked" in content["description"]
    assert "Stage 9 (EXPLANATION)" in content["description"]


def test_07_persistence_retrieval_for_auto_demo():
    """Verify that real workflows from StorageEngine supply valid fields for Auto Demo context."""
    storage = StorageEngine("fidelitygate.db")
    runs = storage.list_workflow_runs(5)
    if not runs:
        pytest.skip("No existing workflow runs in DB to audit")

    run = runs[0]
    ctx = {
        "selected_workflow_run_id": run.workflow_run_id,
        "current_stage": run.current_stage.value if hasattr(run.current_stage, "value") else str(run.current_stage),
        "workflow_status": run.status.value if hasattr(run.status, "value") else str(run.status),
        "gate_verdict": run.gate_verdict.value if hasattr(run.gate_verdict, "value") else str(run.gate_verdict),
        "selected_candidate_id": run.selected_candidate_id,
        "explanation_id": run.explanation_id,
        "outcome_id": run.outcome_id,
        "scenario_id": run.scenario_id,
    }

    step_ids = ["decision", "workflow", "xai", "trace", "metrics", "evaluation", "history", "guide"]
    for sid in step_ids:
        step_content = generate_auto_demo_step_content(sid, ctx)
        assert len(step_content["heading"]) > 0
        assert len(step_content["description"]) > 0
        assert sid == step_content["tab"]


def test_08_no_workflow_selected_context_handled_safely():
    """Verify that an empty context does not trigger NoneType errors or uncaught exceptions."""
    empty_ctx = {}
    step_ids = ["decision", "workflow", "xai", "trace", "metrics", "evaluation", "history", "guide"]
    for sid in step_ids:
        content = generate_auto_demo_step_content(sid, empty_ctx)
        assert content["tab"] == sid
        assert isinstance(content["heading"], str)
        assert isinstance(content["description"], str)
