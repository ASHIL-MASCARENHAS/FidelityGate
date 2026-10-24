#!/usr/bin/env python3
"""scripts/run_explanation.py
CLI runner to execute Layer 6 Evidence-Based Explainable AI (XAI) and Decision Attribution.
Assembles authoritative, evidence-grounded explanations synthesizing:
  1. Deterministic gate rule evaluations (observed vs required threshold).
  2. Counterexample replay and parameter fragility vectors.
  3. Physical diagnostic measurements and dimensional uncertainty reductions.
  4. Local parameter sensitivity gradients and counterfactual edge perturbations.
  5. Multi-source evidence provenance with explicit non-causal descriptors.
  6. Plain-language operational decision summaries.

Usage:
    python scripts/run_explanation.py [--adaptive-run-id <id>] [--evaluation-id <id>] [--scenario-id <id>] [--output-json <path>]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fidelitygate.config import settings
from fidelitygate.storage import StorageEngine
from fidelitygate.xai.engine import ExplanationEngine
from fidelitygate.xai.models import RuleStatus


def main():
    parser = argparse.ArgumentParser(
        description="FidelityGate Layer 6 — Evidence-Based Explainable AI & Decision Attribution"
    )
    parser.add_argument(
        "--adaptive-run-id",
        required=False,
        default=None,
        help="Target Layer 5 adaptive run ID (defaults to most recent if omitted)",
    )
    parser.add_argument(
        "--evaluation-id",
        required=False,
        default=None,
        help="Target Layer 4 mitigation evaluation ID",
    )
    parser.add_argument(
        "--scenario-id",
        required=False,
        default=None,
        help="Optional network scenario context (e.g. wan_congestion)",
    )
    parser.add_argument(
        "--no-sensitivity",
        action="store_true",
        help="Disable local OAT parameter sensitivity computation",
    )
    parser.add_argument(
        "--output-json",
        required=False,
        default=None,
        help="Optional file path to persist full DecisionExplanation JSON",
    )

    args = parser.parse_args()
    storage = StorageEngine(settings.DATABASE_PATH)
    engine = ExplanationEngine(storage)

    adaptive_run_id = args.adaptive_run_id
    evaluation_id = args.evaluation_id

    # Auto-resolve target if none provided
    if not adaptive_run_id and not evaluation_id:
        recent_adapt = storage.list_adaptive_summaries(1)
        if recent_adapt:
            adaptive_run_id = recent_adapt[0].adaptive_run_id
            print(f"[*] No target provided. Using most recent adaptive run: '{adaptive_run_id}'")
        else:
            recent_eval = storage.list_mitigation_summaries(1)
            if recent_eval:
                evaluation_id = recent_eval[0].evaluation_id
                print(f"[*] No adaptive runs found. Using most recent evaluation: '{evaluation_id}'")
            else:
                print("[ERROR] No completed Layer 4/5 runs found in database. Run evaluate-mitigation or run_adaptive_investigation.py first.")
                sys.exit(1)

    print(f"Synthesizing Evidence-Based Decision Explanation for target: adaptive_run='{adaptive_run_id}', evaluation='{evaluation_id}'...")

    try:
        explanation = engine.generate_explanation(
            evaluation_id=evaluation_id,
            adaptive_run_id=adaptive_run_id,
            scenario_id=args.scenario_id,
            compute_sensitivity=not args.no_sensitivity,
        )
    except Exception as exc:
        print(f"[FATAL] Explanation generation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 68)
    print(f"=== FidelityGate Decision Explanation ({explanation.explanation_id}) ===")
    print("=" * 68)
    print(f"Decision Verdict:     {explanation.decision.value}")
    print(f"Scenario Context:     {explanation.scenario_id}")
    print(f"Target Candidate:     {explanation.candidate_id or 'None'}")
    print(f"Agent Execution Mode: {explanation.agent_mode}")
    print(f"Data Substrate Mode:  {explanation.data_mode}")
    print(f"Created At:           {explanation.created_at}")

    print("\n" + "-" * 68)
    print("Plain-Language Decision Summary:")
    print("-" * 68)
    print(explanation.summary)

    print("\n" + "-" * 68)
    print("Deterministic Gate Rule Breakdown (5 Mandatory Rules):")
    print("-" * 68)
    for idx, rule in enumerate(explanation.constraint_results, 1):
        status_icon = "[PASS]" if rule.status == RuleStatus.PASSED else ("[FAIL]" if rule.status == RuleStatus.FAILED else "[WARN]")
        obs_val = f"{rule.observed_value:.4f}" if rule.observed_value is not None else "None"
        thresh_val = f"{rule.threshold_value:.2f}" if rule.threshold_value is not None else "None"
        print(f"  {status_icon} Rule #{idx}: {rule.rule_name} ({rule.rule_id})")
        print(f"         Metric:     {rule.target_metric} = {obs_val} {rule.unit}")
        print(f"         Condition:  {rule.threshold_condition} (Threshold: {thresh_val})")
        print(f"         Evidence:   {rule.supporting_evidence_ref}")
        print(f"         Details:    {rule.explanation}")

    if explanation.counterexample_summary:
        ce = explanation.counterexample_summary
        print("\n" + "-" * 68)
        print("Counterexample Replay & Fragility Analysis:")
        print("-" * 68)
        print(f"  Counterexample ID:    {ce.counterexample_id}")
        print(f"  Violated Constraint:  {ce.violated_constraint}")
        print(f"  Nominal Latency:      {ce.nominal_latency_ms:.2f} ms (Utilization: {ce.nominal_utilization*100:.1f}%)")
        print(f"  Perturbed Latency:    {ce.perturbed_latency_ms:.2f} ms (Breach Margin: +{ce.violation_margin_ms:.2f} ms vs {ce.slo_latency_ms:.1f} ms SLO)")
        print(f"  Perturbation Vector:  {ce.exact_parameter_vector}")
        print(f"  Failure Analysis:     {ce.explanation}")

    if explanation.uncertainty_changes:
        print("\n" + "-" * 68)
        print(f"Diagnostic Measurement & Uncertainty Updates ({len(explanation.uncertainty_changes)} cycle(s)):")
        print("-" * 68)
        for u in explanation.uncertainty_changes:
            raw_str = f"{u.raw_measured_value:.3f} {u.raw_unit} (error: ±{u.raw_error_bound} {u.raw_unit})" if u.raw_measured_value else "N/A"
            print(f"  Cycle #{u.cycle_number}: Tool '{u.tool_id}' -> Parameter '{u.target_parameter}' ({u.target_entity})")
            print(f"    Raw Physical Observation: {raw_str}")
            print(f"    Inverted Parameter Est:   {u.parameter_measured_value:.4f} {u.parameter_unit} (error: ±{u.parameter_error_bound:.4f} {u.parameter_unit})")
            print(f"    Prior Interval:           [{u.prior_interval[0]:.4f}, {u.prior_interval[1]:.4f}] {u.parameter_unit}")
            print(f"    Measurement Interval:     [{u.measurement_interval[0]:.4f}, {u.measurement_interval[1]:.4f}] {u.parameter_unit}")
            post_str = f"[{u.posterior_interval[0]:.4f}, {u.posterior_interval[1]:.4f}] {u.parameter_unit}" if u.posterior_interval else "REJECTED (INCONSISTENT)"
            print(f"    Posterior Interval:       {post_str} (Width Reduction: {u.width_reduction_pct:.1f}%)")
            print(f"    Dimensional Integrity:   Preserved dimensions: {', '.join(u.unrelated_dimensions_preserved)}")
            print(f"    Gate Impact:              {u.subsequent_gate_impact}")

    if explanation.sensitivity_results:
        sens = explanation.sensitivity_results
        print("\n" + "-" * 68)
        print("Local Parameter Sensitivity Gradients (OAT Perturbations):")
        print("-" * 68)
        print(f"  Most Sensitive Parameter: {sens.most_sensitive_parameter}")
        print(f"  Bottleneck Network Edge:  {sens.bottleneck_edge}")
        print("  Evaluated Parameters:")
        for p in sens.evaluated_parameters:
            crit = " [CRITICAL BOTTLENECK]" if p.is_critical_bottleneck else ""
            print(f"    • Rank #{p.sensitivity_rank}: '{p.parameter_name}' (nominal: {p.nominal_value:.3f} {p.unit}){crit}")
            print(f"      Latency Elasticity:     {p.latency_elasticity:+.4f} (Utilization Elasticity: {p.utilization_elasticity:+.4f})")
            for pert in p.perturbations:
                print(f"        {int(pert['perturbation_pct']):+3d}% -> Latency: {pert['resulting_latency_ms']:.2f} ms, Peak Util: {pert['resulting_utilization']*100:.1f}%")
        print(f"  Methodology Note: {sens.methodology_disclosure}")

    print("\n" + "-" * 68)
    print("Multi-Source Evidence Provenance (Layer 1 Telemetry):")
    print("-" * 68)
    for p in explanation.evidence_items:
        print(f"  • Observation '{p.observation_id}' ({p.label_origin}):")
        print(f"    Source:      {p.source_dataset} [{p.source_file}]")
        print(f"    Metric:      {p.metric_name} = {p.value} {p.unit} @ {p.timestamp}")
        print(f"    Entity:      {p.entity_id} (Quality: {p.data_quality_status})")
        print(f"    Descriptor:  {p.relationship_descriptor} (Causal claim: {p.is_causal_claim})")

    print("\n" + "-" * 68)
    print("Explicit Knowledge Limitations & Human Authorization Notice:")
    print("-" * 68)
    for lim in explanation.limitations:
        print(f"  [LIMITATION] {lim}")
    if explanation.unresolved_questions:
        for q in explanation.unresolved_questions:
            print(f"  [UNRESOLVED] {q}")

    if explanation.post_hoc_reference:
        ref = explanation.post_hoc_reference
        print("\n" + "-" * 68)
        print("OFFLINE POST-HOC REFERENCE EVALUATION (HIDDEN BENCHMARK ONLY):")
        print("-" * 68)
        print(f"  Ground Truth Feasible:    {ref.get('ground_truth_safe')}")
        print(f"  True System Latency:      {ref.get('ground_truth_latency_ms')} ms")
        print(f"  True Peak Utilization:    {ref.get('ground_truth_max_utilization')}")
        print(f"  Boundary Disclosure:      {ref.get('boundary_disclosure')}")

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(explanation.model_dump_json(indent=2))
        print(f"\n[OUTPUT] Explanation saved to: {out_p.resolve()}")

    print(f"\n[SUCCESS] Layer 6 evidence-based explanation complete ({explanation.explanation_id}).\n")


if __name__ == "__main__":
    main()
