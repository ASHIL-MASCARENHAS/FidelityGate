"""tests/test_workflow_orchestration.py
Comprehensive test suite for Layer 7: End-to-End Workflow Orchestration,
Human Approval Boundary, Isolated Simulation Adapter, and Outcome Reporting.
"""

import os
import shutil
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.evaluation.models import (
    CandidateAction,
    GateDecision,
    NetworkTopology,
    TopologyEdge,
    TopologyNode,
    TrafficFlow,
)
from fidelitygate.storage import StorageEngine
from fidelitygate.workflow.models import (
    ApprovalDecision,
    ApprovalRequest,
    HumanApprovalRecord,
    OverallImpact,
    WorkflowRunRequest,
    WorkflowStage,
    WorkflowStatus,
)
from fidelitygate.workflow.orchestrator import EndToEndWorkflowOrchestrator
from fidelitygate.workflow.simulation_adapter import SimulationActionAdapter


@pytest.fixture
def test_storage(tmp_path):
    db_file = str(tmp_path / "test_wf.db")
    if os.path.exists(settings.DATABASE_PATH):
        shutil.copy2(settings.DATABASE_PATH, db_file)
    storage = StorageEngine(db_file)
    return storage


@pytest.fixture
def orchestrator(test_storage):
    return EndToEndWorkflowOrchestrator(test_storage)


# ==========================================
# Test 1: Complete Successful Workflow Execution
# ==========================================

def test_01_complete_successful_workflow(orchestrator, test_storage):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=True)
    )

    assert summary.status == WorkflowStatus.COMPLETED
    assert summary.current_stage == WorkflowStage.OUTCOME_REPORTED
    assert summary.approval_status == ApprovalDecision.APPROVED
    assert summary.outcome_id is not None
    assert summary.duration_ms is not None

    outcome = test_storage.get_outcome(summary.outcome_id)
    assert outcome is not None
    assert outcome.pre_action_latency_ms > 0
    assert outcome.post_action_latency_ms > 0
    assert outcome.overall_impact in (OverallImpact.IMPROVED, OverallImpact.NEUTRAL, OverallImpact.DEGRADED)


# ==========================================
# Test 2: Invalid Input Scenario Fails Closed
# ==========================================

def test_02_invalid_scenario_fails_closed(orchestrator):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="non_existent_scenario_xyz")
    )

    assert summary.status == WorkflowStatus.FAILED
    assert summary.current_stage == WorkflowStage.VALIDATING
    assert "Unknown or invalid scenario" in (summary.termination_reason or "")


# ==========================================
# Test 3: Pausing at Human Approval Boundary
# ==========================================

def test_03_pauses_at_human_approval_boundary(orchestrator, test_storage):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    assert summary.status == WorkflowStatus.AWAITING_APPROVAL
    assert summary.current_stage == WorkflowStage.AWAITING_HUMAN_APPROVAL
    assert summary.approval_id is None
    assert summary.outcome_id is None

    # Verify event #09 is awaiting authorization
    events = test_storage.get_workflow_events(summary.workflow_run_id)
    assert any(e.event_type == "AWAITING_HUMAN_AUTHORIZATION" for e in events)


# ==========================================
# Test 4: Human Rejection Halts Execution Safely
# ==========================================

def test_04_human_rejection_halts_intervention(orchestrator, test_storage):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    summary_rej, approval = orchestrator.submit_approval(
        summary.workflow_run_id,
        ApprovalRequest(
            decision=ApprovalDecision.REJECTED,
            reviewer_id="operator-alice",
            reviewer_comment="Peak trading hour freeze; rejected.",
        ),
    )

    assert summary_rej.status == WorkflowStatus.REJECTED_BY_HUMAN
    assert approval.decision == ApprovalDecision.REJECTED
    assert summary_rej.outcome_id is None

    outcome = test_storage.get_outcome_by_workflow(summary.workflow_run_id)
    assert outcome is None  # Simulation was never executed


# ==========================================
# Test 5: Changes Requested State
# ==========================================

