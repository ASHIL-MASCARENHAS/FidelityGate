#!/usr/bin/env python3
"""
scripts/ingest_dataset.py
CLI runner to ingest an approved network telemetry dataset file into FidelityGate.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fidelitygate.ingestion.models import IngestionRequest
from fidelitygate.ingestion.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Ingest telemetry dataset into FidelityGate Layer 1.")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to CSV/CSV.GZ file relative to DATA_ROOT or project root"
    )
    parser.add_argument(
        "--source-id",
        default="cisco-ie-telemetry",
        help="Source identifier (default: cisco-ie-telemetry)"
    )
    parser.add_argument(
        "--version",
        default="master",
        help="Dataset version tag or commit SHA"
    )
    parser.add_argument(
        "--scenario-id",
        default=None,
        help="Optional target network scenario ID"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass idempotency cache and force re-ingestion"
    )
    args = parser.parse_args()

    pipeline = IngestionPipeline()
    req = IngestionRequest(
        source_id=args.source_id,
        relative_path=args.file,
        dataset_version=args.version,
        scenario_id=args.scenario_id,
        force_reingest=args.force,
    )

    print(f"Ingesting: {args.file} (Source: {args.source_id})...")
    report = pipeline.run_ingestion(req)

    print(f"\n--- Ingestion Report ({report.ingestion_id}) ---")
    print(f"Status:            {report.status}")
    print(f"Source Checksum:   {report.source_checksum[:16]}...")
    print(f"Total Rows:        {report.source_row_count}")
    print(f"Accepted Records:  {report.accepted_count}")
    print(f"Quarantined Rows:  {report.quarantined_count}")
    print(f"Duplicate Rows:    {report.duplicate_count}")
    print(f"Quality Issues:    {len(report.quality_issues)}")
    if report.output_artifacts:
        print("Output Artifacts:")
        for k, v in report.output_artifacts.items():
            print(f"  • {k}: {v}")

    if report.status == "FAILED":
        print("\n[ERROR] Ingestion failed:", report.errors_or_limitations)
        sys.exit(1)
    else:
        print("\n[SUCCESS] Layer 1 ingestion complete.")
        sys.exit(0)


if __name__ == "__main__":
    main()

