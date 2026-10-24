#!/usr/bin/env python3
"""
scripts/validate_dataset.py
Dry-run schema and quality inspection for network telemetry files without persistence.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fidelitygate.ingestion.cisco_adapter import CiscoTelemetryAdapter
from fidelitygate.ingestion.pipeline import IngestionPipeline


def main():
    parser = argparse.ArgumentParser(description="Dry-run validation of a telemetry CSV file.")
    parser.add_argument(
        "--file",
        required=True,
        help="Path to CSV/CSV.GZ file to validate"
    )
    args = parser.parse_args()

    pipeline = IngestionPipeline()
    try:
        target_path = pipeline.resolve_safe_path(args.file)
    except Exception as e:
        print(f"[REJECTED] Path validation error: {e}")
        sys.exit(1)

    checksum = pipeline.compute_sha256(target_path)
    adapter = CiscoTelemetryAdapter()

    print(f"Validating: {target_path.name}")
    print(f"SHA-256:    {checksum}")
    print(f"File Size:  {target_path.stat().st_size / (1024*1024):.2f} MB")

    records, issues, total_rows, accepted, quarantined, duplicates = adapter.ingest_file(
        file_path=target_path,
        source_dataset="cisco-validation-dryrun",
        source_version="dryrun",
        source_checksum=checksum,
        ingestion_id="val-dryrun",
    )

    print(f"\n--- Validation Summary ---")
    print(f"Total Rows Scanned:     {total_rows}")
    print(f"Accepted Records:       {len(records)}")
    print(f"Quarantined Rows:       {quarantined}")
    print(f"Duplicate Telemetry:    {duplicates}")
    print(f"Reported Issues:        {len(issues)}")

    critical_issues = [i for i in issues if i.severity == "CRITICAL"]
    warning_issues = [i for i in issues if i.severity == "WARNING"]

    print(f"  • Critical Issues:    {len(critical_issues)}")
    print(f"  • Warnings:           {len(warning_issues)}")

    if issues:
        print("\nTop Quality Issues (first 10):")
        for i, issue in enumerate(issues[:10], 1):
            print(f"  {i}. [{issue.severity}] {issue.category} (Row {issue.row_ref}): {issue.description}")

    if critical_issues or total_rows == 0:
        print("\n[VERDICT] Validation FAILED.")
        sys.exit(1)
    elif warning_issues:
        print("\n[VERDICT] Validation PASSED WITH WARNINGS.")
        sys.exit(0)
    else:
        print("\n[VERDICT] Validation PASSED (Clean).")
        sys.exit(0)


if __name__ == "__main__":
    main()

