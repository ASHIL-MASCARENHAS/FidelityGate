from enum import Enum
from pydantic import BaseModel, ConfigDict, Field


class GateDecision(str, Enum):
    ACCEPT = "ACCEPT"
    GATHER_EVIDENCE = "GATHER_EVIDENCE"
    ABSTAIN = "ABSTAIN"


class Scenario(BaseModel):
    model_config = ConfigDict(frozen=True)
    scenario_id: str
    name: str
    description: str
    nominal_latency_ms: float = Field(gt=0)
    capacity_mbps: float = Field(gt=0)
    offered_load_mbps: float = Field(gt=0)
    slo_latency_ms: float = Field(gt=0)
    latency_multiplier_min: float = Field(default=0.85, gt=0)
    latency_multiplier_max: float = Field(default=1.35, gt=0)
    stability_threshold: float = Field(default=0.90, ge=0, le=1)


class SweepReport(BaseModel):
    evaluations: int
    nominal_latency_ms: float
    worst_latency_ms: float
    peak_utilization: float
    stability_score: float
    violations: int
    sensitivity: dict[str, float]


class GateReport(BaseModel):
    decision: GateDecision
    reason: str
    report: SweepReport


# Re-export Layer 1 ingestion models for central domain schema access
from .ingestion.models import (
    DataMode,
    DatasetSourceManifest,
    RawObservation,
    NormalizedObservation,
    DataQualityIssue,
    IngestionReport,
    IngestionRequest,
    IngestionSummary,
)

# Re-export Layer 2 triage models for central domain schema access
from .triage.models import (
    FindingSeverity,
    FindingStatus,
    LabelOrigin,
    EvidenceType,
    EvidenceItem,
    AnomalyFinding,
    CorrelationReport,
    InvestigationContext,
    TriageRunRequest,
    TriageRunSummary,
)

# Re-export Layer 3 investigation models for central domain schema access
from .investigation.models import (
    AgentMode,
    DiagnosticCandidate,
    DiagnosticPlan,
    Hypothesis,
    HypothesisType,
    InvestigationEvent,
    InvestigationReport,
    InvestigationRequest,
    InvestigationStatus,
    InvestigationSummary,
    PlanStatus,
)


