from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DataMode(str, Enum):
    """Explicit taxonomy of data provenance and fidelity boundaries."""
    PUBLIC_DATA = "PUBLIC_DATA"
    REPLAY = "REPLAY"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    SYNTHETIC_FAULT_INJECTION = "SYNTHETIC_FAULT_INJECTION"
    SIMULATED = "SIMULATED"
    UNKNOWN = "UNKNOWN"


class DatasetSourceManifest(BaseModel):
    """Metadata describing an approved, documented dataset source."""
    model_config = ConfigDict(frozen=True)

    source_id: str = Field(..., description="Stable unique identifier for the dataset source")
    name: str = Field(..., description="Human-readable dataset title")
    source_url: str = Field(..., description="Canonical public repository or download URL")
    publication_reference: str = Field(..., description="Academic or industry publication reference")
    dataset_version: str = Field(..., description="Version tag or Git commit SHA")
    license: str = Field(..., description="Explicit verified license identifier (e.g. CDLA-Permissive-1.0)")
    attribution: str = Field(..., description="Attribution text required by the data license")
    download_timestamp: Optional[str] = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 UTC timestamp of acquisition"
    )
    source_format: str = Field(..., description="Raw format, e.g. CSV, CSV.GZ, PCAP")
    raw_file_path: str = Field(..., description="Relative file path within the approved DATA_ROOT")
    sha256_checksum: str = Field(..., description="Hexadecimal SHA-256 digest of the downloaded file")
    description: str = Field(..., description="Dataset scope and recording conditions")
    limitations: List[str] = Field(
        default_factory=list,
        description="Explicit documentation of missing fields, units, or topology omissions"
    )


class RawObservation(BaseModel):
    """Unaltered raw observation as captured directly from the source."""
    model_config = ConfigDict(frozen=True)

    raw_record_id: str
    source_dataset: str
    source_file: str
    source_row_index: int
    original_timestamp: Optional[str] = None
    original_field_name: str
    original_value: str
    original_unit: Optional[str] = None


class NormalizedObservation(BaseModel):
    """Standardized observation conforming to canonical FidelityGate telemetry contract."""
    model_config = ConfigDict(frozen=True)

    observation_id: str
    source_dataset: str
    source_version: str
    scenario_id: Optional[str] = None
    timestamp: Optional[str] = None  # Validated ISO 8601 UTC string or None if unparseable/missing
    data_mode: DataMode = DataMode.PUBLIC_DATA
    entity_type: str = Field(..., description="'interface', 'node', 'device', or 'unknown'")
    entity_id: str = Field(..., description="Target entity identifier or 'unknown'")
    metric_name: str = Field(..., description="Canonical metric identifier")
    value: float = Field(..., description="Parsed numeric measurement value")
    unit: Optional[str] = Field(default=None, description="Documented physical unit; None if undocumented")
    quality_status: str = Field(default="VALID", description="'VALID', 'SUSPECT', 'QUARANTINED', 'UNKNOWN'")
    provenance: Dict[str, Any] = Field(
        default_factory=dict,
        description="Row and file lineage: source file, row index, source checksum, ingestion ID"
    )
    measurement_uncertainty: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Only populated when defined by an explicit measurement model or sensor spec"
    )


class DataQualityIssue(BaseModel):
    """Reported anomaly, formatting defect, or schema violation encountered during ingestion."""
    model_config = ConfigDict(frozen=True)

    issue_id: str
    severity: str = Field(..., description="'CRITICAL', 'WARNING', or 'INFO'")
    dataset_ref: str
    file_ref: str
    row_ref: Optional[int] = None
    category: str = Field(
        ...,
        description="'MISSING_REQUIRED_COLUMN', 'TIMESTAMP_PARSING_FAILURE', 'NUMERIC_PARSING_FAILURE', "
                    "'DUPLICATE_RECORD', 'INVALID_UNIT', 'UNKNOWN_ENTITY', 'UNSAFE_PATH', 'EMPTY_FILE', "
                    "'SCHEMA_VERSION_MISMATCH', 'MONOTONICITY_VIOLATION'"
    )
    description: str
    disposition: str = Field(..., description="'REJECTED', 'QUARANTINED', or 'ACCEPTED_WITH_WARNING'")


class IngestionReport(BaseModel):
    """Comprehensive, deterministic audit record produced at completion of an ingestion run."""
    model_config = ConfigDict(frozen=True)

    ingestion_id: str
    dataset_id: str
    dataset_version: str
    started_at: str
    completed_at: str
    source_file: str
    source_checksum: str
    source_row_count: int
    accepted_count: int
    rejected_count: int
    quarantined_count: int
    duplicate_count: int
    missing_or_invalid_count: int
    quality_issues: List[DataQualityIssue] = Field(default_factory=list)
    output_artifacts: Dict[str, str] = Field(
        default_factory=dict,
        description="File paths to normalized data, manifest, report, and quarantine store"
    )
    status: str = Field(..., description="'SUCCESS', 'PARTIAL_SUCCESS', or 'FAILED'")
    errors_or_limitations: List[str] = Field(default_factory=list)


class IngestionRequest(BaseModel):
    """Request payload to initiate dataset ingestion."""
    source_id: str = Field(default="cisco-ie-telemetry", description="Registered source identifier")
    relative_path: str = Field(..., description="File path relative to DATA_ROOT/raw")
    dataset_version: str = Field(default="master", description="Source commit or version tag")
    scenario_id: Optional[str] = Field(default=None, description="Optional target scenario association")
    force_reingest: bool = Field(default=False, description="Bypass idempotency cache if True")


class IngestionSummary(BaseModel):
    """High-level summary of an ingestion run for listing/querying."""
    model_config = ConfigDict(frozen=True)

    ingestion_id: str
    dataset_id: str
    status: str
    source_file: str
    source_checksum: str
    source_row_count: int
    accepted_count: int
    quarantined_count: int
    started_at: str
    completed_at: str

