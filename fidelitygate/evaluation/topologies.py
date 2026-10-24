"""fidelitygate/evaluation/topologies.py
Canonical network topology definitions and scenario factories for Layer 4.
"""

from typing import Dict, Optional
from .models import NetworkTopology, TopologyEdge, TopologyNode, TrafficFlow


def create_wan_congestion_topology() -> NetworkTopology:
    """Canonical leaf-spine topology for WAN congestion / reroute scenario (WAN-042)."""
    nodes = {
        "leaf1": TopologyNode(node_id="leaf1", node_type="leaf", status="UP"),
        "spine1": TopologyNode(node_id="spine1", node_type="spine", status="UP"),
        "spine2": TopologyNode(node_id="spine2", node_type="spine", status="UP"),
        "leaf6": TopologyNode(node_id="leaf6", node_type="leaf", status="UP"),
    }
    edges = {
        "e_leaf1_spine1": TopologyEdge(
            edge_id="e_leaf1_spine1",
            source="leaf1",
            target="spine1",
            capacity_mbps=1000.0,
            base_latency_ms=6.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine1_leaf6": TopologyEdge(
            edge_id="e_spine1_leaf6",
            source="spine1",
            target="leaf6",
            capacity_mbps=1000.0,
            base_latency_ms=12.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_leaf1_spine2": TopologyEdge(
            edge_id="e_leaf1_spine2",
            source="leaf1",
            target="spine2",
            capacity_mbps=1000.0,
            base_latency_ms=8.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine2_leaf6": TopologyEdge(
            edge_id="e_spine2_leaf6",
            source="spine2",
            target="leaf6",
            capacity_mbps=1000.0,
            base_latency_ms=12.0,
            background_load_mbps=0.0,
            status="UP",
        ),
    }
    flows = {
        "flow_primary": TrafficFlow(
            flow_id="flow_primary",
            name="Critical Enterprise WAN Traffic",
            source="leaf1",
            destination="leaf6",
            demand_mbps=500.0,
            slo_latency_ms=45.0,
            nominal_path=["leaf1", "spine1", "leaf6"],
        ),
        "flow_shared": TrafficFlow(
            flow_id="flow_shared",
            name="Corporate Bulk WAN Traffic",
            source="leaf1",
            destination="leaf6",
            demand_mbps=260.0,
            slo_latency_ms=50.0,
            nominal_path=["leaf1", "spine1", "leaf6"],
        ),
    }
    return NetworkTopology(
        scenario_id="wan_congestion",
        name="WAN congestion / reroute",
        nodes=nodes,
        edges=edges,
        flows=flows,
    )


def create_fiber_drift_topology() -> NetworkTopology:
    """Canonical topology for Fiber latency calibration drift scenario (FIBER-017)."""
    nodes = {
        "leaf1": TopologyNode(node_id="leaf1", node_type="leaf", status="UP"),
        "spine1": TopologyNode(node_id="spine1", node_type="spine", status="UP"),
        "spine2": TopologyNode(node_id="spine2", node_type="spine", status="UP"),
        "leaf6": TopologyNode(node_id="leaf6", node_type="leaf", status="UP"),
    }
    edges = {
        "e_leaf1_spine1": TopologyEdge(
            edge_id="e_leaf1_spine1",
            source="leaf1",
            target="spine1",
            capacity_mbps=900.0,
            base_latency_ms=10.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine1_leaf6": TopologyEdge(
            edge_id="e_spine1_leaf6",
            source="spine1",
            target="leaf6",
            capacity_mbps=900.0,
            base_latency_ms=14.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_leaf1_spine2": TopologyEdge(
            edge_id="e_leaf1_spine2",
            source="leaf1",
            target="spine2",
            capacity_mbps=900.0,
            base_latency_ms=9.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine2_leaf6": TopologyEdge(
            edge_id="e_spine2_leaf6",
            source="spine2",
            target="leaf6",
            capacity_mbps=900.0,
            base_latency_ms=13.0,
            background_load_mbps=0.0,
            status="UP",
        ),
    }
    flows = {
        "flow_primary": TrafficFlow(
            flow_id="flow_primary",
            name="Drift-Sensitive Transit Traffic",
            source="leaf1",
            destination="leaf6",
            demand_mbps=690.0,
            slo_latency_ms=40.0,
            nominal_path=["leaf1", "spine1", "leaf6"],
        ),
    }
    return NetworkTopology(
        scenario_id="fiber_drift",
        name="Fiber latency calibration drift",
        nodes=nodes,
        edges=edges,
        flows=flows,
    )