def test_05_changes_requested_halts_intervention(orchestrator):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    summary_changes, approval = orchestrator.submit_approval(
        summary.workflow_run_id,
        ApprovalRequest(
            decision=ApprovalDecision.CHANGES_REQUESTED,
            reviewer_id="operator-carol",
            reviewer_comment="Prefer path via Zurich instead of Paris.",
        ),
    )

    assert summary_changes.status == WorkflowStatus.CHANGES_REQUESTED
    assert approval.decision == ApprovalDecision.CHANGES_REQUESTED
    assert summary_changes.outcome_id is None


# ==========================================
# Test 6: Stale Approval Rejection
# ==========================================

def test_06_stale_approval_rejected():
    adapter = SimulationActionAdapter()
    candidate = CandidateAction(
        candidate_id="R-alt1",
        action_type="REROUTE_FLOW",
        flow_id="FLOW_CONGESTION_PRIORITY",
        source_node="cr01.lon",
        destination_node="cr01.fra",
        path=["cr01.lon", "cr01.par", "cr01.fra"],
    )
    stale_approval = HumanApprovalRecord(
        approval_id="appr-stale",
        workflow_run_id="wf-test",
        candidate_id="R-alt1",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-1",
        evidence_version="v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="operator",
        is_stale=True,  # Stale!
    )

    with pytest.raises(ValueError, match="approval is stale"):
        adapter.execute_intervention(
            workflow_run_id="wf-test",
            scenario_id="wan_congestion",
            candidate=candidate,
            approval=stale_approval,
        )


# ==========================================
# Test 7: Unapproved Execution Fails Closed
# ==========================================

def test_07_unapproved_execution_fails_closed():
    adapter = SimulationActionAdapter()
    candidate = CandidateAction(
        candidate_id="R-alt1",
        action_type="REROUTE_FLOW",
        flow_id="FLOW_CONGESTION_PRIORITY",
        source_node="cr01.lon",
        destination_node="cr01.fra",
        path=["cr01.lon", "cr01.par", "cr01.fra"],
    )
    unapproved = HumanApprovalRecord(
        approval_id="appr-rej",
        workflow_run_id="wf-test",
        candidate_id="R-alt1",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-1",
        evidence_version="v1.0",
        decision=ApprovalDecision.REJECTED,
        reviewer_id="operator",
    )

    with pytest.raises(ValueError, match="Cannot execute unapproved intervention"):
        adapter.execute_intervention(
            workflow_run_id="wf-test",
            scenario_id="wan_congestion",
            candidate=candidate,
            approval=unapproved,
        )


# ==========================================
# Test 8: Duplicate Approval Idempotency
# ==========================================

def test_08_duplicate_approval_idempotent(orchestrator):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    # First approval
    req = ApprovalRequest(
        decision=ApprovalDecision.APPROVED,
        reviewer_id="operator-dave",
        idempotency_key="idemp-key-123",
    )
    sum1, appr1 = orchestrator.submit_approval(summary.workflow_run_id, req)

    # Duplicate approval with same idempotency key
    sum2, appr2 = orchestrator.submit_approval(summary.workflow_run_id, req)

    assert appr1.approval_id == appr2.approval_id


# ==========================================
# Test 9: Monotonically Sequenced Audit Events
# ==========================================

def test_09_monotonically_sequenced_audit_events(orchestrator, test_storage):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=True)
    )

    events = test_storage.get_workflow_events(summary.workflow_run_id)
    assert len(events) >= 10

    seq_nums = [e.sequence_number for e in events]
    assert seq_nums == list(range(1, len(events) + 1))


# ==========================================
# Test 10: Constraint Regression Detection
# ==========================================

