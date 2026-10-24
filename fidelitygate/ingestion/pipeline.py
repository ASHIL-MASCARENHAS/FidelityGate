import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from uuid import uuid4

from ..config import settings
from ..storage import StorageEngine
from .cisco_adapter import CiscoTelemetryAdapter
from .models import (
    DataMode,
    DataQualityIssue,
    DatasetSourceManifest,
    IngestionReport,
    IngestionRequest,
    NormalizedObservation,
)
from .quarantine import QuarantineManager


class IngestionSecurityError(Exception):
    """Raised when an unapproved or unsafe file path is requested."""
    pass


class IngestionPipeline:
    """Deterministic, bounded data ingestion and normalization pipeline for FidelityGate."""

    def __init__(self, storage: Optional[StorageEngine] = None):
        self.storage = storage or StorageEngine(settings.DATABASE_PATH)
        self.quarantine_manager = QuarantineManager(settings.quarantine_path)
        self.cisco_adapter = CiscoTelemetryAdapter(self.quarantine_manager)

    def compute_sha256(self, file_path: Path) -> str:
        """Calculates SHA-256 checksum of the local file in chunks."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def resolve_safe_path(self, relative_path: str) -> Path:
        """Enforces that file paths are bounded strictly within approved data directories.
        Rejects directory traversal (..) and absolute path escapes.
        """
        # Clean relative path string
        rel_str = str(relative_path).strip().replace("\\", "/")
        if rel_str.startswith("/") or ".." in rel_str.split("/"):
            raise IngestionSecurityError(
                f"Security violation: path '{relative_path}' contains forbidden directory traversal or absolute roots."
            )

        # Allow resolution inside raw_data_path or project root test fixtures
        candidate_raw = (settings.raw_data_path / rel_str).resolve()
        candidate_direct = (Path.cwd() / rel_str).resolve()

        # Check bounds
        raw_root = settings.raw_data_path.resolve()
        cwd_root = Path.cwd().resolve()

        if candidate_raw.is_relative_to(raw_root) and candidate_raw.exists():
            return candidate_raw
        elif candidate_direct.is_relative_to(cwd_root) and candidate_direct.exists():
            return candidate_direct
        else:
            raise FileNotFoundError(
                f"File not found within approved storage boundaries: '{relative_path}'"
            )

    def run_ingestion(self, request: IngestionRequest) -> IngestionReport:
        """Executes the full bounded ingestion pipeline."""
        started_at = datetime.now(timezone.utc).isoformat()
        ingestion_id = f"ing-{uuid4().hex[:8]}"

        # 1. Resolve safe path
        try:
            target_path = self.resolve_safe_path(request.relative_path)
        except IngestionSecurityError as sec_err:
            failed_report = IngestionReport(
                ingestion_id=ingestion_id,
                dataset_id=request.source_id,
                dataset_version=request.dataset_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                source_file=request.relative_path,
                source_checksum="NONE",
                source_row_count=0,
                accepted_count=0,
                rejected_count=0,
                quarantined_count=0,
                duplicate_count=0,
                missing_or_invalid_count=1,
                quality_issues=[
                    DataQualityIssue(
                        issue_id=f"iss-{uuid4().hex[:8]}",
                        severity="CRITICAL",
                        dataset_ref=request.source_id,
                        file_ref=request.relative_path,
                        row_ref=None,
                        category="UNSAFE_PATH",
                        description=str(sec_err),
                        disposition="REJECTED",
                    )
                ],
                output_artifacts={},
                status="FAILED",
                errors_or_limitations=[str(sec_err)],
            )
            self.storage.save_ingestion_report(failed_report)
            return failed_report
        except FileNotFoundError as fnf_err:
            failed_report = IngestionReport(
                ingestion_id=ingestion_id,
                dataset_id=request.source_id,
                dataset_version=request.dataset_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                source_file=request.relative_path,
                source_checksum="NONE",
                source_row_count=0,
                accepted_count=0,
                rejected_count=0,
                quarantined_count=0,
                duplicate_count=0,
                missing_or_invalid_count=1,
                quality_issues=[
                    DataQualityIssue(
                        issue_id=f"iss-{uuid4().hex[:8]}",
                        severity="CRITICAL",
                        dataset_ref=request.source_id,
                        file_ref=request.relative_path,
                        row_ref=None,
                        category="FILE_NOT_FOUND",
                        description=str(fnf_err),
                        disposition="REJECTED",
                    )
                ],
                output_artifacts={},
                status="FAILED",
                errors_or_limitations=[str(fnf_err)],
            )
            self.storage.save_ingestion_report(failed_report)
            return failed_report

        # 2. Checksum and size verification
        checksum = self.compute_sha256(target_path)
        size_mb = target_path.stat().st_size / (1024 * 1024)
        if size_mb > settings.MAX_FILE_SIZE_MB:
            failed_report = IngestionReport(
                ingestion_id=ingestion_id,
                dataset_id=request.source_id,
                dataset_version=request.dataset_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                source_file=target_path.name,
                source_checksum=checksum,
                source_row_count=0,
                accepted_count=0,
                rejected_count=0,
                quarantined_count=0,
                duplicate_count=0,
                missing_or_invalid_count=1,
                quality_issues=[
                    DataQualityIssue(
                        issue_id=f"iss-{uuid4().hex[:8]}",
                        severity="CRITICAL",
                        dataset_ref=request.source_id,
                        file_ref=target_path.name,
                        row_ref=None,
                        category="FILE_TOO_LARGE",
                        description=f"File size {size_mb:.2f} MB exceeds maximum limit {settings.MAX_FILE_SIZE_MB} MB",
                        disposition="REJECTED",
                    )
                ],
                output_artifacts={},
                status="FAILED",
                errors_or_limitations=["File exceeds configured size limit"],
            )
            self.storage.save_ingestion_report(failed_report)
            return failed_report

        # 3. Idempotency Check
        if not request.force_reingest:
            existing_report = self.storage.find_ingestion_by_checksum_and_version(
                checksum, request.dataset_version
            )
            if existing_report:
                return existing_report

        # 4. Ingest via Adapter and stream to processed artifact
        output_artifacts: Dict[str, str] = {}
        processed_file = settings.processed_data_path / f"{ingestion_id}_normalized.jsonl"
        accepted_records_count = 0

        if request.source_id.lower().startswith("cisco"):
            with open(processed_file, "w", encoding="utf-8") as f_out:
                def write_sink(obs: NormalizedObservation):
                    nonlocal accepted_records_count
                    accepted_records_count += 1
                    f_out.write(obs.model_dump_json() + "\n")

                (
                    _,
                    issues,
                    total_rows,
                    accepted_rows,
                    quarantined_rows,
                    duplicate_rows,
                ) = self.cisco_adapter.ingest_file(
                    file_path=target_path,
                    source_dataset=request.source_id,
                    source_version=request.dataset_version,
                    source_checksum=checksum,
                    ingestion_id=ingestion_id,
                    scenario_id=request.scenario_id,
                    record_sink=write_sink,
                )
        else:
            # Unsupported source adapter
            failed_report = IngestionReport(
                ingestion_id=ingestion_id,
                dataset_id=request.source_id,
                dataset_version=request.dataset_version,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc).isoformat(),
                source_file=target_path.name,
                source_checksum=checksum,
                source_row_count=0,
                accepted_count=0,
                rejected_count=0,
                quarantined_count=0,
                duplicate_count=0,
                missing_or_invalid_count=1,
                quality_issues=[
                    DataQualityIssue(
                        issue_id=f"iss-{uuid4().hex[:8]}",
                        severity="CRITICAL",
                        dataset_ref=request.source_id,
                        file_ref=target_path.name,
                        row_ref=None,
                        category="UNSUPPORTED_ADAPTER",
                        description=f"No adapter available for source_id '{request.source_id}'",
                        disposition="REJECTED",
                    )
                ],
                output_artifacts={},
                status="FAILED",
                errors_or_limitations=[f"Unsupported source_id '{request.source_id}'"],
            )
            self.storage.save_ingestion_report(failed_report)
            return failed_report

        # 5. Record artifact references
        output_artifacts["processed_observations"] = str(processed_file.resolve())

        quarantine_file = self.quarantine_manager.get_quarantine_path(ingestion_id)
        if quarantine_file.exists():
            output_artifacts["quarantine_store"] = str(quarantine_file.resolve())

        # 6. Build Manifest
        manifest = DatasetSourceManifest(
            source_id=request.source_id,
            name="Cisco Innovation Edge Network Telemetry",
            source_url="https://github.com/cisco-ie/telemetry",
            publication_reference="ACM SIGCOMM BigDama'18 / IEEE INFOCOM'18",
            dataset_version=request.dataset_version,
            license="CDLA-Permissive-1.0",
            attribution="Cisco Systems, Inc. (Community Data License Agreement – Permissive – Version 1.0)",
            download_timestamp=datetime.now(timezone.utc).isoformat(),
            source_format="CSV",
            raw_file_path=str(target_path.relative_to(settings.data_root_path))
            if target_path.is_relative_to(settings.data_root_path)
            else str(target_path.name),
            sha256_checksum=checksum,
            description="Interface counters, drop stats, CPU, and route statistics from real-world Cisco IOS-XR lab runs.",
            limitations=[
                "Does not contain topology or link capacity definitions directly in telemetry CSV.",
                "Does not include post-intervention reroute outcomes or synthetic measurement-error envelopes.",
                "Units are preserved as documented; unverified units are kept explicitly null.",
            ],
        )
        self.storage.save_manifest(manifest)
        manifest_file = settings.manifests_path / f"{request.source_id}_manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))
        output_artifacts["manifest"] = str(manifest_file.resolve())

        # 7. Evaluate Status & Compile Report
        critical_issues = [i for i in issues if i.severity == "CRITICAL"]
        if total_rows == 0 or (accepted_records_count == 0 and len(critical_issues) > 0):
            overall_status = "FAILED"
        elif quarantined_rows > 0 or len(issues) > 0:
            overall_status = "PARTIAL_SUCCESS"
        else:
            overall_status = "SUCCESS"

        report = IngestionReport(
            ingestion_id=ingestion_id,
            dataset_id=request.source_id,
            dataset_version=request.dataset_version,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
            source_file=target_path.name,
            source_checksum=checksum,
            source_row_count=total_rows,
            accepted_count=accepted_records_count,
            rejected_count=total_rows - accepted_rows - quarantined_rows,
            quarantined_count=quarantined_rows,
            duplicate_count=duplicate_rows,
            missing_or_invalid_count=len(issues),
            quality_issues=issues,
            output_artifacts=output_artifacts,
            status=overall_status,
            errors_or_limitations=manifest.limitations,
        )

        # Save Report to SQLite and Disk
        self.storage.save_ingestion_report(report)
        report_file = settings.reports_path / f"{ingestion_id}_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report.model_dump_json(indent=2))
        output_artifacts["report"] = str(report_file.resolve())

        return report
