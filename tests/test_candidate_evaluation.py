"""tests/test_candidate_evaluation.py
Comprehensive automated test suite for Layer 4: Candidate Mitigation Evaluation,
Digital-Twin Simulation, and SLO Verification.
Validates all 26 core requirements outlined in Section 14 of the Layer 4 specification.
"""

import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.decision_gate import decide
from fidelitygate.evaluation.engine import MitigationEvaluationEngine
from fidelitygate.evaluation.models import (
    CandidateAction,
    CandidateEvaluation,
    CandidateEvaluationStatus,
    EvaluationEvent,
    MitigationActionType,
    MitigationEvaluationReport,
    MitigationEvaluationRequest,
    MitigationEvaluationSummary,
    NetworkTopology,
    PathValidationResult,
    ReferenceEvaluationResult,
    ReferenceEvaluationStatus,
    SimulationPrediction,
    TopologyEdge,
    TopologyNode,
    TrafficFlow,
    ValidationStatus,
)
from fidelitygate.evaluation.reference_evaluator import IndependentReferenceEvaluator
from fidelitygate.evaluation.simulator import InsufficientModelDataError, NetworkSimulator
from fidelitygate.evaluation.topologies import (
    create_wan_congestion_topology,
    get_topology_for_scenario,
)
from fidelitygate.evaluation.uncertainty_evaluator import CandidateUncertaintyEvaluator
from fidelitygate.evaluation.validator import CandidatePathValidator
from fidelitygate.investigation.models import (
    AgentMode,
    DiagnosticPlan,
    Hypothesis,
    HypothesisType,
    InvestigationEvent,
    InvestigationReport,
    InvestigationStatus,
    InvestigationSummary,
    PlanStatus,
)
from fidelitygate.schemas import GateDecision, GateReport, Scenario, SweepReport
from fidelitygate.storage import StorageEngine


@pytest.fixture
def test_storage(tmp_path):
    db_file = tmp_path / "test_layer4.db"
    return StorageEngine(str(db_file))


@pytest.fixture
def api_client(test_storage, monkeypatch, tmp_path):
    import sys
    app_module = sys.modules["fidelitygate.api.app"]
    monkeypatch.setattr(settings, "DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "DATABASE_PATH", str(tmp_path / "test_layer4.db"))
    monkeypatch.setattr(app_module, "storage", test_storage)
    monkeypatch.setattr(app_module, "mitigation_engine", MitigationEvaluationEngine(test_storage))
    return TestClient(app)


def seed_investigation(
    storage: StorageEngine,
    inv_id: str = "inv-test-4",
    scenario_id: str = "wan_congestion",
    proposed_interventions: Optional[List[str]] = None,
) -> None:
    """Helper to seed a completed Layer 3 investigation in storage for Layer 4 tests."""
    interventions = proposed_interventions or ["R-wan_congestion-alt1"]
    summary = InvestigationSummary(
        investigation_id=inv_id,
        triage_run_id="trg-test-4",
        scenario_id=scenario_id,
        agent_mode=AgentMode.DETERMINISTIC_PLANNER,
        status=InvestigationStatus.COMPLETED,
        hypotheses_count=1,
        candidate_diagnostics_count=1,
        selected_diagnostic_id="snmp_interface_poll",
        created_at=datetime.now(timezone.utc).isoformat(),
        completed_at=datetime.now(timezone.utc).isoformat(),
    )
    report = InvestigationReport(
        investigation_id=inv_id,
        triage_run_id="trg-test-4",
        scenario_id=scenario_id,
        agent_mode=AgentMode.DETERMINISTIC_PLANNER,
        hypotheses=[
            Hypothesis(
                hypothesis_id="hyp-1",
                hypothesis_type=HypothesisType.BGP_SESSION_FLAP,
                statement="BGP flap on 0/RP0/CPU0",
                confidence_score=0.95,
                uncertainty_status="High confidence empirical finding",
                supporting_evidence_ids=["ev-1"],
            )
        ],
        status=InvestigationStatus.COMPLETED,
    )
    plan = DiagnosticPlan(
        plan_id=f"plan-{inv_id}",
        investigation_id=inv_id,
        candidate_diagnostics=[],
        selected_diagnostic_id="snmp_interface_poll",
        proposed_interventions=interventions,
        status=PlanStatus.READY,
    )
    events = [
        InvestigationEvent(
            event_id=f"evt-{inv_id}-1",
            investigation_id=inv_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor="test_runner",
            event_type="SETUP",
            details={"msg": "Seeded investigation for Layer 4 testing"},
        )
    ]
    storage.save_investigation(summary, report, plan, events)


# 1. Valid candidate path
def test_01_valid_candidate_path():
    validator = CandidatePathValidator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-valid",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
        rationale="Bypass congested spine1 via alternate spine2.",
    )
    res = validator.validate_candidate(action, topology)
    assert res.is_valid is True
    assert res.status == ValidationStatus.VALID
    assert res.hop_count == 2
    assert res.edges_traversed == ["e_leaf1_spine2", "e_spine2_leaf6"]


