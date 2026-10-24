"""fidelitygate/evaluation/engine.py
End-to-end orchestration of candidate mitigation evaluation, path validation,
digital-twin simulation, bounded uncertainty sweeps, and decision-gate enforcement.
"""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from ..config import settings
from ..decision_gate import decide
from ..schemas import GateDecision, GateReport, Scenario, SweepReport
from .models import (
    CandidateAction,
    CandidateComparison,
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
    ValidationStatus,
)
from .reference_evaluator import IndependentReferenceEvaluator
from .simulator import InsufficientModelDataError, NetworkSimulator
from .topologies import get_topology_for_scenario
from .uncertainty_evaluator import CandidateUncertaintyEvaluator
from .validator import CandidatePathValidator

logger = logging.getLogger("fidelitygate.evaluation")


class MitigationEvaluationEngine:
    """Orchestrates Layer 4 candidate mitigation evaluation and digital-twin decision assurance."""

    def __init__(self, storage: Any):
        self.storage = storage
        self.validator = CandidatePathValidator()
        self.simulator = NetworkSimulator()
        self.uncertainty_evaluator = CandidateUncertaintyEvaluator(self.simulator)
        self.reference_evaluator = IndependentReferenceEvaluator(self.simulator)

    def run_evaluation(
        self,
        request: MitigationEvaluationRequest,
    ) -> Tuple[MitigationEvaluationSummary, MitigationEvaluationReport, List[CandidateEvaluation], List[EvaluationEvent]]:
        """Executes full Layer 4 candidate mitigation evaluation pipeline."""
        start_time = time.time()
        eval_id = f"eval-{uuid.uuid4().hex[:8]}"
        events: List[EvaluationEvent] = []
        seq = 1

        def log_event(stage: str, event_type: str, details: Dict[str, Any]) -> None:
            nonlocal seq
            events.append(
                EvaluationEvent(
                    event_id=f"evt-{uuid.uuid4().hex[:8]}",
                    evaluation_id=eval_id,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    stage=stage,
                    actor="mitigation_evaluation_engine",
                    event_type=event_type,
                    details=details,
                    sequence_number=seq,
                )
            )
            seq += 1

        log_event(
            stage="RECEIVED",
            event_type="EVALUATION_INITIATED",
            details={
                "investigation_id": request.investigation_id,
                "scenario_id": request.scenario_id,
                "evaluation_budget": request.evaluation_budget,
            },
        )

        # 1. Load Layer 3 Investigation & Diagnostic Plan
        investigation = self.storage.get_investigation_summary(request.investigation_id)
        if not investigation:
            raise ValueError(f"Investigation '{request.investigation_id}' not found in persistence.")

        plan = self.storage.get_investigation_plan(request.investigation_id)
        if not plan:
            raise ValueError(f"Investigation '{request.investigation_id}' does not have a persisted DiagnosticPlan.")

        # Determine Scenario Context
        scenario_key = request.scenario_id or investigation.scenario_id or "wan_congestion"
        topology = get_topology_for_scenario(scenario_key)
        if not topology:
            raise ValueError(f"No canonical network topology found for scenario '{scenario_key}'.")

        from ..scenarios import DEMO_SCENARIOS
        scenario = DEMO_SCENARIOS.get(scenario_key)
        if not scenario:
            scenario = Scenario(
                scenario_id=topology.scenario_id,
                name=topology.name,
                description=f"Topology for {topology.name}",
                nominal_latency_ms=20.0,
                capacity_mbps=1000.0,
                offered_load_mbps=760.0,
                slo_latency_ms=45.0,
            )

        # 2. Resolve Mitigation Candidates
        candidates = self._resolve_candidates(request, plan, topology, scenario_key)
        log_event(
            stage="RESOLVED_CANDIDATES",
            event_type="CANDIDATES_EXTRACTED",
            details={"candidates_count": len(candidates), "candidate_ids": [c.candidate_id for c in candidates]},
        )

        if not candidates:
            # Controlled fallback: NO_VALID_CANDIDATE
            report = MitigationEvaluationReport(
                evaluation_id=eval_id,
                investigation_id=request.investigation_id,
                plan_id=plan.plan_id,
                scenario_id=scenario_key,
                candidate_evaluations=[],
                selected_candidate_id=None,
                gate_verdict=GateDecision.ABSTAIN,
                gate_justification="No actionable or valid mitigation candidate proposed in diagnostic plan.",
                total_simulations=0,
                duration_ms=round((time.time() - start_time) * 1000.0, 2),
                limitations=["Diagnostic plan did not contain usable candidate interventions."],
            )
            summary = MitigationEvaluationSummary(
                evaluation_id=eval_id,
                investigation_id=request.investigation_id,
                scenario_id=scenario_key,
                status="NO_VALID_CANDIDATE",
                gate_verdict=GateDecision.ABSTAIN,
                candidates_count=0,
                evaluated_count=0,
                compliant_count=0,
                selected_candidate_id=None,
                created_at=report.created_at,
                duration_ms=report.duration_ms,
            )
            self.storage.save_mitigation_evaluation(summary, report, [], events)
            return summary, report, [], events

        # 3. Evaluate Each Candidate
        candidate_evaluations: List[CandidateEvaluation] = []
        total_simulations = 0

        for cand in candidates:
            cand_eval, cand_sims = self._evaluate_single_candidate(
                eval_id=eval_id,
                investigation_id=request.investigation_id,
                scenario_key=scenario_key,
                scenario=scenario,
                topology=topology,
                candidate=cand,
                budget=request.evaluation_budget,
                include_reference=request.include_reference_eval,
                log_event=log_event,
            )
            candidate_evaluations.append(cand_eval)
            total_simulations += cand_sims

        # 4. Synthesize Gate Verdict & Select Best Candidate
        compliant_candidates = [ce for ce in candidate_evaluations if ce.status == CandidateEvaluationStatus.COMPLIANT]
        fragile_candidates = [ce for ce in candidate_evaluations if ce.status == CandidateEvaluationStatus.FRAGILE]

        selected_cand_id: Optional[str] = None
        if compliant_candidates:
            # Pick compliant candidate with lowest predicted latency
            compliant_candidates.sort(key=lambda ce: ce.nominal_prediction.latency_ms if ce.nominal_prediction else float("inf"))
            selected_cand = compliant_candidates[0]
            selected_cand_id = selected_cand.candidate_id
            gate_verdict = GateDecision.ACCEPT
            gate_justification = (
                f"Candidate '{selected_cand_id}' passed all connectivity, capacity, and SLO constraints "
                f"under both nominal and perturbation uncertainty sweeps."
            )
        elif fragile_candidates:
            selected_cand = fragile_candidates[0]
            selected_cand_id = selected_cand.candidate_id
            gate_verdict = GateDecision.GATHER_EVIDENCE
            gate_justification = (
                f"Candidate '{selected_cand_id}' passes nominal prediction, but uncertainty sweep exposes "
                f"fragility ({selected_cand.counterexample.explanation if selected_cand.counterexample else 'breaches detected'}). "
                f"Targeted diagnostic evidence required."
            )
        else:
            gate_verdict = GateDecision.ABSTAIN
            gate_justification = "No evaluated candidate satisfies necessary capacity and SLO constraints. Fail-closed."

        duration_ms = round((time.time() - start_time) * 1000.0, 2)
        log_event(
            stage="GATE_REVIEW",
            event_type="GATE_VERDICT_REACHED",
            details={
                "gate_verdict": gate_verdict.value,
                "selected_candidate_id": selected_cand_id,
                "justification": gate_justification,
            },
        )

        # 5. Assemble Report & Summary
        report = MitigationEvaluationReport(
            evaluation_id=eval_id,
            investigation_id=request.investigation_id,
            plan_id=plan.plan_id,
            scenario_id=scenario_key,
            candidate_evaluations=candidate_evaluations,
            selected_candidate_id=selected_cand_id,
            gate_verdict=gate_verdict,
            gate_justification=gate_justification,
            total_simulations=total_simulations,
            duration_ms=duration_ms,
            reference_evaluation_status=(
                candidate_evaluations[0].reference_evaluation.reference_status.value
                if candidate_evaluations and candidate_evaluations[0].reference_evaluation
                else "NOT_EVALUATED"
            ),
            limitations=[
                "Evaluated in isolated simulation environment; physical network mutation not enacted.",
                "Convex queueing delay approximation is a simplified fluid model, not packet-level discrete-event simulation.",
            ],
        )

        summary = MitigationEvaluationSummary(
            evaluation_id=eval_id,
            investigation_id=request.investigation_id,
            scenario_id=scenario_key,
            status="COMPLETE",
            gate_verdict=gate_verdict,
            candidates_count=len(candidates),
            evaluated_count=len(candidate_evaluations),
            compliant_count=len(compliant_candidates),
            selected_candidate_id=selected_cand_id,
            created_at=report.created_at,
            duration_ms=duration_ms,
        )

        # 6. Persist to Storage Engine
        log_event(
            stage="PERSISTENCE",
            event_type="EVALUATION_PERSISTED",
            details={"evaluation_id": eval_id, "status": "SAVED"},
        )
        self.storage.save_mitigation_evaluation(summary, report, candidate_evaluations, events)

        return summary, report, candidate_evaluations, events

    def _evaluate_single_candidate(
        self,
        eval_id: str,
        investigation_id: str,
        scenario_key: str,
        scenario: Scenario,
        topology: NetworkTopology,
        candidate: CandidateAction,
        budget: int,
        include_reference: bool,
        log_event: Any,
    ) -> Tuple[CandidateEvaluation, int]:
        """Evaluates a single candidate through validation, simulation, sweep, and gate."""
        sims_count = 0

        # Step A: Validate candidate path and topology constraints
        validation = self.validator.validate_candidate(candidate, topology)
        log_event(
            stage="VALIDATION",
            event_type="PATH_VALIDATION_COMPLETED",
            details={
                "candidate_id": candidate.candidate_id,
                "is_valid": validation.is_valid,
                "status": validation.status.value,
            },
        )

        if not validation.is_valid:
            # Invalid candidate must NEVER receive ACCEPT
            gate_report = GateReport(
                decision=GateDecision.ABSTAIN,
                reason=f"Candidate path invalid: {'; '.join(validation.reasons)}",
                report=SweepReport(
                    evaluations=0,
                    nominal_latency_ms=float("inf"),
                    worst_latency_ms=float("inf"),
                    peak_utilization=float("inf"),
                    stability_score=0.0,
                    violations=1,
                    sensitivity={},
                ),
            )
            cand_eval = CandidateEvaluation(
                evaluation_id=eval_id,
                investigation_id=investigation_id,
                scenario_id=scenario_key,
                candidate_id=candidate.candidate_id,
                action=candidate,
                validation=validation,
                nominal_prediction=None,
                uncertainty_report=None,
                counterexample=None,
                comparison=None,
                gate_report=gate_report,
                reference_evaluation=None,
                status=CandidateEvaluationStatus.INVALID_PATH,
                explanation_facts={
                    "why_evaluated": candidate.rationale or "Proposed candidate reroute.",
                    "validation_failed": True,
                    "reasons": validation.reasons,
                    "gate_verdict": GateDecision.ABSTAIN.value,
                },
                limitations=["Candidate failed physical topology validation; cannot be simulated safely."],
            )
            return cand_eval, 0

        # Step B: Digital-Twin Simulation & Before/After Comparison
        try:
            comparison = self.simulator.compare_candidate_to_baseline(topology, candidate)
            nominal_pred = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=candidate.flow_id,
                path=candidate.path,
            )
            sims_count += 2
        except InsufficientModelDataError as imde:
            gate_report = GateReport(
                decision=GateDecision.ABSTAIN,
                reason=f"Insufficient model data: {str(imde)}",
                report=SweepReport(
                    evaluations=0,
                    nominal_latency_ms=float("inf"),
                    worst_latency_ms=float("inf"),
                    peak_utilization=float("inf"),
                    stability_score=0.0,
                    violations=1,
                    sensitivity={},
                ),
            )
            cand_eval = CandidateEvaluation(
                evaluation_id=eval_id,
                investigation_id=investigation_id,
                scenario_id=scenario_key,
                candidate_id=candidate.candidate_id,
                action=candidate,
                validation=validation,
                status=CandidateEvaluationStatus.MODEL_DATA_INSUFFICIENT,
                gate_report=gate_report,
                explanation_facts={"error": str(imde)},
                limitations=["Model parameter missing or invalid in scenario topology."],
            )
            return cand_eval, sims_count
        except Exception as exc:
            logger.error(f"Simulation failure on candidate '{candidate.candidate_id}': {exc}", exc_info=True)
            gate_report = GateReport(
                decision=GateDecision.ABSTAIN,
                reason=f"Simulation calculation error: {str(exc)}",
                report=SweepReport(
                    evaluations=0,
                    nominal_latency_ms=float("inf"),
                    worst_latency_ms=float("inf"),
                    peak_utilization=float("inf"),
                    stability_score=0.0,
                    violations=1,
                    sensitivity={},
                ),
            )
            cand_eval = CandidateEvaluation(
                evaluation_id=eval_id,
                investigation_id=investigation_id,
                scenario_id=scenario_key,
                candidate_id=candidate.candidate_id,
                action=candidate,
                validation=validation,
                status=CandidateEvaluationStatus.FAILED,
                gate_report=gate_report,
                explanation_facts={"error": str(exc)},
                limitations=["Unexpected simulation calculation failure."],
            )
            return cand_eval, sims_count

        # Step C: Bounded Uncertainty Sweep & Counterexample Search
        sweep_report, counterexample = self.uncertainty_evaluator.evaluate_uncertainty(
            topology=topology,
            candidate=candidate,
            evaluations=budget,
            latency_multiplier_range=(scenario.latency_multiplier_min, scenario.latency_multiplier_max),
        )
        sims_count += sweep_report.evaluations

        # Step D: Gate Decision Enforcement
        # Rule check:
        # If candidate flow breaches SLO nominally or capacity violated -> ABSTAIN
        # If any shared flow breached constraints -> ABSTAIN
        # If nominal passes, but sweep has violations -> GATHER_EVIDENCE
        # If all variations pass with 0 violations -> ACCEPT
        if nominal_pred.slo_violated or nominal_pred.capacity_violated or not comparison.all_flows_compliant:
            gate_decision = GateDecision.ABSTAIN
            gate_reason = (
                f"Candidate intervention violates nominal constraints "
                f"(Latency: {nominal_pred.latency_ms} ms vs SLO {nominal_pred.slo_latency_ms} ms, "
                f"All flows compliant: {comparison.all_flows_compliant})."
            )
        elif sweep_report.violations > 0:
            gate_decision = GateDecision.GATHER_EVIDENCE
            gate_reason = (
                f"Nominal prediction satisfies SLO ({nominal_pred.latency_ms} ms <= {nominal_pred.slo_latency_ms} ms), "
                f"but {sweep_report.violations}/{sweep_report.evaluations} uncertainty sweep variations breach constraints. "
                f"Diagnostic evidence required."
            )
        else:
            gate_decision = GateDecision.ACCEPT
            gate_reason = "All evaluated parameter variations pass the latency SLO and stability threshold."

        gate_report = GateReport(
            decision=gate_decision,
            reason=gate_reason,
            report=sweep_report,
        )

        # Step E: Optional Independent Reference Evaluation
        ref_result: Optional[ReferenceEvaluationResult] = None
        if include_reference:
            ref_result = self.reference_evaluator.evaluate_against_reference(
                topology=topology,
                candidate=candidate,
                scenario_key=scenario_key,
            )

        # Step F: Status & Explanation Facts
        if gate_decision == GateDecision.ACCEPT:
            status = CandidateEvaluationStatus.COMPLIANT
        elif gate_decision == GateDecision.GATHER_EVIDENCE:
            status = CandidateEvaluationStatus.FRAGILE
        else:
            status = CandidateEvaluationStatus.INFEASIBLE

        explanation_facts = {
            "why_evaluated": candidate.rationale or "Candidate reroute intervention.",
            "nominal_prediction": {
                "latency_ms": nominal_pred.latency_ms,
                "slo_latency_ms": nominal_pred.slo_latency_ms,
                "peak_utilization": nominal_pred.peak_utilization,
                "bottleneck_edge": nominal_pred.bottleneck_edge_id,
            },
            "constraints_summary": {
                "connectivity": "PASS",
                "capacity": "FAIL" if nominal_pred.capacity_violated else "PASS",
                "slo": "FAIL" if nominal_pred.slo_violated else "PASS",
                "shared_flows": "PASS" if comparison.all_flows_compliant else "FAIL",
            },
            "uncertainty_outcome": {
                "evaluations": sweep_report.evaluations,
                "violations": sweep_report.violations,
                "stability_score": sweep_report.stability_score,
                "worst_latency_ms": sweep_report.worst_latency_ms,
            },
            "counterexample": {
                "is_fragile": counterexample.is_fragile if counterexample else False,
                "critical_parameter": counterexample.critical_parameter if counterexample else "none",
                "violating_latency_ms": counterexample.violating_latency_ms if counterexample else None,
                "explanation": counterexample.explanation if counterexample else "",
            },
            "gate_verdict": gate_decision.value,
            "gate_justification": gate_reason,
        }

        cand_eval = CandidateEvaluation(
            evaluation_id=eval_id,
            investigation_id=investigation_id,
            scenario_id=scenario_key,
            candidate_id=candidate.candidate_id,
            action=candidate,
            validation=validation,
            nominal_prediction=nominal_pred,
            uncertainty_report=sweep_report,
            counterexample=counterexample,
            comparison=comparison,
            gate_report=gate_report,
            reference_evaluation=ref_result,
            status=status,
            explanation_facts=explanation_facts,
            limitations=[
                "Fluid queueing delay approximation (not packet-level discrete-event simulation).",
                "Finite parameter sweep does not formally prove continuous interval safety.",
            ],
        )

        return cand_eval, sims_count

    def _resolve_candidates(
        self,
        request: MitigationEvaluationRequest,
        plan: Any,
        topology: NetworkTopology,
        scenario_key: str,
    ) -> List[CandidateAction]:
        """Resolves candidate actions from explicit request or diagnostic plan."""
        # 1. If explicit candidates provided in request, use them directly
        if request.candidate_actions:
            return request.candidate_actions

        candidates: List[CandidateAction] = []
        primary_flow = topology.flows.get("flow_primary") or (
            list(topology.flows.values())[0] if topology.flows else None
        )
        if not primary_flow:
            return []

        # 2. Extract proposed interventions from DiagnosticPlan
        proposed = getattr(plan, "proposed_interventions", [])
        if proposed:
            for i, p_str in enumerate(proposed):
                # Standard proposed alternate route: bypass spine1 via spine2
                cand_id = p_str if isinstance(p_str, str) else f"cand-{i+1}"
                candidates.append(
                    CandidateAction(
                        candidate_id=cand_id,
                        action_type=MitigationActionType.REROUTE_FLOW,
                        flow_id=primary_flow.flow_id,
                        source_node=primary_flow.source,
                        destination_node=primary_flow.destination,
                        path=["leaf1", "spine2", "leaf6"],
                        rationale="Bypasses congested primary forwarding plane through alternate spine transit.",
                        originating_investigation_id=request.investigation_id,
                    )
                )

        # 3. Fallback: if plan had no interventions, generate standard alternate reroute for the scenario
        if not candidates and "spine2" in topology.nodes:
            candidates.append(
                CandidateAction(
                    candidate_id=f"R-{scenario_key}-alt1",
                    action_type=MitigationActionType.REROUTE_FLOW,
                    flow_id=primary_flow.flow_id,
                    source_node=primary_flow.source,
                    destination_node=primary_flow.destination,
                    path=["leaf1", "spine2", "leaf6"],
                    rationale="Standard fallback candidate reroute via alternate spine2 transit.",
                    originating_investigation_id=request.investigation_id,
                )
            )

        return candidates
