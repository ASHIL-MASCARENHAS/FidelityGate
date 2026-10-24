"""tests/test_adaptive_investigation.py
Comprehensive automated test suite for Layer 5 Counterexample-Guided Adaptive Diagnostics,
Measurement Models, Uncertainty Interval Updates, and Decision Re-evaluation.
"""

import os
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from fidelitygate.adaptive.engine import AdaptiveInvestigationEngine
from fidelitygate.adaptive.measurement_registry import (
    ALLOWLISTED_MEASUREMENT_MODELS,
    DiagnosticMeasurementRegistry,
)
from fidelitygate.adaptive.models import (
    AdaptiveEvent,
    AdaptiveInvestigationReport,
    AdaptiveInvestigationRequest,
    AdaptiveInvestigationSummary,
    AdaptiveRunStatus,
    DiagnosticCandidateEvaluation,
    DiagnosticExecutionRecord,
    DiagnosticObservation,
    MeasurementErrorType,
    MeasurementModel,
    ObservationMode,
    UncertaintyInterval,
    UncertaintyUpdate,
)
from fidelitygate.adaptive.selector import AdaptiveDiagnosticSelector
from fidelitygate.adaptive.uncertainty_updater import (
    InconsistentMeasurementError,
    UncertaintyUpdater,
)
from fidelitygate.api.app import app
from fidelitygate.evaluation.models import (
    CandidateAction,
    CandidateEvaluation,
    CandidateEvaluationStatus,
    Counterexample,
    GateDecision,
    MitigationActionType,
    MitigationEvaluationReport,
    MitigationEvaluationSummary,
    PathValidationResult,
    ReferenceEvaluationResult,
    ReferenceEvaluationStatus,
    SimulationPrediction,
    ValidationStatus,
)
from fidelitygate.schemas import GateReport, SweepReport
from fidelitygate.storage import StorageEngine


@pytest.fixture
def test_db(tmp_path):
    db_file = tmp_path / "test_fidelitygate_adaptive.db"
    return StorageEngine(str(db_file))


@pytest.fixture
def mock_gather_evidence_evaluation(test_db):
    """Creates a mock Layer 4 evaluation where the gate verdict is GATHER_EVIDENCE with an active counterexample."""
    eval_id = "eval-gather-123"
    inv_id = "inv-test-456"
    scenario_id = "wan_congestion"

    candidate = CandidateAction(
        candidate_id="R-alt1",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
        action_type=MitigationActionType.REROUTE_FLOW,
        rationale="Alternative path through spine2",
    )

    validation = PathValidationResult(
        is_valid=True,
        status=ValidationStatus.VALID,
        reasons=["Valid path"],
        validated_path=["leaf1", "spine2", "leaf6"],
        hop_count=2,
        edges_traversed=["e_leaf1_spine2", "e_spine2_leaf6"],
    )

    nominal_pred = SimulationPrediction(
        flow_id="flow_primary",
        latency_ms=23.0,
        slo_latency_ms=45.0,
        peak_utilization=0.50,
        is_connected=True,
        capacity_violated=False,
        slo_violated=False,
        link_results=[],
        model_version="v1.0",
        assumptions=["Nominal propagation"],
    )

    counterexample = Counterexample(
        is_fragile=True,
        violating_latency_ms=48.5,
        critical_parameter="fiber_latency_calibration_drift",
        perturbation_factor=1.25,
        slo_latency_ms=45.0,
        margin_breach_ms=3.5,
        explanation="Propagation drift breaches 45 ms SLO.",
    )

    cand_eval = CandidateEvaluation(
        evaluation_id=eval_id,
        investigation_id=inv_id,
        scenario_id=scenario_id,
        candidate_id="R-alt1",
        action=candidate,
        validation=validation,
        nominal_prediction=nominal_pred,
        counterexample=counterexample,
        status=CandidateEvaluationStatus.FRAGILE,
        reference_evaluation=ReferenceEvaluationResult(
            reference_status=ReferenceEvaluationStatus.VERIFIED_SAFE,
            true_latency_ms=27.5,
            true_peak_utilization=0.52,
            ground_truth_safe=True,
            notes=["Synthetic benchmark ground truth."],
        ),
        explanation_facts={},
        limitations=[],
    )

    summary = MitigationEvaluationSummary(
        evaluation_id=eval_id,
        investigation_id=inv_id,
        scenario_id=scenario_id,
        status="COMPLETE",
        gate_verdict=GateDecision.GATHER_EVIDENCE,
        candidates_count=1,
        evaluated_count=1,
        compliant_count=0,
        selected_candidate_id="R-alt1",
        created_at=datetime.now(timezone.utc).isoformat(),
        duration_ms=8.5,
    )

    report = MitigationEvaluationReport(
        evaluation_id=eval_id,
        investigation_id=inv_id,
        scenario_id=scenario_id,
        scenario_version="1.0",
        model_version="1.0",
        policy_version="1.0",
        candidate_evaluations=[cand_eval],
        selected_candidate_id="R-alt1",
        gate_verdict=GateDecision.GATHER_EVIDENCE,
        gate_justification="Candidate passed nominal but breached under perturbation; gather diagnostic evidence.",
        total_simulations=27,
        duration_ms=8.5,
        created_at=datetime.now(timezone.utc).isoformat(),
        data_mode="SYNTHETIC_FIXTURE",
        reference_evaluation_status="VERIFIED_SAFE",
        limitations=[],
    )

    test_db.save_mitigation_evaluation(
        summary=summary,
        report=report,
        candidate_evaluations=[cand_eval],
        events=[],
    )

    return eval_id, summary, cand_eval