def test_10_post_action_constraint_regression():
    adapter = SimulationActionAdapter()
    
    # Construct a topology where candidate creates a severe overload on an intermediate link
    nodes = {
        "A": TopologyNode(node_id="A"),
        "B": TopologyNode(node_id="B"),
        "C": TopologyNode(node_id="C"),
    }
    edges = {
        "e_ab": TopologyEdge(edge_id="e_ab", source="A", target="B", capacity_mbps=100.0, base_latency_ms=10.0, background_load_mbps=95.0),
        "e_bc": TopologyEdge(edge_id="e_bc", source="B", target="C", capacity_mbps=50.0, base_latency_ms=10.0, background_load_mbps=45.0),
        "e_ac": TopologyEdge(edge_id="e_ac", source="A", target="C", capacity_mbps=100.0, base_latency_ms=15.0, background_load_mbps=10.0),
    }
    flows = {
        "flow1": TrafficFlow(flow_id="flow1", name="Flow 1", source="A", destination="C", demand_mbps=20.0, slo_latency_ms=50.0, nominal_path=["A", "C"]),
    }
    top = NetworkTopology(scenario_id="regress_top", name="Regress Top", nodes=nodes, edges=edges, flows=flows)

    # Candidate reroutes flow1 to traverse congested e_ab and e_bc (demand 20 + 45 > 50 capacity)
    cand = CandidateAction(
        candidate_id="R-bad",
        action_type="REROUTE_FLOW",
        flow_id="flow1",
        source_node="A",
        destination_node="C",
        path=["A", "B", "C"],
    )
    appr = HumanApprovalRecord(
        approval_id="appr-test",
        workflow_run_id="wf-test",
        candidate_id="R-bad",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-1",
        evidence_version="v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="test",
    )

    _, outcome = adapter.execute_intervention(
        workflow_run_id="wf-test",
        scenario_id="wan_congestion",
        candidate=cand,
        approval=appr,
        topology=top,
    )

    assert outcome.overall_impact == OverallImpact.REGRESSED
    assert outcome.post_action_capacity_violations > 0


# ==========================================
# Test 11: FastAPI Workflow REST Endpoints
# ==========================================

def test_11_fastapi_workflow_endpoints():
    client = TestClient(app)

    # 1. POST /api/v1/workflows (initiate)
    res_create = client.post(
        "/api/v1/workflows",
        json={"scenario_id": "wan_congestion", "auto_approve_for_testing": False, "reviewer_id": "api-tester"},
    )
    assert res_create.status_code == 201
    wf_data = res_create.json()
    wf_id = wf_data["workflow_run_id"]
    assert wf_id.startswith("wf-")
    assert wf_data["status"] == "AWAITING_APPROVAL"

    # 2. GET /api/v1/workflows/{id}
    res_get = client.get(f"/api/v1/workflows/{wf_id}")
    assert res_get.status_code == 200
    assert res_get.json()["workflow_run_id"] == wf_id

    # 3. GET /api/v1/workflows/{id}/events
    res_events = client.get(f"/api/v1/workflows/{wf_id}/events")
    assert res_events.status_code == 200
    events = res_events.json()
    assert len(events) >= 8

    # 4. POST /api/v1/workflows/{id}/approval (submit approval)
    res_appr = client.post(
        f"/api/v1/workflows/{wf_id}/approval",
        json={"decision": "APPROVED", "reviewer_id": "api-reviewer", "reviewer_comment": "API test approval."},
    )
    assert res_appr.status_code == 200
    appr_data = res_appr.json()
    assert appr_data["status"] == "COMPLETED"
    assert appr_data["approval_status"] == "APPROVED"

    # 5. GET /api/v1/workflows/{id}/approval
    res_get_appr = client.get(f"/api/v1/workflows/{wf_id}/approval")
    assert res_get_appr.status_code == 200
    assert res_get_appr.json()["decision"] == "APPROVED"

    # 6. GET /api/v1/workflows/{id}/outcome
    res_out = client.get(f"/api/v1/workflows/{wf_id}/outcome")
    assert res_out.status_code == 200
    out_data = res_out.json()
    assert out_data["pre_action_latency_ms"] > 0
    assert out_data["post_action_latency_ms"] > 0

    # 7. GET /api/v1/workflows (list)
    res_list = client.get("/api/v1/workflows")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1


# ==========================================
# Test 12: Simulator Mode & Real-Actuation Disclaimers
# ==========================================

def test_12_simulation_mode_disclaimer(orchestrator, test_storage):
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=True)
    )

    outcome = test_storage.get_outcome(summary.outcome_id)
    assert outcome is not None
    assert any("isolated simulation" in lim.lower() for lim in outcome.assumptions_and_limitations)
    assert any("no real-world router interfaces" in lim.lower() for lim in outcome.assumptions_and_limitations)
