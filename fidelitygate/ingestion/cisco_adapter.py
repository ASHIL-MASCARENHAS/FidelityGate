import csv
import gzip
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Tuple
from uuid import uuid4

from .models import (
    DataMode,
    DataQualityIssue,
    NormalizedObservation,
    RawObservation,
)
from .quarantine import QuarantineManager

# Documented physical units from Cisco Innovation Edge Telemetry header definitions
CISCO_METRIC_UNITS: Dict[str, str] = {
    "bytes-received": "bytes",
    "bytes-sent": "bytes",
    "packets-received": "packets",
    "packets-sent": "packets",
    "bandwidth": "kbps",
    "input-data-rate": "bits/sec",
    "output-data-rate": "bits/sec",
    "peak-input-data-rate": "bits/sec",
    "peak-output-data-rate": "bits/sec",
    "input-packet-rate": "packets/sec",
    "output-packet-rate": "packets/sec",
    "peak-input-packet-rate": "packets/sec",
    "peak-output-packet-rate": "packets/sec",
    "total-cpu-fifteen-minute": "percent",
    "total-cpu-five-minute": "percent",
    "total-cpu-one-minute": "percent",
    "free-application-memory": "bytes",
    "free-physical-memory": "bytes",
    "ram-memory": "bytes",
    "system-ram-memory": "bytes",
    "total-number-of-drop-packets": "packets",
    "no-route-packets": "packets",
    "discard-packets": "packets",
    "checksum-error-packets": "packets",
    "acl-in-rpf-packets": "packets",
    "df-unreachable-packets": "packets",
    "encapsulation-failure-packets": "packets",
    "fragmenation-consumed-packets": "packets",
    "fragmenation-failure-packets": "packets",
    "gre-error-drop": "packets",
    "gre-lookup-failed-drop": "packets",
    "incomplete-adjacency-packets": "packets",
    "lisp-decap-error-drops": "packets",
    "lisp-encap-error-drops": "packets",
    "lisp-punt-drops": "packets",
    "multi-label-drops": "packets",
    "null-packets": "packets",
    "punt-unreachable-packets": "packets",
    "rp-destination-drop-packets": "packets",
    "rpf-check-failure-packets": "packets",
    "unresolved-prefix-packets": "packets",
    "unsupported-feature-packets": "packets",
    "active-routes-count": "routes",
    "backup-routes-count": "routes",
    "deleted-routes-count": "routes",
    "paths-count": "routes",
    "routes-counts": "routes",
}

# Core required headers that MUST exist in a valid Cisco telemetry CSV export
MANDATORY_COLUMNS: Set[str] = {"name", "time", "Producer"}

# Complete set of numeric metric columns from Cisco baseline and anomaly header definitions
NUMERIC_COLUMNS: List[str] = [
    "bytes-received",
    "bytes-sent",
    "packets-received",
    "packets-sent",
    "input-data-rate",
    "output-data-rate",
    "input-packet-rate",
    "output-packet-rate",
    "input-drops",
    "output-drops",
    "input-errors",
    "output-errors",
    "crc-errors",
    "bandwidth",
    "total-cpu-one-minute",
    "total-cpu-five-minute",
    "total-cpu-fifteen-minute",
    "free-physical-memory",
    "free-application-memory",
    "ram-memory",
    "system-ram-memory",
    "total-number-of-drop-packets",
    "no-route-packets",
    "discard-packets",
    "checksum-error-packets",
    "acl-in-rpf-packets",
    "df-unreachable-packets",
    "encapsulation-failure-packets",
    "fragmenation-consumed-packets",
    "fragmenation-failure-packets",
    "gre-error-drop",
    "gre-lookup-failed-drop",
    "incomplete-adjacency-packets",
    "lisp-decap-error-drops",
    "lisp-encap-error-drops",
    "lisp-punt-drops",
    "multi-label-drops",
    "null-packets",
    "punt-unreachable-packets",
    "rp-destination-drop-packets",
    "rpf-check-failure-packets",
    "unresolved-prefix-packets",
    "unsupported-feature-packets",
    "active-routes-count",
    "backup-routes-count",
    "deleted-routes-count",
    "paths-count",
    "routes-counts",
    "global__established-neighbors-count-total",
    "global__neighbors-count-total",
    "global__nexthop-count",
    "global__restart-count",
    "vrf__neighbors-count",
    "vrf__network-count",
    "vrf__path-count",
    "vrf__update-messages-received",
]


