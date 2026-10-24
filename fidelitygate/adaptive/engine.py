"""fidelitygate/adaptive/engine.py
End-to-end orchestrator for counterexample-guided adaptive diagnostics,
bounded measurement error integration, parameter uncertainty updates, and Layer 4 decision re-evaluation.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from ..decision_gate import decide
from ..evaluation.engine import MitigationEvaluationEngine
from ..evaluation.models import (
    CandidateAction,
    CandidateEvaluation,
    CandidateEvaluationStatus,
    Counterexample,
    GateDecision,
    NetworkTopology,
    ReferenceEvaluationResult,
    ReferenceEvaluationStatus,
    SimulationPrediction,
    ValidationStatus,
)
from ..evaluation.reference_evaluator import IndependentReferenceEvaluator
from ..evaluation.simulator import NetworkSimulator
from ..evaluation.topologies import get_topology_for_scenario
from ..evaluation.uncertainty_evaluator import CandidateUncertaintyEvaluator
from ..schemas import Scenario
from .measurement_registry import DiagnosticMeasurementRegistry
from .models import (
    AdaptiveCycleResult,
    AdaptiveEvent,
    AdaptiveInvestigationReport,
    AdaptiveInvestigationRequest,
    AdaptiveInvestigationSummary,
    AdaptiveRunStatus,
    DiagnosticExecutionRecord,
    DiagnosticObservation,
    UncertaintyInterval,
    UncertaintyUpdate,
)
from .selector import AdaptiveDiagnosticSelector
from .uncertainty_updater import UncertaintyUpdater

logger = logging.getLogger("fidelitygate.adaptive")


class AdaptiveInvestigationEngine:
    """Orchestrates counterexample-guided adaptive diagnostics and decision re-evaluation."""

    def __init__(self, storage: Any):
        self.storage = storage
        self.simulator = NetworkSimulator()
        self.uncertainty_evaluator = CandidateUncertaintyEvaluator(self.simulator)
        self.reference_evaluator = IndependentReferenceEvaluator(self.simulator)
        self.measurement_registry = DiagnosticMeasurementRegistry()
        self.selector = AdaptiveDiagnosticSelector(self.measurement_registry)
        self.updater = UncertaintyUpdater()

    def run_adaptive_investigation(
        self,
        request: AdaptiveInvestigationRequest,
    ) -> Tuple[AdaptiveInvestigationSummary, AdaptiveInvestigationReport, List[AdaptiveEvent]]:
        """
        Executes bounded, counterexample-guided adaptive diagnostic loop.
        """
        start_time = time.time()
        adaptive_run_id = f"adapt-{uuid.uuid4().hex[:8]}"
        events: List[AdaptiveEvent] = []
        seq = 1

        def log_event(cycle_num: int, stage: str, event_type: str, details: Dict[str, Any]) -> None:
            nonlocal seq
            events.append(
                AdaptiveEvent(
                    event_id=f"aevt-{uuid.uuid4().hex[:8]}",
                    adaptive_run_id=adaptive_run_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    cycle_number=cycle_num,
                    stage=stage,
                    actor="adaptive_investigation_engine",
                    event_type=event_type,
                    details=details,
                    sequence_number=seq,
                )
            )
            seq += 1

        log_event(
            cycle_num=0,
            stage="RECEIVED",
            event_type="ADAPTIVE_INVESTIGATION_INITIATED",
            details={
                "evaluation_id": request.evaluation_id,
                "max_cycles": request.max_cycles,
                "simulation_budget_per_cycle": request.simulation_budget_per_cycle,
                "total_simulation_budget": request.total_simulation_budget,
            },
        )

        # 1. Load Layer 4 Evaluation Summary & Candidates
        eval_summary = self.storage.get_mitigation_summary(request.evaluation_id)
        if not eval_summary:
            raise ValueError(f"Layer 4 Mitigation Evaluation '{request.evaluation_id}' not found in persistence.")

        candidates = self.storage.get_candidate_evaluations(request.evaluation_id)
        if not candidates:
            raise ValueError(f"No evaluated candidates found for evaluation '{request.evaluation_id}'.")

        scenario_id = eval_summary.scenario_id
        initial_decision = eval_summary.gate_verdict
        primary_candidate = candidates[0]
        initial_candidate_id = primary_candidate.candidate_id

        # 2. Initialize Parameter Uncertainty Envelope
        initial_uncertainty: Dict[str, UncertaintyInterval] = {
            "fiber_latency_calibration_drift": UncertaintyInterval(
                parameter_name="fiber_latency_calibration_drift",
                unit="factor",
                min_value=0.85,
                max_value=1.35,
                nominal_value=1.0,
                confidence_level=0.95,
            ),
            "traffic_load_burst": UncertaintyInterval(
                parameter_name="traffic_load_burst",
                unit="factor",
                min_value=0.95,
                max_value=1.15,
                nominal_value=1.0,
                confidence_level=0.95,
            ),
            "cross_traffic_factor": UncertaintyInterval(
                parameter_name="cross_traffic_factor",
                unit="factor",
                min_value=0.80,
                max_value=1.25,
                nominal_value=1.0,
                confidence_level=0.95,
            ),
        }
        current_uncertainty = dict(initial_uncertainty)

        # 3. Check Critical Controls
        # Control A: Initial gate verdict is already ACCEPT
        if initial_decision == GateDecision.ACCEPT:
            log_event(
                cycle_num=0,
                stage="GATE_REVIEW",
                event_type="UNNECESSARY_DIAGNOSTICS_PREVENTED",
                details={
                    "initial_gate_decision": initial_decision.value,
                    "reason": "Candidate already accepted with high confidence; unnecessary diagnostics prevented.",
                },
            )
            duration_ms = round((time.time() - start_time) * 1000, 2)
            summary = AdaptiveInvestigationSummary(
                adaptive_run_id=adaptive_run_id,
                evaluation_id=request.evaluation_id,
                investigation_id=eval_summary.investigation_id,
                scenario_id=scenario_id,
                status=AdaptiveRunStatus.COMPLETED,
                created_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                initial_gate_decision=initial_decision,
                final_gate_decision=initial_decision,
                decision_changed=False,
                candidate_changed=False,
                total_cycles_executed=0,
                diagnostics_executed_count=0,
                total_simulations_consumed=0,
                total_diagnostic_cost_usd=0.0,
                total_duration_ms=duration_ms,
                termination_reason="Candidate already accepted with sufficient confidence; no adaptive diagnostics required.",
            )
            report = AdaptiveInvestigationReport(
                adaptive_run_id=adaptive_run_id,
                evaluation_id=request.evaluation_id,
                investigation_id=eval_summary.investigation_id,
                scenario_id=scenario_id,
                status=AdaptiveRunStatus.COMPLETED,
                created_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                initial_gate_decision=initial_decision,
                final_gate_decision=initial_decision,
                initial_candidate_id=initial_candidate_id,
                final_candidate_id=initial_candidate_id,
                initial_uncertainty=initial_uncertainty,
                final_uncertainty=current_uncertainty,
                cycles=[],
                diagnostic_executions=[],
                uncertainty_updates=[],
                total_simulations_consumed=0,
                total_diagnostic_cost_usd=0.0,
                execution_duration_ms=duration_ms,
                reference_evaluation_status=primary_candidate.reference_evaluation.reference_status if primary_candidate.reference_evaluation else None,
                termination_reason="Candidate already accepted with sufficient confidence; no adaptive diagnostics required.",
                limitations=["No diagnostic cycles required for already-compliant candidate."],
            )
            self._persist_adaptive_run(summary, report, events, [], [])
            return summary, report, events

        # Control B: Structural Invalidity (Cannot be fixed by diagnostics)
        if primary_candidate.validation.status != ValidationStatus.VALID:
            log_event(
                cycle_num=0,
                stage="GATE_REVIEW",
                event_type="STRUCTURAL_DEFECT_ABSTAIN",
                details={
                    "validation_status": primary_candidate.validation.status.value,
                    "reason": "Candidate path is structurally invalid; diagnostics cannot resolve topology defects.",
                },
            )
            duration_ms = round((time.time() - start_time) * 1000, 2)
            summary = AdaptiveInvestigationSummary(
                adaptive_run_id=adaptive_run_id,
                evaluation_id=request.evaluation_id,
                investigation_id=eval_summary.investigation_id,
                scenario_id=scenario_id,
                status=AdaptiveRunStatus.ABSTAINED,
                created_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                initial_gate_decision=initial_decision,
                final_gate_decision=GateDecision.ABSTAIN,
                decision_changed=False,
                candidate_changed=False,
                total_cycles_executed=0,
                diagnostics_executed_count=0,
                total_simulations_consumed=0,
                total_diagnostic_cost_usd=0.0,
                total_duration_ms=duration_ms,
                termination_reason="Candidate path is structurally invalid; diagnostics cannot resolve topology defects.",
            )
            report = AdaptiveInvestigationReport(
                adaptive_run_id=adaptive_run_id,
                evaluation_id=request.evaluation_id,
                investigation_id=eval_summary.investigation_id,
                scenario_id=scenario_id,
                status=AdaptiveRunStatus.ABSTAINED,
                created_at=datetime.now(timezone.utc).isoformat(),
                completed_at=datetime.now(timezone.utc).isoformat(),
                initial_gate_decision=initial_decision,
                final_gate_decision=GateDecision.ABSTAIN,
                initial_candidate_id=initial_candidate_id,
                final_candidate_id=initial_candidate_id,
                initial_uncertainty=initial_uncertainty,
                final_uncertainty=current_uncertainty,
                cycles=[],
                diagnostic_executions=[],
                uncertainty_updates=[],
                total_simulations_consumed=0,
                total_diagnostic_cost_usd=0.0,
                execution_duration_ms=duration_ms,
                reference_evaluation_status=None,
                termination_reason="Candidate path is structurally invalid; diagnostics cannot resolve topology defects.",
                limitations=["Structural topology errors fail closed immediately."],
            )
            self._persist_adaptive_run(summary, report, events, [], [])
            return summary, report, events

        # 4. Adaptive Investigation Loop
        topology = get_topology_for_scenario(scenario_id)
        if not topology:
            raise ValueError(f"Canonical topology not found for scenario '{scenario_id}'.")

        remaining_budget_usd = request.diagnostic_cost_budget_usd
        total_simulations_consumed = 0
        executed_diagnostic_ids: Set[str] = set()
        cycles_results: List[AdaptiveCycleResult] = []
        diagnostic_records: List[DiagnosticExecutionRecord] = []
        uncertainty_updates: List[UncertaintyUpdate] = []

        current_gate_decision = initial_decision
        current_counterexamples = [primary_candidate.counterexample] if primary_candidate.counterexample else []
        termination_reason = "Completed all configured adaptive diagnostic cycles."

        for cycle_idx in range(1, request.max_cycles + 1):
            log_event(
                cycle_num=cycle_idx,
                stage="DIAGNOSTIC_SELECTION",
                event_type="CYCLE_INITIATED",
                details={"cycle": cycle_idx, "active_counterexamples": len(current_counterexamples)},
            )

            # Check Total Simulation Budget
            if total_simulations_consumed + request.simulation_budget_per_cycle > request.total_simulation_budget:
                termination_reason = "Total simulation budget exhausted."
                log_event(
                    cycle_num=cycle_idx,
                    stage="BUDGET_ENFORCEMENT",
                    event_type="SIMULATION_BUDGET_EXCEEDED",
                    details={"consumed": total_simulations_consumed, "ceiling": request.total_simulation_budget},
                )
                break

            # Select Best Diagnostic
            selected_diag, ranked_options = self.selector.select_best_diagnostic(
                counterexamples=current_counterexamples,
                current_uncertainty=current_uncertainty,
                executed_diagnostics=executed_diagnostic_ids,
                remaining_budget_usd=remaining_budget_usd,
            )

            if not selected_diag:
                termination_reason = "No eligible allowlisted diagnostic addresses active counterexamples within budget."
                log_event(
                    cycle_num=cycle_idx,
                    stage="DIAGNOSTIC_SELECTION",
                    event_type="NO_ELIGIBLE_DIAGNOSTIC",
                    details={"evaluated_count": len(ranked_options)},
                )
                break

            log_event(
                cycle_num=cycle_idx,
                stage="DIAGNOSTIC_SELECTION",
                event_type="DIAGNOSTIC_CHOSEN",
                details={
                    "tool_id": selected_diag.diagnostic_id,
                    "target_parameter": selected_diag.target_parameter,
                    "estimated_cost": selected_diag.estimated_cost,
                    "priority_score": selected_diag.priority_score,
                },
            )

            # Determine Simulated Ground Truth for Observation Model
            # Note: The diagnostic tool generates an observation y = h_d(theta) + epsilon with error bounds.
            # Real ground-truth is NOT revealed to agents.
            true_param_val = 1.05 if "latency" in selected_diag.target_parameter else 1.04

            # Calculate physical base scale for observation model mapping
            target_param_unit = current_uncertainty[selected_diag.target_parameter].unit
            if selected_diag.diagnostic_id == "active_rtt_probe":
                # Path base propagation delay in milliseconds
                path = primary_candidate.action.path
                base_scale = sum(
                    topology.get_edge(u, v).base_latency_ms
                    for u, v in zip(path[:-1], path[1:])
                    if topology.get_edge(u, v)
                ) or 20.0
            elif selected_diag.diagnostic_id == "snmp_interface_poll":
                # Nominal flow demand in Mbps
                flow = topology.get_flow(primary_candidate.action.flow_id)
                base_scale = flow.demand_mbps if flow else 250.0
            else:
                base_scale = 1.0

            # Execute Diagnostic Tool with Seeded Error and Physical Scale Inversion
            obs = self.measurement_registry.execute_diagnostic(
                tool_id=selected_diag.diagnostic_id,
                target_entity=selected_diag.target_entity,
                simulated_true_parameter=true_param_val,
                seed=request.deterministic_seed,
                cycle_number=cycle_idx,
                base_scale=base_scale,
                target_unit=target_param_unit,
            )

            exec_record = DiagnosticExecutionRecord(
                execution_id=f"exec-{uuid.uuid4().hex[:8]}",
                cycle_number=cycle_idx,
                diagnostic_id=selected_diag.diagnostic_id,
                target_entity=selected_diag.target_entity,
                target_parameter=selected_diag.target_parameter,
                observation=obs,
                measurement_model=self.measurement_registry.models[selected_diag.diagnostic_id],
                cost_usd=selected_diag.estimated_cost,
                latency_ms=self.measurement_registry.models[selected_diag.diagnostic_id].latency_ms,
                status="SUCCESS",
            )
            diagnostic_records.append(exec_record)
            executed_diagnostic_ids.add(selected_diag.diagnostic_id)
            remaining_budget_usd -= selected_diag.estimated_cost

            log_event(
                cycle_num=cycle_idx,
                stage="MEASUREMENT",
                event_type="OBSERVATION_ACQUIRED",
                details={
                    "observation_id": obs.observation_id,
                    "measured_value": obs.measured_value,
                    "error_bound": obs.declared_error_bound,
                    "confidence_interval": obs.confidence_interval,
                },
            )

            # Update Parameter Uncertainty via Bounded Intersection
            current_uncertainty, update_rec = self.updater.update_uncertainty_state(
                current_state=current_uncertainty,
                observation=obs,
                target_entity=selected_diag.target_entity,
            )
            uncertainty_updates.append(update_rec)

            if not update_rec.is_consistent:
                # Disjoint interval inconsistency detected
                log_event(
                    cycle_num=cycle_idx,
                    stage="UNCERTAINTY_UPDATE",
                    event_type="INCONSISTENCY_DETECTED",
                    details={"justification": update_rec.justification},
                )
                current_gate_decision = GateDecision.ABSTAIN
                termination_reason = "Inconsistency detected between diagnostic measurement and prior uncertainty interval."
                break

            log_event(
                cycle_num=cycle_idx,
                stage="UNCERTAINTY_UPDATE",
                event_type="UNCERTAINTY_NARROWED",
                details={
                    "parameter": update_rec.parameter_name,
                    "prior_width": update_rec.prior_interval.width,
                    "posterior_width": update_rec.posterior_interval.width if update_rec.posterior_interval else 0.0,
                },
            )

            # Re-evaluate Candidate with Layer 4 Digital Twin
            lat_interval = current_uncertainty["fiber_latency_calibration_drift"]
            load_interval = current_uncertainty["traffic_load_burst"]

            re_sweep, re_ce = self.uncertainty_evaluator.evaluate_uncertainty(
                topology=topology,
                candidate=primary_candidate.action,
                evaluations=request.simulation_budget_per_cycle,
                latency_multiplier_range=(lat_interval.min_value, lat_interval.max_value),
                load_multiplier_range=(load_interval.min_value, load_interval.max_value),
            )
            total_simulations_consumed += (1 + request.simulation_budget_per_cycle)

            # Evaluate Deterministic Decision Gate on Updated Evidence
            re_scenario = Scenario(
                scenario_id=scenario_id,
                name=f"{scenario_id}_reeval_cycle_{cycle_idx}",
                description="Re-evaluated scenario under updated uncertainty interval",
                offered_load_mbps=topology.get_flow(primary_candidate.action.flow_id).demand_mbps,
                capacity_mbps=1000.0,
                nominal_latency_ms=re_sweep.nominal_latency_ms,
                slo_latency_ms=topology.get_flow(primary_candidate.action.flow_id).slo_latency_ms,
                latency_multiplier_min=lat_interval.min_value,
                latency_multiplier_max=lat_interval.max_value,
                stability_threshold=0.90,
            )

            # Call deterministic gate
            gate_rep = decide(re_scenario, re_sweep)
            previous_dec = current_gate_decision
            current_gate_decision = gate_rep.decision
            decision_changed = (current_gate_decision != previous_dec)

            log_event(
                cycle_num=cycle_idx,
                stage="GATE_REVIEW",
                event_type="REEVALUATION_GATE_DECISION",
                details={
                    "previous_decision": previous_dec.value,
                    "new_decision": current_gate_decision.value,
                    "decision_changed": decision_changed,
                    "justification": gate_rep.reason,
                    "stability_score": re_sweep.stability_score,
                },
            )

            cycle_result = AdaptiveCycleResult(
                cycle_number=cycle_idx,
                selected_diagnostic_id=selected_diag.diagnostic_id,
                observation=obs,
                uncertainty_update=update_rec,
                previous_gate_decision=previous_dec,
                new_gate_decision=current_gate_decision,
                decision_changed=decision_changed,
                simulations_consumed=1 + request.simulation_budget_per_cycle,
                gate_justification=gate_rep.reason,
            )
            cycles_results.append(cycle_result)

            # Update Active Counterexamples for Next Cycle
            current_counterexamples = [re_ce] if (re_ce and re_ce.is_fragile) else []

            # Check Cycle Termination Rules
            if current_gate_decision == GateDecision.ACCEPT:
                termination_reason = (
                    f"Candidate verified compliant and robust (stability {re_sweep.stability_score * 100:.1f}%) "
                    f"after cycle {cycle_idx} diagnostic measurement; gate reached ACCEPT."
                )
                break
            elif current_gate_decision == GateDecision.ABSTAIN:
                termination_reason = (
                    f"Candidate failed nominal or capacity constraint after cycle {cycle_idx}; gate reached ABSTAIN."
                )
                break

        # 5. Offline Independent Reference Evaluation (Post-Decision Boundary)
        reference_status = None
        if primary_candidate.reference_evaluation:
            # Re-verify against offline reference ground truth strictly post-hoc
            ref_eval = self.reference_evaluator.evaluate_against_reference(
                topology=topology,
                candidate=primary_candidate.action,
                scenario_key=scenario_id,
            )
            reference_status = ref_eval.reference_status

        # 6. Build Final Summary and Report
        duration_ms = round((time.time() - start_time) * 1000, 2)
        final_status = (
            AdaptiveRunStatus.COMPLETED if current_gate_decision == GateDecision.ACCEPT
            else AdaptiveRunStatus.ABSTAINED if current_gate_decision == GateDecision.ABSTAIN
            else AdaptiveRunStatus.BUDGET_EXHAUSTED
        )
        total_diag_cost = round(request.diagnostic_cost_budget_usd - remaining_budget_usd, 4)

        summary = AdaptiveInvestigationSummary(
            adaptive_run_id=adaptive_run_id,
            evaluation_id=request.evaluation_id,
            investigation_id=eval_summary.investigation_id,
            scenario_id=scenario_id,
            status=final_status,
            created_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            initial_gate_decision=initial_decision,
            final_gate_decision=current_gate_decision,
            decision_changed=(current_gate_decision != initial_decision),
            candidate_changed=False,
            total_cycles_executed=len(cycles_results),
            diagnostics_executed_count=len(diagnostic_records),
            total_simulations_consumed=total_simulations_consumed,
            total_diagnostic_cost_usd=total_diag_cost,
            total_duration_ms=duration_ms,
            termination_reason=termination_reason,
        )

        report = AdaptiveInvestigationReport(
            adaptive_run_id=adaptive_run_id,
            evaluation_id=request.evaluation_id,
            investigation_id=eval_summary.investigation_id,
            scenario_id=scenario_id,
            status=final_status,
            created_at=datetime.now(timezone.utc).isoformat(),
            completed_at=datetime.now(timezone.utc).isoformat(),
            initial_gate_decision=initial_decision,
            final_gate_decision=current_gate_decision,
            initial_candidate_id=initial_candidate_id,
            final_candidate_id=initial_candidate_id,
            initial_uncertainty=initial_uncertainty,
            final_uncertainty=current_uncertainty,
            cycles=cycles_results,
            diagnostic_executions=diagnostic_records,
            uncertainty_updates=uncertainty_updates,
            total_simulations_consumed=total_simulations_consumed,
            total_diagnostic_cost_usd=total_diag_cost,
            execution_duration_ms=duration_ms,
            reference_evaluation_status=reference_status,
            termination_reason=termination_reason,
            limitations=[
                "Bounded parameter sweeps provide empirical stability evidence, not exhaustive continuous proofs.",
                "Diagnostic measurement error bounds represent 95% confidence intervals under normal device conditions.",
            ],
            warnings=[],
        )

        # 7. Persist to Storage Engine
        self._persist_adaptive_run(summary, report, events, diagnostic_records, uncertainty_updates)
        return summary, report, events

    def _persist_adaptive_run(
        self,
        summary: AdaptiveInvestigationSummary,
        report: AdaptiveInvestigationReport,
        events: List[AdaptiveEvent],
        diagnostic_records: List[DiagnosticExecutionRecord],
        uncertainty_updates: List[UncertaintyUpdate],
    ) -> None:
        """Saves adaptive investigation summaries, reports, executions, and events to SQLite."""
        if hasattr(self.storage, "save_adaptive_investigation"):
            self.storage.save_adaptive_investigation(
                summary=summary,
                report=report,
                events=events,
                diagnostic_records=diagnostic_records,
                uncertainty_updates=uncertainty_updates,
            )