def create_traffic_burst_topology() -> NetworkTopology:
    """Canonical topology for Hidden traffic burst scenario (BURST-006)."""
    nodes = {
        "leaf1": TopologyNode(node_id="leaf1", node_type="leaf", status="UP"),
        "spine1": TopologyNode(node_id="spine1", node_type="spine", status="UP"),
        "spine2": TopologyNode(node_id="spine2", node_type="spine", status="UP"),
        "leaf6": TopologyNode(node_id="leaf6", node_type="leaf", status="UP"),
    }
    edges = {
        "e_leaf1_spine1": TopologyEdge(
            edge_id="e_leaf1_spine1",
            source="leaf1",
            target="spine1",
            capacity_mbps=800.0,
            base_latency_ms=5.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine1_leaf6": TopologyEdge(
            edge_id="e_spine1_leaf6",
            source="spine1",
            target="leaf6",
            capacity_mbps=800.0,
            base_latency_ms=10.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_leaf1_spine2": TopologyEdge(
            edge_id="e_leaf1_spine2",
            source="leaf1",
            target="spine2",
            capacity_mbps=800.0,
            base_latency_ms=7.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine2_leaf6": TopologyEdge(
            edge_id="e_spine2_leaf6",
            source="spine2",
            target="leaf6",
            capacity_mbps=800.0,
            base_latency_ms=9.0,
            background_load_mbps=0.0,
            status="UP",
        ),
    }
    flows = {
        "flow_primary": TrafficFlow(
            flow_id="flow_primary",
            name="Burst-Prone Ingress Flow",
            source="leaf1",
            destination="leaf6",
            demand_mbps=730.0,
            slo_latency_ms=35.0,
            nominal_path=["leaf1", "spine1", "leaf6"],
        ),
    }
    return NetworkTopology(
        scenario_id="traffic_burst",
        name="Hidden traffic burst",
        nodes=nodes,
        edges=edges,
        flows=flows,
    )


def create_cisco_bgp_clear_topology() -> NetworkTopology:
    """Canonical topology for Cisco BGP clear replay scenario (BGP-CLEAR-001)."""
    nodes = {
        "leaf1": TopologyNode(node_id="leaf1", node_type="leaf", status="UP"),
        "spine1": TopologyNode(node_id="spine1", node_type="spine", status="UP"),
        "spine2": TopologyNode(node_id="spine2", node_type="spine", status="UP"),
        "leaf6": TopologyNode(node_id="leaf6", node_type="leaf", status="UP"),
    }
    edges = {
        "e_leaf1_spine1": TopologyEdge(
            edge_id="e_leaf1_spine1",
            source="leaf1",
            target="spine1",
            capacity_mbps=1000.0,
            base_latency_ms=6.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine1_leaf6": TopologyEdge(
            edge_id="e_spine1_leaf6",
            source="spine1",
            target="leaf6",
            capacity_mbps=1000.0,
            base_latency_ms=12.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_leaf1_spine2": TopologyEdge(
            edge_id="e_leaf1_spine2",
            source="leaf1",
            target="spine2",
            capacity_mbps=1000.0,
            base_latency_ms=8.0,
            background_load_mbps=0.0,
            status="UP",
        ),
        "e_spine2_leaf6": TopologyEdge(
            edge_id="e_spine2_leaf6",
            source="spine2",
            target="leaf6",
            capacity_mbps=1000.0,
            base_latency_ms=12.0,
            background_load_mbps=0.0,
            status="UP",
        ),
    }
    flows = {
        "flow_primary": TrafficFlow(
            flow_id="flow_primary",
            name="Cisco Telemetry Replay Transit Flow",
            source="leaf1",
            destination="leaf6",
            demand_mbps=480.0,
            slo_latency_ms=40.0,
            nominal_path=["leaf1", "spine1", "leaf6"],
        ),
    }
    return NetworkTopology(
        scenario_id="cisco_bgp_clear",
        name="Cisco BGP clear replay",
        nodes=nodes,
        edges=edges,
        flows=flows,
    )


SCENARIO_TOPOLOGIES: Dict[str, NetworkTopology] = {
    "wan_congestion": create_wan_congestion_topology(),
    "WAN-042": create_wan_congestion_topology(),
    "fiber_drift": create_fiber_drift_topology(),
    "FIBER-017": create_fiber_drift_topology(),
    "traffic_burst": create_traffic_burst_topology(),
    "BURST-006": create_traffic_burst_topology(),
    "cisco_bgp_clear": create_cisco_bgp_clear_topology(),
    "BGP-CLEAR-001": create_cisco_bgp_clear_topology(),
}


def get_topology_for_scenario(scenario_key: str) -> Optional[NetworkTopology]:
    """Retrieve canonical topology for a scenario key or ID."""
    return SCENARIO_TOPOLOGIES.get(scenario_key)

