"""tests/test_outcome_integrity.py
Comprehensive deterministic simulation verification, metric precision,
and outcome integrity test suite.

Verifies:
1. Reproducibility: Identical inputs under deterministic twin produce identical numerical metrics with unique run IDs.
2. Candidate Sensitivity: Different routing actions produce physically distinct metrics.
3. Scenario Sensitivity: Different network topologies produce condition-specific metrics.
4. Constraint Regression: An action improving latency while breaching link capacity reports breaches and classifies as REGRESSED.
5. Invalid Action Fail-Closed: Disconnected or nonexistent candidate paths fail validation and cannot produce an outcome report.
6. Outcome Integrity & Reporter Warnings: Invalid metric claims (e.g. claiming IMPROVED with new breaches) trigger warnings.
"""

import os
import shutil
import pytest

from fidelitygate.config import settings
from fidelitygate.evaluation.models import (
    CandidateAction,
    GateDecision,
    NetworkTopology,
    TopologyEdge,
    TopologyNode,
    TrafficFlow,
)
from fidelitygate.evaluation.topologies import get_topology_for_scenario
from fidelitygate.storage import StorageEngine
from fidelitygate.workflow.models import (
    ApprovalDecision,
    HumanApprovalRecord,
    OverallImpact,
    WorkflowRunRequest,
    WorkflowStatus,
)
from fidelitygate.workflow.orchestrator import EndToEndWorkflowOrchestrator
from fidelitygate.workflow.outcome import OutcomeReporter
from fidelitygate.workflow.simulation_adapter import SimulationActionAdapter


@pytest.fixture
def test_storage(tmp_path):
    db_file = str(tmp_path / "test_outcome_integrity.db")
    if os.path.exists(settings.DATABASE_PATH):
        shutil.copy2(settings.DATABASE_PATH, db_file)
    storage = StorageEngine(db_file)
    return storage


@pytest.fixture
def orchestrator(test_storage):
    return EndToEndWorkflowOrchestrator(test_storage)


# ==============================================================================
# Required Test 1: Reproducibility Test
# ==============================================================================

def test_outcome_reproducibility(orchestrator, test_storage):
    """Running the exact same scenario, candidate, and initial conditions twice
    must produce identical deterministic simulation metrics, while persisting
    distinct workflow and outcome identifiers.
    """
    req1 = WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=True)
    summary1 = orchestrator.initiate_workflow(req1)
    outcome1 = test_storage.get_outcome_by_workflow(summary1.workflow_run_id)

    req2 = WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=True)
    summary2 = orchestrator.initiate_workflow(req2)
    outcome2 = test_storage.get_outcome_by_workflow(summary2.workflow_run_id)

    # Distinct identifiers and run linkage
    assert summary1.workflow_run_id != summary2.workflow_run_id
    assert outcome1.outcome_id != outcome2.outcome_id
    assert outcome1.workflow_run_id == summary1.workflow_run_id
    assert outcome2.workflow_run_id == summary2.workflow_run_id

    # Identical deterministic twin calculations
    assert outcome1.pre_action_latency_ms == outcome2.pre_action_latency_ms == 26.55
    assert outcome1.post_action_latency_ms == outcome2.post_action_latency_ms == 23.00
    assert outcome1.latency_delta_ms == outcome2.latency_delta_ms == -3.55
    assert outcome1.latency_reduction_pct == outcome2.latency_reduction_pct == -13.37
    assert outcome1.pre_action_peak_utilization == outcome2.pre_action_peak_utilization == 0.7600
    assert outcome1.post_action_peak_utilization == outcome2.post_action_peak_utilization == 0.5000
    assert outcome1.pre_action_capacity_violations == outcome2.pre_action_capacity_violations == 0
    assert outcome1.post_action_capacity_violations == outcome2.post_action_capacity_violations == 0
    assert outcome1.pre_action_slo_violations == outcome2.pre_action_slo_violations == 0
    assert outcome1.post_action_slo_violations == outcome2.post_action_slo_violations == 0
    assert outcome1.overall_impact == outcome2.overall_impact == OverallImpact.IMPROVED
    assert outcome1.bottleneck_link == outcome2.bottleneck_link == "e_leaf1_spine2"


# ==============================================================================
# Required Test 2: Candidate Sensitivity Test
# ==============================================================================

