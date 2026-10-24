"""fidelitygate/workflow/orchestrator.py
Layer 7 End-to-End Workflow Orchestrator.
Coordinates Layers 1-6 into one cohesive, auditable business workflow:
Triage -> Investigation -> Candidate Evaluation -> Counterexample Analysis ->
Adaptive Diagnostics -> Reevaluation -> Explanation -> Gate Review ->
Human Approval Boundary -> Simulated Action -> Outcome Reporting.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fidelitygate.adaptive.engine import AdaptiveInvestigationEngine
from fidelitygate.adaptive.models import AdaptiveInvestigationRequest
from fidelitygate.evaluation.engine import MitigationEvaluationEngine
from fidelitygate.evaluation.models import (
    CandidateAction,
    GateDecision,
    MitigationEvaluationRequest,
)
from fidelitygate.evaluation.topologies import get_topology_for_scenario
from fidelitygate.investigation.models import InvestigationRequest
from fidelitygate.investigation.orchestrator import InvestigationOrchestrator
from fidelitygate.triage.engine import AnomalyTriageEngine
from fidelitygate.triage.models import TriageRunRequest
from fidelitygate.workflow.models import (
    ApprovalDecision,
    ApprovalRequest,
    HumanApprovalRecord,
    InterventionOutcomeReport,
    OverallImpact,
    WorkflowEvent,
    WorkflowRunRequest,
    WorkflowRunSummary,
    WorkflowStage,
    WorkflowStatus,
)
from fidelitygate.workflow.simulation_adapter import SimulationActionAdapter
from fidelitygate.xai.engine import ExplanationEngine

logger = logging.getLogger("fidelitygate.workflow.orchestrator")


class EndToEndWorkflowOrchestrator:
    """Master orchestrator driving the full decision assurance workflow."""

    def __init__(self, storage: Optional[Any] = None):
        if storage is None:
            from fidelitygate.storage import StorageEngine
            storage = StorageEngine()
        self.storage = storage

        # Layer Engines
        self.triage_engine = AnomalyTriageEngine(self.storage)
        self.investigation_orchestrator = InvestigationOrchestrator(self.storage)
        self.mitigation_engine = MitigationEvaluationEngine(self.storage)
        self.adaptive_engine = AdaptiveInvestigationEngine(self.storage)
        self.explanation_engine = ExplanationEngine(self.storage)
        self.simulation_adapter = SimulationActionAdapter()

    def initiate_workflow(self, request: WorkflowRunRequest) -> WorkflowRunSummary:
        """Executes the full automated workflow up to the human approval boundary."""
        start_time = time.time()
        started_at = datetime.now(timezone.utc).isoformat()
        wf_id = f"wf-{uuid4().hex[:8]}"
        seq = 1
        events: List[WorkflowEvent] = []

        def log_event(stage: WorkflowStage, event_type: str, details: Dict[str, Any], in_refs: List[str] = None, out_refs: List[str] = None):
            nonlocal seq
            evt = WorkflowEvent(
                event_id=f"wfe-{uuid4().hex[:8]}",
                workflow_run_id=wf_id,
                sequence_number=seq,
                stage=stage,
                event_type=event_type,
                timestamp=datetime.now(timezone.utc).isoformat(),
                input_artifact_refs=in_refs or [],
                output_artifact_refs=out_refs or [],
                details=details,
            )
            seq += 1
            events.append(evt)
            self.storage.save_workflow_event(evt)
            return evt

        # 1. Stage: RECEIVED
        log_event(
            WorkflowStage.RECEIVED,
            "WORKFLOW_INITIATED",
            {"scenario_id": request.scenario_id, "reviewer_id": request.reviewer_id},
        )

        # 2. Stage: VALIDATING
        topology = get_topology_for_scenario(request.scenario_id)
        if not topology:
            err_msg = f"Unknown or invalid scenario '{request.scenario_id}'"
            log_event(WorkflowStage.VALIDATING, "VALIDATION_FAILED", {"error": err_msg})
            summary = WorkflowRunSummary(
                workflow_run_id=wf_id,
                scenario_id=request.scenario_id,
                current_stage=WorkflowStage.VALIDATING,
                status=WorkflowStatus.FAILED,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration_ms=round((time.time() - start_time) * 1000, 2),
                termination_reason=err_msg,
            )
            self.storage.save_workflow_run(summary)
            return summary

        log_event(
            WorkflowStage.VALIDATING,
            "SCENARIO_VALIDATED",
            {"nodes_count": len(topology.nodes), "edges_count": len(topology.edges), "flows_count": len(topology.flows)},
        )

        # 3. Stage: TRIAGE (Layer 2)
        triage_run_id = request.triage_run_id
        if not triage_run_id:
            recent_triages = self.storage.list_triage_summaries(10)
            if recent_triages:
                triage_run_id = recent_triages[0].triage_run_id
            else:
                try:
                    triage_summary, _, _, _ = self.triage_engine.run_triage(
                        TriageRunRequest(source_dataset="cisco-ie/telemetry", anomaly_detection_sensitivity=2.5)
                    )
                    triage_run_id = triage_summary.triage_run_id
                except Exception as exc:
                    err_msg = f"Layer 2 triage execution failed: {exc}"
                    log_event(WorkflowStage.TRIAGE, "TRIAGE_FAILED", {"error": err_msg})
                    summary = WorkflowRunSummary(
                        workflow_run_id=wf_id,
                        scenario_id=request.scenario_id,
                        current_stage=WorkflowStage.TRIAGE,
                        status=WorkflowStatus.FAILED,
                        started_at=started_at,
                        completed_at=datetime.now(timezone.utc).isoformat(),
                        duration_ms=round((time.time() - start_time) * 1000, 2),
                        termination_reason=err_msg,
                    )
                    self.storage.save_workflow_run(summary)
                    return summary

        log_event(WorkflowStage.TRIAGE, "TRIAGE_RESOLVED", {"triage_run_id": triage_run_id}, out_refs=[triage_run_id])

        # 4. Stage: INVESTIGATION (Layer 3)
        inv_summary = None
        recent_invs = self.storage.list_investigation_summaries(10)
        matching_inv = next((i for i in recent_invs if i.triage_run_id == triage_run_id), None)
        if matching_inv:
            inv_summary = matching_inv
            investigation_id = matching_inv.investigation_id
        else:
            try:
                inv_summary, _, _, _ = self.investigation_orchestrator.run_investigation(
                    InvestigationRequest(triage_run_id=triage_run_id)
                )
                investigation_id = inv_summary.investigation_id
            except Exception as exc:
                err_msg = f"Layer 3 agentic investigation failed: {exc}"
                log_event(WorkflowStage.INVESTIGATION, "INVESTIGATION_FAILED", {"error": err_msg})
                summary = WorkflowRunSummary(
                    workflow_run_id=wf_id,
                    scenario_id=request.scenario_id,
                    current_stage=WorkflowStage.INVESTIGATION,
                    status=WorkflowStatus.FAILED,
                    triage_run_id=triage_run_id,
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc).isoformat(),
                    duration_ms=round((time.time() - start_time) * 1000, 2),
                    termination_reason=err_msg,
                )
                self.storage.save_workflow_run(summary)
                return summary

        log_event(
            WorkflowStage.INVESTIGATION,
            "INVESTIGATION_RESOLVED",
            {
                "investigation_id": investigation_id,
                "hypotheses_count": inv_summary.hypotheses_count,
                "selected_diagnostic_id": inv_summary.selected_diagnostic_id,
            },
            in_refs=[triage_run_id],
            out_refs=[investigation_id],
        )

        # 5. Stage: CANDIDATE_EVALUATION (Layer 4)
        try:
            eval_summary, eval_report, candidates, _ = self.mitigation_engine.run_evaluation(
                MitigationEvaluationRequest(
                    investigation_id=investigation_id,
                    scenario_id=request.scenario_id,
                    evaluation_budget=request.simulation_budget,
                )
            )
            evaluation_id = eval_summary.evaluation_id
            selected_cand_id = eval_report.selected_candidate_id
            current_gate_verdict = eval_summary.gate_verdict
        except Exception as exc:
            err_msg = f"Layer 4 mitigation evaluation failed: {exc}"
            log_event(WorkflowStage.CANDIDATE_EVALUATION, "EVALUATION_FAILED", {"error": err_msg})
            summary = WorkflowRunSummary(
                workflow_run_id=wf_id,
                scenario_id=request.scenario_id,
                current_stage=WorkflowStage.CANDIDATE_EVALUATION,
                status=WorkflowStatus.FAILED,
                triage_run_id=triage_run_id,
                investigation_id=investigation_id,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration_ms=round((time.time() - start_time) * 1000, 2),
                termination_reason=err_msg,
            )
            self.storage.save_workflow_run(summary)
            return summary

        log_event(
            WorkflowStage.CANDIDATE_EVALUATION,
            "CANDIDATES_EVALUATED",
            {"evaluation_id": evaluation_id, "selected_candidate_id": selected_cand_id, "initial_verdict": current_gate_verdict.value},
            in_refs=[investigation_id],
            out_refs=[evaluation_id],
        )

        # 6. Stage: COUNTEREXAMPLE_ANALYSIS (Layer 4)
        has_counterexamples = False
        ce_cause = None
        cand_evals = self.storage.get_candidate_evaluations(evaluation_id)
        selected_cand_eval = next((c for c in cand_evals if c.candidate_id == selected_cand_id), (cand_evals[0] if cand_evals else None))
        if selected_cand_eval and selected_cand_eval.counterexample:
            has_counterexamples = selected_cand_eval.counterexample.is_fragile
            ce_cause = selected_cand_eval.counterexample.critical_parameter

        log_event(
            WorkflowStage.COUNTEREXAMPLE_ANALYSIS,
            "COUNTEREXAMPLE_ANALYSIS_COMPLETED",
            {"has_counterexamples": has_counterexamples, "fragility_cause": ce_cause},
            in_refs=[evaluation_id],
        )

        # 7 & 8. Stage: ADAPTIVE_DIAGNOSTICS & REEVALUATION (Layer 5)
        adaptive_run_id = None
        if current_gate_verdict == GateDecision.GATHER_EVIDENCE:
            try:
                adapt_req = AdaptiveInvestigationRequest(
                    evaluation_id=evaluation_id,
                    max_diagnostic_cycles=request.max_adaptive_cycles,
                    simulation_budget_per_cycle=request.simulation_budget,
                )
                adapt_summary, adapt_report, _ = self.adaptive_engine.run_adaptive_investigation(adapt_req)
                adaptive_run_id = adapt_summary.adaptive_run_id
                current_gate_verdict = adapt_summary.final_gate_decision

                log_event(
                    WorkflowStage.ADAPTIVE_DIAGNOSTICS,
                    "DIAGNOSTIC_MEASUREMENT_ACQUIRED",
                    {
                        "adaptive_run_id": adaptive_run_id,
                        "diagnostics_executed": adapt_summary.diagnostics_executed_count,
                        "total_cost": adapt_summary.total_diagnostic_cost_usd,
                    },
                    in_refs=[evaluation_id],
                    out_refs=[adaptive_run_id],
                )

                log_event(
                    WorkflowStage.REEVALUATION,
                    "UNCERTAINTY_REEVALUATION_COMPLETED",
                    {
                        "initial_decision": adapt_summary.initial_gate_decision.value,
                        "new_decision": adapt_summary.final_gate_decision.value,
                        "decision_changed": adapt_summary.decision_changed,
                    },
                    in_refs=[adaptive_run_id],
                )
            except Exception as exc:
                logger.warning(f"Adaptive diagnostic loop failed; proceeding with pre-adaptive gate: {exc}")

        # 9. Stage: EXPLANATION (Layer 6)
        try:
            explanation = self.explanation_engine.generate_explanation(
                evaluation_id=evaluation_id if not adaptive_run_id else None,
                adaptive_run_id=adaptive_run_id,
                scenario_id=request.scenario_id,
                compute_sensitivity=True,
            )
            explanation_id = explanation.explanation_id
            log_event(
                WorkflowStage.EXPLANATION,
                "EXPLANATION_SYNTHESIZED",
                {"explanation_id": explanation_id, "rules_evaluated": len(explanation.constraint_results)},
                out_refs=[explanation_id],
            )
        except Exception as exc:
            explanation_id = None
            logger.warning(f"Explanation synthesis failed: {exc}")

        # 10. Stage: GATE_REVIEW
        log_event(
            WorkflowStage.GATE_REVIEW,
            "GATE_DECISION_FINALIZED",
            {"authoritative_gate_verdict": current_gate_verdict.value, "candidate_id": selected_cand_id},
        )

        # Check Abstain Termination Condition
        if current_gate_verdict == GateDecision.ABSTAIN:
            summary = WorkflowRunSummary(
                workflow_run_id=wf_id,
                scenario_id=request.scenario_id,
                current_stage=WorkflowStage.GATE_REVIEW,
                status=WorkflowStatus.ABSTAINED,
                triage_run_id=triage_run_id,
                investigation_id=investigation_id,
                evaluation_id=evaluation_id,
                adaptive_run_id=adaptive_run_id,
                explanation_id=explanation_id,
                selected_candidate_id=selected_cand_id,
                gate_verdict=current_gate_verdict,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                duration_ms=round((time.time() - start_time) * 1000, 2),
                termination_reason="Authoritative decision gate evaluated ABSTAIN: no proposed candidate satisfies policy constraints.",
            )
            log_event(WorkflowStage.GATE_REVIEW, "WORKFLOW_ABSTAINED", {"reason": summary.termination_reason})
            self.storage.save_workflow_run(summary)
            return summary

        # 11. Stage: AWAITING_HUMAN_APPROVAL
        summary = WorkflowRunSummary(
            workflow_run_id=wf_id,
            scenario_id=request.scenario_id,
            current_stage=WorkflowStage.AWAITING_HUMAN_APPROVAL,
            status=WorkflowStatus.AWAITING_APPROVAL,
            triage_run_id=triage_run_id,
            investigation_id=investigation_id,
            evaluation_id=evaluation_id,
            adaptive_run_id=adaptive_run_id,
            explanation_id=explanation_id,
            selected_candidate_id=selected_cand_id,
            gate_verdict=current_gate_verdict,
            started_at=started_at,
            duration_ms=round((time.time() - start_time) * 1000, 2),
        )
        log_event(
            WorkflowStage.AWAITING_HUMAN_APPROVAL,
            "AWAITING_HUMAN_AUTHORIZATION",
            {
                "candidate_id": selected_cand_id,
                "gate_verdict": current_gate_verdict.value,
                "notice": "Consequential routing change requires explicit human authorization before simulation execution.",
            },
        )
        self.storage.save_workflow_run(summary)

        # Auto-approve if requested
        if request.auto_approve_for_testing:
            summary, _ = self.submit_approval(
                wf_id,
                ApprovalRequest(
                    decision=ApprovalDecision.APPROVED,
                    reviewer_id=request.reviewer_id,
                    reviewer_comment="Auto-approved in testing mode.",
                ),
            )

        return summary

    def submit_approval(self, workflow_run_id: str, request: ApprovalRequest) -> Tuple[WorkflowRunSummary, HumanApprovalRecord]:
        """Records a human authorization, rejection, or changes-requested decision."""
        summary = self.storage.get_workflow_run(workflow_run_id)
        if not summary:
            raise ValueError(f"Workflow run '{workflow_run_id}' not found.")

        # Check existing approval idempotency first
        existing_approval = self.storage.get_approval_by_workflow(workflow_run_id)
        if existing_approval and request.idempotency_key and existing_approval.idempotency_key == request.idempotency_key:
            return summary, existing_approval

        if summary.current_stage not in (WorkflowStage.AWAITING_HUMAN_APPROVAL, WorkflowStage.GATE_REVIEW):
            raise ValueError(
                f"Cannot record approval for workflow in stage '{summary.current_stage.value}'. Must be in 'AWAITING_HUMAN_APPROVAL'."
            )

        if summary.gate_verdict == GateDecision.ABSTAIN and request.decision == ApprovalDecision.APPROVED:
            raise ValueError("Gate ABSTAIN cannot be overridden by human approval. The intervention violates mandatory safety constraints.")

        approval_id = f"appr-{uuid4().hex[:8]}"
        approval = HumanApprovalRecord(
            approval_id=approval_id,
            workflow_run_id=workflow_run_id,
            candidate_id=summary.selected_candidate_id or "R-alt1",
            gate_verdict=summary.gate_verdict or GateDecision.ACCEPT,
            explanation_id=summary.explanation_id or "expl-none",
            evidence_version="fidelitygate-v1.0",
            decision=request.decision,
            reviewer_id=request.reviewer_id,
            reviewer_comment=request.reviewer_comment,
            is_stale=False,
            idempotency_key=request.idempotency_key,
        )
        self.storage.save_approval(approval)

        events = self.storage.get_workflow_events(workflow_run_id)
        next_seq = (events[-1].sequence_number + 1) if events else 1

        if request.decision == ApprovalDecision.REJECTED:
            evt = WorkflowEvent(
                event_id=f"wfe-{uuid4().hex[:8]}",
                workflow_run_id=workflow_run_id,
                sequence_number=next_seq,
                stage=WorkflowStage.AWAITING_HUMAN_APPROVAL,
                event_type="HUMAN_AUTHORIZATION_REJECTED",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"reviewer_id": request.reviewer_id, "comment": request.reviewer_comment},
            )
            self.storage.save_workflow_event(evt)
            updated_summary = WorkflowRunSummary(
                workflow_run_id=summary.workflow_run_id,
                scenario_id=summary.scenario_id,
                current_stage=WorkflowStage.AWAITING_HUMAN_APPROVAL,
                status=WorkflowStatus.REJECTED_BY_HUMAN,
                triage_run_id=summary.triage_run_id,
                investigation_id=summary.investigation_id,
                evaluation_id=summary.evaluation_id,
                adaptive_run_id=summary.adaptive_run_id,
                explanation_id=summary.explanation_id,
                selected_candidate_id=summary.selected_candidate_id,
                gate_verdict=summary.gate_verdict,
                approval_id=approval_id,
                approval_status=ApprovalDecision.REJECTED,
                started_at=summary.started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                termination_reason=f"Intervention rejected by operator '{request.reviewer_id}'. Network remains unchanged.",
            )
            self.storage.save_workflow_run(updated_summary)
            return updated_summary, approval

        if request.decision == ApprovalDecision.CHANGES_REQUESTED:
            evt = WorkflowEvent(
                event_id=f"wfe-{uuid4().hex[:8]}",
                workflow_run_id=workflow_run_id,
                sequence_number=next_seq,
                stage=WorkflowStage.AWAITING_HUMAN_APPROVAL,
                event_type="CHANGES_REQUESTED_BY_HUMAN",
                timestamp=datetime.now(timezone.utc).isoformat(),
                details={"reviewer_id": request.reviewer_id, "comment": request.reviewer_comment},
            )
            self.storage.save_workflow_event(evt)
            updated_summary = WorkflowRunSummary(
                workflow_run_id=summary.workflow_run_id,
                scenario_id=summary.scenario_id,
                current_stage=WorkflowStage.AWAITING_HUMAN_APPROVAL,
                status=WorkflowStatus.CHANGES_REQUESTED,
                triage_run_id=summary.triage_run_id,
                investigation_id=summary.investigation_id,
                evaluation_id=summary.evaluation_id,
                adaptive_run_id=summary.adaptive_run_id,
                explanation_id=summary.explanation_id,
                selected_candidate_id=summary.selected_candidate_id,
                gate_verdict=summary.gate_verdict,
                approval_id=approval_id,
                approval_status=ApprovalDecision.CHANGES_REQUESTED,
                started_at=summary.started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                termination_reason=f"Operator requested alternative candidates or parameter modifications: {request.reviewer_comment}",
            )
            self.storage.save_workflow_run(updated_summary)
            return updated_summary, approval

        # Decision is APPROVED: Transition and trigger simulation
        evt = WorkflowEvent(
            event_id=f"wfe-{uuid4().hex[:8]}",
            workflow_run_id=workflow_run_id,
            sequence_number=next_seq,
            stage=WorkflowStage.AWAITING_HUMAN_APPROVAL,
            event_type="HUMAN_AUTHORIZATION_GRANTED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"reviewer_id": request.reviewer_id, "approval_id": approval_id},
        )
        self.storage.save_workflow_event(evt)

        # Update summary to approved and execute simulation
        summary_approved = WorkflowRunSummary(
            workflow_run_id=summary.workflow_run_id,
            scenario_id=summary.scenario_id,
            current_stage=WorkflowStage.SIMULATED_ACTION,
            status=WorkflowStatus.IN_PROGRESS,
            triage_run_id=summary.triage_run_id,
            investigation_id=summary.investigation_id,
            evaluation_id=summary.evaluation_id,
            adaptive_run_id=summary.adaptive_run_id,
            explanation_id=summary.explanation_id,
            selected_candidate_id=summary.selected_candidate_id,
            gate_verdict=summary.gate_verdict,
            approval_id=approval_id,
            approval_status=ApprovalDecision.APPROVED,
            started_at=summary.started_at,
        )
        self.storage.save_workflow_run(summary_approved)

        final_summary, _ = self.execute_simulated_intervention(workflow_run_id)
        return final_summary, approval

    def execute_simulated_intervention(self, workflow_run_id: str) -> Tuple[WorkflowRunSummary, InterventionOutcomeReport]:
        """Executes the approved intervention in the isolated simulator and reports outcome."""
        summary = self.storage.get_workflow_run(workflow_run_id)
        if not summary:
            raise ValueError(f"Workflow run '{workflow_run_id}' not found.")

        approval = self.storage.get_approval_by_workflow(workflow_run_id)
        if not approval or approval.decision != ApprovalDecision.APPROVED:
            raise ValueError(f"Cannot execute intervention: workflow '{workflow_run_id}' lacks valid human approval.")

        # Resolve candidate action
        candidate_evals = self.storage.get_candidate_evaluations(summary.evaluation_id) if summary.evaluation_id else []
        cand_eval = next((c for c in candidate_evals if c.candidate_id == approval.candidate_id), None)
        if not cand_eval and candidate_evals:
            cand_eval = candidate_evals[0]

        topology = get_topology_for_scenario(summary.scenario_id)
        if not topology:
            raise ValueError(f"Topology for scenario '{summary.scenario_id}' not found.")

        if not cand_eval:
            primary_flow = topology.flows.get("flow_primary") or (
                list(topology.flows.values())[0] if topology.flows else None
            )
            if not primary_flow:
                raise ValueError(f"Scenario '{summary.scenario_id}' has no configured traffic flows.")
            alt_path = ["leaf1", "spine2", "leaf6"] if "spine2" in topology.nodes else primary_flow.nominal_path
            candidate = CandidateAction(
                candidate_id=approval.candidate_id,
                action_type="REROUTE_FLOW",
                flow_id=primary_flow.flow_id,
                source_node=primary_flow.source,
                destination_node=primary_flow.destination,
                path=alt_path,
                description=f"Alternate path for {summary.scenario_id}.",
            )
        else:
            candidate = cand_eval.action

        events = self.storage.get_workflow_events(workflow_run_id)
        next_seq = (events[-1].sequence_number + 1) if events else 1

        evt_sim = WorkflowEvent(
            event_id=f"wfe-{uuid4().hex[:8]}",
            workflow_run_id=workflow_run_id,
            sequence_number=next_seq,
            stage=WorkflowStage.SIMULATED_ACTION,
            event_type="SIMULATED_ACTION_EXECUTED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={"candidate_id": candidate.candidate_id, "path": candidate.path, "mode": "ISOLATED_DIGITAL_TWIN"},
        )
        self.storage.save_workflow_event(evt_sim)

        # Execute simulation
        exec_record, outcome_report = self.simulation_adapter.execute_intervention(
            workflow_run_id=workflow_run_id,
            scenario_id=summary.scenario_id,
            candidate=candidate,
            approval=approval,
            topology=topology,
            baseline_evaluation_id=summary.evaluation_id,
        )
        self.storage.save_outcome(outcome_report)

        # Log completion event
        evt_out = WorkflowEvent(
            event_id=f"wfe-{uuid4().hex[:8]}",
            workflow_run_id=workflow_run_id,
            sequence_number=next_seq + 1,
            stage=WorkflowStage.OUTCOME_REPORTED,
            event_type="OUTCOME_REPORTED",
            timestamp=datetime.now(timezone.utc).isoformat(),
            details={
                "outcome_id": outcome_report.outcome_id,
                "overall_impact": outcome_report.overall_impact.value,
                "pre_latency_ms": outcome_report.pre_action_latency_ms,
                "post_latency_ms": outcome_report.post_action_latency_ms,
                "latency_delta_ms": outcome_report.latency_delta_ms,
            },
            out_refs=[outcome_report.outcome_id],
        )
        self.storage.save_workflow_event(evt_out)

        completed_at = datetime.now(timezone.utc).isoformat()
        try:
            t0 = datetime.fromisoformat(summary.started_at)
            t1 = datetime.fromisoformat(completed_at)
            duration_ms = round((t1 - t0).total_seconds() * 1000, 2)
        except Exception:
            duration_ms = 0.0

        final_summary = WorkflowRunSummary(
            workflow_run_id=summary.workflow_run_id,
            scenario_id=summary.scenario_id,
            current_stage=WorkflowStage.OUTCOME_REPORTED,
            status=WorkflowStatus.COMPLETED,
            triage_run_id=summary.triage_run_id,
            investigation_id=summary.investigation_id,
            evaluation_id=summary.evaluation_id,
            adaptive_run_id=summary.adaptive_run_id,
            explanation_id=summary.explanation_id,
            selected_candidate_id=summary.selected_candidate_id,
            gate_verdict=summary.gate_verdict,
            approval_id=approval.approval_id,
            approval_status=ApprovalDecision.APPROVED,
            outcome_id=outcome_report.outcome_id,
            overall_impact=outcome_report.overall_impact,
            started_at=summary.started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
        )
        self.storage.save_workflow_run(final_summary)
        return final_summary, outcome_report
