from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

from ..triage.models import AnomalyFinding, EvidenceItem, FindingSeverity, LabelOrigin


class AgentMode(str, Enum):
    """Execution provenance mode for agent decisions."""
    LIVE_LLM_AGENT = "LIVE_LLM_AGENT"
    DETERMINISTIC_PLANNER = "DETERMINISTIC_PLANNER"
    DETERMINISTIC_BASELINE = "DETERMINISTIC_BASELINE"


class InvestigationStatus(str, Enum):
    """Investigation lifecycle state."""
    INITIALIZED = "INITIALIZED"
    INVESTIGATING = "INVESTIGATING"
    COMPLETED = "COMPLETED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"


class HypothesisType(str, Enum):
    """Classified operational network hypothesis category."""
    FORWARDING_DROP_SURGE = "FORWARDING_DROP_SURGE"
    BGP_SESSION_FLAP = "BGP_SESSION_FLAP"
    BUFFER_CONGESTION = "BUFFER_CONGESTION"
    CONTROL_PLANE_CPU_SPIKE = "CONTROL_PLANE_CPU_SPIKE"
    UNCONFIRMED_ANOMALY = "UNCONFIRMED_ANOMALY"


class Hypothesis(BaseModel):
    """Evidence-supported operational hypothesis formulated by Agent A."""
    model_config = ConfigDict(frozen=True)

    hypothesis_id: str = Field(..., description="Unique hypothesis identifier")
    statement: str = Field(..., description="Operational explanation using non-causal descriptors")
    hypothesis_type: HypothesisType
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradictory_evidence_ids: List[str] = Field(default_factory=list)
    uncertainty_status: str = Field(..., description="Explicit characterization of certainty or evidence gaps")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Epistemic confidence decoupled from severity")
    label_origin: LabelOrigin = Field(default=LabelOrigin.STATISTICAL_DETECTOR)
    limitations: List[str] = Field(default_factory=list)


class InvestigationReport(BaseModel):
    """Structured report produced by Agent A (Anomaly Investigator)."""
    model_config = ConfigDict(frozen=True)

    investigation_id: str
    triage_run_id: str
    scenario_id: Optional[str] = None
    agent_mode: AgentMode
    primary_finding_ids: List[str] = Field(default_factory=list)
    hypotheses: List[Hypothesis] = Field(default_factory=list)
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    contradictory_evidence_ids: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    data_quality_warnings: List[str] = Field(default_factory=list)
    suggested_diagnostic_categories: List[str] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)
    status: InvestigationStatus
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DiagnosticCandidate(BaseModel):
    """Permitted diagnostic candidate evaluated by Agent B."""
    model_config = ConfigDict(frozen=True)

    diagnostic_id: str = Field(..., description="Unique candidate ID matching allowlisted catalog")
    tool_name: str
    target_entity: str = Field(..., description="Device or interface under investigation")
    target_parameter: str = Field(..., description="Specific uncertain physical parameter")
    purpose: str = Field(..., description="Targeted rationale for resolving uncertainty")
    related_finding_ids: List[str] = Field(default_factory=list)
    related_evidence_ids: List[str] = Field(default_factory=list)
    expected_information_type: str = Field(..., description="Metric or variance bound expected")
    estimated_cost_usd: float = Field(default=0.0, ge=0.0)
    availability_status: str = "AVAILABLE"
    rank: int = Field(default=1, ge=1)


class PlanStatus(str, Enum):
    """Diagnostic plan disposition status."""
    READY = "READY"
    NO_USEFUL_DIAGNOSTIC = "NO_USEFUL_DIAGNOSTIC"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    FAILED = "FAILED"


class DiagnosticPlan(BaseModel):
    """Actionable diagnostic and candidate mitigation plan produced by Agent B."""
    model_config = ConfigDict(frozen=True)

    plan_id: str
    investigation_id: str
    candidate_diagnostics: List[DiagnosticCandidate] = Field(default_factory=list)
    selected_diagnostic_id: Optional[str] = None
    proposed_interventions: List[str] = Field(
        default_factory=list,
        description="Candidate reroute options for subsequent digital-twin simulation"
    )
    stop_conditions: List[str] = Field(default_factory=list)
    budget_remaining: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)
    status: PlanStatus
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InvestigationEvent(BaseModel):
    """Audit log entry capturing state transitions, tool invocations, and agent handoffs."""
    model_config = ConfigDict(frozen=True)

    event_id: str
    investigation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    actor: str
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)


class InvestigationRequest(BaseModel):
    """Request payload to initiate agentic investigation and diagnostic planning."""
    triage_run_id: str = Field(..., description="Target Layer 2 triage run ID")
    scenario_id: Optional[str] = Field(default=None, description="Optional network scenario context")
    agent_mode: Optional[AgentMode] = Field(
        default=None,
        description="Override execution mode (default: auto-detect live LLM or fallback)"
    )
    max_hypotheses: int = Field(default=3, ge=1, le=10)
    max_diagnostics: int = Field(default=3, ge=1, le=5)


class InvestigationSummary(BaseModel):
    """High-level summary of an investigation lifecycle."""
    model_config = ConfigDict(frozen=True)

    investigation_id: str
    triage_run_id: str
    scenario_id: Optional[str] = None
    agent_mode: AgentMode
    status: InvestigationStatus
    hypotheses_count: int
    candidate_diagnostics_count: int
    selected_diagnostic_id: Optional[str] = None
    created_at: str
    completed_at: Optional[str] = None
    fallback_reason: Optional[str] = None

