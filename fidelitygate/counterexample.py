from dataclasses import dataclass
from typing import Optional
import numpy as np
from .schemas import Scenario
from .twin import predict_latency_ms, peak_utilization

@dataclass(frozen=True)
class Counterexample:
    is_fragile: bool
    violating_latency_ms: float
    critical_parameter: str
    perturbation_factor: float
    slo_latency_ms: float
    margin_breach_ms: float
    explanation: str

def find_counterexample(scenario: Scenario, search_steps: int = 30) -> Optional[Counterexample]:
    """
    Searches the plausible uncertainty set for the minimal or most sensitive perturbation
    that causes the candidate intervention to breach the latency SLO.
    """
    nominal_latency = predict_latency_ms(scenario, 1.0, 1.0)
    
    # 1. Test Latency Calibration Drift perturbation
    latency_factors = np.linspace(scenario.latency_multiplier_min, scenario.latency_multiplier_max, search_steps)
    for factor in latency_factors:
        lat = predict_latency_ms(scenario, float(factor), 1.0)
        if lat > scenario.slo_latency_ms:
            return Counterexample(
                is_fragile=True,
                violating_latency_ms=round(float(lat), 2),
                critical_parameter="fiber_latency_calibration_drift",
                perturbation_factor=round(float(factor), 3),
                slo_latency_ms=scenario.slo_latency_ms,
                margin_breach_ms=round(float(lat - scenario.slo_latency_ms), 2),
                explanation=f"A plausible {round((factor - 1.0) * 100, 1)}% propagation latency drift causes end-to-end delay ({round(lat, 1)} ms) to breach the {scenario.slo_latency_ms} ms SLO."
            )
            
    # 2. Test Traffic Load Burst perturbation
    load_factors = np.linspace(1.0, 1.25, search_steps)
    for l_factor in load_factors:
        lat = predict_latency_ms(scenario, 1.0, float(l_factor))
        if lat > scenario.slo_latency_ms:
            return Counterexample(
                is_fragile=True,
                violating_latency_ms=round(float(lat), 2),
                critical_parameter="traffic_load_burst",
                perturbation_factor=round(float(l_factor), 3),
                slo_latency_ms=scenario.slo_latency_ms,
                margin_breach_ms=round(float(lat - scenario.slo_latency_ms), 2),
                explanation=f"A plausible {round((l_factor - 1.0) * 100, 1)}% traffic burst causes buffer queueing delay ({round(lat, 1)} ms) to breach the {scenario.slo_latency_ms} ms SLO."
            )
            
    # 3. Test Coupled Perturbation (both drifting simultaneously)
    for lat_f, load_f in zip(latency_factors, load_factors):
        lat = predict_latency_ms(scenario, float(lat_f), float(load_f))
        if lat > scenario.slo_latency_ms:
            return Counterexample(
                is_fragile=True,
                violating_latency_ms=round(float(lat), 2),
                critical_parameter="coupled_latency_and_load_drift",
                perturbation_factor=round(float(lat_f), 3),
                slo_latency_ms=scenario.slo_latency_ms,
                margin_breach_ms=round(float(lat - scenario.slo_latency_ms), 2),
                explanation=f"Coupled uncertainty drift ({round((lat_f - 1.0) * 100, 1)}% latency, {round((load_f - 1.0) * 100, 1)}% load) breaches the {scenario.slo_latency_ms} ms SLO at {round(lat, 1)} ms."
            )
            
    # Robust: No plausible perturbation breaches the SLO
    return Counterexample(
        is_fragile=False,
        violating_latency_ms=round(nominal_latency, 2),
        critical_parameter="none",
        perturbation_factor=1.0,
        slo_latency_ms=scenario.slo_latency_ms,
        margin_breach_ms=0.0,
        explanation=f"No plausible parameter variations in the uncertainty set breach the {scenario.slo_latency_ms} ms SLO."
    )