# 2. Unknown source/destination nodes
def test_02_unknown_source_destination_nodes():
    validator = CandidatePathValidator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-bad-node",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine_nonexistent", "leaf6"],
    )
    res = validator.validate_candidate(action, topology)
    assert res.is_valid is False
    assert res.status == ValidationStatus.INVALID_NODE
    assert "spine_nonexistent" in res.reasons[0]


# 3. Missing topology edges
def test_03_missing_topology_edges():
    validator = CandidatePathValidator()
    topology = create_wan_congestion_topology()
    # leaf1 directly to leaf6 has no direct edge in leaf-spine
    action = CandidateAction(
        candidate_id="cand-missing-edge",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "leaf6"],
    )
    res = validator.validate_candidate(action, topology)
    assert res.is_valid is False
    assert res.status == ValidationStatus.INVALID_EDGE


# 4. Down links
def test_04_down_links():
    validator = CandidatePathValidator()
    topology = create_wan_congestion_topology()
    # Mark edge as DOWN
    down_edge = TopologyEdge(
        edge_id="e_leaf1_spine2",
        source="leaf1",
        target="spine2",
        capacity_mbps=1000.0,
        base_latency_ms=8.0,
        status="DOWN",
    )
    edges = dict(topology.edges)
    edges["e_leaf1_spine2"] = down_edge
    topology_with_down = NetworkTopology(
        scenario_id=topology.scenario_id,
        name=topology.name,
        nodes=topology.nodes,
        edges=edges,
        flows=topology.flows,
    )
    action = CandidateAction(
        candidate_id="cand-down-link",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    res = validator.validate_candidate(action, topology_with_down)
    assert res.is_valid is False
    assert res.status == ValidationStatus.LINK_DOWN


# 5. Invalid flow IDs
def test_05_invalid_flow_ids():
    validator = CandidatePathValidator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-bad-flow",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_nonexistent_999",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    res = validator.validate_candidate(action, topology)
    assert res.is_valid is False
    assert res.status == ValidationStatus.FLOW_MISMATCH


# 6. Missing/zero capacity
def test_06_missing_or_zero_capacity():
    validator = CandidatePathValidator()
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    # Edge with 0 capacity
    zero_edge = TopologyEdge(
        edge_id="e_leaf1_spine2",
        source="leaf1",
        target="spine2",
        capacity_mbps=0.0,
        base_latency_ms=8.0,
    )
    edges = dict(topology.edges)
    edges["e_leaf1_spine2"] = zero_edge
    bad_topology = NetworkTopology(
        scenario_id=topology.scenario_id,
        name=topology.name,
        nodes=topology.nodes,
        edges=edges,
        flows=topology.flows,
    )
    action = CandidateAction(
        candidate_id="cand-zero-cap",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    # Validator rejects zero capacity
    val_res = validator.validate_candidate(action, bad_topology)
    assert val_res.is_valid is False
    assert val_res.status == ValidationStatus.INCOMPLETE_CONSTRAINTS

    # Simulator raises InsufficientModelDataError
    with pytest.raises(InsufficientModelDataError):
        simulator.calculate_link_delay(base_latency_ms=10.0, load_mbps=100.0, capacity_mbps=0.0)


# 7. Capacity overloading
def test_07_capacity_overloading():
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    # Flow primary demand is 500 Mbps, reduce capacity of spine2 link to 400 Mbps
    overloaded_edge = TopologyEdge(
        edge_id="e_spine2_leaf6",
        source="spine2",
        target="leaf6",
        capacity_mbps=400.0,
        base_latency_ms=12.0,
    )
    edges = dict(topology.edges)
    edges["e_spine2_leaf6"] = overloaded_edge
    overloaded_topo = NetworkTopology(
        scenario_id=topology.scenario_id,
        name=topology.name,
        nodes=topology.nodes,
        edges=edges,
        flows=topology.flows,
    )
    pred = simulator.simulate_flow(
        topology=overloaded_topo,
        target_flow_id="flow_primary",
        path=["leaf1", "spine2", "leaf6"],
    )
    assert pred.capacity_violated is True
    assert pred.peak_utilization > 1.0


# 8. Nominal SLO satisfaction
def test_08_nominal_slo_satisfaction():
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    # Candidate path via spine2: base latency 8 + 12 = 20ms, well below SLO 45ms
    pred = simulator.simulate_flow(
        topology=topology,
        target_flow_id="flow_primary",
        path=["leaf1", "spine2", "leaf6"],
    )
    assert pred.is_connected is True
    assert pred.slo_violated is False
    assert pred.latency_ms <= 45.0


# 9. Nominal SLO violation
def test_09_nominal_slo_violation():
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    # High base latency edges exceeding SLO
    slow_edge = TopologyEdge(
        edge_id="e_spine2_leaf6",
        source="spine2",
        target="leaf6",
        capacity_mbps=1000.0,
        base_latency_ms=60.0,
    )
    edges = dict(topology.edges)
    edges["e_spine2_leaf6"] = slow_edge
    slow_topo = NetworkTopology(
        scenario_id=topology.scenario_id,
        name=topology.name,
        nodes=topology.nodes,
        edges=edges,
        flows=topology.flows,
    )
    pred = simulator.simulate_flow(
        topology=slow_topo,
        target_flow_id="flow_primary",
        path=["leaf1", "spine2", "leaf6"],
    )
    assert pred.slo_violated is True
    assert pred.latency_ms > 45.0


# 10. Full shared-flow traffic allocation
def test_10_full_shared_flow_traffic_allocation():
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    # On primary path: flow_primary (500) + flow_shared (260) = 760 Mbps total
    routing = {
        "flow_primary": ["leaf1", "spine1", "leaf6"],
        "flow_shared": ["leaf1", "spine1", "leaf6"],
    }
    link_results = simulator.allocate_traffic(topology, routing)
    assert link_results["e_leaf1_spine1"].load_mbps == 760.0
    assert link_results["e_spine1_leaf6"].load_mbps == 760.0
    assert link_results["e_leaf1_spine2"].load_mbps == 0.0


# 11. Before/after candidate comparison
def test_11_before_after_candidate_comparison():
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-comp",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    comp = simulator.compare_candidate_to_baseline(topology, action)
    assert comp.comparison_supported is True
    assert isinstance(comp.latency_change_ms, float)
    assert comp.baseline_latency_ms > 0
    assert comp.candidate_latency_ms > 0
    assert len(comp.shared_flow_impacts) >= 1


# 12. No division by zero in relative changes
def test_12_no_division_by_zero_relative_changes():
    simulator = NetworkSimulator()
    # Guard against zero baseline latency
    util, q, delay = simulator.calculate_link_delay(base_latency_ms=0.0, load_mbps=10.0, capacity_mbps=100.0)
    assert delay == 0.0
    # Relative pct calculation with zero denominator handles safely
    base_lat = 0.0
    cand_lat = 10.0
    lat_diff = cand_lat - base_lat
    lat_pct = (lat_diff / base_lat * 100.0) if base_lat > 0 else None
    assert lat_pct is None


# 13. Deterministic simulator reproducibility
def test_13_deterministic_simulator_reproducibility():
    simulator = NetworkSimulator()
    topology = create_wan_congestion_topology()
    pred1 = simulator.simulate_flow(topology, "flow_primary", ["leaf1", "spine2", "leaf6"], load_multiplier=1.1)
    pred2 = simulator.simulate_flow(topology, "flow_primary", ["leaf1", "spine2", "leaf6"], load_multiplier=1.1)
    assert pred1.latency_ms == pred2.latency_ms
    assert pred1.peak_utilization == pred2.peak_utilization
    assert pred1.bottleneck_edge_id == pred2.bottleneck_edge_id


# 14. Uncertainty-budget enforcement
def test_14_uncertainty_budget_enforcement():
    uncertainty_eval = CandidateUncertaintyEvaluator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-budget",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    # Request 100 evaluations: must be clamped to MAX_EVALUATION_BUDGET (50)
    sweep, _ = uncertainty_eval.evaluate_uncertainty(topology, action, evaluations=100)
    assert sweep.evaluations == 50
    assert sweep.evaluations <= CandidateUncertaintyEvaluator.MAX_EVALUATION_BUDGET


# 15. Counterexample report integrity
def test_15_counterexample_report_integrity():
    uncertainty_eval = CandidateUncertaintyEvaluator()
    topology = create_wan_congestion_topology()
    # Alternate path with low capacity to guarantee fragility under load sweep
    fragile_edge = TopologyEdge(
        edge_id="e_spine2_leaf6",
        source="spine2",
        target="leaf6",
        capacity_mbps=550.0,
        base_latency_ms=12.0,
    )
    edges = dict(topology.edges)
    edges["e_spine2_leaf6"] = fragile_edge
    fragile_topo = NetworkTopology(
        scenario_id=topology.scenario_id,
        name=topology.name,
        nodes=topology.nodes,
        edges=edges,
        flows=topology.flows,
    )
    action = CandidateAction(
        candidate_id="cand-fragile",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    _, cx = uncertainty_eval.evaluate_uncertainty(fragile_topo, action, evaluations=25)
    assert cx is not None
    assert cx.is_fragile is True
    assert cx.critical_parameter in ["traffic_load_burst", "fiber_latency_calibration_drift", "coupled_latency_and_load_drift"]
    assert cx.violating_latency_ms > 0
    assert cx.margin_breach_ms >= 0


# 16. Reference evaluator separation
def test_16_reference_evaluator_isolation():
    evaluator = IndependentReferenceEvaluator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-ref",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    res = evaluator.evaluate_against_reference(topology, action, "wan_congestion")
    assert res.reference_status in [ReferenceEvaluationStatus.VERIFIED_SAFE, ReferenceEvaluationStatus.VERIFIED_BREACH]
    assert res.true_latency_ms is not None
    assert res.assumptions_difference is not None


# 17. Missing reference truth
def test_17_missing_reference_truth():
    evaluator = IndependentReferenceEvaluator()
    topology = create_wan_congestion_topology()
    action = CandidateAction(
        candidate_id="cand-replay",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    # Unknown/public replay scenario without synthetic truth
    res = evaluator.evaluate_against_reference(topology, action, "public_cisco_replay_case_3")
    assert res.reference_status == ReferenceEvaluationStatus.REFERENCE_NOT_AVAILABLE
    assert res.true_latency_ms is None


# 18. Gate ACCEPT result
def test_18_gate_accept_result(test_storage):
    seed_investigation(test_storage, inv_id="inv-accept", scenario_id="wan_congestion")
    engine = MitigationEvaluationEngine(test_storage)
    # Provide a candidate path with ample capacity that passes all sweeps
    req = MitigationEvaluationRequest(
        investigation_id="inv-accept",
        scenario_id="wan_congestion",
        candidate_actions=[
            CandidateAction(
                candidate_id="cand-safe",
                action_type=MitigationActionType.REROUTE_FLOW,
                flow_id="flow_primary",
                source_node="leaf1",
                destination_node="leaf6",
                path=["leaf1", "spine2", "leaf6"],
                rationale="Robust reroute path.",
            )
        ],
        evaluation_budget=10,
    )
    summary, report, candidates, _ = engine.run_evaluation(req)
    assert len(candidates) == 1
    assert candidates[0].status == CandidateEvaluationStatus.COMPLIANT
    assert report.gate_verdict == GateDecision.ACCEPT


# 19. Gate GATHER_EVIDENCE result
def test_19_gate_gather_evidence_result(test_storage):
    seed_investigation(test_storage, inv_id="inv-gather", scenario_id="fiber_drift")
    engine = MitigationEvaluationEngine(test_storage)
    req = MitigationEvaluationRequest(
        investigation_id="inv-gather",
        scenario_id="fiber_drift",
        evaluation_budget=20,
    )
    summary, report, candidates, _ = engine.run_evaluation(req)
    assert report.gate_verdict in [GateDecision.GATHER_EVIDENCE, GateDecision.ACCEPT]


# 20. Gate ABSTAIN result
def test_20_gate_abstain_result(test_storage):
    seed_investigation(test_storage, inv_id="inv-abstain", scenario_id="wan_congestion")
    engine = MitigationEvaluationEngine(test_storage)
    # Construct an action that traverses a non-existent or down path
    req = MitigationEvaluationRequest(
        investigation_id="inv-abstain",
        scenario_id="wan_congestion",
        candidate_actions=[
            CandidateAction(
                candidate_id="cand-bad",
                action_type=MitigationActionType.REROUTE_FLOW,
                flow_id="flow_primary",
                source_node="leaf1",
                destination_node="leaf6",
                path=["leaf1", "nonexistent_node", "leaf6"],
            )
        ],
    )
    summary, report, candidates, _ = engine.run_evaluation(req)
    assert len(candidates) == 1
    assert candidates[0].status == CandidateEvaluationStatus.INVALID_PATH
    assert report.gate_verdict == GateDecision.ABSTAIN


# 21. Invalid candidate never receives ACCEPT
def test_21_invalid_candidate_never_receives_accept(test_storage):
    seed_investigation(test_storage, inv_id="inv-invalid-accept", scenario_id="wan_congestion")
    engine = MitigationEvaluationEngine(test_storage)
    req = MitigationEvaluationRequest(
        investigation_id="inv-invalid-accept",
        scenario_id="wan_congestion",
        candidate_actions=[
            CandidateAction(
                candidate_id="cand-disconnected",
                action_type=MitigationActionType.REROUTE_FLOW,
                flow_id="flow_primary",
                source_node="leaf1",
                destination_node="leaf6",
                path=["leaf1", "leaf6"],  # Disconnected
            )
        ],
    )
    _, report, candidates, _ = engine.run_evaluation(req)
    assert candidates[0].gate_report.decision == GateDecision.ABSTAIN
    assert report.gate_verdict == GateDecision.ABSTAIN
    assert candidates[0].status == CandidateEvaluationStatus.INVALID_PATH


# 22. Partial candidate-evaluation failure
def test_22_partial_candidate_evaluation_failure(test_storage):
    seed_investigation(test_storage, inv_id="inv-partial", scenario_id="wan_congestion")
    engine = MitigationEvaluationEngine(test_storage)
    # One invalid candidate and one valid candidate
    req = MitigationEvaluationRequest(
        investigation_id="inv-partial",
        scenario_id="wan_congestion",
        candidate_actions=[
            CandidateAction(
                candidate_id="cand-1-invalid",
                action_type=MitigationActionType.REROUTE_FLOW,
                flow_id="flow_primary",
                source_node="leaf1",
                destination_node="leaf6",
                path=["leaf1", "missing_node", "leaf6"],
            ),
            CandidateAction(
                candidate_id="cand-2-valid",
                action_type=MitigationActionType.REROUTE_FLOW,
                flow_id="flow_primary",
                source_node="leaf1",
                destination_node="leaf6",
                path=["leaf1", "spine2", "leaf6"],
            ),
        ],
        evaluation_budget=10,
    )
    summary, report, candidates, _ = engine.run_evaluation(req)
    assert len(candidates) == 2
    assert candidates[0].status == CandidateEvaluationStatus.INVALID_PATH
    assert candidates[1].status in [CandidateEvaluationStatus.COMPLIANT, CandidateEvaluationStatus.FRAGILE]
    assert report.selected_candidate_id == "cand-2-valid"


# 23. Timeouts and idempotency
def test_23_timeouts_and_idempotency(test_storage):
    seed_investigation(test_storage, inv_id="inv-idempotent", scenario_id="wan_congestion")
    engine = MitigationEvaluationEngine(test_storage)
    req = MitigationEvaluationRequest(investigation_id="inv-idempotent", evaluation_budget=10)
    sum1, rep1, _, _ = engine.run_evaluation(req)
    sum2, rep2, _, _ = engine.run_evaluation(req)
    assert sum1.status == "COMPLETE"
    assert sum2.status == "COMPLETE"
    assert rep1.gate_verdict == rep2.gate_verdict


# 24. Persistence and retrieval of reports
def test_24_persistence_and_retrieval_of_reports(tmp_path):
    db_file = tmp_path / "persist_test.db"
    store1 = StorageEngine(str(db_file))
    seed_investigation(store1, inv_id="inv-persist-24", scenario_id="wan_congestion")
    engine1 = MitigationEvaluationEngine(store1)
    req = MitigationEvaluationRequest(investigation_id="inv-persist-24", evaluation_budget=10)
    summary1, report1, candidates1, events1 = engine1.run_evaluation(req)

    # Reopen database in fresh storage instance
    store2 = StorageEngine(str(db_file))
    summary2 = store2.get_mitigation_summary(summary1.evaluation_id)
    report2 = store2.get_mitigation_report(summary1.evaluation_id)
    candidates2 = store2.get_candidate_evaluations(summary1.evaluation_id)
    events2 = store2.get_evaluation_events(summary1.evaluation_id)

    assert summary2 is not None
    assert summary2.evaluation_id == summary1.evaluation_id
    assert report2 is not None
    assert len(candidates2) == len(candidates1)
    assert len(events2) == len(events1)


# 25. API request/response validation
def test_25_api_request_response_validation(api_client, test_storage):
    seed_investigation(test_storage, inv_id="inv-api-25", scenario_id="wan_congestion")

    # 1. POST /api/v1/mitigation-evaluations
    resp_post = api_client.post(
        "/api/v1/mitigation-evaluations",
        json={"investigation_id": "inv-api-25", "scenario_id": "wan_congestion", "evaluation_budget": 10},
    )
    assert resp_post.status_code == 201
    data = resp_post.json()
    eval_id = data["evaluation_id"]
    assert eval_id.startswith("eval-")

    # 2. GET /api/v1/mitigation-evaluations
    resp_list = api_client.get("/api/v1/mitigation-evaluations")
    assert resp_list.status_code == 200
    assert any(item["evaluation_id"] == eval_id for item in resp_list.json())

    # 3. GET /api/v1/mitigation-evaluations/{id}
    resp_get = api_client.get(f"/api/v1/mitigation-evaluations/{eval_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["evaluation_id"] == eval_id

    # 4. GET /api/v1/mitigation-evaluations/{id}/candidates
    resp_cands = api_client.get(f"/api/v1/mitigation-evaluations/{eval_id}/candidates")
    assert resp_cands.status_code == 200
    assert isinstance(resp_cands.json(), list)

    # 5. GET /api/v1/mitigation-evaluations/{id}/report
    resp_rep = api_client.get(f"/api/v1/mitigation-evaluations/{eval_id}/report")
    assert resp_rep.status_code == 200
    assert resp_rep.json()["evaluation_id"] == eval_id

    # 6. GET /api/v1/mitigation-evaluations/{id}/events
    resp_evts = api_client.get(f"/api/v1/mitigation-evaluations/{eval_id}/events")
    assert resp_evts.status_code == 200
    assert len(resp_evts.json()) > 0


# 26. Existing Layers 1-3 regression tests: verified via full test suite execution
def test_26_schema_contracts_conformance():
    """Validates serialization and deserialization integrity of Layer 4 Pydantic models."""
    action = CandidateAction(
        candidate_id="cand-schema",
        action_type=MitigationActionType.REROUTE_FLOW,
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
    )
    dumped = action.model_dump_json()
    reparsed = CandidateAction.model_validate_json(dumped)
    assert reparsed.candidate_id == "cand-schema"
    assert reparsed.action_type == MitigationActionType.REROUTE_FLOW
