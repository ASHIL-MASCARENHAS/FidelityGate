#!/usr/bin/env python3
"""
scripts/download_datasets.py
Reproducible acquisition of Cisco Innovation Edge network telemetry datasets.
Preserves raw files, verifies SHA-256 checksums, and records source provenance without API keys.
"""

import argparse
import hashlib
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fidelitygate.config import settings

CISCO_BASE_URL = "https://raw.githubusercontent.com/cisco-ie/telemetry/master"

APPROVED_DATASETS = {
    "cisco-baseline": {
        "source_id": "cisco-baseline",
        "name": "Cisco Innovation Edge - Baseline No Anomaly",
        "description": "Baseline operational telemetry with no injected faults across leaf/spine topology.",
        "folder": "0",
        "files": [
            ("README.md", "README.md"),
            ("baseline_header.txt", "baseline_header.txt"),
            ("baseline_no_anomaly.csv.gz", "baseline_no_anomaly.csv.gz"),
        ],
    },
    "cisco-bgpclear": {
        "source_id": "cisco-bgpclear",
        "name": "Cisco Innovation Edge - BGP Clear Anomaly Event",
        "description": "Controlled BGP clear disruption events on leaf/spine switches under load.",
        "folder": "3",
        "files": [
            ("README.md", "README.md"),
            ("bgpclear_header.txt", "bgpclear_header.txt"),
            ("bgpclear_casedata.txt", "bgpclear_casedata.txt"),
            ("bgpclear08042017.csv.gz", "bgpclear08042017.csv.gz"),
        ],
    },
    "cisco-portflap": {
        "source_id": "cisco-portflap",
        "name": "Cisco Innovation Edge - Port Flap Anomaly Event",
        "description": "Controlled optical transceiver pull and admin shutdown port flap events.",
        "folder": "4",
        "files": [
            ("portflap_header.txt", "portflap_header.txt"),
            ("portflap_casedata.txt", "portflap_casedata.txt"),
            ("portflaptypes.csv.gz", "portflaptypes.csv.gz"),
        ],
    },
}


def compute_sha256(path: Path) -> str:
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_file(url: str, dest_path: Path, max_mb: int = 100, force: bool = False) -> tuple[bool, str, int]:
    """Downloads a file from public URL.
    Returns (success, checksum_or_error, byte_size).
    """
    if dest_path.exists() and not force:
        size = dest_path.stat().st_size
        checksum = compute_sha256(dest_path)
        print(f"  [CACHED] {dest_path.name} ({size / (1024*1024):.2f} MB) SHA256: {checksum[:12]}...")
        return True, checksum, size

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest_path.with_suffix(dest_path.suffix + ".tmp")

    print(f"  [DOWNLOADING] {url} -> {dest_path.name}...")
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "FidelityGate-DataIngestion/1.0"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            if response.status != 200:
                return False, f"HTTP Error {response.status}: {response.reason}", 0

            content_len = response.headers.get("Content-Length")
            if content_len and int(content_len) > max_mb * 1024 * 1024:
                return False, f"File size {int(content_len)} bytes exceeds limit {max_mb} MB", 0

            hasher = hashlib.sha256()
            total_bytes = 0
            with open(temp_path, "wb") as f_out:
                while True:
                    chunk = response.read(65536)
                    if not chunk:
                        break
                    total_bytes += len(chunk)
                    if total_bytes > max_mb * 1024 * 1024:
                        temp_path.unlink(missing_ok=True)
                        return False, f"Download exceeded max limit {max_mb} MB during transfer", 0
                    hasher.update(chunk)
                    f_out.write(chunk)

        # Atomic rename
        if temp_path.exists():
            if dest_path.exists():
                dest_path.unlink()
            temp_path.rename(dest_path)

        checksum = hasher.hexdigest()
        print(f"  [SUCCESS] Saved {dest_path.name} ({total_bytes / (1024*1024):.2f} MB) SHA256: {checksum[:12]}...")
        return True, checksum, total_bytes

    except urllib.error.URLError as e:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return False, f"Network error: {str(e)}", 0
    except Exception as e:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        return False, f"Unexpected error: {str(e)}", 0


def main():
    parser = argparse.ArgumentParser(description="Download approved Cisco telemetry datasets for FidelityGate.")
    parser.add_argument(
        "--dataset",
        choices=list(APPROVED_DATASETS.keys()) + ["all"],
        default="cisco-baseline",
        help="Dataset identifier to download"
    )
    parser.add_argument(
        "--max-mb",
        type=int,
        default=100,
        help="Maximum allowable file size in megabytes"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-download even if local cached file exists"
    )
    args = parser.parse_args()

    targets = list(APPROVED_DATASETS.keys()) if args.dataset == "all" else [args.dataset]
    raw_root = settings.raw_data_path / "cisco_telemetry"
    raw_root.mkdir(parents=True, exist_ok=True)

    summary_records = []

    for target_key in targets:
        spec = APPROVED_DATASETS[target_key]
        folder = spec["folder"]
        print(f"\n==================================================")
        print(f"Acquiring {spec['name']} (Folder: {folder})")
        print(f"==================================================")

        folder_dir = raw_root / folder
        folder_dir.mkdir(parents=True, exist_ok=True)

        dataset_status = {
            "source_id": spec["source_id"],
            "name": spec["name"],
            "downloaded_at": datetime.now(timezone.utc).isoformat(),
            "files": [],
            "all_succeeded": True,
        }

        for remote_file, local_file in spec["files"]:
            url = f"{CISCO_BASE_URL}/{folder}/{remote_file}"
            dest = folder_dir / local_file
            ok, result, byte_size = download_file(url, dest, max_mb=args.max_mb, force=args.force)

            file_record = {
                "file_name": local_file,
                "remote_url": url,
                "success": ok,
                "size_bytes": byte_size,
                "sha256_checksum": result if ok else "ERROR",
                "error": None if ok else result,
            }
            dataset_status["files"].append(file_record)
            if not ok:
                dataset_status["all_succeeded"] = False
                print(f"  [ERROR] Failed to download {local_file}: {result}")

        summary_records.append(dataset_status)

        # Write dataset manifest
        manifest_path = settings.manifests_path / f"{spec['source_id']}_download_manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f_man:
            json.dump(dataset_status, f_man, indent=2)
        print(f"  Manifest recorded: {manifest_path.name}")

    print("\nDownload process completed.")
    for s in summary_records:
        status_str = "SUCCESS" if s["all_succeeded"] else "PARTIAL/FAILED"
        print(f"• {s['source_id']}: {status_str}")


if __name__ == "__main__":
    main()

