from fidelitygate.scenarios import DEMO_SCENARIOS
from fidelitygate.uncertainty import run_sweep


def test_sweep_is_deterministic():
    s=DEMO_SCENARIOS["wan_congestion"]
    assert run_sweep(s,15)==run_sweep(s,15)


def test_sweep_count_matches_request():
    assert run_sweep(DEMO_SCENARIOS["fiber_drift"],20).evaluations==20
