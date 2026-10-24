"""fidelitygate/workflow/models.py
Strongly typed data contracts for Layer 7: End-to-End Workflow Orchestration,
Human Approval Boundary, Isolated Simulated Action Execution, and Pre/Post Intervention Outcome Reporting.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from fidelitygate.evaluation.models import GateDecision


class WorkflowStage(str, Enum):
    """Execution stages of the FidelityGate end-to-end decision workflow."""
    RECEIVED = "RECEIVED"
    VALIDATING = "VALIDATING"
    TRIAGE = "TRIAGE"
    INVESTIGATION = "INVESTIGATION"
    CANDIDATE_EVALUATION = "CANDIDATE_EVALUATION"
    COUNTEREXAMPLE_ANALYSIS = "COUNTEREXAMPLE_ANALYSIS"
    ADAPTIVE_DIAGNOSTICS = "ADAPTIVE_DIAGNOSTICS"
    REEVALUATION = "REEVALUATION"
    EXPLANATION = "EXPLANATION"
    GATE_REVIEW = "GATE_REVIEW"
    AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"
    SIMULATED_ACTION = "SIMULATED_ACTION"
    OUTCOME_REPORTED = "OUTCOME_REPORTED"


class WorkflowStatus(str, Enum):
    """High-level lifecycle status of a workflow run."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    COMPLETED = "COMPLETED"
    ABSTAINED = "ABSTAINED"
    NEEDS_OPERATOR_INPUT = "NEEDS_OPERATOR_INPUT"
    REJECTED_BY_HUMAN = "REJECTED_BY_HUMAN"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    FAILED = "FAILED"
    TIMED_OUT = "TIMED_OUT"
    CANCELLED = "CANCELLED"


class ApprovalDecision(str, Enum):
    """Human-in-the-loop decision options."""
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"


class OverallImpact(str, Enum):
    """Categorical evaluation of post-action network impact."""
    IMPROVED = "IMPROVED"
    REGRESSED = "REGRESSED"
    MIXED = "MIXED"
    UNCHANGED = "UNCHANGED"
    DEGRADED = "DEGRADED"
    NEUTRAL = "NEUTRAL"


class WorkflowEvent(BaseModel):
    """Monotonically sequenced audit event recorded during workflow execution."""
    model_config = ConfigDict(frozen=True)

    event_id: str
    workflow_run_id: str
    sequence_number: int
    stage: WorkflowStage
    event_type: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    input_artifact_refs: List[str] = Field(default_factory=list)
    output_artifact_refs: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class HumanApprovalRecord(BaseModel):
    """Authoritative audit record of human authorization or rejection."""
    model_config = ConfigDict(frozen=True)

    approval_id: str
    workflow_run_id: str
    candidate_id: str
    gate_verdict: GateDecision
    explanation_id: str
    evidence_version: str
    decision: ApprovalDecision
    reviewer_id: str
    reviewer_comment: Optional[str] = None
    is_stale: bool = False
    idempotency_key: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class SimulatedInterventionRecord(BaseModel):
    """Record of an intervention executed inside the isolated digital-twin simulator."""
    model_config = ConfigDict(frozen=True)

    execution_id: str
    workflow_run_id: str
    approval_id: str
    candidate_id: str
    action_type: str = "REROUTE_FLOW"
    target_flow_id: str
    applied_path: List[str]
    execution_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    simulator_mode: str = "ISOLATED_DIGITAL_TWIN"
    status: str = "SUCCESS"
    notes: List[str] = Field(default_factory=list)


class InterventionOutcomeReport(BaseModel):
    """Structured pre-action vs post-action comparative evaluation report."""
    model_config = ConfigDict(frozen=True)

    outcome_id: str
    workflow_run_id: str
    scenario_id: str
    candidate_id: str
    approval_id: str
    execution_id: str
    baseline_evaluation_id: Optional[str] = None
    post_action_evaluation_id: Optional[str] = None
    model_version: str = "fidelitygate-v1.0"
    metric_status: str = "COMPUTED"
    units: Dict[str, str] = Field(default_factory=lambda: {
        "latency": "ms",
        "utilization": "ratio",
        "capacity_violations": "count",
        "slo_violations": "count",
    })
    pre_action_latency_ms: float
    post_action_latency_ms: float
    latency_delta_ms: float
    latency_reduction_pct: float
    pre_action_peak_utilization: float
    post_action_peak_utilization: float
    pre_action_slo_violations: int
    post_action_slo_violations: int
    pre_action_capacity_violations: int
    post_action_capacity_violations: int
    affected_flows: List[str]
    bottleneck_link: str
    overall_impact: OverallImpact
    reference_evaluation_status: str = "REFERENCE_NOT_AVAILABLE"
    is_reference_safe: Optional[bool] = None
    assumptions_and_limitations: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class WorkflowRunSummary(BaseModel):
    """High-level summary of a workflow run."""
    model_config = ConfigDict(frozen=True)

    workflow_run_id: str
    scenario_id: str
    current_stage: WorkflowStage
    status: WorkflowStatus
    triage_run_id: Optional[str] = None
    investigation_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    adaptive_run_id: Optional[str] = None
    explanation_id: Optional[str] = None
    selected_candidate_id: Optional[str] = None
    gate_verdict: Optional[GateDecision] = None
    approval_id: Optional[str] = None
    approval_status: Optional[ApprovalDecision] = None
    outcome_id: Optional[str] = None
    overall_impact: Optional[OverallImpact] = None
    started_at: str
    completed_at: Optional[str] = None
    duration_ms: Optional[float] = None
    termination_reason: Optional[str] = None


class WorkflowRunRequest(BaseModel):
    """Input payload to trigger a full workflow run."""
    scenario_id: str = "wan_congestion"
    triage_run_id: Optional[str] = None
    max_adaptive_cycles: int = 2
    simulation_budget: int = 25
    auto_approve_for_testing: bool = False
    reviewer_id: str = "operator-local"
    idempotency_key: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Payload to record human approval or rejection."""
    decision: ApprovalDecision = ApprovalDecision.APPROVED
    reviewer_id: str = "operator-human"
    reviewer_comment: Optional[str] = None
    idempotency_key: Optional[str] = None

