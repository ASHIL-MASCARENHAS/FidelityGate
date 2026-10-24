from fidelitygate.schemas import GateDecision, Scenario, SweepReport
from fidelitygate.decision_gate import decide


def make_scenario():
    return Scenario(scenario_id="T1", name="test", description="test",
        nominal_latency_ms=10, capacity_mbps=100, offered_load_mbps=50,
        slo_latency_ms=20, stability_threshold=.9)


def make_report(nominal=10, worst=15, violations=0, stability=1):
    return SweepReport(evaluations=25, nominal_latency_ms=nominal,
        worst_latency_ms=worst, peak_utilization=.7, stability_score=stability,
        violations=violations, sensitivity={"latency":5})


def test_accept_when_all_variations_pass():
    assert decide(make_scenario(), make_report()).decision == GateDecision.ACCEPT


def test_gather_evidence_when_nominal_passes_but_sweep_breaches():
    assert decide(make_scenario(), make_report(worst=24, violations=3, stability=.88)).decision == GateDecision.GATHER_EVIDENCE


def test_abstain_when_nominal_prediction_fails():
    assert decide(make_scenario(), make_report(nominal=25, worst=30, violations=10, stability=.6)).decision == GateDecision.ABSTAIN