# 1. Diagnostic ranking addresses actual counterexample
def test_01_diagnostic_ranking_addresses_actual_counterexample():
    selector = AdaptiveDiagnosticSelector()
    ce = Counterexample(
        is_fragile=True,
        violating_latency_ms=49.0,
        critical_parameter="fiber_latency_calibration_drift",
        perturbation_factor=1.20,
        slo_latency_ms=45.0,
        margin_breach_ms=4.0,
        explanation="Latency drift violation",
    )
    uncertainty = {
        "fiber_latency_calibration_drift": UncertaintyInterval(
            parameter_name="fiber_latency_calibration_drift",
            unit="factor",
            min_value=0.85,
            max_value=1.35,
            nominal_value=1.0,
        ),
        "traffic_load_burst": UncertaintyInterval(
            parameter_name="traffic_load_burst",
            unit="factor",
            min_value=0.95,
            max_value=1.15,
            nominal_value=1.0,
        ),
    }

    selected, ranked = selector.select_best_diagnostic(
        counterexamples=[ce],
        current_uncertainty=uncertainty,
        executed_diagnostics=set(),
        remaining_budget_usd=0.05,
    )

    assert selected is not None
    assert selected.diagnostic_id == "active_rtt_probe"
    assert selected.target_parameter == "fiber_latency_calibration_drift"
    assert selected.is_eligible is True
    assert selected.priority_score > 0


# 2. Irrelevant diagnostics excluded or ranked lower
def test_02_irrelevant_diagnostics_excluded():
    selector = AdaptiveDiagnosticSelector()
    ce = Counterexample(
        is_fragile=True,
        violating_latency_ms=49.0,
        critical_parameter="fiber_latency_calibration_drift",
        perturbation_factor=1.20,
        slo_latency_ms=45.0,
        margin_breach_ms=4.0,
        explanation="Latency drift violation",
    )
    uncertainty = {
        "fiber_latency_calibration_drift": UncertaintyInterval(
            parameter_name="fiber_latency_calibration_drift",
            unit="factor",
            min_value=0.85,
            max_value=1.35,
            nominal_value=1.0,
        ),
    }

    ranked = selector.evaluate_and_rank_diagnostics(
        counterexamples=[ce],
        current_uncertainty=uncertainty,
        executed_diagnostics=set(),
        remaining_budget_usd=0.05,
    )

    snmp_diag = next(d for d in ranked if d.diagnostic_id == "snmp_interface_poll")
    assert snmp_diag.is_eligible is False
    assert "does not address any active counterexample" in snmp_diag.rejection_reason


# 3. Diagnostics requiring unsupported parameters or non-allowlisted rejected
def test_03_diagnostics_requiring_unsupported_parameters_excluded():
    registry = DiagnosticMeasurementRegistry()
    with pytest.raises(ValueError, match="not found in allowlisted"):
        registry.execute_diagnostic("arbitrary_unknown_tool", "link1", 1.0)


