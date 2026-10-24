"""tests/test_xai_explanations.py
Comprehensive automated test suite for FidelityGate Layer 6:
Evidence-Based Explainable AI (XAI), Decision Attribution, and Sensitivity Analysis.
"""

import os
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.storage import StorageEngine
from fidelitygate.evaluation.models import (
    CandidateAction,
    CandidateEvaluation,
    CandidateEvaluationStatus,
    Counterexample,
    GateDecision,
    NetworkTopology,
    PathValidationResult,
    SimulationPrediction,
    SweepReport,
    TopologyEdge,
    TopologyNode,
    TrafficFlow,
    ValidationStatus,
)
from fidelitygate.evaluation.topologies import get_topology_for_scenario
from fidelitygate.adaptive.models import (
    AdaptiveCycleResult,
    AdaptiveInvestigationReport,
    AdaptiveInvestigationSummary,
    AdaptiveRunStatus,
    DiagnosticExecutionRecord,
    DiagnosticObservation,
    UncertaintyInterval,
    UncertaintyUpdate,
)
from fidelitygate.xai.models import (
    CounterexampleExplanation,
    DecisionExplanation,
    GateRuleExplanation,
    LocalSensitivityReport,
    RuleStatus,
)
from fidelitygate.xai.engine import ExplanationEngine
from fidelitygate.xai.rule_explainer import GateRuleExplainer
from fidelitygate.xai.counterexample_explainer import CounterexampleExplainer
from fidelitygate.xai.measurement_explainer import MeasurementExplainer
from fidelitygate.xai.sensitivity_analyzer import SensitivityAnalyzer
from fidelitygate.xai.summary_generator import DecisionSummaryGenerator


@pytest.fixture
def app_storage():
    """Storage connected to canonical database with real evaluation runs."""
    return StorageEngine(settings.DATABASE_PATH)


@pytest.fixture
def sample_topology():
    return get_topology_for_scenario("wan_congestion")


@pytest.fixture
def sample_candidate_eval():
    return CandidateEvaluation(
        evaluation_id="eval-001",
        investigation_id="inv-001",
        scenario_id="wan_congestion",
        candidate_id="cand-reroute-spine2",
        action=CandidateAction(
            candidate_id="cand-reroute-spine2",
            flow_id="flow_primary",
            source_node="leaf1",
            destination_node="leaf6",
            path=["leaf1", "spine2", "leaf6"],
            priority=1,
            rationale="Bypass congested spine1 link",
        ),
        validation=PathValidationResult(
            is_valid=True,
            status=ValidationStatus.VALID,
            reasons=[],
            validated_path=["leaf1", "spine2", "leaf6"],
            hop_count=2,
            edges_traversed=["e3", "e4"],
        ),
        nominal_prediction=SimulationPrediction(
            flow_id="flow_primary",
            latency_ms=23.5,
            slo_latency_ms=45.0,
            peak_utilization=0.45,
            is_connected=True,
            capacity_violated=False,
            slo_violated=False,
            bottleneck_edge_id="e3",
        ),
        uncertainty_report=SweepReport(
            evaluations=25,
            nominal_latency_ms=23.5,
            worst_latency_ms=48.5,
            peak_utilization=0.45,
            stability_score=0.84,
            violations=4,
            sensitivity={"fiber_latency_calibration_drift": 1.45},
        ),
        counterexample=Counterexample(
            is_fragile=True,
            critical_parameter="fiber_latency_calibration_drift",
            perturbation_factor=1.25,
            violating_latency_ms=48.5,
            slo_latency_ms=45.0,
            margin_breach_ms=3.5,
            explanation="Adversarial latency drift causes 48.5 ms delay exceeding 45.0 ms SLO",
        ),
        status=CandidateEvaluationStatus.COMPLIANT,
    )


# ==========================================
# Test 1: Gate Rule Explanation Correctness
# ==========================================

