"""fidelitygate/adaptive/models.py
Strongly typed Pydantic data contracts for Layer 5 counterexample-guided adaptive diagnostics,
measurement models, uncertainty interval updates, and decision re-evaluation.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from ..schemas import GateDecision
from ..evaluation.models import (
    CandidateComparison,
    CandidateEvaluation,
    Counterexample,
    MitigationEvaluationReport,
    MitigationEvaluationSummary,
    ReferenceEvaluationResult,
    ReferenceEvaluationStatus,
    SimulationPrediction,
)


class MeasurementErrorType(str, Enum):
    """Classification of diagnostic measurement error models."""
    BOUNDED_ABSOLUTE = "BOUNDED_ABSOLUTE"
    BOUNDED_RELATIVE = "BOUNDED_RELATIVE"
    GAUSSIAN_TRUNCATED = "GAUSSIAN_TRUNCATED"
    DISCRETE_INTERVAL = "DISCRETE_INTERVAL"


class ObservationMode(str, Enum):
    """Data provenance and operational mode of diagnostic observations."""
    PUBLIC_TELEMETRY_OBSERVED = "PUBLIC_TELEMETRY_OBSERVED"
    REPLAY = "REPLAY"
    SYNTHETIC_DIAGNOSTIC_MEASUREMENT = "SYNTHETIC_DIAGNOSTIC_MEASUREMENT"
    UNAVAILABLE = "UNAVAILABLE"


class MeasurementModel(BaseModel):
    """Specification of a diagnostic tool's measurement and error characteristics."""
    model_config = ConfigDict(frozen=True)

    tool_id: str
    tool_name: str
    target_entity: str
    target_parameter: str
    unit: str
    error_type: MeasurementErrorType = MeasurementErrorType.BOUNDED_ABSOLUTE
    error_bound: float
    cost_usd: float = 0.002
    latency_ms: float = 10.0
    sampling_behavior: str = "single_shot_probe"
    repeatability_config: str = "deterministic_seed"
    description: str = ""
    limitations: List[str] = Field(default_factory=list)


class DiagnosticObservation(BaseModel):
    """Typed observation payload produced by executing a diagnostic tool."""
    model_config = ConfigDict(frozen=True)

    observation_id: str
    tool_id: str
    tool_name: str
    target_entity: str
    target_parameter: str
    measured_value: float
    unit: str
    declared_error_bound: float
    confidence_interval: Tuple[float, float]
    raw_measured_value: Optional[float] = None
    raw_unit: Optional[str] = None
    raw_error_bound: Optional[float] = None
    mapping_description: Optional[str] = None
    observation_mode: ObservationMode = ObservationMode.SYNTHETIC_DIAGNOSTIC_MEASUREMENT
    source_provenance: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    is_valid: bool = True
    limitations: List[str] = Field(default_factory=list)


class UncertaintyInterval(BaseModel):
    """Bounded uncertainty interval for a model parameter."""
    model_config = ConfigDict(frozen=True)

    parameter_name: str
    unit: str
    min_value: float
    max_value: float
    nominal_value: float
    confidence_level: float = 0.95
    is_bounded: bool = True

    @property
    def width(self) -> float:
        return round(self.max_value - self.min_value, 4)


class UncertaintyUpdate(BaseModel):
    """Audit record of a parameter uncertainty interval update."""
    model_config = ConfigDict(frozen=True)

    update_id: str
    parameter_name: str
    target_entity: str
    prior_interval: UncertaintyInterval
    measurement_interval: Tuple[float, float]
    posterior_interval: Optional[UncertaintyInterval] = None
    is_consistent: bool = True
    update_method: str = "BOUNDED_INTERVAL_INTERSECTION"
    justification: str = ""
    assumptions: List[str] = Field(default_factory=list)


class DiagnosticCandidateEvaluation(BaseModel):
    """Evaluation of an eligible diagnostic probe considered for execution."""
    model_config = ConfigDict(frozen=True)

    diagnostic_id: str
    tool_name: str
    target_entity: str
    target_parameter: str
    addressed_counterexample_id: Optional[str] = None
    current_uncertainty_width: float
    affected_constraints: List[str] = Field(default_factory=list)
    estimated_cost: float
    expected_uncertainty_reduction: float
    decision_relevance_score: float
    priority_score: float
    is_eligible: bool = True
    rejection_reason: Optional[str] = None