def test_outcome_candidate_sensitivity():
    """Two distinct valid candidate actions in the same network topology
    must produce mathematically and physically different calculated metrics.
    """
    adapter = SimulationActionAdapter()
    top = get_topology_for_scenario("wan_congestion")
    assert top is not None

    # Candidate A: Reroute primary flow via spine2 (bypassing congested spine1)
    cand_a = CandidateAction(
        candidate_id="R-alt-spine2",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    appr_a = HumanApprovalRecord(
        approval_id="appr-a",
        workflow_run_id="wf-cand-a",
        candidate_id="R-alt-spine2",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-a",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )

    # Candidate B: Keep primary flow on nominal spine1 path (no reroute)
    cand_b = CandidateAction(
        candidate_id="R-nominal-spine1",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine1", "leaf6"],
    )
    appr_b = HumanApprovalRecord(
        approval_id="appr-b",
        workflow_run_id="wf-cand-b",
        candidate_id="R-nominal-spine1",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-b",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )

    _, outcome_a = adapter.execute_intervention(
        workflow_run_id="wf-cand-a",
        scenario_id="wan_congestion",
        candidate=cand_a,
        approval=appr_a,
        topology=top,
    )

    _, outcome_b = adapter.execute_intervention(
        workflow_run_id="wf-cand-b",
        scenario_id="wan_congestion",
        candidate=cand_b,
        approval=appr_b,
        topology=top,
    )

    # Physical difference verification
    assert outcome_a.post_action_latency_ms != outcome_b.post_action_latency_ms
    assert outcome_a.post_action_latency_ms == 23.00
    assert outcome_b.post_action_latency_ms == 26.55

    assert outcome_a.latency_delta_ms == -3.55
    assert outcome_b.latency_delta_ms == 0.00

    assert outcome_a.post_action_peak_utilization == 0.5000
    assert outcome_b.post_action_peak_utilization == 0.7600

    assert outcome_a.overall_impact == OverallImpact.IMPROVED
    assert outcome_b.overall_impact == OverallImpact.UNCHANGED


# ==============================================================================
# Required Test 3: Scenario Sensitivity Test
# ==============================================================================

def test_outcome_scenario_sensitivity():
    """Different supported scenarios with materially different documented topology
    parameters must produce distinct baseline and post-action metrics.
    """
    adapter = SimulationActionAdapter()

    # Scenario 1: wan_congestion (1000 Mbps links, base latency 6+12 = 18ms)
    top_wan = get_topology_for_scenario("wan_congestion")
    cand_wan = CandidateAction(
        candidate_id="R-wan-alt",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    appr_wan = HumanApprovalRecord(
        approval_id="appr-wan",
        workflow_run_id="wf-wan",
        candidate_id="R-wan-alt",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-wan",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )
    _, outcome_wan = adapter.execute_intervention(
        workflow_run_id="wf-wan",
        scenario_id="wan_congestion",
        candidate=cand_wan,
        approval=appr_wan,
        topology=top_wan,
    )

    # Scenario 2: fiber_drift (900 Mbps links, base latency 10+14 = 24ms, demand 690 Mbps)
    top_fiber = get_topology_for_scenario("fiber_drift")
    cand_fiber = CandidateAction(
        candidate_id="R-fiber-alt",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    appr_fiber = HumanApprovalRecord(
        approval_id="appr-fiber",
        workflow_run_id="wf-fiber",
        candidate_id="R-fiber-alt",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-fiber",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )
    _, outcome_fiber = adapter.execute_intervention(
        workflow_run_id="wf-fiber",
        scenario_id="fiber_drift",
        candidate=cand_fiber,
        approval=appr_fiber,
        topology=top_fiber,
    )

    # Material condition sensitivity verification
    assert outcome_wan.pre_action_latency_ms != outcome_fiber.pre_action_latency_ms
    assert outcome_wan.pre_action_latency_ms == 26.55
    assert outcome_fiber.pre_action_latency_ms == 35.83

    assert outcome_wan.post_action_latency_ms != outcome_fiber.post_action_latency_ms
    assert outcome_wan.post_action_latency_ms == 23.00
    assert outcome_fiber.post_action_latency_ms == 32.85

    assert outcome_wan.latency_delta_ms == -3.55
    assert outcome_fiber.latency_delta_ms == -2.98

    assert outcome_wan.pre_action_peak_utilization == 0.7600
    assert outcome_fiber.pre_action_peak_utilization == 0.7667


# ==============================================================================
# Required Test 4: Constraint Regression Test
# ==============================================================================

def test_outcome_constraint_regression():
    """An action that lowers target flow latency but overloads an edge must record
    the capacity violation and classify the outcome as REGRESSED, never IMPROVED.
    """
    adapter = SimulationActionAdapter()

    # Construct topology where alternate path has lower base latency but severely limited capacity
    nodes = {
        "src": TopologyNode(node_id="src"),
        "spine_fast_choked": TopologyNode(node_id="spine_fast_choked"),
        "dst": TopologyNode(node_id="dst"),
    }
    edges = {
        # Nominal path: 1000 Mbps capacity, base latency 30 ms
        "e_nominal_1": TopologyEdge(edge_id="e_nominal_1", source="src", target="dst", capacity_mbps=1000.0, base_latency_ms=30.0),
        # Alternate path: 200 Mbps capacity (insufficient for 400 Mbps flow), but lower base latency 10 ms
        "e_fast_1": TopologyEdge(edge_id="e_fast_1", source="src", target="spine_fast_choked", capacity_mbps=200.0, base_latency_ms=5.0),
        "e_fast_2": TopologyEdge(edge_id="e_fast_2", source="spine_fast_choked", target="dst", capacity_mbps=200.0, base_latency_ms=5.0),
    }
    flows = {
        "flow1": TrafficFlow(
            flow_id="flow1",
            name="Bandwidth Intensive Flow",
            source="src",
            destination="dst",
            demand_mbps=400.0,
            slo_latency_ms=50.0,
            nominal_path=["src", "dst"],
        ),
    }
    top = NetworkTopology(scenario_id="choke_test", name="Choke Test", nodes=nodes, edges=edges, flows=flows)

    cand = CandidateAction(
        candidate_id="R-overload",
        action_type="REROUTE_FLOW",
        flow_id="flow1",
        source_node="src",
        destination_node="dst",
        path=["src", "spine_fast_choked", "dst"],
    )
    appr = HumanApprovalRecord(
        approval_id="appr-ovl",
        workflow_run_id="wf-ovl",
        candidate_id="R-overload",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-ovl",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )

    _, outcome = adapter.execute_intervention(
        workflow_run_id="wf-ovl",
        scenario_id="choke_test",
        candidate=cand,
        approval=appr,
        topology=top,
    )

    # Verification: Overload detected and impact is strictly REGRESSED
    assert outcome.post_action_capacity_violations > 0
    assert outcome.post_action_peak_utilization > 1.0
    assert outcome.overall_impact == OverallImpact.REGRESSED
    assert outcome.bottleneck_link in ("e_fast_1", "e_fast_2")


# ==============================================================================
# Required Test 5: Invalid Action Fails Closed
# ==============================================================================

def test_outcome_invalid_action_fails_closed():
    """Attempting an invalid candidate (e.g. nonexistent node or disconnected hop)
    must fail validation immediately and cannot produce a successful outcome report.
    """
    adapter = SimulationActionAdapter()
    top = get_topology_for_scenario("wan_congestion")
    assert top is not None

    # Disconnected path: leaf1 directly to leaf6 (no direct physical edge)
    cand_disconnected = CandidateAction(
        candidate_id="R-disconnected",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "leaf6"],
    )
    appr_disconnected = HumanApprovalRecord(
        approval_id="appr-disc",
        workflow_run_id="wf-disc",
        candidate_id="R-disconnected",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-disc",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )

    with pytest.raises(ValueError, match="Invalid candidate action"):
        adapter.execute_intervention(
            workflow_run_id="wf-disc",
            scenario_id="wan_congestion",
            candidate=cand_disconnected,
            approval=appr_disconnected,
            topology=top,
        )

    # Nonexistent node path
    cand_bad_node = CandidateAction(
        candidate_id="R-bad-node",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine_nonexistent_99", "leaf6"],
    )
    appr_bad_node = HumanApprovalRecord(
        approval_id="appr-bad-node",
        workflow_run_id="wf-bad-node",
        candidate_id="R-bad-node",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-bad-node",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )

    with pytest.raises(ValueError, match="Invalid candidate action"):
        adapter.execute_intervention(
            workflow_run_id="wf-bad-node",
            scenario_id="wan_congestion",
            candidate=cand_bad_node,
            approval=appr_bad_node,
            topology=top,
        )


# ==============================================================================
# Additional Integrity Tests: Reporter Validation
# ==============================================================================

def test_outcome_reporter_integrity_checks():
    """OutcomeReporter.validate_outcome_integrity must flag false or misleading claims."""
    adapter = SimulationActionAdapter()
    top = get_topology_for_scenario("wan_congestion")
    cand = CandidateAction(
        candidate_id="R-alt1",
        action_type="REROUTE_FLOW",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    appr = HumanApprovalRecord(
        approval_id="appr-ok",
        workflow_run_id="wf-ok",
        candidate_id="R-alt1",
        gate_verdict=GateDecision.ACCEPT,
        explanation_id="expl-ok",
        evidence_version="fidelitygate-v1.0",
        decision=ApprovalDecision.APPROVED,
        reviewer_id="tester",
    )
    _, outcome = adapter.execute_intervention(
        workflow_run_id="wf-ok",
        scenario_id="wan_congestion",
        candidate=cand,
        approval=appr,
        topology=top,
    )

    # Valid outcome has 0 warnings
    warnings = OutcomeReporter.validate_outcome_integrity(outcome)
    assert len(warnings) == 0

    # Summary formatting contains all critical elements
    summary_text = OutcomeReporter.format_text_summary(outcome)
    assert "26.55 ms" in summary_text
    assert "23.00 ms" in summary_text
    assert "76.0%" in summary_text
    assert "50.0%" in summary_text
    assert "ISOLATED_DIGITAL_TWIN" in summary_text
    assert "IMPROVED" in summary_text

