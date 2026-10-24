"""fidelitygate/xai/models.py
Strongly typed data contracts for evidence-based explainable AI (XAI), decision attribution,
local parameter sensitivity, and deterministic decision summaries.
Aligned with NISTIR 8312 explainability principles (Explanation, Meaningfulness, Accuracy, Knowledge Limits).
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from fidelitygate.evaluation.models import GateDecision


class RuleStatus(str, Enum):
    """Evaluation status of a deterministic gate decision rule."""
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ExplanationMode(str, Enum):
    """Operational mode used to synthesize decision explanations."""
    DETERMINISTIC_EXPLAINER = "DETERMINISTIC_EXPLAINER"
    LLM_ASSISTED_VERIFIED = "LLM_ASSISTED_VERIFIED"
    FALLBACK_RECORDED = "FALLBACK_RECORDED"


class GateRuleExplanation(BaseModel):
    """Structured explanation of a single deterministic gate predicate."""
    model_config = ConfigDict(frozen=True)

    rule_id: str
    rule_name: str
    target_metric: str
    observed_value: Optional[float] = None
    unit: str
    threshold_condition: str
    threshold_value: Optional[float] = None
    comparison_symbol: str
    status: RuleStatus
    is_mandatory: bool = True
    supporting_evidence_ref: str
    explanation: str


class CounterexampleExplanation(BaseModel):
    """Detailed explanation of an adversarial counterexample causing fragility."""
    model_config = ConfigDict(frozen=True)

    counterexample_id: str
    candidate_id: str
    violated_constraint: str
    nominal_latency_ms: float
    nominal_utilization: float
    perturbed_latency_ms: float
    perturbed_utilization: float
    slo_latency_ms: float
    violation_margin_ms: float
    exact_parameter_vector: Dict[str, float]
    primary_failure_cause: str
    simulation_event_id: Optional[str] = None
    explanation: str


class ProvenanceItem(BaseModel):
    """Detailed audit record of an evidence item and its origin."""
    model_config = ConfigDict(frozen=True)

    observation_id: str
    source_dataset: str
    source_file: str
    entity_id: str
    metric_name: str
    value: float
    unit: str
    timestamp: str
    label_origin: str
    data_quality_status: str
    relationship_descriptor: str
    is_causal_claim: bool = False
    evidence_url: Optional[str] = None


class UncertaintyExplanation(BaseModel):
    """Audit explanation of an adaptive diagnostic measurement and interval update."""
    model_config = ConfigDict(frozen=True)

    cycle_number: int
    tool_id: str
    tool_name: str
    target_parameter: str
    target_entity: str
    relevance_rationale: str
    addressed_counterexample_id: Optional[str] = None
    raw_measured_value: Optional[float] = None
    raw_unit: Optional[str] = None
    raw_error_bound: Optional[float] = None
    parameter_measured_value: float
    parameter_unit: str
    parameter_error_bound: float
    prior_interval: Tuple[float, float]
    measurement_interval: Tuple[float, float]
    posterior_interval: Optional[Tuple[float, float]] = None
    width_reduction_pct: float
    is_consistent: bool
    unrelated_dimensions_preserved: List[str] = Field(default_factory=list)
    subsequent_gate_impact: str


class ParameterSensitivity(BaseModel):
    """Local sensitivity analysis for a single model parameter."""
    model_config = ConfigDict(frozen=True)

    parameter_name: str
    unit: str
    nominal_value: float
    perturbations: List[Dict[str, Any]]
    latency_elasticity: float
    utilization_elasticity: float
    sensitivity_rank: int
    is_critical_bottleneck: bool = False


class LocalSensitivityReport(BaseModel):
    """Report on local parameter sensitivity gradients and counterfactual edge perturbations."""
    model_config = ConfigDict(frozen=True)

    candidate_id: str
    scenario_id: str
    evaluated_parameters: List[ParameterSensitivity]
    most_sensitive_parameter: str
    bottleneck_edge: str
    counterfactual_edge_perturbation: Dict[str, Any]
    methodology_disclosure: str = (
        "Local sensitivity is computed via deterministic one-at-a-time (OAT) parameter perturbation "
        "in the digital-twin simulator. It measures local model response gradients, not physical real-world causality."
    )


class DecisionExplanation(BaseModel):
    """Complete, evidence-grounded explanation of an autonomous network decision."""
    model_config = ConfigDict(frozen=True)

    explanation_id: str
    run_id: str
    scenario_id: str
    candidate_id: Optional[str] = None
    data_mode: str
    agent_mode: str
    summary: str
    decision: GateDecision
    decision_rationale: str
    evidence_items: List[ProvenanceItem] = Field(default_factory=list)
    supporting_findings: List[str] = Field(default_factory=list)
    counterexample_summary: Optional[CounterexampleExplanation] = None
    measurement_summary: Optional[UncertaintyExplanation] = None
    uncertainty_changes: List[UncertaintyExplanation] = Field(default_factory=list)
    constraint_results: List[GateRuleExplanation] = Field(default_factory=list)
    sensitivity_results: Optional[LocalSensitivityReport] = None
    limitations: List[str] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    model_version: str = "fidelitygate-v1.0"
    policy_version: str = "gate-policy-v1.0"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    post_hoc_reference: Optional[Dict[str, Any]] = None


class ExplanationRequest(BaseModel):
    """Request payload to construct a DecisionExplanation."""
    run_id: Optional[str] = Field(None, description="Generic run ID, adaptive run ID, or evaluation ID")
    evaluation_id: Optional[str] = None
    adaptive_run_id: Optional[str] = None
    scenario_id: Optional[str] = None
    compute_sensitivity: bool = True
    llm_rephrase: bool = False
    force_regenerate: bool = False


class ExplanationSummary(BaseModel):
    """Lightweight summary record of an explanation for catalog queries."""
    model_config = ConfigDict(frozen=True)

    explanation_id: str
    run_id: str
    scenario_id: str
    candidate_id: Optional[str] = None
    decision: GateDecision
    summary: str
    rule_pass_count: int
    rule_fail_count: int
    has_counterexample: bool
    diagnostics_count: int
    created_at: str