# 4. Same diagnostic not repeated without justification
def test_04_same_diagnostic_not_repeated_without_justification():
    selector = AdaptiveDiagnosticSelector()
    ce = Counterexample(
        is_fragile=True,
        violating_latency_ms=49.0,
        critical_parameter="fiber_latency_calibration_drift",
        perturbation_factor=1.20,
        slo_latency_ms=45.0,
        margin_breach_ms=4.0,
        explanation="Latency drift violation",
    )
    uncertainty = {
        "fiber_latency_calibration_drift": UncertaintyInterval(
            parameter_name="fiber_latency_calibration_drift",
            unit="factor",
            min_value=0.85,
            max_value=1.35,
            nominal_value=1.0,
        ),
    }

    # Mark active_rtt_probe as already executed
    selected, ranked = selector.select_best_diagnostic(
        counterexamples=[ce],
        current_uncertainty=uncertainty,
        executed_diagnostics={"active_rtt_probe"},
        remaining_budget_usd=0.05,
    )

    rtt_diag = next(d for d in ranked if d.diagnostic_id == "active_rtt_probe")
    assert rtt_diag.is_eligible is False
    assert "already been executed" in rtt_diag.rejection_reason
    assert selected is None


# 5. Valid bounded-error measurement produces justified interval update
def test_05_valid_bounded_error_measurement_produces_justified_interval_update():
    updater = UncertaintyUpdater()
    prior = UncertaintyInterval(
        parameter_name="fiber_latency_calibration_drift",
        unit="factor",
        min_value=0.85,
        max_value=1.35,
        nominal_value=1.0,
    )
    obs = DiagnosticObservation(
        observation_id="obs-1",
        tool_id="active_rtt_probe",
        tool_name="High-Precision Active RTT Probe",
        target_entity="e_leaf1_spine2",
        target_parameter="fiber_latency_calibration_drift",
        measured_value=1.05,
        unit="factor",
        declared_error_bound=0.08,
        confidence_interval=(0.97, 1.13),
        observation_mode=ObservationMode.SYNTHETIC_DIAGNOSTIC_MEASUREMENT,
    )

    update = updater.update_parameter_uncertainty(
        parameter_name="fiber_latency_calibration_drift",
        target_entity="e_leaf1_spine2",
        prior_interval=prior,
        observation=obs,
    )

    assert update.is_consistent is True
    assert update.posterior_interval is not None
    assert update.posterior_interval.min_value == 0.97
    assert update.posterior_interval.max_value == 1.13
    assert update.posterior_interval.width < prior.width


# 6. Unrelated parameter interval remains unchanged
def test_06_unrelated_parameter_interval_remains_unchanged():
    updater = UncertaintyUpdater()
    prior_state = {
        "fiber_latency_calibration_drift": UncertaintyInterval(
            parameter_name="fiber_latency_calibration_drift",
            unit="factor",
            min_value=0.85,
            max_value=1.35,
            nominal_value=1.0,
        ),
        "traffic_load_burst": UncertaintyInterval(
            parameter_name="traffic_load_burst",
            unit="factor",
            min_value=0.95,
            max_value=1.15,
            nominal_value=1.0,
        ),
    }

    obs = DiagnosticObservation(
        observation_id="obs-rtt",
        tool_id="active_rtt_probe",
        tool_name="Active RTT Probe",
        target_entity="link1",
        target_parameter="fiber_latency_calibration_drift",
        measured_value=1.02,
        unit="factor",
        declared_error_bound=0.05,
        confidence_interval=(0.97, 1.07),
    )

    new_state, update = updater.update_uncertainty_state(prior_state, obs, "link1")

    # Target parameter narrowed
    assert new_state["fiber_latency_calibration_drift"].width < prior_state["fiber_latency_calibration_drift"].width
    # Unrelated parameter strictly preserved bit-identical
    assert new_state["traffic_load_burst"] == prior_state["traffic_load_burst"]


