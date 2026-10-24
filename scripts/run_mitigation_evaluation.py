#!/usr/bin/env python3
"""scripts/run_mitigation_evaluation.py
CLI runner to execute Layer 4 Candidate Mitigation Evaluation and Digital-Twin Simulation.
Connects completed Layer 3 investigation and DiagnosticPlan to the deterministic simulator,
performs path validation, uncertainty sweeps, and decision-gate enforcement.

Usage:
    python scripts/run_mitigation_evaluation.py --investigation-id <id> [--scenario-id <id>] [--budget 25] [--output-json <path>]
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fidelitygate.config import settings
from fidelitygate.storage import StorageEngine
from fidelitygate.evaluation.engine import MitigationEvaluationEngine
from fidelitygate.evaluation.models import MitigationEvaluationRequest


def main():
    parser = argparse.ArgumentParser(
        description="FidelityGate Layer 4 — Candidate Mitigation Evaluation & Digital-Twin Simulation"
    )
    parser.add_argument(
        "--investigation-id",
        required=False,
        default=None,
        help="Target Layer 3 investigation ID (defaults to most recent investigation if omitted)",
    )
    parser.add_argument(
        "--scenario-id",
        required=False,
        default=None,
        help="Optional network scenario context (e.g. wan_congestion, fiber_drift)",
    )
    parser.add_argument(
        "--budget",
        type=int,
        default=25,
        help="Bounded uncertainty simulation budget per candidate (default: 25, max: 50)",
    )
    parser.add_argument(
        "--include-reference",
        action="store_true",
        help="Execute offline reference evaluation against hidden ground truth",
    )
    parser.add_argument(
        "--output-json",
        required=False,
        default=None,
        help="Optional file path to persist full MitigationEvaluationReport JSON",
    )
    args = parser.parse_args()

    storage = StorageEngine(settings.DATABASE_PATH)
    inv_id = args.investigation_id

    if not inv_id:
        recent_invs = storage.list_investigation_summaries(1)
        if not recent_invs:
            print("[ERROR] No completed investigations found in database. Run investigation first:")
            print("        python scripts/run_investigation.py")
            sys.exit(1)
        inv_id = recent_invs[0].investigation_id
        print(f"[*] No --investigation-id provided. Using most recent: '{inv_id}'")

    print(f"Executing Candidate Mitigation Evaluation on investigation='{inv_id}'...")

    engine = MitigationEvaluationEngine(storage)
    request = MitigationEvaluationRequest(
        investigation_id=inv_id,
        scenario_id=args.scenario_id,
        evaluation_budget=args.budget,
        include_reference_eval=args.include_reference,
    )

    try:
        summary, report, candidates, events = engine.run_evaluation(request)
    except Exception as exc:
        print(f"[ERROR] Evaluation execution failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print("\n" + "=" * 55)
    print(f"=== Mitigation Evaluation Summary ({summary.evaluation_id}) ===")
    print("=" * 55)
    print(f"Status:                      {summary.status}")
    print(f"Gate Verdict:                {summary.gate_verdict.value}")
    print(f"Scenario Context:            {summary.scenario_id}")
    print(f"Total Candidates:            {summary.candidates_count}")
    print(f"Evaluated Candidates:        {summary.evaluated_count}")
    print(f"Compliant Candidates:        {summary.compliant_count}")
    print(f"Selected Candidate ID:       {summary.selected_candidate_id or 'NONE'}")
    print(f"Total Simulations Executed:  {report.total_simulations}")
    print(f"Evaluation Duration:         {summary.duration_ms} ms")
    print(f"Gate Justification:          {report.gate_justification}")

    print("\nCandidate Evaluations:")
    for i, ce in enumerate(candidates, 1):
        nom_lat = ce.nominal_prediction.latency_ms if ce.nominal_prediction else "N/A"
        nom_slo = ce.nominal_prediction.slo_latency_ms if ce.nominal_prediction else "N/A"
        nom_util = f"{ce.nominal_prediction.peak_utilization * 100:.1f}%" if ce.nominal_prediction else "N/A"
        bot_edge = ce.nominal_prediction.bottleneck_edge_id if ce.nominal_prediction else "N/A"
        gate_dec = ce.gate_report.decision.value if ce.gate_report else "N/A"

        print(f"  {i}. [{ce.status.value}] Candidate '{ce.candidate_id}' | Gate: {gate_dec}")
        print(f"     Path: {' -> '.join(ce.action.path)}")
        print(f"     Nominal Latency: {nom_lat} ms (SLO: {nom_slo} ms) | Peak Util: {nom_util} | Bottleneck: {bot_edge}")
        if ce.comparison:
            lat_change = f"{ce.comparison.latency_change_ms:+0.1f} ms"
            print(f"     Before/After Latency Change: {lat_change} | Newly Overloaded Edges: {ce.comparison.newly_overloaded_edges or 'None'}")
        if ce.counterexample and ce.counterexample.is_fragile:
            print(f"     Counterexample: {ce.counterexample.explanation}")
        if ce.reference_evaluation:
            print(f"     Reference Ground Truth: {ce.reference_evaluation.reference_status.value} (True Latency: {ce.reference_evaluation.true_latency_ms} ms)")

    print("\nAudit Events Recorded:")
    for ev in events:
        print(f"  • #{ev.sequence_number} [{ev.stage}] {ev.actor} -> {ev.event_type}: {json.dumps(ev.details)}")

    if args.output_json:
        out_path = Path(args.output_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        print(f"\nMitigation evaluation report saved to: {out_path.resolve()}")

    print("\n[SUCCESS] Layer 4 candidate mitigation evaluation complete.")


if __name__ == "__main__":
    main()