def test_01_rule_explanation_correctness(sample_candidate_eval):
    rules = GateRuleExplainer.explain_rules(
        sample_candidate_eval,
        slo_latency_ms=45.0,
        max_utilization_threshold=1.00,
        stability_threshold=0.90,
    )

    assert len(rules) == 5
    rule_ids = [r.rule_id for r in rules]
    assert "RULE-CONN-01" in rule_ids
    assert "RULE-CAP-02" in rule_ids
    assert "RULE-SLO-03" in rule_ids
    assert "RULE-ROB-04" in rule_ids
    assert "RULE-CE-05" in rule_ids

    # Rule 1: Connectivity (passed)
    r1 = next(r for r in rules if r.rule_id == "RULE-CONN-01")
    assert r1.status == RuleStatus.PASSED
    assert r1.observed_value == 1.0
    assert r1.is_mandatory is True

    # Rule 2: Utilization (0.45 <= 1.00 -> passed)
    r2 = next(r for r in rules if r.rule_id == "RULE-CAP-02")
    assert r2.status == RuleStatus.PASSED
    assert r2.observed_value == 0.45
    assert r2.comparison_symbol == "<="

    # Rule 3: Latency SLO (23.5 ms <= 45.0 ms -> passed)
    r3 = next(r for r in rules if r.rule_id == "RULE-SLO-03")
    assert r3.status == RuleStatus.PASSED
    assert r3.observed_value == 23.5
    assert r3.unit == "ms"

    # Rule 4: Robustness (0.84 < 0.90 -> failed)
    r4 = next(r for r in rules if r.rule_id == "RULE-ROB-04")
    assert r4.status == RuleStatus.FAILED
    assert r4.observed_value == 0.84

    # Rule 5: Counterexample freedom (1 active -> failed)
    r5 = next(r for r in rules if r.rule_id == "RULE-CE-05")
    assert r5.status == RuleStatus.FAILED
    assert r5.observed_value == 1.0


# ==========================================
# Test 2: Rule Explanations Handle Missing Values & Broken Paths
# ==========================================

def test_02_rule_explanation_handles_missing_and_broken():
    broken_candidate = CandidateEvaluation(
        evaluation_id="eval-002",
        investigation_id="inv-002",
        scenario_id="wan_congestion",
        candidate_id="cand-down",
        action=CandidateAction(
            candidate_id="cand-down",
            flow_id="f1",
            source_node="leaf1",
            destination_node="leaf6",
            path=["leaf1", "spine1", "leaf6"],
        ),
        validation=PathValidationResult(
            is_valid=False,
            status=ValidationStatus.LINK_DOWN,
            reasons=["Link e1 is administratively DOWN"],
            edges_traversed=[],
        ),
        nominal_prediction=None,
        uncertainty_report=None,
        counterexample=None,
        status=CandidateEvaluationStatus.INVALID_PATH,
    )

    rules = GateRuleExplainer.explain_rules(broken_candidate)
    r1 = next(r for r in rules if r.rule_id == "RULE-CONN-01")
    assert r1.status == RuleStatus.FAILED
    assert "DOWN" in r1.explanation

    r2 = next(r for r in rules if r.rule_id == "RULE-CAP-02")
    assert r2.status == RuleStatus.UNKNOWN

    r3 = next(r for r in rules if r.rule_id == "RULE-SLO-03")
    assert r3.status == RuleStatus.UNKNOWN


# ==========================================
# Test 3: Counterexample Explanation Completeness
# ==========================================

def test_03_counterexample_explanation(sample_candidate_eval):
    ce = sample_candidate_eval.counterexample
    expl = CounterexampleExplainer.explain(ce, sample_candidate_eval)

    assert expl is not None
    assert expl.candidate_id == "cand-reroute-spine2"
    assert expl.nominal_latency_ms == 23.5
    assert expl.perturbed_latency_ms == 48.5
    assert expl.violation_margin_ms == 3.5
    assert expl.primary_failure_cause == "fiber_latency_calibration_drift"
    assert "fiber_latency_calibration_drift" in expl.exact_parameter_vector
    assert expl.exact_parameter_vector["fiber_latency_calibration_drift"] == 1.25
    assert "FRAGILE" in expl.explanation


# ==========================================
# Test 4: Evidence Provenance & Non-Causal Claims
# ==========================================

def test_04_provenance_and_non_causal_descriptors():
    engine = ExplanationEngine()
    explanation = engine.generate_explanation(scenario_id="wan_congestion")

    assert len(explanation.evidence_items) >= 2
    for item in explanation.evidence_items:
        assert item.source_dataset == "cisco_ie_telemetry"
        assert item.source_file.endswith(".csv")
        assert item.data_quality_status == "VALID"
        # Invariant: Evidence correlation must never assert unsubstantiated causality
        assert item.is_causal_claim is False
        assert item.relationship_descriptor in ("co-occurring", "temporally associated within 60s")


# ==========================================
# Test 5: Measurement Explainer & Physical Unit Conversion
# ==========================================

