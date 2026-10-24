"""fidelitygate/workflow/outcome.py
Outcome reporting, metric synthesis, and operator verification summaries.
"""

from typing import Dict, Any, List
from fidelitygate.workflow.models import InterventionOutcomeReport, OverallImpact


class OutcomeReporter:
    """Formats and validates comparative pre vs post intervention outcome reports."""

    @staticmethod
    def format_text_summary(report: InterventionOutcomeReport) -> str:
        """Constructs an unambiguous plain-text summary of intervention impact."""
        if report.latency_delta_ms < 0:
            direction = f"reduced by {abs(report.latency_delta_ms):.2f} ms ({abs(report.latency_reduction_pct):.1f}%)"
        elif report.latency_delta_ms > 0:
            direction = f"increased by {report.latency_delta_ms:.2f} ms (+{abs(report.latency_reduction_pct):.1f}%)"
        else:
            direction = "remained unchanged (0.00 ms, 0.0%)"
        
        status_line = (
            f"Intervention '{report.candidate_id}' for flow '{report.affected_flows[0] if report.affected_flows else 'primary'}' "
            f"resulted in an {report.overall_impact.value} outcome. "
            f"Transit latency {direction}, "
            f"moving from {report.pre_action_latency_ms:.2f} ms to {report.post_action_latency_ms:.2f} ms. "
            f"Peak link utilization transitioned from {report.pre_action_peak_utilization*100:.1f}% to {report.post_action_peak_utilization*100:.1f}% "
            f"(bottleneck: {report.bottleneck_link}). "
            f"SLO violations after action: {report.post_action_slo_violations} (prior: {report.pre_action_slo_violations}). "
            f"Capacity violations after action: {report.post_action_capacity_violations} (prior: {report.pre_action_capacity_violations}). "
            f"Execution mode: ISOLATED_DIGITAL_TWIN (no physical configuration enacted)."
        )
        return status_line

    @staticmethod
    def validate_outcome_integrity(report: InterventionOutcomeReport) -> List[str]:
        """Validates that outcome comparisons do not make misleading claims."""
        warnings: List[str] = []
        if report.pre_action_latency_ms <= 0 or report.post_action_latency_ms <= 0:
            warnings.append("Latency values must be strictly positive real numbers.")
        if report.post_action_slo_violations > report.pre_action_slo_violations and report.overall_impact == OverallImpact.IMPROVED:
            warnings.append("Cannot claim IMPROVED outcome when post-action SLO violations increased.")
        if report.post_action_capacity_violations > report.pre_action_capacity_violations and report.overall_impact == OverallImpact.IMPROVED:
            warnings.append("Cannot claim IMPROVED outcome when post-action link overloads increased.")
        if report.latency_delta_ms == 0 and report.pre_action_peak_utilization == report.post_action_peak_utilization and report.overall_impact == OverallImpact.IMPROVED:
            warnings.append("Cannot claim IMPROVED outcome when latency and utilization are identical to baseline.")
        return warnings

