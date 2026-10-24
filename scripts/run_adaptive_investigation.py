#!/usr/bin/env python3
"""scripts/run_adaptive_investigation.py
CLI runner to execute Layer 5 Counterexample-Guided Adaptive Diagnostics and Re-evaluation.
Loads completed Layer 4 mitigation evaluation, selects targeted diagnostics addressing counterexamples,
applies bounded-error measurement updates, re-evaluates candidate routes in the digital twin,
and enforces decision-gate verification.

Usage:
    python scripts/run_adaptive_investigation.py [--evaluation-id <id>] [--max-cycles 2] [--output-json <path>]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fidelitygate.adaptive.engine import AdaptiveInvestigationEngine
from fidelitygate.adaptive.models import AdaptiveInvestigationRequest
from fidelitygate.config import settings
from fidelitygate.storage import StorageEngine


def main():
    parser = argparse.ArgumentParser(
        description="FidelityGate Layer 5 — Counterexample-Guided Adaptive Diagnostics & Re-evaluation"
    )
    parser.add_argument(
        "--evaluation-id",
        required=False,
        default=None,
        help="Target Layer 4 evaluation ID (defaults to most recent evaluation if omitted)",
    )
    parser.add_argument(
        "--max-cycles",
        type=int,
        default=2,
        help="Maximum adaptive diagnostic cycles (default: 2, max: 5)",
    )
    parser.add_argument(
        "--budget-per-cycle",
        type=int,
        default=25,
        help="Simulation budget per cycle (default: 25, max: 50)",
    )
    parser.add_argument(
        "--total-budget",
        type=int,
        default=100,
        help="Total simulation budget ceiling (default: 100)",
    )
    parser.add_argument(
        "--cost-budget",
        type=float,
        default=0.05,
        help="Diagnostic monetary budget ceiling in USD (default: 0.05)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="PRNG seed for reproducible synthetic observation error (default: 42)",
    )
    parser.add_argument(
        "--output-json",
        required=False,
        default=None,
        help="Optional file path to persist full AdaptiveInvestigationReport JSON",
    )
    args = parser.parse_args()

    storage = StorageEngine(settings.DATABASE_PATH)
    eval_id = args.evaluation_id

    if not eval_id:
        recent_evals = storage.list_mitigation_summaries(1)
        if not recent_evals:
            print("[ERROR] No completed Layer 4 mitigation evaluations found in database.")
            print("        Run mitigation evaluation first:")
            print("        python scripts/run_mitigation_evaluation.py")
            sys.exit(1)
        eval_id = recent_evals[0].evaluation_id
        print(f"[*] No --evaluation-id provided. Using most recent: '{eval_id}'")

    print(f"Executing Adaptive Investigation on evaluation='{eval_id}'...")

    engine = AdaptiveInvestigationEngine(storage)
    request = AdaptiveInvestigationRequest(
        evaluation_id=eval_id,
        max_cycles=args.max_cycles,
        simulation_budget_per_cycle=args.budget_per_cycle,
        total_simulation_budget=args.total_budget,
        diagnostic_cost_budget_usd=args.cost_budget,
        deterministic_seed=args.seed,
    )

    try:
        summary, report, events = engine.run_adaptive_investigation(request)
    except Exception as exc:
        print(f"[ERROR] Adaptive investigation failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 60)
    print(f"=== Adaptive Investigation Summary ({summary.adaptive_run_id}) ===")
    print("=" * 60)
    print(f"Status:                      {summary.status.value}")
    print(f"Initial Gate Decision:       {summary.initial_gate_decision.value}")
    print(f"Final Gate Decision:         {summary.final_gate_decision.value}")
    print(f"Decision Changed:            {'YES' if summary.decision_changed else 'NO'}")
    print(f"Scenario Context:            {summary.scenario_id}")
    print(f"Total Cycles Executed:       {summary.total_cycles_executed}")
    print(f"Diagnostics Executed:        {summary.diagnostics_executed_count}")
    print(f"Total Simulations Consumed:  {summary.total_simulations_consumed}")
    print(f"Total Diagnostic Cost:       ${summary.total_diagnostic_cost_usd:.4f}")
    print(f"Execution Duration:          {summary.total_duration_ms} ms")
    print(f"Termination Reason:          {summary.termination_reason}")

    if report.cycles:
        print("\nAdaptive Diagnostic Cycles:")
        for cycle in report.cycles:
            obs = cycle.observation
            upd = cycle.uncertainty_update
            print(f"  • Cycle #{cycle.cycle_number}: Tool '{cycle.selected_diagnostic_id}'")
            if obs.raw_measured_value is not None and obs.raw_unit != obs.unit:
                print(f"    Raw Physical Observation: {obs.raw_measured_value:.3f} {obs.raw_unit} (error: ±{obs.raw_error_bound:.1f} {obs.raw_unit})")
                print(f"    Inverted Parameter Estimate: {obs.measured_value:.4f} {obs.unit} (propagated error: ±{obs.declared_error_bound:.4f} {obs.unit})")
            else:
                print(f"    Observation: {obs.measured_value} {obs.unit} (error: ±{obs.declared_error_bound})")
            print(f"    Parameter Confidence Interval: [{obs.confidence_interval[0]}, {obs.confidence_interval[1]}] {obs.unit}")
            if upd.posterior_interval:
                print(f"    Updated '{upd.parameter_name}': [{upd.prior_interval.min_value}, {upd.prior_interval.max_value}] -> [{upd.posterior_interval.min_value}, {upd.posterior_interval.max_value}]")
            print(f"    Gate Transition: {cycle.previous_gate_decision.value} -> {cycle.new_gate_decision.value}")
            print(f"    Gate Reason: {cycle.gate_justification}")

    print("\nAudit Events Recorded:")
    for ev in events[:6]:
        print(f"  • #{ev.sequence_number} [Cycle {ev.cycle_number} / {ev.stage}] {ev.actor} -> {ev.event_type}: {json.dumps(ev.details)}")
    if len(events) > 6:
        print(f"  ... and {len(events) - 6} additional audit events persisted.")

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        print(f"\nAdaptive investigation report saved to: {out_path.resolve()}")

    print("\n[SUCCESS] Layer 5 counterexample-guided adaptive investigation complete.")


if __name__ == "__main__":
    main()

