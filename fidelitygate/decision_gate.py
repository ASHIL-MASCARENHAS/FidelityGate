from .schemas import GateDecision, GateReport, Scenario, SweepReport


def decide(scenario: Scenario, report: SweepReport) -> GateReport:
    if report.violations == 0 and report.stability_score >= scenario.stability_threshold:
        decision = GateDecision.ACCEPT
        reason = "All evaluated variations satisfy the latency SLO and stability threshold."
    elif report.nominal_latency_ms <= scenario.slo_latency_ms and report.violations > 0:
        decision = GateDecision.GATHER_EVIDENCE
        reason = "Nominal prediction passes, but uncertainty variations breach the SLO; gather diagnostics."
    else:
        decision = GateDecision.ABSTAIN
        reason = "The candidate cannot be justified within the configured uncertainty envelope; fail closed."
    return GateReport(decision=decision, reason=reason, report=report)
