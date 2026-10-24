from .schemas import Scenario


def predict_latency_ms(scenario: Scenario, latency_multiplier: float = 1.0,
                       load_multiplier: float = 1.0) -> float:
    # Illustrative convex queueing approximation, not packet-level simulation.
    utilization = min((scenario.offered_load_mbps * load_multiplier) /
                     scenario.capacity_mbps, .999)
    queue_factor = .15 * utilization / max(1.0 - utilization, .05)
    return float(scenario.nominal_latency_ms * latency_multiplier * (1 + queue_factor))


def peak_utilization(scenario: Scenario, load_multiplier: float = 1.0) -> float:
    return float(min(scenario.offered_load_mbps * load_multiplier /
                     scenario.capacity_mbps, 1.5))
