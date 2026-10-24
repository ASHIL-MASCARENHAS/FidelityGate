"""fidelitygate/adaptive/selector.py
Adaptive diagnostic selector evaluating Layer 4 counterexamples, uncertainty widths,
diagnostic costs, and decision relevance under a constrained deterministic ranking strategy.
"""

from typing import Dict, List, Optional, Set, Tuple

from .measurement_registry import (
    ALLOWLISTED_MEASUREMENT_MODELS,
    DiagnosticMeasurementRegistry,
)
from .models import (
    DiagnosticCandidateEvaluation,
    MeasurementModel,
    UncertaintyInterval,
)
from ..evaluation.models import Counterexample


class AdaptiveDiagnosticSelector:
    """Selects targeted diagnostics capable of resolving counterexample-indicated uncertainties."""

    SELECTION_MODE = "DETERMINISTIC_DIAGNOSTIC_SELECTOR"

    def __init__(self, registry: Optional[DiagnosticMeasurementRegistry] = None):
        self.registry = registry or DiagnosticMeasurementRegistry()

    def evaluate_and_rank_diagnostics(
        self,
        counterexamples: List[Counterexample],
        current_uncertainty: Dict[str, UncertaintyInterval],
        executed_diagnostics: Set[str],
        remaining_budget_usd: float,
        target_entity: str = "primary_path_egress",
    ) -> List[DiagnosticCandidateEvaluation]:
        """
        Evaluates allowlisted diagnostics against active counterexamples and ranks by utility.
        """
        candidates: List[DiagnosticCandidateEvaluation] = []
        active_critical_params = {ce.critical_parameter for ce in counterexamples if ce.is_fragile}

        for tool_id, model in self.registry.models.items():
            # Check 1: Already executed in this adaptive run
            if tool_id in executed_diagnostics:
                candidates.append(
                    DiagnosticCandidateEvaluation(
                        diagnostic_id=tool_id,
                        tool_name=model.tool_name,
                        target_entity=target_entity,
                        target_parameter=model.target_parameter,
                        addressed_counterexample_id=None,
                        current_uncertainty_width=0.0,
                        affected_constraints=[],
                        estimated_cost=model.cost_usd,
                        expected_uncertainty_reduction=0.0,
                        decision_relevance_score=0.0,
                        priority_score=0.0,
                        is_eligible=False,
                        rejection_reason=f"Diagnostic '{tool_id}' has already been executed in this adaptive run.",
                    )
                )
                continue

            # Check 2: Exceeds remaining monetary budget
            if model.cost_usd > remaining_budget_usd:
                candidates.append(
                    DiagnosticCandidateEvaluation(
                        diagnostic_id=tool_id,
                        tool_name=model.tool_name,
                        target_entity=target_entity,
                        target_parameter=model.target_parameter,
                        addressed_counterexample_id=None,
                        current_uncertainty_width=0.0,
                        affected_constraints=[],
                        estimated_cost=model.cost_usd,
                        expected_uncertainty_reduction=0.0,
                        decision_relevance_score=0.0,
                        priority_score=0.0,
                        is_eligible=False,
                        rejection_reason=f"Cost (${model.cost_usd:.4f}) exceeds remaining budget (${remaining_budget_usd:.4f}).",
                    )
                )
                continue

            # Check 3: Current parameter uncertainty available
            prior_interval = current_uncertainty.get(model.target_parameter)
            current_width = prior_interval.width if prior_interval else 0.0

            # Check 4: Relevance to active counterexamples
            is_relevant = model.target_parameter in active_critical_params
            addressed_ce_id = None
            for ce in counterexamples:
                if ce.critical_parameter == model.target_parameter:
                    addressed_ce_id = f"ce-{ce.critical_parameter}"
                    break

            if not is_relevant and len(active_critical_params) > 0:
                candidates.append(
                    DiagnosticCandidateEvaluation(
                        diagnostic_id=tool_id,
                        tool_name=model.tool_name,
                        target_entity=target_entity,
                        target_parameter=model.target_parameter,
                        addressed_counterexample_id=None,
                        current_uncertainty_width=current_width,
                        affected_constraints=[],
                        estimated_cost=model.cost_usd,
                        expected_uncertainty_reduction=0.0,
                        decision_relevance_score=0.0,
                        priority_score=0.0,
                        is_eligible=False,
                        rejection_reason=(
                            f"Diagnostic parameter '{model.target_parameter}' does not address any active "
                            f"counterexample failure modes: {sorted(list(active_critical_params))}."
                        ),
                    )
                )
                continue

            # Calculate Expected Uncertainty Reduction
            # Expected posterior width is approximately 2 * delta if prior is wider than measurement
            delta = model.error_bound
            meas_width = 2.0 * delta
            if current_width > 0:
                expected_red = max(0.0, (current_width - min(current_width, meas_width)) / current_width)
            else:
                expected_red = 0.5

            # Calculate Decision Relevance & Priority Score
            relevance_weight = 10.0 if is_relevant else 1.0
            cost_efficiency = 1.0 / (1.0 + 100.0 * model.cost_usd)
            latency_efficiency = 1.0 / (1.0 + 0.05 * model.latency_ms)

            priority_score = round(
                relevance_weight * 10.0 + expected_red * 5.0 + cost_efficiency * 3.0 + latency_efficiency * 2.0,
                3,
            )

            candidates.append(
                DiagnosticCandidateEvaluation(
                    diagnostic_id=tool_id,
                    tool_name=model.tool_name,
                    target_entity=target_entity,
                    target_parameter=model.target_parameter,
                    addressed_counterexample_id=addressed_ce_id,
                    current_uncertainty_width=round(current_width, 4),
                    affected_constraints=["slo_latency", "link_capacity"],
                    estimated_cost=model.cost_usd,
                    expected_uncertainty_reduction=round(expected_red, 4),
                    decision_relevance_score=relevance_weight,
                    priority_score=priority_score,
                    is_eligible=True,
                    rejection_reason=None,
                )
            )

        # Sort descending by priority_score
        candidates.sort(key=lambda c: (c.is_eligible, c.priority_score), reverse=True)
        return candidates

    def select_best_diagnostic(
        self,
        counterexamples: List[Counterexample],
        current_uncertainty: Dict[str, UncertaintyInterval],
        executed_diagnostics: Set[str],
        remaining_budget_usd: float,
        target_entity: str = "primary_path_egress",
    ) -> Tuple[Optional[DiagnosticCandidateEvaluation], List[DiagnosticCandidateEvaluation]]:
        """Selects the top-ranked eligible diagnostic, or returns None if no eligible diagnostic exists."""
        ranked = self.evaluate_and_rank_diagnostics(
            counterexamples=counterexamples,
            current_uncertainty=current_uncertainty,
            executed_diagnostics=executed_diagnostics,
            remaining_budget_usd=remaining_budget_usd,
            target_entity=target_entity,
        )
        eligible = [c for c in ranked if c.is_eligible]
        selected = eligible[0] if eligible else None
        return selected, ranked