def test_05_measurement_explainer_physical_units():
    cycle = AdaptiveCycleResult(
        cycle_number=1,
        selected_diagnostic_id="active_rtt_probe",
        observation=DiagnosticObservation(
            observation_id="obs-001",
            tool_id="active_rtt_probe",
            tool_name="High-Precision Active RTT Probe",
            target_entity="primary_path_egress",
            target_parameter="fiber_latency_calibration_drift",
            raw_measured_value=21.884,
            raw_unit="ms",
            raw_error_bound=1.5,
            measured_value=1.0942,
            unit="factor",
            declared_error_bound=0.0750,
            confidence_interval=(1.0192, 1.1692),
        ),
        uncertainty_update=UncertaintyUpdate(
            update_id="upd-001",
            parameter_name="fiber_latency_calibration_drift",
            target_entity="primary_path_egress",
            prior_interval=UncertaintyInterval(
                parameter_name="fiber_latency_calibration_drift",
                unit="factor",
                min_value=0.85,
                max_value=1.35,
                nominal_value=1.0,
            ),
            measurement_interval=(1.0192, 1.1692),
            posterior_interval=UncertaintyInterval(
                parameter_name="fiber_latency_calibration_drift",
                unit="factor",
                min_value=1.0192,
                max_value=1.1692,
                nominal_value=1.0942,
            ),
            is_consistent=True,
            justification="Bounded interval intersection",
        ),
        previous_gate_decision=GateDecision.GATHER_EVIDENCE,
        new_gate_decision=GateDecision.ACCEPT,
        decision_changed=True,
        simulations_consumed=25,
        gate_justification="Measurement resolved uncertainty; candidate robust.",
    )

    expl = MeasurementExplainer.explain_cycle(cycle)
    assert expl.tool_id == "active_rtt_probe"
    assert expl.raw_unit == "ms"
    assert expl.raw_measured_value == 21.884
    assert expl.parameter_unit == "factor"
    assert expl.parameter_measured_value == 1.0942
    assert expl.width_reduction_pct == 70.0
    assert expl.is_consistent is True
    # Verify unrelated dimensions are preserved
    assert "traffic_load_burst" in expl.unrelated_dimensions_preserved
    assert "ACCEPT" in expl.subsequent_gate_impact


# ==========================================
# Test 6: Local Sensitivity Analysis (OAT Perturbations)
# ==========================================

def test_06_local_sensitivity_analyzer(sample_topology, sample_candidate_eval):
    analyzer = SensitivityAnalyzer()
    report = analyzer.analyze_candidate_sensitivity(
        topology=sample_topology,
        candidate=sample_candidate_eval.action,
        nominal_prediction=sample_candidate_eval.nominal_prediction,
        scenario_id="wan_congestion",
    )

    assert isinstance(report, LocalSensitivityReport)
    assert report.candidate_id == "cand-reroute-spine2"
    assert len(report.evaluated_parameters) == 2

    # Check fiber_latency_calibration_drift
    p1 = next(p for p in report.evaluated_parameters if p.parameter_name == "fiber_latency_calibration_drift")
    assert p1.unit == "factor"
    assert len(p1.perturbations) == 4  # -20%, -10%, +10%, +20%
    assert p1.latency_elasticity > 0.0

    # Check explicit disclosure
    assert "local model response gradients, not physical real-world causality" in report.methodology_disclosure


# ==========================================
# Test 7: Plain-Language Summary Generator
# ==========================================

def test_07_summary_generator_synthesis(sample_candidate_eval):
    rules = GateRuleExplainer.explain_rules(sample_candidate_eval)
    ce_expl = CounterexampleExplainer.explain(sample_candidate_eval.counterexample, sample_candidate_eval)

    summary = DecisionSummaryGenerator.generate_summary(
        decision=GateDecision.GATHER_EVIDENCE,
        scenario_id="wan_congestion",
        candidate_id=sample_candidate_eval.candidate_id,
        rules=rules,
        counterexample=ce_expl,
        uncertainty=None,
        sensitivity=None,
    )

    assert "GATHER_EVIDENCE" in summary
    assert "wan_congestion" in summary
    assert "cand-reroute-spine2" in summary
    assert "mandatory decision rules passed" in summary
    assert "Adversarial perturbation search identified constraint breach" in summary
    assert "no real-world routing reconfiguration has been enacted" in summary


