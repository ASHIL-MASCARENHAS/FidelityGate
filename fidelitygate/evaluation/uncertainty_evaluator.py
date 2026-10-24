"""fidelitygate/evaluation/uncertainty_evaluator.py
Bounded multidimensional parameter sweep and counterexample search for candidate mitigations.
"""

from typing import List, Optional, Tuple
import numpy as np

from ..schemas import SweepReport
from .models import (
    CandidateAction,
    Counterexample,
    NetworkTopology,
    SimulationPrediction,
)
from .simulator import NetworkSimulator


class CandidateUncertaintyEvaluator:
    """Evaluates candidate actions across declared multidimensional uncertainty envelopes."""

    MAX_EVALUATION_BUDGET = 50

    def __init__(self, simulator: Optional[NetworkSimulator] = None):
        self.simulator = simulator or NetworkSimulator()

    def evaluate_uncertainty(
        self,
        topology: NetworkTopology,
        candidate: CandidateAction,
        evaluations: int = 25,
        latency_multiplier_range: Tuple[float, float] = (0.85, 1.35),
        load_multiplier_range: Tuple[float, float] = (0.95, 1.15),
    ) -> Tuple[SweepReport, Optional[Counterexample]]:
        """
        Executes bounded deterministic perturbation sweep and identifies critical counterexamples.
        """
        # 1. Enforce Budget Invariant
        budget = min(max(evaluations, 5), self.MAX_EVALUATION_BUDGET)

        flow = topology.get_flow(candidate.flow_id)
        if not flow:
            raise ValueError(f"Flow '{candidate.flow_id}' not found in scenario.")

        # 2. Generate Perturbation Sequences
        lat_factors = np.linspace(latency_multiplier_range[0], latency_multiplier_range[1], budget)
        load_factors = np.linspace(load_multiplier_range[0], load_multiplier_range[1], budget)

        # 3. Nominal Prediction
        nominal_pred = self.simulator.simulate_flow(
            topology=topology,
            target_flow_id=candidate.flow_id,
            path=candidate.path,
            load_multiplier=1.0,
            latency_multiplier=1.0,
        )

        # 4. Sweep Evaluations
        sim_latencies: List[float] = []
        sim_utils: List[float] = []
        violations = 0

        for a, b in zip(lat_factors, load_factors):
            pred = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=candidate.flow_id,
                path=candidate.path,
                load_multiplier=float(b),
                latency_multiplier=float(a),
            )
            sim_latencies.append(pred.latency_ms)
            sim_utils.append(pred.peak_utilization)

            if pred.slo_violated or pred.capacity_violated:
                violations += 1

        worst_latency = max(sim_latencies) if sim_latencies else nominal_pred.latency_ms
        worst_util = max(sim_utils) if sim_utils else nominal_pred.peak_utilization
        stability_score = 1.0 - (violations / budget)

        sensitivity = {
            "propagation_drift_ms": round(float(max(sim_latencies) - min(sim_latencies)), 2),
            "traffic_load_burst_util": round(float(max(sim_utils) - min(sim_utils)), 4),
        }

        sweep_report = SweepReport(
            evaluations=budget,
            nominal_latency_ms=nominal_pred.latency_ms,
            worst_latency_ms=round(float(worst_latency), 2),
            peak_utilization=round(float(worst_util), 4),
            stability_score=round(float(stability_score), 4),
            violations=violations,
            sensitivity=sensitivity,
        )

        # 5. Counterexample Search
        counterexample = self._find_counterexample(
            topology=topology,
            candidate=candidate,
            nominal_pred=nominal_pred,
            lat_factors=lat_factors,
            load_factors=load_factors,
        )

        return sweep_report, counterexample

    def _find_counterexample(
        self,
        topology: NetworkTopology,
        candidate: CandidateAction,
        nominal_pred: SimulationPrediction,
        lat_factors: np.ndarray,
        load_factors: np.ndarray,
    ) -> Counterexample:
        """Searches for the minimal single or coupled perturbation causing SLO breach."""
        flow = topology.get_flow(candidate.flow_id)
        slo = flow.slo_latency_ms if flow else 45.0

        # Check 1: Latency drift perturbation alone
        for factor in lat_factors:
            pred = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=candidate.flow_id,
                path=candidate.path,
                latency_multiplier=float(factor),
                load_multiplier=1.0,
            )
            if pred.slo_violated:
                drift_pct = round((factor - 1.0) * 100.0, 1)
                return Counterexample(
                    is_fragile=True,
                    violating_latency_ms=pred.latency_ms,
                    critical_parameter="fiber_latency_calibration_drift",
                    perturbation_factor=round(float(factor), 3),
                    slo_latency_ms=slo,
                    margin_breach_ms=round(pred.latency_ms - slo, 2),
                    explanation=(
                        f"A plausible {drift_pct}% propagation latency drift causes candidate path latency "
                        f"({pred.latency_ms} ms) to breach the {slo} ms SLO."
                    ),
                )

        # Check 2: Traffic load burst perturbation alone
        for l_factor in load_factors:
            pred = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=candidate.flow_id,
                path=candidate.path,
                latency_multiplier=1.0,
                load_multiplier=float(l_factor),
            )
            if pred.slo_violated or pred.capacity_violated:
                burst_pct = round((l_factor - 1.0) * 100.0, 1)
                return Counterexample(
                    is_fragile=True,
                    violating_latency_ms=pred.latency_ms,
                    critical_parameter="traffic_load_burst",
                    perturbation_factor=round(float(l_factor), 3),
                    slo_latency_ms=slo,
                    margin_breach_ms=round(pred.latency_ms - slo, 2),
                    explanation=(
                        f"A plausible {burst_pct}% traffic load burst causes buffer queueing delay "
                        f"({pred.latency_ms} ms) to breach the {slo} ms SLO."
                    ),
                )

        # Check 3: Coupled perturbation
        for lat_f, load_f in zip(lat_factors, load_factors):
            pred = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=candidate.flow_id,
                path=candidate.path,
                latency_multiplier=float(lat_f),
                load_multiplier=float(load_f),
            )
            if pred.slo_violated or pred.capacity_violated:
                return Counterexample(
                    is_fragile=True,
                    violating_latency_ms=pred.latency_ms,
                    critical_parameter="coupled_latency_and_load_drift",
                    perturbation_factor=round(float(lat_f), 3),
                    slo_latency_ms=slo,
                    margin_breach_ms=round(pred.latency_ms - slo, 2),
                    explanation=(
                        f"Coupled uncertainty drift ({round((lat_f - 1.0) * 100, 1)}% latency, "
                        f"{round((load_f - 1.0) * 100, 1)}% load) breaches the {slo} ms SLO at {pred.latency_ms} ms."
                    ),
                )

        # No perturbation breached SLO: Robust candidate
        return Counterexample(
            is_fragile=False,
            violating_latency_ms=nominal_pred.latency_ms,
            critical_parameter="none",
            perturbation_factor=1.0,
            slo_latency_ms=slo,
            margin_breach_ms=0.0,
            explanation=f"All evaluated parameter variations within declared envelope satisfy the {slo} ms SLO.",
        )