# 7. Inconsistent measurement intervals rejected (empty intersection)
def test_07_inconsistent_measurement_intervals_rejected():
    updater = UncertaintyUpdater()
    prior = UncertaintyInterval(
        parameter_name="fiber_latency_calibration_drift",
        unit="factor",
        min_value=0.85,
        max_value=1.10,
        nominal_value=1.0,
    )
    # Measurement is completely disjoint: [1.25, 1.35]
    obs = DiagnosticObservation(
        observation_id="obs-disjoint",
        tool_id="active_rtt_probe",
        tool_name="Active RTT Probe",
        target_entity="link1",
        target_parameter="fiber_latency_calibration_drift",
        measured_value=1.30,
        unit="factor",
        declared_error_bound=0.05,
        confidence_interval=(1.25, 1.35),
    )

    update = updater.update_parameter_uncertainty("fiber_latency_calibration_drift", "link1", prior, obs)

    assert update.is_consistent is False
    assert update.posterior_interval is None
    assert "Inconsistency detected" in update.justification


# 8. Measurement error and units validated
def test_08_measurement_error_and_units_validated():
    registry = DiagnosticMeasurementRegistry()
    rtt_spec = registry.get_model("active_rtt_probe")
    assert rtt_spec.unit == "ms"
    assert rtt_spec.error_bound == 1.5
    assert rtt_spec.error_type == MeasurementErrorType.BOUNDED_ABSOLUTE

    snmp_spec = registry.get_model("snmp_interface_poll")
    assert snmp_spec.unit == "Mbps"
    assert snmp_spec.error_bound == 15.0


# 9. Malformed or invalid measurement output handled safely
def test_09_malformed_measurement_output_handled_safely():
    updater = UncertaintyUpdater()
    prior = UncertaintyInterval(
        parameter_name="fiber_latency_calibration_drift",
        unit="factor",
        min_value=0.85,
        max_value=1.35,
        nominal_value=1.0,
    )
    invalid_obs = DiagnosticObservation(
        observation_id="obs-invalid",
        tool_id="active_rtt_probe",
        tool_name="Probe",
        target_entity="link1",
        target_parameter="fiber_latency_calibration_drift",
        measured_value=0.0,
        unit="factor",
        declared_error_bound=0.0,
        confidence_interval=(0.0, 0.0),
        is_valid=False,
    )

    update = updater.update_parameter_uncertainty("fiber_latency_calibration_drift", "link1", prior, invalid_obs)
    assert update.is_consistent is False
    assert update.posterior_interval == prior


# 10. Synthetic diagnostic noise is reproducible using fixed seed
def test_10_synthetic_diagnostic_noise_reproducible_fixed_seed():
    registry = DiagnosticMeasurementRegistry()
    obs1 = registry.execute_diagnostic("active_rtt_probe", "link1", simulated_true_parameter=1.06, seed=123)
    obs2 = registry.execute_diagnostic("active_rtt_probe", "link1", simulated_true_parameter=1.06, seed=123)
    obs_diff = registry.execute_diagnostic("active_rtt_probe", "link1", simulated_true_parameter=1.06, seed=999)

    assert obs1.measured_value == obs2.measured_value
    assert obs1.confidence_interval == obs2.confidence_interval
    assert obs1.measured_value != obs_diff.measured_value


# 11. Public replay observations never relabelled as real diagnostic measurements
def test_11_public_replay_observations_never_relabelled():
    registry = DiagnosticMeasurementRegistry()
    # When public replay telemetry does not have active probe data
    obs = registry.execute_diagnostic(
        tool_id="active_rtt_probe",
        target_entity="0/RP0/CPU0",
        simulated_true_parameter=1.0,
        is_public_replay=True,
        public_replay_observation=None,
    )
    assert obs.observation_mode == ObservationMode.UNAVAILABLE
    assert obs.is_valid is False
    assert "not_present_in_public_telemetry" in obs.source_provenance["status"]


# 12. Hidden reference truth is not exposed to selector or agents
def test_12_hidden_reference_truth_not_exposed():
    registry = DiagnosticMeasurementRegistry()
    obs = registry.execute_diagnostic("active_rtt_probe", "link1", simulated_true_parameter=1.06, seed=42)

    # Observation payload only contains measured value and interval, no reference ground truth
    obs_dict = obs.model_dump()
    assert "simulated_true_parameter" not in obs_dict
    assert "reference_truth" not in obs_dict
    assert "true_latency" not in obs_dict


