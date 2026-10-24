"""fidelitygate/adaptive/measurement_registry.py
Allowlisted registry of diagnostic measurement models and seed-reproducible observation generators.
Ensures observation models, physical units, and error bounds are mathematically rigorous and transparent.
"""

import random
import uuid
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    DiagnosticObservation,
    MeasurementErrorType,
    MeasurementModel,
    ObservationMode,
)


ALLOWLISTED_MEASUREMENT_MODELS: Dict[str, MeasurementModel] = {
    "active_rtt_probe": MeasurementModel(
        tool_id="active_rtt_probe",
        tool_name="High-Precision Active RTT Probe",
        target_entity="candidate_path_edges",
        target_parameter="fiber_latency_calibration_drift",
        unit="ms",
        error_type=MeasurementErrorType.BOUNDED_ABSOLUTE,
        error_bound=1.5,
        cost_usd=0.0045,
        latency_ms=18.0,
        sampling_behavior="icmp_udp_microburst_series",
        repeatability_config="seeded_prng_uniform_noise",
        description="Dispatches timestamped micro-probes across links to measure propagation delay under bounded jitter.",
        limitations=[
            "Affected by transient control-plane queueing if router CPU is high.",
            "Measures link round-trip time, not individual switch fabric internal delay.",
        ],
    ),
    "snmp_interface_poll": MeasurementModel(
        tool_id="snmp_interface_poll",
        tool_name="SNMP v3 Interface Queue Telemetry",
        target_entity="egress_interface",
        target_parameter="traffic_load_burst",
        unit="Mbps",
        error_type=MeasurementErrorType.BOUNDED_ABSOLUTE,
        error_bound=15.0,
        cost_usd=0.0020,
        latency_ms=8.0,
        sampling_behavior="hardware_octet_counter_delta",
        repeatability_config="seeded_prng_uniform_noise",
        description="Polls hardware octet counters and queue buffer occupancy on switch egress ports.",
        limitations=[
            "Octet counter sampling interval is discrete (1-5 second resolution).",
            "Hardware buffer counters may under-report microbursts shorter than 100 microseconds.",
        ],
    ),
    "passive_telemetry_flow": MeasurementModel(
        tool_id="passive_telemetry_flow",
        tool_name="sFlow / IPFIX Telemetry Sampler",
        target_entity="border_router_fabric",
        target_parameter="cross_traffic_factor",
        unit="factor",
        error_type=MeasurementErrorType.BOUNDED_ABSOLUTE,
        error_bound=0.04,
        cost_usd=0.0015,
        latency_ms=6.0,
        sampling_behavior="1_in_1000_packet_sample",
        repeatability_config="seeded_prng_uniform_noise",
        description="Statistically samples transit packet headers from line cards to estimate cross-flow demand.",
        limitations=[
            "Statistical sampling has higher variance on low-volume flows.",
            "Does not measure physical fiber degradation or optical dispersion.",
        ],
    ),
}