class CiscoTelemetryAdapter:
    """Ingests and validates Cisco Innovation Edge network telemetry CSV/CSV.GZ files."""

    def __init__(self, quarantine_manager: Optional[QuarantineManager] = None):
        self.quarantine_manager = quarantine_manager

    def parse_timestamp_nanos(self, time_raw: str) -> Tuple[Optional[str], Optional[str]]:
        """Parses nanosecond Unix epoch into an ISO 8601 UTC string.
        Returns (iso_timestamp, error_message).
        """
        if not time_raw or time_raw.strip() == "":
            return None, "Empty timestamp field"

        try:
            val = int(time_raw.strip())
            # Cisco timestamps are nanoseconds (18-19 digits, e.g. 1503019768316000000)
            if val > 1_000_000_000_000_000:
                seconds = val / 1_000_000_000.0
            elif val > 1_000_000_000_000:  # milliseconds
                seconds = val / 1_000.0
            else:  # seconds
                seconds = float(val)

            # Plausible epoch range: 2000-01-01 to 2100-01-01
            if seconds < 946684800 or seconds > 4102444800:
                return None, f"Timestamp value {val} out of plausible historical range"

            dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
            return dt.isoformat(), None
        except (ValueError, OverflowError) as e:
            return None, f"Unparseable numeric timestamp '{time_raw}': {str(e)}"

    def parse_numeric(self, val_raw: str) -> Tuple[Optional[float], Optional[str]]:
        """Validates and parses a numeric measurement string without mutating its numeric value."""
        if val_raw is None or val_raw.strip() == "":
            return None, "Empty numeric field"
        try:
            v = float(val_raw.strip())
            if math.isnan(v) or math.isinf(v):
                return None, f"NaN or Inf numeric value '{val_raw}'"
            return v, None
        except ValueError:
            return None, f"Could not parse '{val_raw}' as a numeric float"

    def read_rows(self, file_path: Path) -> Generator[Dict[str, str], None, None]:
        """Yields raw CSV row dictionaries from plain CSV or GZipped CSV files."""
        if file_path.suffix == ".gz":
            with gzip.open(file_path, "rt", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row
        else:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    yield row

    def ingest_file(
        self,
        file_path: Path,
        source_dataset: str,
        source_version: str,
        source_checksum: str,
        ingestion_id: str,
        scenario_id: Optional[str] = None,
        max_rows: Optional[int] = None,
        record_sink: Optional[Callable[[NormalizedObservation], None]] = None,
        max_issues_retained: int = 200,
    ) -> Tuple[List[NormalizedObservation], List[DataQualityIssue], int, int, int, int]:
        """Runs bounded validation and normalization on the source telemetry file.

        Returns:
            (normalized_records, issues, total_rows, accepted_rows, quarantined_rows, duplicate_rows)
        """
        normalized_records: List[NormalizedObservation] = []
        issues: List[DataQualityIssue] = []
        total_rows = 0
        accepted_rows = 0
        quarantined_rows = 0
        duplicate_rows = 0

        # Verify file is not empty
        if not file_path.exists() or file_path.stat().st_size == 0:
            issues.append(
                DataQualityIssue(
                    issue_id=f"iss-{uuid4().hex[:8]}",
                    severity="CRITICAL",
                    dataset_ref=source_dataset,
                    file_ref=str(file_path.name),
                    row_ref=0,
                    category="EMPTY_FILE",
                    description=f"Source file {file_path.name} is empty (0 bytes).",
                    disposition="REJECTED",
                )
            )
            return normalized_records, issues, 0, 0, 0, 0

        # Read first line / check header
        try:
            if file_path.suffix == ".gz":
                with gzip.open(file_path, "rt", encoding="utf-8", errors="replace") as f:
                    first_line = f.readline()
            else:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    first_line = f.readline()
        except Exception as e:
            issues.append(
                DataQualityIssue(
                    issue_id=f"iss-{uuid4().hex[:8]}",
                    severity="CRITICAL",
                    dataset_ref=source_dataset,
                    file_ref=str(file_path.name),
                    row_ref=0,
                    category="PARSE_FAILURE",
                    description=f"Failed to read file stream: {str(e)}",
                    disposition="REJECTED",
                )
            )
            return normalized_records, issues, 0, 0, 0, 0

        if not first_line.strip():
            issues.append(
                DataQualityIssue(
                    issue_id=f"iss-{uuid4().hex[:8]}",
                    severity="CRITICAL",
                    dataset_ref=source_dataset,
                    file_ref=str(file_path.name),
                    row_ref=0,
                    category="EMPTY_FILE",
                    description="File has no header line or contents.",
                    disposition="REJECTED",
                )
            )
            return normalized_records, issues, 0, 0, 0, 0

        reader_sample = csv.reader([first_line])
        headers = set(next(reader_sample, []))
        missing_mandatory = MANDATORY_COLUMNS - headers
        if missing_mandatory:
            issues.append(
                DataQualityIssue(
                    issue_id=f"iss-{uuid4().hex[:8]}",
                    severity="CRITICAL",
                    dataset_ref=source_dataset,
                    file_ref=str(file_path.name),
                    row_ref=1,
                    category="MISSING_REQUIRED_COLUMN",
                    description=f"Missing mandatory Cisco telemetry column(s): {sorted(list(missing_mandatory))}",
                    disposition="REJECTED",
                )
            )
            return normalized_records, issues, 0, 0, 0, 0

        # Track duplicates and monotonicity
        seen_events: Set[Tuple[str, str, str, str]] = set()
        last_entity_timestamp: Dict[str, float] = {}

        def record_issue(issue: DataQualityIssue):
            if len(issues) < max_issues_retained:
                issues.append(issue)

        row_idx = 1
        for row in self.read_rows(file_path):
            row_idx += 1
            total_rows += 1

            if max_rows and total_rows > max_rows:
                break

            producer = row.get("Producer", "").strip()
            time_raw = row.get("time", "").strip()
            name = row.get("name", "").strip()
            iface = row.get("interface-name", "").strip()
            node = row.get("node-name", "").strip()

            # Determine entity type and ID
            if iface:
                entity_type = "interface"
                entity_id = iface
            elif node:
                entity_type = "node"
                entity_id = node
            elif producer:
                entity_type = "device"
                entity_id = producer
            else:
                entity_type = "unknown"
                entity_id = "unknown"

            # Parse and validate timestamp
            ts_iso, ts_err = self.parse_timestamp_nanos(time_raw)
            if ts_err:
                record_issue(
                    DataQualityIssue(
                        issue_id=f"iss-{uuid4().hex[:8]}",
                        severity="WARNING",
                        dataset_ref=source_dataset,
                        file_ref=str(file_path.name),
                        row_ref=row_idx,
                        category="TIMESTAMP_PARSING_FAILURE",
                        description=f"Row {row_idx}: {ts_err}",
                        disposition="ACCEPTED_WITH_WARNING",
                    )
                )

            # Monotonicity check
            if ts_iso and time_raw.isdigit():
                current_sec = float(time_raw) / (1e9 if len(time_raw) > 15 else 1.0)
                stream_key = f"{producer}:{entity_id}"
                if stream_key in last_entity_timestamp:
                    if current_sec < last_entity_timestamp[stream_key]:
                        record_issue(
                            DataQualityIssue(
                                issue_id=f"iss-{uuid4().hex[:8]}",
                                severity="WARNING",
                                dataset_ref=source_dataset,
                                file_ref=str(file_path.name),
                                row_ref=row_idx,
                                category="MONOTONICITY_VIOLATION",
                                description=f"Row {row_idx}: Timestamp {current_sec} is out of order for stream '{stream_key}'",
                                disposition="ACCEPTED_WITH_WARNING",
                            )
                        )
                last_entity_timestamp[stream_key] = current_sec

            # Duplicate event check
            event_sig = (producer, time_raw, name, iface)
            if event_sig in seen_events:
                duplicate_rows += 1
                record_issue(
                    DataQualityIssue(
                        issue_id=f"iss-{uuid4().hex[:8]}",
                        severity="WARNING",
                        dataset_ref=source_dataset,
                        file_ref=str(file_path.name),
                        row_ref=row_idx,
                        category="DUPLICATE_RECORD",
                        description=f"Row {row_idx}: Duplicate event telemetry key {event_sig}",
                        disposition="ACCEPTED_WITH_WARNING",
                    )
                )
            else:
                seen_events.add(event_sig)

            # Extract numeric metrics
            row_normalized_count = 0
            row_has_quarantine = False

            for col in NUMERIC_COLUMNS:
                if col in row and row[col].strip() != "":
                    raw_str = row[col].strip()
                    val, num_err = self.parse_numeric(raw_str)
                    if num_err:
                        record_issue(
                            DataQualityIssue(
                                issue_id=f"iss-{uuid4().hex[:8]}",
                                severity="CRITICAL",
                                dataset_ref=source_dataset,
                                file_ref=str(file_path.name),
                                row_ref=row_idx,
                                category="NUMERIC_PARSING_FAILURE",
                                description=f"Row {row_idx}, column '{col}': {num_err}",
                                disposition="QUARANTINED",
                            )
                        )
                        if self.quarantine_manager:
                            self.quarantine_manager.record_quarantine(
                                ingestion_id=ingestion_id,
                                row_index=row_idx,
                                raw_row=row,
                                category="NUMERIC_PARSING_FAILURE",
                                reason=f"Column '{col}' failed numeric parsing: {num_err}",
                            )
                        row_has_quarantine = True
                        break

                    unit = CISCO_METRIC_UNITS.get(col, None)
                    obs = NormalizedObservation(
                        observation_id=f"obs-{uuid4().hex[:12]}",
                        source_dataset=source_dataset,
                        source_version=source_version,
                        scenario_id=scenario_id,
                        timestamp=ts_iso,
                        data_mode=DataMode.PUBLIC_DATA,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        metric_name=col,
                        value=val,
                        unit=unit,
                        quality_status="VALID" if not ts_err else "SUSPECT",
                        provenance={
                            "source_file": file_path.name,
                            "source_row_index": row_idx,
                            "source_checksum": source_checksum,
                            "raw_timestamp": time_raw,
                            "ingestion_id": ingestion_id,
                        },
                        measurement_uncertainty=None,
                    )
                    if record_sink:
                        record_sink(obs)
                    else:
                        normalized_records.append(obs)
                    row_normalized_count += 1

            if row_has_quarantine:
                quarantined_rows += 1
            elif row_normalized_count > 0:
                accepted_rows += 1

        return (
            normalized_records,
            issues,
            total_rows,
            accepted_rows,
            quarantined_rows,
            duplicate_rows,
        )