# 13. Diagnostic measurement can cause genuine candidate re-evaluation
def test_13_diagnostic_measurement_can_cause_genuine_reevaluation(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    request = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        max_cycles=1,
        simulation_budget_per_cycle=10,
        total_simulation_budget=50,
    )

    summary, report, events = engine.run_adaptive_investigation(request)

    assert summary.total_cycles_executed >= 1
    assert summary.total_simulations_consumed > 0
    assert len(report.cycles) >= 1
    assert report.cycles[0].simulations_consumed == 11


# 14. Diagnostic that does not alter decision reported honestly
def test_14_diagnostic_not_altering_decision_reported_honestly(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    # Using tiny budget that might maintain gather evidence or abstain
    request = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        max_cycles=1,
        simulation_budget_per_cycle=5,
        total_simulation_budget=20,
    )

    summary, report, events = engine.run_adaptive_investigation(request)
    assert isinstance(summary.decision_changed, bool)
    assert summary.termination_reason != ""


# 15. ACCEPT result does not trigger unnecessary diagnostics
def test_15_accept_result_does_not_trigger_unnecessary_diagnostics(test_db):
    eval_id = "eval-accept-999"
    candidate = CandidateAction(
        candidate_id="R-safe",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine2", "leaf6"],
        action_type=MitigationActionType.REROUTE_FLOW,
    )
    cand_eval = CandidateEvaluation(
        evaluation_id=eval_id,
        investigation_id="inv-safe",
        scenario_id="wan_congestion",
        candidate_id="R-safe",
        action=candidate,
        validation=PathValidationResult(is_valid=True, status=ValidationStatus.VALID),
        status=CandidateEvaluationStatus.COMPLIANT,
    )
    summary = MitigationEvaluationSummary(
        evaluation_id=eval_id,
        investigation_id="inv-safe",
        scenario_id="wan_congestion",
        status="COMPLETE",
        gate_verdict=GateDecision.ACCEPT,
        candidates_count=1,
        evaluated_count=1,
        compliant_count=1,
        selected_candidate_id="R-safe",
        created_at=datetime.now(timezone.utc).isoformat(),
        duration_ms=5.0,
    )
    report = MitigationEvaluationReport(
        evaluation_id=eval_id,
        investigation_id="inv-safe",
        scenario_id="wan_congestion",
        scenario_version="1.0",
        model_version="1.0",
        policy_version="1.0",
        candidate_evaluations=[cand_eval],
        selected_candidate_id="R-safe",
        gate_verdict=GateDecision.ACCEPT,
        gate_justification="Compliant",
        total_simulations=25,
        duration_ms=5.0,
        created_at=datetime.now(timezone.utc).isoformat(),
        data_mode="SYNTHETIC_FIXTURE",
        reference_evaluation_status="VERIFIED_SAFE",
    )
    test_db.save_mitigation_evaluation(summary, report, [cand_eval], [])

    engine = AdaptiveInvestigationEngine(test_db)
    req = AdaptiveInvestigationRequest(evaluation_id=eval_id)
    adapt_summary, adapt_report, _ = engine.run_adaptive_investigation(req)

    assert adapt_summary.total_cycles_executed == 0
    assert adapt_summary.diagnostics_executed_count == 0
    assert adapt_summary.final_gate_decision == GateDecision.ACCEPT
    assert "already accepted" in adapt_summary.termination_reason


# 16. GATHER_EVIDENCE triggers measurement only when useful diagnostic exists
def test_16_gather_evidence_triggers_measurement_only_when_useful(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    # Set cost budget to 0 so no diagnostic can be bought
    req = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        diagnostic_cost_budget_usd=0.0001,
    )
    summary, report, _ = engine.run_adaptive_investigation(req)

    assert summary.diagnostics_executed_count == 0
    assert "No eligible allowlisted diagnostic" in summary.termination_reason