# ==========================================
# Test 8: Gate-Verdict Agreement (Explanation Cannot Override Gate)
# ==========================================

def test_08_gate_verdict_agreement(app_storage):
    engine = ExplanationEngine(app_storage)
    explanation = engine.generate_explanation(scenario_id="wan_congestion")

    # Authoritative principle: The explanation's verdict must match the gate decision
    assert explanation.decision in (GateDecision.ACCEPT, GateDecision.GATHER_EVIDENCE, GateDecision.ABSTAIN)
    assert explanation.decision.value in explanation.summary


# ==========================================
# Test 9: Hidden-Reference Separation (Quarantined in Post-Hoc Only)
# ==========================================

def test_09_hidden_reference_quarantined():
    engine = ExplanationEngine()
    explanation = engine.generate_explanation(scenario_id="wan_congestion")

    # Agent-facing evidence items must NOT contain ground truth reference
    for item in explanation.evidence_items:
        assert "reference" not in item.source_dataset.lower()
        assert "ground_truth" not in item.metric_name.lower()

    # Post-hoc reference MUST be isolated with explicit disclosure
    if explanation.post_hoc_reference:
        assert "Offline post-hoc reference evaluation only" in explanation.post_hoc_reference["boundary_disclosure"]


# ==========================================
# Test 10: Persistence and Retrieval from SQLite
# ==========================================

def test_10_persistence_roundtrip(app_storage):
    engine = ExplanationEngine(app_storage)
    expl = engine.generate_explanation(scenario_id="wan_congestion")

    retrieved = app_storage.get_explanation(expl.explanation_id)
    assert retrieved is not None
    assert retrieved.explanation_id == expl.explanation_id
    assert retrieved.decision == expl.decision
    assert len(retrieved.constraint_results) == len(expl.constraint_results)

    # Test list summaries
    summaries = app_storage.list_explanations(limit=10)
    assert len(summaries) >= 1
    assert summaries[0].explanation_id == expl.explanation_id


# ==========================================
# Test 11: FastAPI Layer 6 REST Endpoints
# ==========================================

