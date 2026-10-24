#!/usr/bin/env python3
"""
scripts/prepare_sample_subsets.py
Extracts calibrated 1,000-row sample subsets directly from downloaded raw Cisco datasets.
Enables rapid interactive verification and testing while preserving exact byte/row lineage.
"""

import gzip
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "raw" / "cisco_telemetry"


def extract_subset(gz_path: Path, out_path: Path, num_rows: int = 1000):
    if not gz_path.exists():
        print(f"Skipping {gz_path.name}: file does not exist.")
        return

    print(f"Extracting {num_rows} rows from {gz_path.name} -> {out_path.name}...")
    with gzip.open(gz_path, "rt", encoding="utf-8", errors="replace") as f_in:
        with open(out_path, "w", encoding="utf-8") as f_out:
            # Header
            header = f_in.readline()
            f_out.write(header)
            count = 0
            for line in f_in:
                f_out.write(line)
                count += 1
                if count >= num_rows:
                    break
    print(f"  Extracted {count} rows successfully to {out_path.name}")


def main():
    # 1. Baseline subset
    base_gz = DATA_DIR / "0" / "baseline_no_anomaly.csv.gz"
    base_out = DATA_DIR / "0" / "baseline_sample_1000.csv"
    extract_subset(base_gz, base_out, 1000)

    # 2. BGP Clear anomaly subset
    bgp_gz = DATA_DIR / "3" / "bgpclear08042017.csv.gz"
    bgp_out = DATA_DIR / "3" / "bgpclear_sample_1000.csv"
    extract_subset(bgp_gz, bgp_out, 1000)


if __name__ == "__main__":
    main()

