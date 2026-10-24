"""fidelitygate/workflow/simulation_adapter.py
Safe, allowlisted simulation-only intervention adapter.
Executes approved routing interventions purely within the isolated digital-twin simulator,
strictly enforcing human authorization, evidence currency, and before/after outcome calculation.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from fidelitygate.evaluation.models import CandidateAction, NetworkTopology
from fidelitygate.evaluation.simulator import InsufficientModelDataError, NetworkSimulator
from fidelitygate.evaluation.topologies import get_topology_for_scenario
from fidelitygate.evaluation.validator import CandidatePathValidator
from fidelitygate.workflow.models import (
    ApprovalDecision,
    HumanApprovalRecord,
    InterventionOutcomeReport,
    OverallImpact,
    SimulatedInterventionRecord,
)

logger = logging.getLogger("fidelitygate.workflow.simulation")


class SimulationActionAdapter:
    """Executes human-approved interventions strictly in the isolated digital-twin simulator."""

    def __init__(self, simulator: Optional[NetworkSimulator] = None):
        self.simulator = simulator or NetworkSimulator()

    def execute_intervention(
        self,
        workflow_run_id: str,
        scenario_id: str,
        candidate: CandidateAction,
        approval: HumanApprovalRecord,
        topology: Optional[NetworkTopology] = None,
        baseline_evaluation_id: Optional[str] = None,
        ground_truth_reference: Optional[Dict[str, Any]] = None,
    ) -> Tuple[SimulatedInterventionRecord, InterventionOutcomeReport]:
        """Validates authorization, executes isolated digital-twin reroute,
        and computes before/after outcome metrics across all flows.
        """
        # 1. Guardrails & Validation Checks
        if approval.decision != ApprovalDecision.APPROVED:
            raise ValueError(
                f"Cannot execute unapproved intervention. Approval status is '{approval.decision.value}'."
            )

        if approval.is_stale:
            raise ValueError(
                "Cannot execute intervention: evidence or model parameters changed since human approval was granted (approval is stale)."
            )

        if approval.candidate_id != candidate.candidate_id:
            raise ValueError(
                f"Candidate mismatch: approved candidate '{approval.candidate_id}' does not match requested candidate '{candidate.candidate_id}'."
            )

        top = topology or get_topology_for_scenario(scenario_id)
        if not top:
            raise InsufficientModelDataError(f"No validated network topology found for scenario '{scenario_id}'.")

        flow = top.get_flow(candidate.flow_id)
        if not flow:
            raise InsufficientModelDataError(f"Target flow '{candidate.flow_id}' not found in topology for scenario '{scenario_id}'.")

        # 2. Strict Physical & Topological Validation of Candidate
        validator = CandidatePathValidator()
        validation = validator.validate_candidate(candidate, top)
        if not validation.is_valid:
            raise ValueError(f"Invalid candidate action '{candidate.candidate_id}': {'; '.join(validation.reasons)}")

        # 3. Baseline & Candidate Routing State Setup
        baseline_routing = {fid: f.nominal_path for fid, f in top.flows.items()}
        cand_routing = dict(baseline_routing)
        cand_routing[candidate.flow_id] = candidate.path

        # 4. Digital-Twin Full Network Traffic Allocation
        baseline_links = self.simulator.allocate_traffic(top, baseline_routing)
        cand_links = self.simulator.allocate_traffic(top, cand_routing)

        # 5. Simulate Flow-Specific Performance
        base_pred = self.simulator.simulate_flow(top, candidate.flow_id, flow.nominal_path, baseline_routing)
        cand_pred = self.simulator.simulate_flow(top, candidate.flow_id, candidate.path, cand_routing)

        if not cand_pred.is_connected or cand_pred.latency_ms == float("inf"):
            raise ValueError(f"Candidate action '{candidate.candidate_id}' produces a disconnected path in digital-twin simulation.")

        # Full comparison for auxiliary signals
        comparison = self.simulator.compare_candidate_to_baseline(top, candidate)

        # 6. Create execution record
        exec_id = f"sim-exec-{uuid4().hex[:8]}"
        execution_record = SimulatedInterventionRecord(
            execution_id=exec_id,
            workflow_run_id=workflow_run_id,
            approval_id=approval.approval_id,
            candidate_id=candidate.candidate_id,
            action_type="REROUTE_FLOW",
            target_flow_id=candidate.flow_id,
            applied_path=candidate.path,
            simulator_mode="ISOLATED_DIGITAL_TWIN",
            status="SUCCESS",
            notes=[
                "Action executed strictly inside isolated digital-twin simulator.",
                "No live router configurations or physical device control planes were modified.",
            ],
        )

        # 7. Analyze Pre vs Post Metrics & Network-Wide Violations
        pre_lat = round(base_pred.latency_ms, 2)
        post_lat = round(cand_pred.latency_ms, 2)
        delta_lat = round(post_lat - pre_lat, 2)
        pct_reduction = round((delta_lat / pre_lat) * 100.0, 2) if pre_lat > 0 else 0.0

        # Peak link utilization (same documented set of links before and after)
        pre_util = round(max((l.utilization for l in baseline_links.values()), default=0.0), 4)
        post_util = round(max((l.utilization for l in cand_links.values()), default=0.0), 4)

        # Capacity violations: count of relevant links violating capacity constraints
        pre_cap_viols = sum(1 for l in baseline_links.values() if l.is_overloaded or l.utilization > 1.0)
        post_cap_viols = sum(1 for l in cand_links.values() if l.is_overloaded or l.utilization > 1.0)

        # SLO violations: count of relevant flows violating service objectives
        all_base_flow_preds = {
            fid: self.simulator.simulate_flow(top, fid, f.nominal_path, baseline_routing)
            for fid, f in top.flows.items()
        }
        all_cand_flow_preds = {
            fid: self.simulator.simulate_flow(top, fid, cand_routing[fid], cand_routing)
            for fid, f in top.flows.items()
        }

        pre_slo_viols = sum(
            1 for fid, f in top.flows.items()
            if all_base_flow_preds[fid].latency_ms > f.slo_latency_ms
        )
        post_slo_viols = sum(
            1 for fid, f in top.flows.items()
            if all_cand_flow_preds[fid].latency_ms > f.slo_latency_ms
        )

        # Affected flows: target flow + any flows whose latency changed
        affected_flows = sorted(list({
            fid for fid in top.flows
            if fid == candidate.flow_id or round(all_cand_flow_preds[fid].latency_ms, 2) != round(all_base_flow_preds[fid].latency_ms, 2)
        }))

        # Dynamic Bottleneck Link: overloaded link or link with maximum utilization in candidate state
        cand_overloaded = [eid for eid, l in cand_links.items() if l.is_overloaded or l.utilization > 1.0]
        if cand_overloaded:
            bottleneck_edge = cand_overloaded[0]
        else:
            bottleneck_edge = max(cand_links.values(), key=lambda l: l.utilization).edge_id if cand_links else "none"

        # 8. Assess Overall Impact
        has_new_capacity_violation = (post_cap_viols > pre_cap_viols) or bool(cand_overloaded)
        has_new_slo_violation = (post_slo_viols > pre_slo_viols)

        if has_new_capacity_violation or has_new_slo_violation:
            # An intervention that causes any new capacity or SLO violations cannot be claimed improved
            impact = OverallImpact.REGRESSED
        elif delta_lat == 0.0 and post_util == pre_util:
            impact = OverallImpact.UNCHANGED
        elif delta_lat < 0:
            if post_util <= pre_util:
                impact = OverallImpact.IMPROVED
            else:
                # Latency improved but peak link utilization increased
                impact = OverallImpact.MIXED
        elif delta_lat > 0:
            if post_util < pre_util:
                # Latency degraded but utilization improved
                impact = OverallImpact.MIXED
            else:
                impact = OverallImpact.DEGRADED
        else:
            impact = OverallImpact.NEUTRAL

        # 9. Reference Evaluation Check
        ref_status = "REFERENCE_NOT_AVAILABLE"
        is_ref_safe = None
        if ground_truth_reference:
            ref_status = ground_truth_reference.get("reference_status", "POST_HOC_VERIFIED")
            is_ref_safe = ground_truth_reference.get("is_reference_safe")

        # 10. Build InterventionOutcomeReport
        outcome_id = f"out-{uuid4().hex[:8]}"
        post_eval_id = f"eval-post-{uuid4().hex[:8]}"

        outcome_report = InterventionOutcomeReport(
            outcome_id=outcome_id,
            workflow_run_id=workflow_run_id,
            scenario_id=scenario_id,
            candidate_id=candidate.candidate_id,
            approval_id=approval.approval_id,
            execution_id=exec_id,
            baseline_evaluation_id=baseline_evaluation_id,
            post_action_evaluation_id=post_eval_id,
            model_version="fidelitygate-v1.0",
            metric_status="COMPUTED",
            units={
                "latency": "ms",
                "utilization": "ratio",
                "capacity_violations": "count",
                "slo_violations": "count",
            },
            pre_action_latency_ms=pre_lat,
            post_action_latency_ms=post_lat,
            latency_delta_ms=delta_lat,
            latency_reduction_pct=pct_reduction,
            pre_action_peak_utilization=pre_util,
            post_action_peak_utilization=post_util,
            pre_action_slo_violations=pre_slo_viols,
            post_action_slo_violations=post_slo_viols,
            pre_action_capacity_violations=pre_cap_viols,
            post_action_capacity_violations=post_cap_viols,
            affected_flows=affected_flows,
            bottleneck_link=bottleneck_edge,
            overall_impact=impact,
            reference_evaluation_status=ref_status,
            is_reference_safe=is_ref_safe,
            assumptions_and_limitations=[
                "Execution is isolated simulation; no real-world router interfaces or BGP sessions were modified.",
                "Simulator utilizes an M/M/1-inspired convex queueing buffer model under steady-state assumptions.",
                "Telemetry provenance is grounded in Cisco Innovation Edge replay observations and documented topology parameters.",
            ],
        )

        return execution_record, outcome_report