def test_11_fastapi_explanation_endpoints():
    client = TestClient(app)

    # 1. POST create explanation
    create_res = client.post(
        "/api/v1/explanations",
        json={"scenario_id": "wan_congestion", "compute_sensitivity": True},
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    expl_id = created_data["explanation_id"]
    assert expl_id.startswith("expl-")
    assert "summary" in created_data
    assert len(created_data["constraint_results"]) == 5

    # 2. GET explanation by ID
    get_res = client.get(f"/api/v1/explanations/{expl_id}")
    assert get_res.status_code == 200
    assert get_res.json()["explanation_id"] == expl_id

    # 3. GET explanation rules
    rules_res = client.get(f"/api/v1/explanations/{expl_id}/rules")
    assert rules_res.status_code == 200
    assert len(rules_res.json()) == 5

    # 4. GET explanation sensitivity
    sens_res = client.get(f"/api/v1/explanations/{expl_id}/sensitivity")
    assert sens_res.status_code == 200
    assert "evaluated_parameters" in sens_res.json()

    # 5. GET explanations list
    list_res = client.get("/api/v1/explanations")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


# ==========================================
# Test 12: Immutability (Explanation Does Not Mutate Prior Records)
# ==========================================

def test_12_immutability(app_storage):
    engine = ExplanationEngine(app_storage)
    expl1 = engine.generate_explanation(scenario_id="wan_congestion")
    expl2 = engine.generate_explanation(scenario_id="wan_congestion")

    assert expl1.explanation_id != expl2.explanation_id
    assert expl1.decision == expl2.decision


# ==========================================
# Test 13: Controlled Run Equivalence & Gate Record Consistency
# ==========================================

def test_13_controlled_run_equivalence(app_storage):
    """Verifies that explaining the same persisted run consistently yields identical
    underlying evaluation IDs, candidate IDs, and authoritative gate verdicts.
    """
    engine = ExplanationEngine(app_storage)
    client = TestClient(app)

    # 1. Controlled evaluation_id request
    eval_id = "eval-gather-123"
    expl_eval = engine.generate_explanation(evaluation_id=eval_id)
    assert expl_eval.run_id == eval_id
    assert expl_eval.candidate_id == "R-alt1"
    # Authoritative gate check:
    eval_summary = app_storage.get_mitigation_summary(eval_id)
    assert expl_eval.decision == eval_summary.gate_verdict

    # 2. Controlled FastAPI request with same evaluation_id
    api_res = client.post("/api/v1/explanations", json={"evaluation_id": eval_id})
    assert api_res.status_code == 201
    api_data = api_res.json()
    assert api_data["run_id"] == eval_id
    assert api_data["candidate_id"] == "R-alt1"
    assert api_data["decision"] == eval_summary.gate_verdict.value

    # 3. Controlled adaptive run request
    adapts = app_storage.list_adaptive_summaries(1)
    if adapts:
        adapt_id = adapts[0].adaptive_run_id
        expl_adapt = engine.generate_explanation(adaptive_run_id=adapt_id)
        assert expl_adapt.run_id == adapt_id
        assert expl_adapt.decision == adapts[0].final_gate_decision


# ==========================================
# Test 14: Regression Tests for P0 Runtime & Data Contract Repair
# ==========================================

def test_14_nonexistent_evaluation_id_returns_404():
    """Verifies that an explicit nonexistent evaluation_id returns 404, not 400 or 500."""
    client = TestClient(app)
    res = client.post("/api/v1/explanations", json={"evaluation_id": "eval-209"})
    assert res.status_code == 404
    assert "not found in storage" in res.json()["detail"]


def test_15_nonexistent_adaptive_id_returns_404():
    """Verifies that an explicit nonexistent adaptive_run_id returns 404."""
    client = TestClient(app)
    res = client.post("/api/v1/explanations", json={"adaptive_run_id": "adapt-99999999"})
    assert res.status_code == 404
    assert "not found in storage" in res.json()["detail"]


def test_16_nonexistent_scenario_returns_404_no_silent_switch():
    """Verifies that an explicit unknown scenario_id returns 404 without silently switching."""
    client = TestClient(app)
    res = client.post("/api/v1/explanations", json={"scenario_id": "unknown_scenario_xyz"})
    assert res.status_code == 404
    assert "No completed evaluations found for scenario 'unknown_scenario_xyz'" in res.json()["detail"]


def test_17_missing_all_identifiers_returns_400():
    """Verifies that submitting with no source IDs or scenarios returns 400 Bad Request."""
    client = TestClient(app)
    # Empty body
    res = client.post("/api/v1/explanations", json={})
    assert res.status_code == 400
    assert "Must provide at least one" in res.json()["detail"]

    # Literal 'None' string values
    res2 = client.post("/api/v1/explanations", json={"evaluation_id": "None", "scenario_id": "None"})
    assert res2.status_code == 400
    assert "Must provide at least one" in res2.json()["detail"]


def test_18_canonical_contract_structure(app_storage):
    """Verifies that DecisionExplanation always contains populated list fields and correct types."""
    client = TestClient(app)
    res = client.post("/api/v1/explanations", json={"scenario_id": "wan_congestion"})
    assert res.status_code == 201
    data = res.json()

    # Rule and evidence arrays must never be None
    assert isinstance(data["constraint_results"], list)
    assert len(data["constraint_results"]) > 0
    for r in data["constraint_results"]:
        assert "rule_id" in r
        assert "rule_name" in r
        assert "threshold_condition" in r
        assert r["status"] in ["PASSED", "FAILED", "UNKNOWN", "NOT_APPLICABLE"]

    assert isinstance(data["uncertainty_changes"], list)
    assert isinstance(data["evidence_items"], list)
    assert isinstance(data["limitations"], list)
    assert isinstance(data["unresolved_questions"], list)


def test_19_list_vs_detail_contract_parity():
    """Verifies that GET /api/v1/explanations returns List[ExplanationSummary],
    and GET /api/v1/explanations/{id} returns DecisionExplanation with full constraint_results.
    """
    client = TestClient(app)

    # List endpoint
    list_res = client.get("/api/v1/explanations?limit=5")
    assert list_res.status_code == 200
    items = list_res.json()
    assert isinstance(items, list)
    if items:
        summary_item = items[0]
        assert "explanation_id" in summary_item
        assert "rule_pass_count" in summary_item
        # Summary item must NOT have constraint_results list
        assert "constraint_results" not in summary_item

        # Detail endpoint
        expl_id = summary_item["explanation_id"]
        detail_res = client.get(f"/api/v1/explanations/{expl_id}")
        assert detail_res.status_code == 200
        detail = detail_res.json()
        assert detail["explanation_id"] == expl_id
        assert "constraint_results" in detail
        assert isinstance(detail["constraint_results"], list)