class DiagnosticExecutionRecord(BaseModel):
    """Persistent audit record of an executed diagnostic tool."""
    model_config = ConfigDict(frozen=True)

    execution_id: str
    cycle_number: int
    diagnostic_id: str
    target_entity: str
    target_parameter: str
    observation: DiagnosticObservation
    measurement_model: MeasurementModel
    cost_usd: float
    latency_ms: float
    status: str = "SUCCESS"


class AdaptiveCycleResult(BaseModel):
    """Outcome of a single adaptive diagnostic and re-evaluation cycle."""
    model_config = ConfigDict(frozen=True)

    cycle_number: int
    selected_diagnostic_id: str
    observation: DiagnosticObservation
    uncertainty_update: UncertaintyUpdate
    previous_gate_decision: GateDecision
    new_gate_decision: GateDecision
    decision_changed: bool
    simulations_consumed: int
    gate_justification: str


class AdaptiveRunStatus(str, Enum):
    """Lifecycle status of an adaptive investigation run."""
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    INCONSISTENCY_DETECTED = "INCONSISTENCY_DETECTED"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"


class AdaptiveInvestigationRequest(BaseModel):
    """Request payload to trigger counterexample-guided adaptive diagnostics."""
    evaluation_id: str = Field(..., description="Target Layer 4 mitigation evaluation ID")
    max_cycles: int = Field(default=2, ge=1, le=5, description="Maximum adaptive diagnostic cycles")
    simulation_budget_per_cycle: int = Field(default=25, ge=5, le=50, description="Sweeps per candidate per cycle")
    total_simulation_budget: int = Field(default=100, ge=10, le=200, description="Total simulation budget ceiling")
    diagnostic_cost_budget_usd: float = Field(default=0.05, ge=0.0, le=1.0)
    deterministic_seed: int = Field(default=42, description="PRNG seed for reproducible synthetic observation error")


class AdaptiveInvestigationSummary(BaseModel):
    """High-level summary of an adaptive investigation run."""
    model_config = ConfigDict(frozen=True)

    adaptive_run_id: str
    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: AdaptiveRunStatus
    created_at: str
    completed_at: Optional[str] = None
    initial_gate_decision: GateDecision
    final_gate_decision: GateDecision
    decision_changed: bool
    candidate_changed: bool
    total_cycles_executed: int
    diagnostics_executed_count: int
    total_simulations_consumed: int
    total_diagnostic_cost_usd: float
    total_duration_ms: float
    termination_reason: str


class AdaptiveInvestigationReport(BaseModel):
    """Complete detailed audit report of a counterexample-guided adaptive investigation."""
    model_config = ConfigDict(frozen=True)

    adaptive_run_id: str
    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: AdaptiveRunStatus
    created_at: str
    completed_at: Optional[str] = None
    initial_gate_decision: GateDecision
    final_gate_decision: GateDecision
    initial_candidate_id: Optional[str] = None
    final_candidate_id: Optional[str] = None
    initial_uncertainty: Dict[str, UncertaintyInterval]
    final_uncertainty: Dict[str, UncertaintyInterval]
    cycles: List[AdaptiveCycleResult]
    diagnostic_executions: List[DiagnosticExecutionRecord]
    uncertainty_updates: List[UncertaintyUpdate]
    total_simulations_consumed: int
    total_diagnostic_cost_usd: float
    execution_duration_ms: float
    reference_evaluation_status: Optional[ReferenceEvaluationStatus] = None
    termination_reason: str
    limitations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class AdaptiveEvent(BaseModel):
    """Monotonically sequenced audit event during adaptive investigation."""
    model_config = ConfigDict(frozen=True)

    event_id: str
    adaptive_run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    cycle_number: int
    stage: str
    actor: str
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
    sequence_number: int = 1
