"""fidelitygate/xai/counterexample_explainer.py
Formats and explains adversarial counterexamples causing candidate fragility.
Preserves exact perturbation values, violated predicates, and breach margins.
"""

from typing import Optional
from fidelitygate.evaluation.models import CandidateEvaluation, Counterexample
from .models import CounterexampleExplanation


class CounterexampleExplainer:
    """Explains adversarial counterexamples found during bounded uncertainty sweeps."""

    @staticmethod
    def explain_counterexample(
        counterexample: Counterexample,
        candidate_eval: CandidateEvaluation,
        slo_latency_ms: float = 45.0,
        simulation_event_id: Optional[str] = None,
    ) -> CounterexampleExplanation:
        """Constructs an evidence-backed CounterexampleExplanation from a Counterexample object."""
        nom = candidate_eval.nominal_prediction
        nom_lat = nom.latency_ms if nom else 0.0
        nom_util = nom.peak_utilization if nom else 0.0

        pert_lat = counterexample.violating_latency_ms
        pert_util = nom_util  # peak util under perturbation

        params = {counterexample.critical_parameter: counterexample.perturbation_factor}
        cand_id = candidate_eval.candidate_id

        explanation_text = (
            f"Under adversarial parameter perturbation on '{counterexample.critical_parameter}' "
            f"(factor {counterexample.perturbation_factor:.3f}), candidate '{cand_id}' "
            f"breached the latency SLO. Projected path delay reached {pert_lat:.2f} ms "
            f"(SLO: {counterexample.slo_latency_ms:.1f} ms, margin breach: +{counterexample.margin_breach_ms:.2f} ms). "
            f"Nominal prediction was {nom_lat:.2f} ms ({nom_util*100:.1f}% peak util), but worst perturbed delay "
            f"breaches SLO, classifying the candidate as FRAGILE."
        )

        return CounterexampleExplanation(
            counterexample_id=f"ce-{cand_id}-{counterexample.critical_parameter}",
            candidate_id=cand_id,
            violated_constraint=f"latency_slo_exceeded_{counterexample.critical_parameter}",
            nominal_latency_ms=round(nom_lat, 2),
            nominal_utilization=round(nom_util, 4),
            perturbed_latency_ms=round(pert_lat, 2),
            perturbed_utilization=round(pert_util, 4),
            slo_latency_ms=round(counterexample.slo_latency_ms, 2),
            violation_margin_ms=round(counterexample.margin_breach_ms, 2),
            exact_parameter_vector=params,
            primary_failure_cause=counterexample.critical_parameter,
            simulation_event_id=simulation_event_id,
            explanation=explanation_text,
        )

    explain = explain_counterexample

    @staticmethod
    def summarize_counterexamples(
        candidate_eval: CandidateEvaluation,
        slo_latency_ms: float = 45.0,
    ) -> Optional[CounterexampleExplanation]:
        """Summarizes the primary/minimal counterexample if one exists."""
        if not candidate_eval.counterexample or not candidate_eval.counterexample.is_fragile:
            return None
        return CounterexampleExplainer.explain_counterexample(
            candidate_eval.counterexample,
            candidate_eval,
            slo_latency_ms=slo_latency_ms,
        )
