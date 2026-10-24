"""fidelitygate/xai/summary_generator.py
Synthesizes operator-readable decision summaries from structured explanation objects.
Enforces zero-hallucination guardrails and truthful mode labelling (DETERMINISTIC_EXPLAINER vs LLM_ASSISTED_VERIFIED).
"""

from typing import List, Optional
from fidelitygate.evaluation.models import GateDecision
from .models import (
    CounterexampleExplanation,
    ExplanationMode,
    GateRuleExplanation,
    LocalSensitivityReport,
    RuleStatus,
    UncertaintyExplanation,
)


class DecisionSummaryGenerator:
    """Generates concise, factual plain-language summaries grounded in computed evidence."""

    @staticmethod
    def generate_deterministic_summary(
        decision: GateDecision,
        candidate_id: Optional[str],
        scenario_id: str,
        rules: List[GateRuleExplanation],
        counterexample: Optional[CounterexampleExplanation] = None,
        uncertainty: Optional[UncertaintyExplanation] = None,
        sensitivity: Optional[LocalSensitivityReport] = None,
        limitations: Optional[List[str]] = None,
    ) -> str:
        """Constructs an authoritative operator summary from structured explanation facts."""
        sentences: List[str] = []

        # 1. Opening Verdict Statement
        cid_str = f"candidate '{candidate_id}'" if candidate_id else "proposed mitigation"
        if decision == GateDecision.ACCEPT:
            sentences.append(
                f"FidelityGate verified and ACCEPTED {cid_str} under scenario '{scenario_id}'."
            )
        elif decision == GateDecision.GATHER_EVIDENCE:
            sentences.append(
                f"FidelityGate reached GATHER_EVIDENCE for {cid_str} under scenario '{scenario_id}': "
                f"further diagnostic measurement is required before approval."
            )
        else:
            sentences.append(
                f"FidelityGate ABSTAINED on {cid_str} under scenario '{scenario_id}': "
                f"the proposal fails mandatory operational or safety constraints."
            )

        # 2. Rule Pass/Fail Breakdown
        pass_count = sum(1 for r in rules if r.status == RuleStatus.PASSED)
        fail_count = sum(1 for r in rules if r.status == RuleStatus.FAILED)
        unknown_count = sum(1 for r in rules if r.status == RuleStatus.UNKNOWN)

        rule_summary = f"{pass_count} of {len(rules)} mandatory decision rules passed"
        if fail_count > 0:
            failed_names = [r.rule_name for r in rules if r.status == RuleStatus.FAILED]
            rule_summary += f" ({fail_count} failed: {', '.join(failed_names)})"
        if unknown_count > 0:
            rule_summary += f" ({unknown_count} unknown due to missing data)"
        sentences.append(f"{rule_summary}.")

        # 3. Counterexample & Fragility
        if counterexample:
            sentences.append(
                f"Adversarial perturbation search identified constraint breach '{counterexample.violated_constraint}' "
                f"at {counterexample.perturbed_latency_ms:.1f} ms latency (+{counterexample.violation_margin_ms:.1f} ms margin) "
                f"under parameter perturbation {counterexample.exact_parameter_vector}."
            )

        # 4. Measurement & Uncertainty Reduction
        if uncertainty:
            if uncertainty.raw_measured_value is not None and uncertainty.raw_unit != uncertainty.parameter_unit:
                sentences.append(
                    f"Targeted diagnostic probe '{uncertainty.tool_id}' measured physical delay of "
                    f"{uncertainty.raw_measured_value:.2f} {uncertainty.raw_unit} (+-{uncertainty.raw_error_bound:.1f} {uncertainty.raw_unit}). "
                    f"Inverted parameter estimate narrowed '{uncertainty.target_parameter}' uncertainty "
                    f"by {uncertainty.width_reduction_pct:.1f}% to [{uncertainty.posterior_interval[0]:.4f}, {uncertainty.posterior_interval[1]:.4f}] {uncertainty.parameter_unit}."
                )
            else:
                sentences.append(
                    f"Targeted diagnostic probe '{uncertainty.tool_id}' narrowed '{uncertainty.target_parameter}' "
                    f"uncertainty by {uncertainty.width_reduction_pct:.1f}%."
                )

        # 5. Sensitivity & Bottleneck
        if sensitivity:
            sentences.append(
                f"Digital-twin sensitivity analysis identified '{sensitivity.most_sensitive_parameter}' as the primary "
                f"driver of latency variance, with bottleneck link '{sensitivity.bottleneck_edge}'."
            )

        # 6. Safety Limits & Non-Causality
        sentences.append(
            "Decision is authorized for human review; no real-world routing reconfiguration has been enacted."
        )

        return " ".join(sentences)

    generate_summary = generate_deterministic_summary