class DiagnosticMeasurementRegistry:
    """Registry and executor for authorized diagnostic measurement tools."""

    def __init__(self, models: Optional[Dict[str, MeasurementModel]] = None):
        self.models = models or dict(ALLOWLISTED_MEASUREMENT_MODELS)

    def get_model(self, tool_id: str) -> Optional[MeasurementModel]:
        return self.models.get(tool_id)

    def list_models(self) -> List[MeasurementModel]:
        return list(self.models.values())

    def execute_diagnostic(
        self,
        tool_id: str,
        target_entity: str,
        simulated_true_parameter: float,
        seed: int = 42,
        cycle_number: int = 1,
        is_public_replay: bool = False,
        public_replay_observation: Optional[float] = None,
        base_scale: Optional[float] = None,
        target_unit: Optional[str] = None,
    ) -> DiagnosticObservation:
        """
        Executes a diagnostic measurement with declared bounded error.
        If base_scale is provided (e.g. nominal latency or load), the physical observation
        y = h(theta) + epsilon is inverted to parameter space theta_hat = y / base_scale,
        with properly propagated parameter error bound delta_param = delta_raw / base_scale.
        """
        model = self.models.get(tool_id)
        if not model:
            raise ValueError(f"Diagnostic tool '{tool_id}' not found in allowlisted measurement registry.")

        obs_id = f"obs-{uuid.uuid4().hex[:8]}"

        # Handle Public Replay Mode
        if is_public_replay:
            if public_replay_observation is not None:
                measured_val = round(public_replay_observation, 3)
                delta = model.error_bound
                ci = (round(measured_val - delta, 3), round(measured_val + delta, 3))
                return DiagnosticObservation(
                    observation_id=obs_id,
                    tool_id=tool_id,
                    tool_name=model.tool_name,
                    target_entity=target_entity,
                    target_parameter=model.target_parameter,
                    measured_value=measured_val,
                    unit=model.unit,
                    declared_error_bound=delta,
                    confidence_interval=ci,
                    raw_measured_value=measured_val,
                    raw_unit=model.unit,
                    raw_error_bound=delta,
                    mapping_description="Direct public replay observation without latent model inversion.",
                    observation_mode=ObservationMode.PUBLIC_TELEMETRY_OBSERVED,
                    source_provenance={"dataset": "cisco_ie_telemetry", "field": "sampled_counter"},
                    is_valid=True,
                    limitations=list(model.limitations),
                )
            else:
                # Public dataset did not contain active diagnostic probe
                return DiagnosticObservation(
                    observation_id=obs_id,
                    tool_id=tool_id,
                    tool_name=model.tool_name,
                    target_entity=target_entity,
                    target_parameter=model.target_parameter,
                    measured_value=0.0,
                    unit=model.unit,
                    declared_error_bound=model.error_bound,
                    confidence_interval=(0.0, 0.0),
                    raw_measured_value=0.0,
                    raw_unit=model.unit,
                    raw_error_bound=model.error_bound,
                    mapping_description="Unavailable in public telemetry.",
                    observation_mode=ObservationMode.UNAVAILABLE,
                    source_provenance={"status": "not_present_in_public_telemetry"},
                    is_valid=False,
                    limitations=["Public telemetry dataset does not contain an active probe for this metric/device."],
                )

        # Synthetic Scenario Mode: Deterministic, Seeded Error
        rng = random.Random(seed + cycle_number * 1000 + hash(tool_id) % 1000)
        delta = model.error_bound

        if base_scale is not None and base_scale > 0:
            # Physical Observation Model: y_raw = base_scale * theta + epsilon
            # Example: base latency 20.0 ms * drift factor 1.05 = 21.0 ms true delay
            true_physical_val = base_scale * simulated_true_parameter
            epsilon = rng.uniform(-delta, delta)
            raw_measured = round(true_physical_val + epsilon, 3)
            raw_ci = (round(raw_measured - delta, 3), round(raw_measured + delta, 3))

            # Invert observation model to parameter space: theta = y / base_scale
            # Error propagation: delta_param = delta_raw / base_scale
            param_measured = round(raw_measured / base_scale, 4)
            param_delta = round(delta / base_scale, 4)
            param_ci = (round(param_measured - param_delta, 4), round(param_measured + param_delta, 4))
            p_unit = target_unit or "factor"
            mapping_desc = (
                f"Inverted via declared observation model h(theta) = {base_scale:.1f} {model.unit} * theta. "
                f"Raw observation {raw_measured:.2f} {model.unit} (+-{delta:.1f} {model.unit}) maps to "
                f"parameter estimate {param_measured:.4f} {p_unit} (+-{param_delta:.4f} {p_unit})."
            )

            return DiagnosticObservation(
                observation_id=obs_id,
                tool_id=tool_id,
                tool_name=model.tool_name,
                target_entity=target_entity,
                target_parameter=model.target_parameter,
                measured_value=param_measured,
                unit=p_unit,
                declared_error_bound=param_delta,
                confidence_interval=param_ci,
                raw_measured_value=raw_measured,
                raw_unit=model.unit,
                raw_error_bound=delta,
                mapping_description=mapping_desc,
                observation_mode=ObservationMode.SYNTHETIC_DIAGNOSTIC_MEASUREMENT,
                source_provenance={
                    "generator": "deterministic_seeded_error_model",
                    "seed": seed,
                    "cycle": cycle_number,
                    "base_scale": base_scale,
                    "raw_unit": model.unit,
                    "error_type": model.error_type.value,
                },
                is_valid=True,
                limitations=list(model.limitations),
            )
        else:
            # Direct parameter observation (e.g. dimensionless factor or direct metric)
            epsilon = rng.uniform(-delta, delta)
            measured_val = round(simulated_true_parameter + epsilon, 3)
            ci = (round(measured_val - delta, 3), round(measured_val + delta, 3))

            return DiagnosticObservation(
                observation_id=obs_id,
                tool_id=tool_id,
                tool_name=model.tool_name,
                target_entity=target_entity,
                target_parameter=model.target_parameter,
                measured_value=measured_val,
                unit=model.unit,
                declared_error_bound=delta,
                confidence_interval=ci,
                raw_measured_value=measured_val,
                raw_unit=model.unit,
                raw_error_bound=delta,
                mapping_description="Direct parameter observation without base scale conversion.",
                observation_mode=ObservationMode.SYNTHETIC_DIAGNOSTIC_MEASUREMENT,
                source_provenance={
                    "generator": "deterministic_seeded_error_model",
                    "seed": seed,
                    "cycle": cycle_number,
                    "error_type": model.error_type.value,
                },
                is_valid=True,
                limitations=list(model.limitations),
            )

