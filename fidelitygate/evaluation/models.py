"""fidelitygate/evaluation/models.py
Strongly typed Pydantic models for Layer 4: Candidate Mitigation Evaluation,
Digital-Twin Simulation, and SLO Verification.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field

from ..schemas import GateDecision, GateReport, SweepReport
from ..ingestion.models import DataMode


class MitigationActionType(str, Enum):
    """Allowlisted candidate mitigation action types."""
    REROUTE_FLOW = "REROUTE_FLOW"
    LOAD_BALANCE = "LOAD_BALANCE"
    TRAFFIC_SHAPING = "TRAFFIC_SHAPING"


class ValidationStatus(str, Enum):
    """Candidate path and topology validation outcome."""
    VALID = "VALID"
    INVALID_NODE = "INVALID_NODE"
    INVALID_EDGE = "INVALID_EDGE"
    LINK_DOWN = "LINK_DOWN"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    FLOW_MISMATCH = "FLOW_MISMATCH"
    INVALID_ACTION_TYPE = "INVALID_ACTION_TYPE"
    INCOMPLETE_CONSTRAINTS = "INCOMPLETE_CONSTRAINTS"
    NO_VALID_CANDIDATE = "NO_VALID_CANDIDATE"


class CandidateEvaluationStatus(str, Enum):
    """Operational evaluation status for a single candidate."""
    COMPLIANT = "COMPLIANT"
    FRAGILE = "FRAGILE"
    INFEASIBLE = "INFEASIBLE"
    INVALID_PATH = "INVALID_PATH"
    MODEL_DATA_INSUFFICIENT = "MODEL_DATA_INSUFFICIENT"
    FAILED = "FAILED"


class ReferenceEvaluationStatus(str, Enum):
    """Independent reference evaluation outcome."""
    VERIFIED_SAFE = "VERIFIED_SAFE"
    VERIFIED_BREACH = "VERIFIED_BREACH"
    REFERENCE_NOT_AVAILABLE = "REFERENCE_NOT_AVAILABLE"
    UNVERIFIED = "UNVERIFIED"


class TopologyNode(BaseModel):
    """Node in the network topology graph."""
    model_config = ConfigDict(frozen=True)

    node_id: str
    node_type: str = "switch"
    status: str = "UP"  # "UP" or "DOWN"


class TopologyEdge(BaseModel):
    """Directed link in the network topology graph."""
    model_config = ConfigDict(frozen=True)

    edge_id: str
    source: str
    target: str
    capacity_mbps: float = Field(ge=0, description="Link bandwidth capacity in Mbps")
    base_latency_ms: float = Field(ge=0, description="Base physical propagation delay in ms")
    background_load_mbps: float = Field(default=0.0, ge=0, description="Background load in Mbps")
    status: str = "UP"  # "UP" or "DOWN"


class TrafficFlow(BaseModel):
    """Traffic demand flow between source and destination endpoints."""
    model_config = ConfigDict(frozen=True)

    flow_id: str
    name: str
    source: str
    destination: str
    demand_mbps: float = Field(gt=0, description="Flow demand in Mbps")
    slo_latency_ms: float = Field(gt=0, description="Maximum acceptable path latency in ms")
    nominal_path: List[str] = Field(..., description="Default nominal path node sequence")


class NetworkTopology(BaseModel):
    """Full canonical network topology graph with nodes, links, and flows."""
    model_config = ConfigDict(frozen=True)

    scenario_id: str
    name: str
    nodes: Dict[str, TopologyNode] = Field(default_factory=dict)
    edges: Dict[str, TopologyEdge] = Field(default_factory=dict)
    flows: Dict[str, TrafficFlow] = Field(default_factory=dict)

    def get_edge(self, u: str, v: str) -> Optional[TopologyEdge]:
        """Find directed edge from node u to node v."""
        for edge in self.edges.values():
            if edge.source == u and edge.target == v:
                return edge
        return None

    def get_node(self, node_id: str) -> Optional[TopologyNode]:
        return self.nodes.get(node_id)

    def get_flow(self, flow_id: str) -> Optional[TrafficFlow]:
        return self.flows.get(flow_id)


class CandidateAction(BaseModel):
    """Structured proposal for a network intervention."""
    model_config = ConfigDict(frozen=True)

    candidate_id: str
    action_type: MitigationActionType = MitigationActionType.REROUTE_FLOW
    flow_id: str
    source_node: str
    destination_node: str
    path: List[str] = Field(..., description="Ordered sequence of nodes defining the proposed path")
    rationale: str = ""
    supporting_evidence_ids: List[str] = Field(default_factory=list)
    originating_investigation_id: Optional[str] = None


class PathValidationResult(BaseModel):
    """Outcome of validating a candidate action against canonical topology and flow rules."""
    model_config = ConfigDict(frozen=True)

    is_valid: bool
    status: ValidationStatus
    reasons: List[str] = Field(default_factory=list)
    validated_path: List[str] = Field(default_factory=list)
    hop_count: int = 0
    edges_traversed: List[str] = Field(default_factory=list)


class LinkSimulationResult(BaseModel):
    """Per-link simulation output."""
    model_config = ConfigDict(frozen=True)

    edge_id: str
    source: str
    target: str
    load_mbps: float
    capacity_mbps: float
    utilization: float
    delay_ms: float
    is_overloaded: bool = False


class SimulationPrediction(BaseModel):
    """Deterministic digital-twin simulation prediction for a flow under a candidate intervention."""
    model_config = ConfigDict(frozen=True)

    flow_id: str
    latency_ms: float
    slo_latency_ms: float
    peak_utilization: float
    is_connected: bool
    capacity_violated: bool
    slo_violated: bool
    bottleneck_edge_id: Optional[str] = None
    link_results: List[LinkSimulationResult] = Field(default_factory=list)
    model_version: str = "M/M/1-convex-queueing-v1.0"
    assumptions: List[str] = Field(default_factory=list)


class CandidateComparison(BaseModel):
    """Before/after comparison of network state between baseline and candidate intervention."""
    model_config = ConfigDict(frozen=True)

    baseline_latency_ms: float
    candidate_latency_ms: float
    latency_change_ms: float
    latency_change_pct: Optional[float] = None
    baseline_peak_utilization: float
    candidate_peak_utilization: float
    peak_utilization_change: float
    newly_overloaded_edges: List[str] = Field(default_factory=list)
    shared_flow_impacts: List[Dict[str, Any]] = Field(default_factory=list)
    all_flows_compliant: bool = True
    comparison_supported: bool = True
    notes: List[str] = Field(default_factory=list)


class Counterexample(BaseModel):
    """Minimal or critical parameter variation causing constraint breach under uncertainty."""
    model_config = ConfigDict(frozen=True)

    is_fragile: bool
    violating_latency_ms: float
    critical_parameter: str
    perturbation_factor: float
    slo_latency_ms: float
    margin_breach_ms: float
    explanation: str


class ReferenceEvaluationResult(BaseModel):
    """Evaluation of the candidate against hidden reference ground truth."""
    model_config = ConfigDict(frozen=True)

    reference_status: ReferenceEvaluationStatus
    true_latency_ms: Optional[float] = None
    true_peak_utilization: Optional[float] = None
    ground_truth_safe: Optional[bool] = None
    assumptions_difference: Optional[str] = None
    notes: List[str] = Field(default_factory=list)


class CandidateEvaluation(BaseModel):
    """Complete evaluation report for a single candidate intervention."""
    model_config = ConfigDict(frozen=True)

    evaluation_id: str
    investigation_id: str
    scenario_id: str
    candidate_id: str
    action: CandidateAction
    validation: PathValidationResult
    nominal_prediction: Optional[SimulationPrediction] = None
    uncertainty_report: Optional[SweepReport] = None
    counterexample: Optional[Counterexample] = None
    comparison: Optional[CandidateComparison] = None
    gate_report: Optional[GateReport] = None
    reference_evaluation: Optional[ReferenceEvaluationResult] = None
    status: CandidateEvaluationStatus
    explanation_facts: Dict[str, Any] = Field(default_factory=dict)
    limitations: List[str] = Field(default_factory=list)


class EvaluationEvent(BaseModel):
    """Monotonically sequenced audit event during mitigation evaluation."""
    model_config = ConfigDict(frozen=True)

    event_id: str
    evaluation_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    stage: str
    actor: str
    event_type: str
    details: Dict[str, Any] = Field(default_factory=dict)
    sequence_number: int = 1


class MitigationEvaluationRequest(BaseModel):
    """Request payload to trigger candidate mitigation evaluation."""
    investigation_id: str = Field(..., description="Layer 3 investigation ID providing diagnostic plan")
    scenario_id: Optional[str] = Field(default=None, description="Target scenario context")
    candidate_actions: Optional[List[CandidateAction]] = Field(
        default=None,
        description="Optional explicit candidate actions; if omitted, resolved from DiagnosticPlan"
    )
    evaluation_budget: int = Field(default=25, ge=5, le=50, description="Bounded simulations budget per candidate")
    include_reference_eval: bool = Field(default=False, description="Whether to execute offline reference evaluation")


class MitigationEvaluationSummary(BaseModel):
    """High-level summary of a mitigation evaluation run."""
    model_config = ConfigDict(frozen=True)

    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: str
    gate_verdict: GateDecision
    candidates_count: int
    evaluated_count: int
    compliant_count: int
    selected_candidate_id: Optional[str] = None
    created_at: str
    duration_ms: float


class MitigationEvaluationReport(BaseModel):
    """Comprehensive structured mitigation evaluation report."""
    model_config = ConfigDict(frozen=True)

    evaluation_id: str
    investigation_id: str
    plan_id: Optional[str] = None
    scenario_id: str
    scenario_version: str = "v1.0"
    model_version: str = "M/M/1-convex-queueing-v1.0"
    policy_version: str = "zero-drift-gate-v1.0"
    candidate_evaluations: List[CandidateEvaluation] = Field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    gate_verdict: GateDecision
    gate_justification: str
    total_simulations: int = 0
    duration_ms: float = 0.0
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    data_mode: DataMode = DataMode.SIMULATED
    reference_evaluation_status: str = "NOT_EVALUATED"
    limitations: List[str] = Field(default_factory=list)
