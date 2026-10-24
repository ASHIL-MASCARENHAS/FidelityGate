from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from ..ingestion.models import DataMode


class FindingSeverity(str, Enum):
    """Transparent triage severity classification."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class FindingStatus(str, Enum):
    """Investigation disposition status."""
    CANDIDATE = "CANDIDATE"
    CONFIRMED = "CONFIRMED"
    SUPPRESSED = "SUPPRESSED"
    RESOLVED = "RESOLVED"


class LabelOrigin(str, Enum):
    """Rigorous attribution of anomaly label provenance."""
    SOURCE_DEFINED = "SOURCE_DEFINED"
    RULE_BASED = "RULE_BASED"
    STATISTICAL_DETECTOR = "STATISTICAL_DETECTOR"
    SYNTHETIC_INJECTED_FAULT = "SYNTHETIC_INJECTED_FAULT"
    UNKNOWN = "UNKNOWN"


class EvidenceType(str, Enum):
    """Taxonomy of evidence records supporting a triage finding."""
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    DERIVED_RATE = "DERIVED_RATE"
    SOURCE_EVENT_CASE = "SOURCE_EVENT_CASE"
    BASELINE_WINDOW = "BASELINE_WINDOW"


class EvidenceItem(BaseModel):
    """Immutable evidence reference linked to an underlying telemetry observation or case file."""
    model_config = ConfigDict(frozen=True)

    evidence_id: str
    source_dataset: str
    source_version: str
    source_file: str
    source_row_or_event_reference: Any
    timestamp: Optional[str] = None
    entity_type: str
    entity_id: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    quality_status: str
    evidence_type: EvidenceType
    transformation: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)


class AnomalyFinding(BaseModel):
    """Individual candidate network anomaly identified by deterministic triage."""
    model_config = ConfigDict(frozen=True)

    anomaly_id: str
    triage_run_id: str
    source_dataset: str
    source_version: str
    scenario_id: Optional[str] = None
    entity_type: str
    entity_id: str
    metric_name: str
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    detector_name: str
    detector_version: str
    observed_value: float
    baseline_value: Optional[float] = None
    deviation_score: Optional[float] = None
    severity: FindingSeverity
    confidence: float = Field(ge=0.0, le=1.0, description="Justified belief in anomaly validity, strictly separate from severity")
    label_origin: LabelOrigin
    status: FindingStatus = FindingStatus.CANDIDATE
    evidence_ids: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)


class CorrelationReport(BaseModel):
    """Deterministic relational mapping between findings, devices, and observed telemetry spans."""
    model_config = ConfigDict(frozen=True)

    correlation_id: str
    triage_run_id: str
    time_window: Dict[str, Optional[str]]
    affected_entities: List[str]
    finding_ids: List[str]
    evidence_ids: List[str]
    supported_relationships: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Candidate relational links using non-causal descriptors ('temporally_associated', 'co_occurring')"
    )
    unresolved_questions: List[str] = Field(default_factory=list)
    data_quality_warnings: List[str] = Field(default_factory=list)
    correlation_method: str = "DETERMINISTIC_TEMPORAL_AND_ENTITY_GRAPH"
    limitations: List[str] = Field(default_factory=list)


class InvestigationContext(BaseModel):
    """Compact, typed investigation payload consumed by future Layer 3 Anomaly Investigator agents."""
    model_config = ConfigDict(frozen=True)

    triage_run_id: str
    source_dataset: str
    source_version: str
    scenario_id: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    primary_anomaly_candidates: List[AnomalyFinding]
    correlated_evidence: List[EvidenceItem]
    baseline_comparisons: List[Dict[str, Any]] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradictory_evidence_ids: List[str] = Field(default_factory=list)
    source_defined_event_metadata: Optional[Dict[str, Any]] = None
    data_quality_warnings: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    recommended_diagnostic_categories: List[str] = Field(default_factory=list)
    explicitly_unavailable_information: List[str] = Field(default_factory=list)


class TriageRunRequest(BaseModel):
    """Request payload to initiate deterministic anomaly triage."""
    ingestion_id: Optional[str] = Field(default=None, description="Ingestion run ID whose processed observations are evaluated")
    source_id: str = Field(default="cisco-ie-telemetry", description="Approved registered source identifier")
    dataset_version: str = Field(default="master", description="Dataset version tag or commit SHA")
    case_file: Optional[str] = Field(default=None, description="Optional relative path to case metadata file (e.g. casedata.txt)")
    scenario_id: Optional[str] = Field(default=None, description="Optional target scenario association")
    metrics_filter: Optional[List[str]] = Field(default=None, description="Restrict analysis to specific metric names")
    entities_filter: Optional[List[str]] = Field(default=None, description="Restrict analysis to specific entities")
    z_threshold: float = Field(default=3.5, gt=0, description="Robust MAD deviation score threshold")
    min_samples: int = Field(default=5, ge=3, description="Minimum sample count required to compute baseline statistics")
    max_context_evidence: int = Field(default=50, ge=1, le=500, description="Upper bound on evidence items returned in context")


class TriageRunSummary(BaseModel):
    """Execution summary of an anomaly triage run."""
    model_config = ConfigDict(frozen=True)

    triage_run_id: str
    ingestion_id: str
    source_dataset: str
    started_at: str
    completed_at: str
    total_observations_scanned: int
    findings_count: int
    evidence_items_count: int
    status: str
    highest_severity: FindingSeverity

