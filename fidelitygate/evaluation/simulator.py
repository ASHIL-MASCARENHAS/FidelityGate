"""fidelitygate/evaluation/simulator.py
Deterministic digital-twin network simulation engine implementing M/M/1
convex queueing delay approximation, full multi-flow traffic allocation,
and before/after intervention comparison.
"""

from typing import Dict, List, Optional, Set, Tuple
from .models import (
    CandidateAction,
    CandidateComparison,
    LinkSimulationResult,
    NetworkTopology,
    SimulationPrediction,
    TopologyEdge,
    TrafficFlow,
)


class InsufficientModelDataError(ValueError):
    """Raised when critical model parameters (capacities, latencies) are missing or invalid."""
    pass


class NetworkSimulator:
    """Calculates network link utilization, queueing delay, and path latencies."""

    MODEL_VERSION = "M/M/1-convex-queueing-v1.0"
    ASSUMPTIONS = [
        "M/M/1-inspired convex buffer queueing delay approximation (not packet-level discrete-event simulation).",
        "Steady-state fluid traffic demands across the evaluation window.",
        "Additive independent link propagation delays with bounded queueing interaction.",
    ]

    def __init__(self, model_version: Optional[str] = None):
        self.model_version = model_version or self.MODEL_VERSION

    def calculate_link_delay(
        self,
        base_latency_ms: float,
        load_mbps: float,
        capacity_mbps: float,
        latency_multiplier: float = 1.0,
    ) -> Tuple[float, float, float]:
        """
        Calculates link utilization, queue factor, and resulting link delay.
        Returns: (utilization, queue_factor, delay_ms)
        """
        if capacity_mbps <= 0:
            raise InsufficientModelDataError(f"Link capacity must be strictly positive, got {capacity_mbps} Mbps.")

        raw_util = load_mbps / capacity_mbps
        bounded_util = min(raw_util, 0.999)
        queue_factor = 0.15 * bounded_util / max(1.0 - bounded_util, 0.05)
        delay_ms = base_latency_ms * latency_multiplier * (1.0 + queue_factor)

        return float(raw_util), float(queue_factor), float(delay_ms)

    def allocate_traffic(
        self,
        topology: NetworkTopology,
        flow_paths: Dict[str, List[str]],
        load_multiplier: float = 1.0,
        latency_multiplier: float = 1.0,
    ) -> Dict[str, LinkSimulationResult]:
        """
        Calculates traffic allocation for all links under specified routing of all flows.
        Equation: B_e = b_e + sum_k (q_k * x_ke)
        """
        # 1. Initialize link loads with background traffic
        link_loads: Dict[str, float] = {}
        for edge_id, edge in topology.edges.items():
            if edge.capacity_mbps <= 0:
                raise InsufficientModelDataError(f"Edge '{edge_id}' has invalid capacity {edge.capacity_mbps} Mbps.")
            link_loads[edge_id] = edge.background_load_mbps * load_multiplier

        # 2. Add demand of each active flow to traversed edges
        for flow_id, path in flow_paths.items():
            flow = topology.get_flow(flow_id)
            if not flow:
                continue

            demand = flow.demand_mbps * load_multiplier
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i + 1]
                edge = topology.get_edge(u, v)
                if not edge:
                    raise InsufficientModelDataError(f"Missing edge between '{u}' and '{v}' for flow '{flow_id}'.")
                link_loads[edge.edge_id] += demand

        # 3. Compute per-link utilization and delay
        link_results: Dict[str, LinkSimulationResult] = {}
        for edge_id, edge in topology.edges.items():
            load = link_loads[edge_id]
            util, _, delay = self.calculate_link_delay(
                base_latency_ms=edge.base_latency_ms,
                load_mbps=load,
                capacity_mbps=edge.capacity_mbps,
                latency_multiplier=latency_multiplier,
            )
            link_results[edge_id] = LinkSimulationResult(
                edge_id=edge_id,
                source=edge.source,
                target=edge.target,
                load_mbps=round(load, 2),
                capacity_mbps=edge.capacity_mbps,
                utilization=round(util, 4),
                delay_ms=round(delay, 2),
                is_overloaded=(load > edge.capacity_mbps),
            )

        return link_results

    def simulate_flow(
        self,
        topology: NetworkTopology,
        target_flow_id: str,
        path: List[str],
        all_flow_paths: Optional[Dict[str, List[str]]] = None,
        load_multiplier: float = 1.0,
        latency_multiplier: float = 1.0,
    ) -> SimulationPrediction:
        """Simulates path latency, bottleneck link, and SLO compliance for a target flow."""
        flow = topology.get_flow(target_flow_id)
        if not flow:
            raise InsufficientModelDataError(f"Target flow '{target_flow_id}' not found in scenario.")

        # Default routing for all flows if not provided
        routing = dict(all_flow_paths) if all_flow_paths else {}
        for fid, f in topology.flows.items():
            if fid not in routing:
                routing[fid] = f.nominal_path
        routing[target_flow_id] = path

        # Allocate traffic across entire graph
        link_sims = self.allocate_traffic(
            topology=topology,
            flow_paths=routing,
            load_multiplier=load_multiplier,
            latency_multiplier=latency_multiplier,
        )

        # Compute path metrics
        path_latency = 0.0
        path_link_results: List[LinkSimulationResult] = []
        bottleneck_edge: Optional[str] = None
        max_edge_util = 0.0
        capacity_violated = False

        for i in range(len(path) - 1):
            u = path[i]
            v = path[i + 1]
            edge = topology.get_edge(u, v)
            if not edge:
                return SimulationPrediction(
                    flow_id=target_flow_id,
                    latency_ms=float("inf"),
                    slo_latency_ms=flow.slo_latency_ms,
                    peak_utilization=float("inf"),
                    is_connected=False,
                    capacity_violated=True,
                    slo_violated=True,
                    bottleneck_edge_id=None,
                    model_version=self.model_version,
                    assumptions=self.ASSUMPTIONS,
                )

            res = link_sims[edge.edge_id]
            path_link_results.append(res)
            path_latency += res.delay_ms

            if res.utilization > max_edge_util:
                max_edge_util = res.utilization
                bottleneck_edge = edge.edge_id

            if res.is_overloaded:
                capacity_violated = True

        slo_violated = path_latency > flow.slo_latency_ms

        return SimulationPrediction(
            flow_id=target_flow_id,
            latency_ms=round(path_latency, 2),
            slo_latency_ms=flow.slo_latency_ms,
            peak_utilization=round(max_edge_util, 4),
            is_connected=True,
            capacity_violated=capacity_violated,
            slo_violated=slo_violated,
            bottleneck_edge_id=bottleneck_edge,
            link_results=path_link_results,
            model_version=self.model_version,
            assumptions=self.ASSUMPTIONS,
        )

    def compare_candidate_to_baseline(
        self,
        topology: NetworkTopology,
        candidate: CandidateAction,
        load_multiplier: float = 1.0,
        latency_multiplier: float = 1.0,
    ) -> CandidateComparison:
        """
        Computes structured before/after comparison between baseline nominal state
        and post-candidate state, evaluating full shared traffic allocation.
        """
        flow = topology.get_flow(candidate.flow_id)
        if not flow:
            raise InsufficientModelDataError(f"Flow '{candidate.flow_id}' not found.")

        # 1. Baseline State (all flows on nominal paths)
        baseline_routing = {fid: f.nominal_path for fid, f in topology.flows.items()}
        baseline_links = self.allocate_traffic(
            topology=topology,
            flow_paths=baseline_routing,
            load_multiplier=load_multiplier,
            latency_multiplier=latency_multiplier,
        )
        base_pred = self.simulate_flow(
            topology=topology,
            target_flow_id=candidate.flow_id,
            path=flow.nominal_path,
            all_flow_paths=baseline_routing,
            load_multiplier=load_multiplier,
            latency_multiplier=latency_multiplier,
        )

        # 2. Candidate State (target flow rerouted to candidate path)
        cand_routing = dict(baseline_routing)
        cand_routing[candidate.flow_id] = candidate.path
        cand_links = self.allocate_traffic(
            topology=topology,
            flow_paths=cand_routing,
            load_multiplier=load_multiplier,
            latency_multiplier=latency_multiplier,
        )
        cand_pred = self.simulate_flow(
            topology=topology,
            target_flow_id=candidate.flow_id,
            path=candidate.path,
            all_flow_paths=cand_routing,
            load_multiplier=load_multiplier,
            latency_multiplier=latency_multiplier,
        )

        # 3. Latency differences (guarded against division by zero)
        lat_diff = round(cand_pred.latency_ms - base_pred.latency_ms, 2)
        lat_pct: Optional[float] = None
        if base_pred.latency_ms > 0:
            lat_pct = round((lat_diff / base_pred.latency_ms) * 100.0, 2)

        # 4. Peak utilization difference
        peak_diff = round(cand_pred.peak_utilization - base_pred.peak_utilization, 4)

        # 5. Newly Overloaded Edges
        newly_overloaded: List[str] = []
        for eid, cand_res in cand_links.items():
            base_res = baseline_links.get(eid)
            was_overloaded = base_res.is_overloaded if base_res else False
            if cand_res.is_overloaded and not was_overloaded:
                newly_overloaded.append(eid)

        # 6. Shared Flow Impacts
        shared_impacts: List[Dict[str, Any]] = []
        all_flows_compliant = not cand_pred.slo_violated and not cand_pred.capacity_violated

        for other_fid, other_flow in topology.flows.items():
            if other_fid == candidate.flow_id:
                continue

            other_base_pred = self.simulate_flow(
                topology=topology,
                target_flow_id=other_fid,
                path=other_flow.nominal_path,
                all_flow_paths=baseline_routing,
                load_multiplier=load_multiplier,
                latency_multiplier=latency_multiplier,
            )
            other_cand_pred = self.simulate_flow(
                topology=topology,
                target_flow_id=other_fid,
                path=other_flow.nominal_path,
                all_flow_paths=cand_routing,
                load_multiplier=load_multiplier,
                latency_multiplier=latency_multiplier,
            )

            shared_impacts.append({
                "flow_id": other_fid,
                "baseline_latency_ms": other_base_pred.latency_ms,
                "candidate_latency_ms": other_cand_pred.latency_ms,
                "latency_change_ms": round(other_cand_pred.latency_ms - other_base_pred.latency_ms, 2),
                "slo_latency_ms": other_flow.slo_latency_ms,
                "is_compliant": not other_cand_pred.slo_violated and not other_cand_pred.capacity_violated,
            })

            if other_cand_pred.slo_violated or other_cand_pred.capacity_violated:
                all_flows_compliant = False

        notes: List[str] = []
        if lat_diff < 0:
            notes.append(f"Candidate reduces path latency by {abs(lat_diff)} ms ({abs(lat_pct or 0.0)}%).")
        elif lat_diff > 0:
            notes.append(f"Candidate increases path latency by {lat_diff} ms ({lat_pct or 0.0}%).")
        else:
            notes.append("Candidate latency is identical to baseline.")

        if newly_overloaded:
            notes.append(f"Warning: Candidate newly overloads link(s): {newly_overloaded}.")

        if not all_flows_compliant:
            notes.append("Critical: Intervention causes one or more shared flows or links to breach constraints.")

        return CandidateComparison(
            baseline_latency_ms=base_pred.latency_ms,
            candidate_latency_ms=cand_pred.latency_ms,
            latency_change_ms=lat_diff,
            latency_change_pct=lat_pct,
            baseline_peak_utilization=base_pred.peak_utilization,
            candidate_peak_utilization=cand_pred.peak_utilization,
            peak_utilization_change=peak_diff,
            newly_overloaded_edges=newly_overloaded,
            shared_flow_impacts=shared_impacts,
            all_flows_compliant=all_flows_compliant,
            comparison_supported=True,
            notes=notes,
        )

