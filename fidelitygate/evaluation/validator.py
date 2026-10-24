"""fidelitygate/evaluation/validator.py
Strict, deterministic validation of candidate paths against canonical topology,
flow constraints, and allowable mitigation action types.
"""

from typing import List
from .models import (
    CandidateAction,
    MitigationActionType,
    NetworkTopology,
    PathValidationResult,
    ValidationStatus,
)


class CandidatePathValidator:
    """Validates candidate actions against canonical topology graphs and flow rules."""

    ALLOWLISTED_ACTION_TYPES = {
        MitigationActionType.REROUTE_FLOW,
        MitigationActionType.LOAD_BALANCE,
        MitigationActionType.TRAFFIC_SHAPING,
    }

    def validate_candidate(
        self,
        candidate: CandidateAction,
        topology: NetworkTopology,
    ) -> PathValidationResult:
        """Deterministically evaluates candidate path structure, connectivity, and flow constraints."""
        reasons: List[str] = []

        # 1. Action Type Allowlist Check
        if candidate.action_type not in self.ALLOWLISTED_ACTION_TYPES:
            reasons.append(
                f"Action type '{candidate.action_type}' is not allowlisted. Permitted: {[a.value for a in self.ALLOWLISTED_ACTION_TYPES]}"
            )
            return PathValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID_ACTION_TYPE,
                reasons=reasons,
                validated_path=candidate.path,
            )

        # 2. Flow Existence Check
        flow = topology.get_flow(candidate.flow_id)
        if not flow:
            reasons.append(
                f"Flow ID '{candidate.flow_id}' does not exist in scenario '{topology.scenario_id}'."
            )
            return PathValidationResult(
                is_valid=False,
                status=ValidationStatus.FLOW_MISMATCH,
                reasons=reasons,
                validated_path=candidate.path,
            )

        # 3. Path Length Check
        if not candidate.path or len(candidate.path) < 2:
            reasons.append("Candidate path must contain at least two connected nodes (source and destination).")
            return PathValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID_EDGE,
                reasons=reasons,
                validated_path=candidate.path,
            )

        # 4. Source & Destination Alignment Check
        path_src = candidate.path[0]
        path_dst = candidate.path[-1]

        if path_src != candidate.source_node or path_dst != candidate.destination_node:
            reasons.append(
                f"Candidate path endpoints [{path_src} -> {path_dst}] do not match candidate action endpoints [{candidate.source_node} -> {candidate.destination_node}]."
            )
            return PathValidationResult(
                is_valid=False,
                status=ValidationStatus.FLOW_MISMATCH,
                reasons=reasons,
                validated_path=candidate.path,
            )

        if path_src != flow.source or path_dst != flow.destination:
            reasons.append(
                f"Candidate endpoints [{path_src} -> {path_dst}] do not match flow '{candidate.flow_id}' endpoints [{flow.source} -> {flow.destination}]."
            )
            return PathValidationResult(
                is_valid=False,
                status=ValidationStatus.FLOW_MISMATCH,
                reasons=reasons,
                validated_path=candidate.path,
            )

        # 5. Node Existence Check
        for node_id in candidate.path:
            node = topology.get_node(node_id)
            if not node:
                reasons.append(
                    f"Node '{node_id}' does not exist in scenario topology '{topology.scenario_id}'."
                )
                return PathValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID_NODE,
                    reasons=reasons,
                    validated_path=candidate.path,
                )
            if node.status != "UP":
                reasons.append(f"Node '{node_id}' is down or offline (status: {node.status}).")
                return PathValidationResult(
                    is_valid=False,
                    status=ValidationStatus.LINK_DOWN,
                    reasons=reasons,
                    validated_path=candidate.path,
                )

        # 6. Cycle / Repeated Node Check
        seen_nodes = set()
        for node_id in candidate.path:
            if node_id in seen_nodes:
                reasons.append(f"Cycle detected in candidate path: node '{node_id}' appears multiple times.")
                return PathValidationResult(
                    is_valid=False,
                    status=ValidationStatus.CYCLE_DETECTED,
                    reasons=reasons,
                    validated_path=candidate.path,
                )
            seen_nodes.add(node_id)

        # 7. Directed Edge Existence and Operational Status Check
        edges_traversed: List[str] = []
        for i in range(len(candidate.path) - 1):
            u = candidate.path[i]
            v = candidate.path[i + 1]
            edge = topology.get_edge(u, v)

            if not edge:
                reasons.append(f"Missing directed edge between consecutive nodes '{u}' and '{v}'.")
                return PathValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INVALID_EDGE,
                    reasons=reasons,
                    validated_path=candidate.path,
                )

            if edge.status != "UP":
                reasons.append(f"Link '{edge.edge_id}' ({u} -> {v}) is offline (status: {edge.status}).")
                return PathValidationResult(
                    is_valid=False,
                    status=ValidationStatus.LINK_DOWN,
                    reasons=reasons,
                    validated_path=candidate.path,
                )

            if edge.capacity_mbps <= 0:
                reasons.append(f"Link '{edge.edge_id}' ({u} -> {v}) has zero or invalid capacity ({edge.capacity_mbps} Mbps).")
                return PathValidationResult(
                    is_valid=False,
                    status=ValidationStatus.INCOMPLETE_CONSTRAINTS,
                    reasons=reasons,
                    validated_path=candidate.path,
                )

            edges_traversed.append(edge.edge_id)

        # Candidate path is fully valid
        return PathValidationResult(
            is_valid=True,
            status=ValidationStatus.VALID,
            reasons=["All nodes, directed edges, and flow constraints successfully verified."],
            validated_path=candidate.path,
            hop_count=len(candidate.path) - 1,
            edges_traversed=edges_traversed,
        )

