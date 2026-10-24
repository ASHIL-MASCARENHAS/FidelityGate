from dataclasses import dataclass
from typing import Dict, Any, Tuple
import math
from .schemas import Scenario
from .twin import predict_latency_ms

@dataclass(frozen=True)
class DiagnosticObservation:
    tool_id: str
    tool_name: str
    target_parameter: str
    measured_value: float
    unit: str
    declared_error_bound: float
    confidence_interval: Tuple[float, float]
    cost_usd: float
    execution_time_ms: float
    observation_summary: str

DIAGNOSTIC_TOOLS = {
    "active_rtt_probe": {
        "name": "High-Precision Active RTT Probe",
        "target_parameter": "fiber_latency_calibration_drift",
        "unit": "ms",
        "declared_error_bound": 1.5,
        "cost_usd": 0.0045,
        "execution_time_ms": 18.0,
        "description": "Dispatches ICMP/UDP micro-probes across the candidate link to measure actual physical transit delay."
    },
    "snmp_interface_poll": {
        "name": "SNMP v3 Interface Queue Telemetry",
        "target_parameter": "traffic_load_burst",
        "unit": "Mbps",
        "declared_error_bound": 15.0,
        "cost_usd": 0.0020,
        "execution_time_ms": 8.0,
        "description": "Polls hardware octet counters and queue depth on the egress switch fabric."
    },
    "passive_telemetry_flow": {
        "name": "sFlow / IPFIX Telemetry Sampler",
        "target_parameter": "coupled_latency_and_load_drift",
        "unit": "composite_index",
        "declared_error_bound": 0.05,
        "cost_usd": 0.0015,
        "execution_time_ms": 6.0,
        "description": "Queries statistical flow samples from the border router packet buffer."
    }
}

def select_targeted_diagnostic(critical_parameter: str) -> str:
    """
    Agentic tool selection: Chooses the specific bounded diagnostic tool
    that measures the uncertain parameter identified by the counterexample.
    """
    if "traffic" in critical_parameter or "load" in critical_parameter:
        return "snmp_interface_poll"
    elif "fiber" in critical_parameter or "latency" in critical_parameter:
        return "active_rtt_probe"
    else:
        return "active_rtt_probe"

def execute_diagnostic(
    tool_id: str,
    scenario: Scenario,
    simulated_ground_truth_factor: float = 1.06
) -> DiagnosticObservation:
    """
    Simulates executing the real diagnostic tool against the network fixture
    with declared measurement error.
    """
    tool_spec = DIAGNOSTIC_TOOLS.get(tool_id, DIAGNOSTIC_TOOLS["active_rtt_probe"])
    
    if tool_id == "active_rtt_probe":
        # Measure link RTT with ±1.5ms declared measurement error
        true_latency = scenario.nominal_latency_ms * simulated_ground_truth_factor
        error = tool_spec["declared_error_bound"]
        measured = round(true_latency, 2)
        ci = (round(measured - error, 2), round(measured + error, 2))
        summary = f"Measured active link latency at {measured} ms (declared error ±{error} ms, 95% CI: [{ci[0]}, {ci[1]} ms])."
        
    elif tool_id == "snmp_interface_poll":
        true_load = scenario.offered_load_mbps * simulated_ground_truth_factor
        error = tool_spec["declared_error_bound"]
        measured = round(true_load, 1)
        ci = (round(measured - error, 1), round(measured + error, 1))
        summary = f"Polled interface traffic load at {measured} Mbps (declared error ±{error} Mbps, 95% CI: [{ci[0]}, {ci[1]} Mbps])."
        
    else:
        measured = round(simulated_ground_truth_factor, 3)
        error = tool_spec["declared_error_bound"]
        ci = (round(measured - error, 3), round(measured + error, 3))
        summary = f"Sampled flow telemetry factor at {measured}x (declared error ±{error})."

    return DiagnosticObservation(
        tool_id=tool_id,
        tool_name=tool_spec["name"],
        target_parameter=tool_spec["target_parameter"],
        measured_value=measured,
        unit=tool_spec["unit"],
        declared_error_bound=error,
        confidence_interval=ci,
        cost_usd=tool_spec["cost_usd"],
        execution_time_ms=tool_spec["execution_time_ms"],
        observation_summary=summary
    )
