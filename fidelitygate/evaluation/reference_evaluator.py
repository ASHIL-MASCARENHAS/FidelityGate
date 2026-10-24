"""fidelitygate/evaluation/reference_evaluator.py
Independent reference evaluator measuring candidate intervention safety
against hidden reference ground truth.
Strictly isolated from agent tools, agent prompts, and operational decision paths.
"""

from typing import Any, Dict, List, Optional
from .models import (
    CandidateAction,
    NetworkTopology,
    ReferenceEvaluationResult,
    ReferenceEvaluationStatus,
    TopologyEdge,
)
from .simulator import NetworkSimulator


class IndependentReferenceEvaluator:
    """Offline reference evaluator measuring candidate safety against hidden reference ground truth."""

    # Synthetic reference ground truth profiles for controlled benchmark scenarios
    HIDDEN_REFERENCE_PROFILES: Dict[str, Dict[str, Any]] = {
        "wan_congestion": {
            "has_reference_truth": True,
            # In WAN-042 reality, alternate spine2 has hidden background load or reduced capacity
            "true_load_drift": 1.15,
            "true_latency_drift": 1.10,
            "edge_capacity_overrides": {
                "e_spine2_leaf6": 850.0,  # Actual residual capacity is 850 Mbps instead of nominal 1000 Mbps
            },
        },
        "fiber_drift": {
            "has_reference_truth": True,
            "true_load_drift": 1.05,
            "true_latency_drift": 1.45,  # Real propagation delay has drifted +45%
            "edge_capacity_overrides": {},
        },
        "traffic_burst": {
            "has_reference_truth": True,
            "true_load_drift": 1.25,  # Real burst is +25%
            "true_latency_drift": 1.05,
            "edge_capacity_overrides": {},
        },
    }

    def __init__(self, simulator: Optional[NetworkSimulator] = None):
        self.simulator = simulator or NetworkSimulator()

    def evaluate_against_reference(
        self,
        topology: NetworkTopology,
        candidate: CandidateAction,
        scenario_key: str,
    ) -> ReferenceEvaluationResult:
        """
        Evaluates candidate action against isolated hidden reference ground truth.
        Never called by or accessible to agents during investigation.
        """
        profile = self.HIDDEN_REFERENCE_PROFILES.get(scenario_key)

        # If scenario is a public-data replay or has no reference truth, mark unavailable
        if not profile or not profile.get("has_reference_truth", False):
            return ReferenceEvaluationResult(
                reference_status=ReferenceEvaluationStatus.REFERENCE_NOT_AVAILABLE,
                true_latency_ms=None,
                true_peak_utilization=None,
                ground_truth_safe=None,
                assumptions_difference=None,
                notes=["No hidden synthetic ground truth exists for this scenario (public telemetry replay mode)."],
            )

        # Construct reference topology with hidden parameters
        ref_edges: Dict[str, TopologyEdge] = {}
        for edge_id, edge in topology.edges.items():
            cap = profile.get("edge_capacity_overrides", {}).get(edge_id, edge.capacity_mbps)
            ref_edges[edge_id] = TopologyEdge(
                edge_id=edge.edge_id,
                source=edge.source,
                target=edge.target,
                capacity_mbps=cap,
                base_latency_ms=edge.base_latency_ms,
                background_load_mbps=edge.background_load_mbps,
                status=edge.status,
            )

        ref_topology = NetworkTopology(
            scenario_id=topology.scenario_id,
            name=f"{topology.name} (Hidden Reference Truth)",
            nodes=topology.nodes,
            edges=ref_edges,
            flows=topology.flows,
        )

        true_load_drift = profile.get("true_load_drift", 1.0)
        true_lat_drift = profile.get("true_latency_drift", 1.0)

        # Simulate candidate under hidden reference conditions
        ref_pred = self.simulator.simulate_flow(
            topology=ref_topology,
            target_flow_id=candidate.flow_id,
            path=candidate.path,
            load_multiplier=true_load_drift,
            latency_multiplier=true_lat_drift,
        )

        ground_truth_safe = not ref_pred.slo_violated and not ref_pred.capacity_violated
        status = (
            ReferenceEvaluationStatus.VERIFIED_SAFE
            if ground_truth_safe
            else ReferenceEvaluationStatus.VERIFIED_BREACH
        )

        diff_notes: List[str] = []
        if profile.get("edge_capacity_overrides"):
            diff_notes.append(f"Hidden capacity overrides: {profile['edge_capacity_overrides']}")
        if true_load_drift != 1.0:
            diff_notes.append(f"True load drift: {true_load_drift}x")
        if true_lat_drift != 1.0:
            diff_notes.append(f"True propagation drift: {true_lat_drift}x")

        assumptions_diff = "; ".join(diff_notes) if diff_notes else "Identical to nominal assumptions"

        return ReferenceEvaluationResult(
            reference_status=status,
            true_latency_ms=ref_pred.latency_ms,
            true_peak_utilization=ref_pred.peak_utilization,
            ground_truth_safe=ground_truth_safe,
            assumptions_difference=assumptions_diff,
            notes=[
                f"Reference outcome: {'SAFE' if ground_truth_safe else 'BREACH'}.",
                f"True predicted latency: {ref_pred.latency_ms} ms vs SLO {ref_pred.slo_latency_ms} ms.",
                f"True peak utilization: {ref_pred.peak_utilization:.2f}.",
            ],
        )
