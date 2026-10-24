from fidelitygate.scenarios import DEMO_SCENARIOS
from fidelitygate.counterexample import find_counterexample
from fidelitygate.diagnostics import select_targeted_diagnostic, execute_diagnostic
from fidelitygate.baseline_evaluator import run_four_way_comparison

def test_counterexample_detects_fragility_in_wan():
    scenario = DEMO_SCENARIOS["wan_congestion"]
    cx = find_counterexample(scenario)
    assert cx is not None
    assert cx.is_fragile is True
    assert cx.violating_latency_ms > scenario.slo_latency_ms

def test_diagnostic_tool_selection():
    assert select_targeted_diagnostic("traffic_load_burst") == "snmp_interface_poll"
    assert select_targeted_diagnostic("fiber_latency_calibration_drift") == "active_rtt_probe"

def test_diagnostic_execution_has_error_bounds():
    scenario = DEMO_SCENARIOS["wan_congestion"]
    obs = execute_diagnostic("active_rtt_probe", scenario, 1.05)
    assert obs.measured_value > 0
    assert obs.declared_error_bound == 1.5
    assert obs.confidence_interval[0] < obs.measured_value < obs.confidence_interval[1]
    assert obs.cost_usd > 0

def test_four_way_baseline_comparison():
    res = run_four_way_comparison()
    assert "baselines" in res
    b = res["baselines"]
    assert "nominal_only" in b
    assert "fixed_safety_margin" in b
    assert "non_adaptive_sweep" in b
    assert "adaptive_fidelitygate" in b
    # Adaptive FidelityGate must have zero unsafe acceptances
    assert b["adaptive_fidelitygate"]["unsafe_acceptances"] == 0