# 17. Irrecoverable ABSTAIN condition remains an abstention
def test_17_irrecoverable_abstain_condition_remains_abstention(test_db):
    eval_id = "eval-down-edge"
    candidate = CandidateAction(
        candidate_id="R-broken",
        flow_id="flow_primary",
        source_node="leaf1",
        destination_node="leaf6",
        path=["leaf1", "spine1", "leaf6"],
        action_type=MitigationActionType.REROUTE_FLOW,
    )
    # Structural defect: edge is down
    validation = PathValidationResult(
        is_valid=False,
        status=ValidationStatus.LINK_DOWN,
        reasons=["Edge e_leaf1_spine1 is DOWN"],
    )
    cand_eval = CandidateEvaluation(
        evaluation_id=eval_id,
        investigation_id="inv-broken",
        scenario_id="wan_congestion",
        candidate_id="R-broken",
        action=candidate,
        validation=validation,
        status=CandidateEvaluationStatus.INVALID_PATH,
    )
    summary = MitigationEvaluationSummary(
        evaluation_id=eval_id,
        investigation_id="inv-broken",
        scenario_id="wan_congestion",
        status="COMPLETE",
        gate_verdict=GateDecision.ABSTAIN,
        candidates_count=1,
        evaluated_count=1,
        compliant_count=0,
        selected_candidate_id=None,
        created_at=datetime.now(timezone.utc).isoformat(),
        duration_ms=2.0,
    )
    report = MitigationEvaluationReport(
        evaluation_id=eval_id,
        investigation_id="inv-broken",
        scenario_id="wan_congestion",
        scenario_version="1.0",
        model_version="1.0",
        policy_version="1.0",
        candidate_evaluations=[cand_eval],
        gate_verdict=GateDecision.ABSTAIN,
        gate_justification="Edge down",
        total_simulations=0,
        duration_ms=2.0,
        created_at=datetime.now(timezone.utc).isoformat(),
        data_mode="SYNTHETIC_FIXTURE",
        reference_evaluation_status="INCORRECT_ABSTENTION",
    )
    test_db.save_mitigation_evaluation(summary, report, [cand_eval], [])

    engine = AdaptiveInvestigationEngine(test_db)
    req = AdaptiveInvestigationRequest(evaluation_id=eval_id)
    adapt_summary, _, _ = engine.run_adaptive_investigation(req)

    assert adapt_summary.total_cycles_executed == 0
    assert adapt_summary.final_gate_decision == GateDecision.ABSTAIN
    assert "structurally invalid" in adapt_summary.termination_reason


# 18. Justified measurement followed by ACCEPT when requirements pass
def test_18_justified_measurement_followed_by_accept(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    req = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        max_cycles=2,
        simulation_budget_per_cycle=15,
        total_simulation_budget=80,
        deterministic_seed=42,
    )

    summary, report, events = engine.run_adaptive_investigation(req)

    assert summary.initial_gate_decision == GateDecision.GATHER_EVIDENCE
    assert summary.final_gate_decision == GateDecision.ACCEPT
    assert summary.decision_changed is True
    assert summary.status == AdaptiveRunStatus.COMPLETED


# 19. Inconsistency detection fails closed to ABSTAIN
def test_19_inconsistency_fails_closed(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)

    # Monkey-patch measurement registry to simulate a disjoint contradictory measurement
    class ContradictoryRegistry(DiagnosticMeasurementRegistry):
        def execute_diagnostic(self, *args, **kwargs):
            return DiagnosticObservation(
                observation_id="obs-contradictory",
                tool_id="active_rtt_probe",
                tool_name="Probe",
                target_entity="link1",
                target_parameter="fiber_latency_calibration_drift",
                measured_value=1.85,
                unit="factor",
                declared_error_bound=0.05,
                confidence_interval=(1.80, 1.90),  # Completely disjoint from [0.85, 1.35]
            )

    engine.measurement_registry = ContradictoryRegistry()
    engine.selector.registry = engine.measurement_registry

    req = AdaptiveInvestigationRequest(evaluation_id=eval_id, max_cycles=1)
    summary, report, _ = engine.run_adaptive_investigation(req)

    assert summary.final_gate_decision == GateDecision.ABSTAIN
    assert "Inconsistency detected" in summary.termination_reason


# 20. Two-cycle limit enforced
def test_20_two_cycle_limit_enforced(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    req = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        max_cycles=2,
        simulation_budget_per_cycle=10,
    )
    summary, _, _ = engine.run_adaptive_investigation(req)
    assert summary.total_cycles_executed <= 2


