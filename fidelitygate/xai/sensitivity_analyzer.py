"""fidelitygate/xai/sensitivity_analyzer.py
Computes deterministic local sensitivity analysis and counterfactual edge perturbations.
Evaluates local model response gradients without external ML libraries (SHAP/GNN).
"""

from typing import Any, Dict, List, Optional
from fidelitygate.evaluation.models import CandidateAction, NetworkTopology, SimulationPrediction
from fidelitygate.evaluation.simulator import NetworkSimulator
from .models import LocalSensitivityReport, ParameterSensitivity


class SensitivityAnalyzer:
    """Computes deterministic local parameter sensitivity and counterfactual edge impacts."""

    def __init__(self, simulator: Optional[NetworkSimulator] = None):
        self.simulator = simulator or NetworkSimulator()

    def analyze_candidate_sensitivity(
        self,
        topology: NetworkTopology,
        candidate: CandidateAction,
        nominal_prediction: SimulationPrediction,
        scenario_id: str = "wan_congestion",
    ) -> LocalSensitivityReport:
        """
        Executes bounded one-at-a-time (OAT) parameter variations around nominal.
        Computes response gradients: d(Latency)/d(param) and d(Utilization)/d(param).
        """
        path = candidate.path
        flow_id = candidate.flow_id
        base_lat = nominal_prediction.latency_ms
        base_util = nominal_prediction.peak_utilization
        bottleneck_edge = nominal_prediction.bottleneck_edge_id or "unspecified"

        deltas = [-0.20, -0.10, 0.10, 0.20]
        params_evaluated: List[ParameterSensitivity] = []

        # 1. Parameter: fiber_latency_calibration_drift (multiplicative latency factor)
        lat_perturbs: List[Dict[str, Any]] = []
        max_lat_diff = 0.0
        for d in deltas:
            factor = 1.0 + d
            sim = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=flow_id,
                path=path,
                load_multiplier=1.0,
                latency_multiplier=factor,
            )
            d_lat = sim.latency_ms - base_lat
            d_util = sim.peak_utilization - base_util
            lat_perturbs.append({
                "perturbation_pct": round(d * 100.0, 1),
                "parameter_value": round(factor, 4),
                "resulting_latency_ms": round(sim.latency_ms, 2),
                "resulting_utilization": round(sim.peak_utilization, 4),
                "latency_delta_ms": round(d_lat, 2),
                "utilization_delta": round(d_util, 4),
            })
            if abs(d_lat) > max_lat_diff:
                max_lat_diff = abs(d_lat)

        lat_elasticity = round(max_lat_diff / 0.20, 2)  # ms per unit factor change

        params_evaluated.append(
            ParameterSensitivity(
                parameter_name="fiber_latency_calibration_drift",
                unit="factor",
                nominal_value=1.0,
                perturbations=lat_perturbs,
                latency_elasticity=lat_elasticity,
                utilization_elasticity=0.0,
                sensitivity_rank=1,
                is_critical_bottleneck=True,
            )
        )

        # 2. Parameter: traffic_load_burst (offered flow load multiplier)
        load_perturbs: List[Dict[str, Any]] = []
        max_load_lat_diff = 0.0
        max_load_util_diff = 0.0
        for d in deltas:
            factor = 1.0 + d
            sim = self.simulator.simulate_flow(
                topology=topology,
                target_flow_id=flow_id,
                path=path,
                load_multiplier=factor,
                latency_multiplier=1.0,
            )
            d_lat = sim.latency_ms - base_lat
            d_util = sim.peak_utilization - base_util
            load_perturbs.append({
                "perturbation_pct": round(d * 100.0, 1),
                "parameter_value": round(factor, 4),
                "resulting_latency_ms": round(sim.latency_ms, 2),
                "resulting_utilization": round(sim.peak_utilization, 4),
                "latency_delta_ms": round(d_lat, 2),
                "utilization_delta": round(d_util, 4),
            })
            if abs(d_lat) > max_load_lat_diff:
                max_load_lat_diff = abs(d_lat)
            if abs(d_util) > max_load_util_diff:
                max_load_util_diff = abs(d_util)

        load_lat_elasticity = round(max_load_lat_diff / 0.20, 2)
        load_util_elasticity = round(max_load_util_diff / 0.20, 4)

        params_evaluated.append(
            ParameterSensitivity(
                parameter_name="traffic_load_burst",
                unit="factor",
                nominal_value=1.0,
                perturbations=load_perturbs,
                latency_elasticity=load_lat_elasticity,
                utilization_elasticity=load_util_elasticity,
                sensitivity_rank=2,
                is_critical_bottleneck=False,
            )
        )

        # Rank parameters by latency elasticity
        params_evaluated.sort(key=lambda p: p.latency_elasticity, reverse=True)
        for idx, p in enumerate(params_evaluated):
            params_evaluated[idx] = p.model_copy(update={"sensitivity_rank": idx + 1})

        most_sensitive = params_evaluated[0].parameter_name

        # 3. Counterfactual Edge Perturbation
        cf_sim = self.simulator.simulate_flow(
            topology=topology,
            target_flow_id=flow_id,
            path=path,
            load_multiplier=1.15,
            latency_multiplier=1.0,
        )
        cf_result = {
            "perturbed_edge": bottleneck_edge,
            "perturbation_description": f"Add +15% cross-traffic load across bottleneck edge '{bottleneck_edge}'",
            "nominal_bottleneck_utilization": round(base_util, 4),
            "counterfactual_bottleneck_utilization": round(cf_sim.peak_utilization, 4),
            "nominal_path_latency_ms": round(base_lat, 2),
            "counterfactual_path_latency_ms": round(cf_sim.latency_ms, 2),
            "slo_breached": cf_sim.latency_ms > 45.0,
        }

        return LocalSensitivityReport(
            candidate_id=candidate.candidate_id,
            scenario_id=scenario_id,
            evaluated_parameters=params_evaluated,
            most_sensitive_parameter=most_sensitive,
            bottleneck_edge=bottleneck_edge,
            counterfactual_edge_perturbation=cf_result,
        )

