from .schemas import Scenario

# Synthetic fixtures for UI development only; not operational telemetry.
DEMO_SCENARIOS = {
    "wan_congestion": Scenario(
        scenario_id="WAN-042", name="WAN congestion / reroute",
        description="Illustrative branch-to-core traffic burst with a proposed reroute.",
        nominal_latency_ms=18, capacity_mbps=1000, offered_load_mbps=760,
        slo_latency_ms=45, latency_multiplier_min=.85, latency_multiplier_max=1.35),
    "fiber_drift": Scenario(
        scenario_id="FIBER-017", name="Fiber latency calibration drift",
        description="Illustrative route where the twin may understate propagation delay.",
        nominal_latency_ms=24, capacity_mbps=900, offered_load_mbps=690,
        slo_latency_ms=40, latency_multiplier_min=.85, latency_multiplier_max=1.60),
    "traffic_burst": Scenario(
        scenario_id="BURST-006", name="Hidden traffic burst",
        description="Illustrative load spike used to exercise conservative gate behavior.",
        nominal_latency_ms=15, capacity_mbps=800, offered_load_mbps=730,
        slo_latency_ms=35, latency_multiplier_min=.90, latency_multiplier_max=1.50),
    "cisco_bgp_clear": Scenario(
        scenario_id="BGP-CLEAR-001", name="Cisco BGP clear replay",
        description="Empirical replay of BGP route withdrawal and convergence delay.",
        nominal_latency_ms=18, capacity_mbps=1000, offered_load_mbps=480,
        slo_latency_ms=40, latency_multiplier_min=.85, latency_multiplier_max=1.35),
}
