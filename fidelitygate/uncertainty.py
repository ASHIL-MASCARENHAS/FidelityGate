import numpy as np
from .schemas import Scenario, SweepReport
from .twin import predict_latency_ms, peak_utilization


def run_sweep(scenario: Scenario, evaluations: int = 25) -> SweepReport:
    if evaluations < 1:
        raise ValueError("evaluations must be positive")
    latency_factors = np.linspace(scenario.latency_multiplier_min,
                                  scenario.latency_multiplier_max, evaluations)
    load_factors = np.linspace(.95, 1.15, evaluations)
    latencies = [predict_latency_ms(scenario, float(a), float(b))
                 for a, b in zip(latency_factors, load_factors)]
    utils = [peak_utilization(scenario, float(b)) for b in load_factors]
    violations = sum(x > scenario.slo_latency_ms for x in latencies)
    return SweepReport(
        evaluations=evaluations,
        nominal_latency_ms=predict_latency_ms(scenario),
        worst_latency_ms=float(max(latencies)),
        peak_utilization=float(max(utils)),
        stability_score=1 - violations / evaluations,
        violations=violations,
        sensitivity={"Latency calibration": float(max(latencies)-min(latencies)),
                     "Traffic load": float(max(utils)-min(utils))},
    )