# 21. Overall diagnostic and simulation budgets enforced across cycles
def test_21_simulation_budget_enforced(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    # Total budget smaller than 1 cycle of 25 simulations
    req = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        max_cycles=3,
        simulation_budget_per_cycle=25,
        total_simulation_budget=15,  # Too small
    )
    summary, _, _ = engine.run_adaptive_investigation(req)
    assert summary.total_simulations_consumed == 0
    assert "budget exhausted" in summary.termination_reason.lower()


# 22. Persistence and API contracts work correctly
def test_22_persistence_survives_restart(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    req = AdaptiveInvestigationRequest(evaluation_id=eval_id, max_cycles=1)
    summary, report, events = engine.run_adaptive_investigation(req)

    # Query from new database connection instance
    reloaded_db = StorageEngine(test_db.path)
    loaded_summary = reloaded_db.get_adaptive_summary(summary.adaptive_run_id)
    assert loaded_summary is not None
    assert loaded_summary.adaptive_run_id == summary.adaptive_run_id
    assert loaded_summary.final_gate_decision == summary.final_gate_decision

    loaded_report = reloaded_db.get_adaptive_report(summary.adaptive_run_id)
    assert loaded_report is not None
    assert len(loaded_report.cycles) == len(report.cycles)

    loaded_events = reloaded_db.get_adaptive_events(summary.adaptive_run_id)
    assert len(loaded_events) == len(events)


# 23. FastAPI adaptive endpoints
def test_23_fastapi_adaptive_endpoints(mock_gather_evidence_evaluation):
    eval_id, summary, cand_eval = mock_gather_evidence_evaluation
    from fidelitygate.api.app import storage as app_storage
    test_report = MitigationEvaluationReport(
        evaluation_id=eval_id,
        investigation_id=summary.investigation_id,
        scenario_id=summary.scenario_id,
        scenario_version="1.0",
        model_version="1.0",
        policy_version="1.0",
        candidate_evaluations=[cand_eval],
        selected_candidate_id=summary.selected_candidate_id,
        gate_verdict=summary.gate_verdict,
        gate_justification="Candidate passed nominal but breached under perturbation",
        total_simulations=27,
        duration_ms=8.5,
        created_at=summary.created_at,
        data_mode="SYNTHETIC_FIXTURE",
        reference_evaluation_status="VERIFIED_SAFE",
        limitations=[],
    )
    app_storage.save_mitigation_evaluation(
        summary=summary,
        report=test_report,
        candidate_evaluations=[cand_eval],
        events=[],
    )
    client = TestClient(app)

    # POST trigger
    resp = client.post("/api/v1/adaptive-investigations", json={
        "evaluation_id": eval_id,
        "max_cycles": 1,
        "simulation_budget_per_cycle": 10,
    })
    assert resp.status_code == 201
    data = resp.json()
    run_id = data["adaptive_run_id"]
    assert data["evaluation_id"] == eval_id

    # GET summary
    resp2 = client.get(f"/api/v1/adaptive-investigations/{run_id}")
    assert resp2.status_code == 200
    assert resp2.json()["adaptive_run_id"] == run_id

    # GET list
    resp3 = client.get("/api/v1/adaptive-investigations")
    assert resp3.status_code == 200
    assert len(resp3.json()) >= 1

    # GET diagnostics
    resp4 = client.get(f"/api/v1/adaptive-investigations/{run_id}/diagnostics")
    assert resp4.status_code == 200

    # GET events
    resp5 = client.get(f"/api/v1/adaptive-investigations/{run_id}/events")
    assert resp5.status_code == 200
    assert len(resp5.json()) >= 1

    # GET report
    resp6 = client.get(f"/api/v1/adaptive-investigations/{run_id}/report")
    assert resp6.status_code == 200
    assert resp6.json()["adaptive_run_id"] == run_id


# 24. Monotonically sequenced audit events
def test_24_monotonically_sequenced_audit_events(test_db, mock_gather_evidence_evaluation):
    eval_id, _, _ = mock_gather_evidence_evaluation
    engine = AdaptiveInvestigationEngine(test_db)
    req = AdaptiveInvestigationRequest(evaluation_id=eval_id, max_cycles=1)
    _, _, events = engine.run_adaptive_investigation(req)

    assert len(events) >= 3
    seq_nums = [e.sequence_number for e in events]
    assert seq_nums == sorted(seq_nums)
    assert seq_nums == list(range(1, len(events) + 1))
