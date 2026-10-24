#!/usr/bin/env python3
"""
scripts/run_triage.py
CLI runner for Layer 2: Explainable Anomaly Triage and Evidence Correlation.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fidelitygate.triage.engine import AnomalyTriageEngine
from fidelitygate.triage.models import TriageRunRequest


def main():
    parser = argparse.ArgumentParser(description="Run deterministic anomaly triage and evidence correlation.")
    parser.add_argument(
        "--ingestion-id",
        default=None,
        help="Target ingestion run ID (if omitted, most recent ingestion run is used)"
    )
    parser.add_argument(
        "--source-id",
        default="cisco-ie-telemetry",
        help="Dataset source identifier (default: cisco-ie-telemetry)"
    )
    parser.add_argument(
        "--case-file",
        default=None,
        help="Optional path to documented case metadata file (e.g. casedata.txt)"
    )
    parser.add_argument(
        "--scenario-id",
        default=None,
        help="Optional network scenario ID"
    )
    parser.add_argument(
        "--z-threshold",
        type=float,
        default=3.5,
        help="Robust MAD deviation score threshold (default: 3.5)"
    )
    parser.add_argument(
        "--min-samples",
        type=int,
        default=5,
        help="Minimum baseline samples required (default: 5)"
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional file path to persist full investigation context JSON"
    )
    args = parser.parse_args()

    engine = AnomalyTriageEngine()
    req = TriageRunRequest(
        ingestion_id=args.ingestion_id,
        source_id=args.source_id,
        case_file=args.case_file,
        scenario_id=args.scenario_id,
        z_threshold=args.z_threshold,
        min_samples=args.min_samples,
    )

    print(f"Executing Anomaly Triage on ingestion='{args.ingestion_id or 'latest'}', source='{args.source_id}'...")
    try:
        summary, context, correlation, findings, evidence = engine.run_triage(req)
    except Exception as exc:
        print(f"\n[ERROR] Triage execution failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== Triage Run Summary ({summary.triage_run_id}) ===")
    print(f"Status:                      {summary.status}")
    print(f"Source Dataset:              {summary.source_dataset}")
    print(f"Total Observations Scanned:  {summary.total_observations_scanned}")
    print(f"Total Candidate Findings:    {summary.findings_count}")
    print(f"Highest Severity Detected:   {summary.highest_severity.value}")
    print(f"Correlated Evidence Items:   {summary.evidence_items_count}")
    print(f"Supported Relationships:     {len(correlation.supported_relationships)}")

    # Severity distribution
    sev_counts = {}
    for f in findings:
        sev_counts[f.severity.value] = sev_counts.get(f.severity.value, 0) + 1
    print("\nFindings by Severity:")
    for sev, count in sorted(sev_counts.items()):
        print(f"  • {sev:<8}: {count}")

    if findings:
        print("\nTop Candidate Findings (up to 5):")
        for i, f in enumerate(findings[:5], 1):
            dev_str = f"{f.deviation_score:+.2f} MAD" if f.deviation_score is not None else "step_delta"
            base_str = f"{f.baseline_value:.2f}" if f.baseline_value is not None else "N/A"
            print(
                f"  {i}. [{f.severity.value}] {f.entity_id} | {f.metric_name} | "
                f"Obs: {f.observed_value} vs Base: {base_str} ({dev_str}) | "
                f"Conf: {f.confidence*100:.0f}% | Origin: {f.label_origin.value}"
            )

    if correlation.supported_relationships:
        print("\nKey Supported Evidence Relationships:")
        for rel in correlation.supported_relationships[:3]:
            print(f"  • [{rel['relationship_type']}] {rel['description']}")

    print("\nRecommended Diagnostic Categories:")
    for diag in context.recommended_diagnostic_categories:
        print(f"  • {diag}")

    if context.explicitly_unavailable_information:
        print("\nDeclared Limitations / Unavailable Data:")
        for lim in context.explicitly_unavailable_information:
            print(f"  • {lim}")

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f_out:
            f_out.write(context.model_dump_json(indent=2))
        print(f"\nInvestigation context saved to: {out_p.resolve()}")

    print("\n[SUCCESS] Layer 2 triage execution complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()

