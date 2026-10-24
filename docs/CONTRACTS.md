# FidelityGate — Contracts & API Schema

This document specifies the authoritative Pydantic models, REST API request/response contracts, and matching TypeScript interfaces for FidelityGate.

---

## 1. Layer 1 Pydantic Schemas

### `DataMode`
```python
class DatasetSourceManifest(BaseModel):
    source_id: str
    name: str
    source_url: str
    publication_reference: str
    dataset_version: str
    license: str
    attribution: str
    download_timestamp: Optional[str]
    source_format: str
    raw_file_path: str
    sha256_checksum: str
    description: str
    limitations: List[str] = []
```

### `RawObservation`
```python
class RawObservation(BaseModel):
    raw_record_id: str
    source_dataset: str
    source_file: str
    source_row_index: int
    original_timestamp: Optional[str] = None
    original_field_name: str
    original_value: str
    original_unit: Optional[str] = None
```

### `NormalizedObservation`
```python
class NormalizedObservation(BaseModel):
    observation_id: str
    source_dataset: str
    source_version: str
    scenario_id: Optional[str] = None
    timestamp: Optional[str] = None  # Validated ISO 8601 UTC
    data_mode: DataMode = DataMode.PUBLIC_DATA
    entity_type: str                  # 'interface', 'node', 'device', or 'unknown'
    entity_id: str                    # Target interface/device or 'unknown'
    metric_name: str                  # Normalized metric key
    value: float                      # Parsed numeric measurement
    unit: Optional[str] = None        # Documented physical unit; None if undocumented
    quality_status: str = "VALID"     # 'VALID', 'SUSPECT', 'QUARANTINED', 'UNKNOWN'
    provenance: Dict[str, Any]        # row, file, checksum, raw timestamp, ingestion_id
    measurement_uncertainty: Optional[Dict[str, Any]] = None
```

### `DataQualityIssue`
```python
class DataQualityIssue(BaseModel):
    issue_id: str
    severity: Literal["CRITICAL", "WARNING", "INFO"]
    dataset_ref: str
    file_ref: str
    row_ref: Optional[int] = None
    category: str
    description: str
    disposition: Literal["REJECTED", "QUARANTINED", "ACCEPTED_WITH_WARNING"]
```

### `IngestionReport`
```python
class IngestionReport(BaseModel):
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
    quality_issues: List[DataQualityIssue] = []
    output_artifacts: Dict[str, str] = {}
    status: Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILED"]
    errors_or_limitations: List[str] = []
```

### `IngestionRequest`
```python
class IngestionRequest(BaseModel):
    source_id: str = "cisco-ie-telemetry"
    relative_path: str
    dataset_version: str = "master"
    scenario_id: Optional[str] = None
    force_reingest: bool = False
```

### `IngestionSummary`
```python
class IngestionSummary(BaseModel):
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
```

---

## 2. Decision Assurance Domain Schemas

### `Scenario`
```python
class Scenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    nominal_latency_ms: float
    capacity_mbps: float
    offered_load_mbps: float
    slo_latency_ms: float
    latency_multiplier_min: float = 0.85
    latency_multiplier_max: float = 1.35
    stability_threshold: float = 0.90
```

### `GateReport`
```python
class GateReport(BaseModel):
    decision: Literal["ACCEPT", "GATHER_EVIDENCE", "ABSTAIN"]
    reason: str
    report: SweepReport
    posterior_latency_ms: Optional[float] = None
```

---

## 3. Canonical REST API Endpoints

| Endpoint | Method | Status | Request Body | Response Body |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/health` | `GET` | 200 | None | Health status object |
| `/api/v1/sources` | `GET` | 200 | None | `List[DatasetSourceManifest]` |
| `/api/v1/sources/{source_id}` | `GET` | 200 / 404 | None | `DatasetSourceManifest` |
| `/api/v1/ingestions` | `POST` | 201 / 400 | `IngestionRequest` | `IngestionReport` |
| `/api/v1/ingestions` | `GET` | 200 | Query: `limit` | `List[IngestionSummary]` |
| `/api/v1/ingestions/{id}` | `GET` | 200 / 404 | None | `IngestionSummary` |
| `/api/v1/ingestions/{id}/report` | `GET` | 200 / 404 | None | `IngestionReport` |
| `/api/v1/ingestions/{id}/quarantine` | `GET` | 200 | None | `List[Dict[str, Any]]` |

---

## 4. TypeScript Client Interfaces (`src/types/index.ts`)

```typescript
export type DataMode =
  | 'PUBLIC_DATA'
  | 'REPLAY'
  | 'SYNTHETIC_FIXTURE'
  | 'SYNTHETIC_FAULT_INJECTION'
  | 'SIMULATED'
  | 'UNKNOWN';

export interface DatasetSourceManifest {
  source_id: string;
  name: string;
  source_url: string;
  publication_reference: string;
  dataset_version: string;
  license: string;
  attribution: string;
  download_timestamp?: string;
  source_format: string;
  raw_file_path: string;
  sha256_checksum: string;
  description: string;
  limitations: string[];
}

export interface NormalizedObservation {
  observation_id: string;
  source_dataset: string;
  source_version: string;
  scenario_id?: string;
  timestamp?: string;
  data_mode: DataMode;
  entity_type: string;
  entity_id: string;
  metric_name: string;
  value: number;
  unit?: string;
  quality_status: string;
  provenance: {
    source_file: string;
    source_row_index: number;
    source_checksum: string;
    raw_timestamp?: string;
    ingestion_id: string;
    [key: string]: any;
  };
  measurement_uncertainty?: Record<string, any>;
}

export interface DataQualityIssue {
  issue_id: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO';
  dataset_ref: string;
  file_ref: string;
  row_ref?: number;
  category: string;
  description: string;
  disposition: 'REJECTED' | 'QUARANTINED' | 'ACCEPTED_WITH_WARNING';
}

export interface IngestionReport {
  ingestion_id: string;
  dataset_id: string;
  dataset_version: string;
  started_at: string;
  completed_at: string;
  source_file: string;
  source_checksum: string;
  source_row_count: number;
  accepted_count: number;
  rejected_count: number;
  quarantined_count: number;
  duplicate_count: number;
  missing_or_invalid_count: number;
  quality_issues: DataQualityIssue[];
  output_artifacts: Record<string, string>;
  status: 'SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED';
  errors_or_limitations: string[];
}
```

---

## 3. Layer 2 Pydantic Schemas

### `FindingSeverity` & `FindingStatus`
```python
class FindingSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

class FindingStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    CONFIRMED = "CONFIRMED"
    SUPPRESSED = "SUPPRESSED"
    RESOLVED = "RESOLVED"
```

### `LabelOrigin` & `EvidenceType`
```python
class LabelOrigin(str, Enum):
    SOURCE_DEFINED = "SOURCE_DEFINED"
    RULE_BASED = "RULE_BASED"
    STATISTICAL_DETECTOR = "STATISTICAL_DETECTOR"
    SYNTHETIC_INJECTED_FAULT = "SYNTHETIC_INJECTED_FAULT"
    UNKNOWN = "UNKNOWN"

class EvidenceType(str, Enum):
    DIRECT_OBSERVATION = "DIRECT_OBSERVATION"
    DERIVED_RATE = "DERIVED_RATE"
    SOURCE_EVENT_CASE = "SOURCE_EVENT_CASE"
    BASELINE_WINDOW = "BASELINE_WINDOW"
```

### `EvidenceItem`
```python
class EvidenceItem(BaseModel):
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
    limitations: List[str] = []
```

### `AnomalyFinding`
```python
class AnomalyFinding(BaseModel):
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
    confidence: float
    label_origin: LabelOrigin
    status: FindingStatus = FindingStatus.CANDIDATE
    evidence_ids: List[str] = []
    limitations: List[str] = []
```

### `CorrelationReport`
```python
class CorrelationReport(BaseModel):
    correlation_id: str
    triage_run_id: str
    time_window: Dict[str, Optional[str]]
    affected_entities: List[str]
    finding_ids: List[str]
    evidence_ids: List[str]
    supported_relationships: List[Dict[str, Any]] = []
    unresolved_questions: List[str] = []
    data_quality_warnings: List[str] = []
    correlation_method: str = "DETERMINISTIC_TEMPORAL_AND_ENTITY_GRAPH"
    limitations: List[str] = []
```

### `InvestigationContext`
```python
class InvestigationContext(BaseModel):
    triage_run_id: str
    source_dataset: str
    source_version: str
    scenario_id: Optional[str] = None
    generated_at: str
    primary_anomaly_candidates: List[AnomalyFinding]
    correlated_evidence: List[EvidenceItem]
    baseline_comparisons: List[Dict[str, Any]] = []
    supporting_evidence_ids: List[str] = []
    contradictory_evidence_ids: List[str] = []
    source_defined_event_metadata: Optional[Dict[str, Any]] = None
    data_quality_warnings: List[str] = []
    unresolved_questions: List[str] = []
    recommended_diagnostic_categories: List[str] = []
    explicitly_unavailable_information: List[str] = []
```

### `TriageRunRequest` & `TriageRunSummary`
```python
class TriageRunRequest(BaseModel):
    ingestion_id: Optional[str] = None
    source_id: str = "cisco-ie-telemetry"
    dataset_version: str = "master"
    case_file: Optional[str] = None
    scenario_id: Optional[str] = None
    metrics_filter: Optional[List[str]] = None
    entities_filter: Optional[List[str]] = None
    z_threshold: float = 3.5
    min_samples: int = 5

class TriageRunSummary(BaseModel):
    triage_run_id: str
    ingestion_id: Optional[str]
    source_dataset: str
    started_at: str
    completed_at: str
    total_observations_scanned: int
    findings_count: int
    evidence_items_count: int
    status: Literal["SUCCESS", "PARTIAL_SUCCESS", "FAILED"]
    highest_severity: FindingSeverity
    errors_or_limitations: List[str] = []
```

---

## 4. Layer 2 TypeScript Interfaces

```typescript
export type FindingSeverity = 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'UNKNOWN';
export type FindingStatus = 'CANDIDATE' | 'CONFIRMED' | 'SUPPRESSED' | 'RESOLVED';
export type LabelOrigin = 'SOURCE_DEFINED' | 'RULE_BASED' | 'STATISTICAL_DETECTOR' | 'SYNTHETIC_INJECTED_FAULT' | 'UNKNOWN';
export type EvidenceType = 'DIRECT_OBSERVATION' | 'DERIVED_RATE' | 'SOURCE_EVENT_CASE' | 'BASELINE_WINDOW';

export interface EvidenceItem {
  evidence_id: string;
  source_dataset: string;
  source_version: string;
  source_file: string;
  source_row_or_event_reference: any;
  timestamp?: string;
  entity_type: string;
  entity_id: string;
  metric_name: string;
  value: number;
  unit?: string;
  quality_status: string;
  evidence_type: EvidenceType;
  transformation?: string;
  limitations: string[];
}

export interface AnomalyFinding {
  anomaly_id: string;
  triage_run_id: string;
  source_dataset: string;
  source_version: string;
  scenario_id?: string;
  entity_type: string;
  entity_id: string;
  metric_name: string;
  window_start?: string;
  window_end?: string;
  detector_name: string;
  detector_version: string;
  observed_value: number;
  baseline_value?: number;
  deviation_score?: number;
  severity: FindingSeverity;
  confidence: number;
  label_origin: LabelOrigin;
  status: FindingStatus;
  evidence_ids: string[];
  limitations: string[];
}

export interface CorrelationRelationship {
  relationship_type: 'co_occurring_metric_cluster' | 'temporally_associated';
  description: string;
  entity_id?: string;
  entity_ids?: string[];
  finding_ids: string[];
  metrics?: string[];
  delta_seconds?: number;
}

export interface CorrelationReport {
  correlation_id: string;
  triage_run_id: string;
  time_window: { start?: string; end?: string };
  affected_entities: string[];
  finding_ids: string[];
  evidence_ids: string[];
  supported_relationships: CorrelationRelationship[];
  unresolved_questions: string[];
  data_quality_warnings: string[];
  correlation_method: string;
  limitations: string[];
}

export interface InvestigationContext {
  triage_run_id: string;
  source_dataset: string;
  source_version: string;
  scenario_id?: string;
  generated_at: string;
  primary_anomaly_candidates: AnomalyFinding[];
  correlated_evidence: EvidenceItem[];
  baseline_comparisons: Array<{
    entity_id: string;
    metric_name: string;
    observed: number;
    baseline: number;
    deviation_score?: number;
    severity: string;
    confidence: number;
  }>;
  supporting_evidence_ids: string[];
  contradictory_evidence_ids: string[];
  source_defined_event_metadata?: Record<string, any>;
  data_quality_warnings: string[];
  unresolved_questions: string[];
  recommended_diagnostic_categories: string[];
  explicitly_unavailable_information: string[];
}

export interface TriageRunSummary {
  triage_run_id: string;
  ingestion_id?: string;
  source_dataset: string;
  started_at: string;
  completed_at: string;
  total_observations_scanned: number;
  findings_count: number;
  evidence_items_count: number;
  status: 'SUCCESS' | 'PARTIAL_SUCCESS' | 'FAILED';
  highest_severity: FindingSeverity;
  errors_or_limitations: string[];
}

---

## 5. Layer 3 Pydantic Schemas (Agentic Investigation & Diagnostic Planning)

```python
class AgentMode(str, Enum):
    LIVE_LLM_AGENT = "LIVE_LLM_AGENT"
    DETERMINISTIC_PLANNER = "DETERMINISTIC_PLANNER"
    DETERMINISTIC_BASELINE = "DETERMINISTIC_BASELINE"

class InvestigationStatus(str, Enum):
    RECEIVED = "RECEIVED"
    INVESTIGATING = "INVESTIGATING"
    DIAGNOSTIC_PLANNING = "DIAGNOSTIC_PLANNING"
    COMPLETE = "COMPLETE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    FAILED = "FAILED"

class HypothesisType(str, Enum):
    BGP_SESSION_FLAP = "BGP_SESSION_FLAP"
    LINK_CONGESTION = "LINK_CONGESTION"
    INTERFACE_DROPS = "INTERFACE_DROPS"
    CPU_SPIKE = "CPU_SPIKE"
    OPTICAL_TRANSCEIVER_FAILURE = "OPTICAL_TRANSCEIVER_FAILURE"
    UNSPECIFIED_ANOMALY = "UNSPECIFIED_ANOMALY"

class Hypothesis(BaseModel):
    hypothesis_id: str
    anomaly_id: Optional[str] = None
    hypothesis_type: HypothesisType
    target_entity: str
    description: str
    evidence_ids: List[str]
    confidence_score: float
    is_source_confirmed: bool = False
    competing_hypotheses: List[str] = []
    recommended_checks: List[str] = []

class InvestigationReport(BaseModel):
    investigation_id: str
    triage_run_id: str
    agent_mode: AgentMode
    model_identifier: str
    created_at: str
    hypotheses: List[Hypothesis]
    supporting_evidence_ids: List[str]
    contradictory_evidence_ids: List[str]
    data_limitations: List[str]
    status: InvestigationStatus
    tool_calls_count: int

class DiagnosticCandidate(BaseModel):
    candidate_id: str
    tool_name: str
    target_entity: str
    parameter_informed: str
    expected_uncertainty_reduction: float
    estimated_resource_cost: float
    selection_rationale: str
    error_bounds: str
    priority_rank: int

class DiagnosticPlan(BaseModel):
    plan_id: str
    investigation_id: str
    status: PlanStatus
    agent_mode: AgentMode
    ranked_candidates: List[DiagnosticCandidate]
    proposed_reroutes: List[str]
    max_diagnostic_budget: int
    estimated_total_cost: float
    created_at: str
    limitations: List[str]

class InvestigationEvent(BaseModel):
    event_id: str
    investigation_id: str
    timestamp: str
    stage: str
    agent_name: str
    event_type: str
    details: Dict[str, Any]
    sequence_number: int

class InvestigationRequest(BaseModel):
    triage_run_id: str
    scenario_id: Optional[str] = None
    force_agent_mode: Optional[AgentMode] = None
    max_tool_calls: int = 5
    max_diagnostics: int = 2

class InvestigationSummary(BaseModel):
    investigation_id: str
    triage_run_id: str
    agent_mode: AgentMode
    model_identifier: str
    status: InvestigationStatus
    started_at: str
    completed_at: str
    hypotheses_count: int
    top_hypothesis: Optional[str] = None
    top_hypothesis_confidence: Optional[float] = None
    diagnostic_candidates_count: int
    top_candidate_tool: Optional[str] = None
    tool_calls_count: int
    errors: List[str] = []
```

---

## 6. Layer 3 TypeScript Interfaces

```typescript
export type AgentMode = 'LIVE_LLM_AGENT' | 'DETERMINISTIC_PLANNER' | 'DETERMINISTIC_BASELINE';
export type InvestigationStatus = 'RECEIVED' | 'INVESTIGATING' | 'DIAGNOSTIC_PLANNING' | 'COMPLETE' | 'INSUFFICIENT_EVIDENCE' | 'FAILED';
export type HypothesisType = 'BGP_SESSION_FLAP' | 'LINK_CONGESTION' | 'INTERFACE_DROPS' | 'CPU_SPIKE' | 'OPTICAL_TRANSCEIVER_FAILURE' | 'UNSPECIFIED_ANOMALY';
export type PlanStatus = 'PROPOSED' | 'APPROVED' | 'EXECUTING' | 'REJECTED' | 'BUDGET_EXHAUSTED';

export interface Hypothesis {
  hypothesis_id: string;
  anomaly_id?: string;
  hypothesis_type: HypothesisType;
  target_entity: string;
  description: string;
  evidence_ids: string[];
  confidence_score: number;
  is_source_confirmed: boolean;
  competing_hypotheses: string[];
  recommended_checks: string[];
}

export interface InvestigationReport {
  investigation_id: string;
  triage_run_id: string;
  agent_mode: AgentMode;
  model_identifier: string;
  created_at: string;
  hypotheses: Hypothesis[];
  supporting_evidence_ids: string[];
  contradictory_evidence_ids: string[];
  data_limitations: string[];
  status: InvestigationStatus;
  tool_calls_count: number;
}

export interface DiagnosticCandidate {
  candidate_id: string;
  tool_name: string;
  target_entity: string;
  parameter_informed: string;
  expected_uncertainty_reduction: number;
  estimated_resource_cost: number;
  selection_rationale: string;
  error_bounds: string;
  priority_rank: number;
}

export interface DiagnosticPlan {
  plan_id: string;
  investigation_id: string;
  status: PlanStatus;
  agent_mode: AgentMode;
  ranked_candidates: DiagnosticCandidate[];
  proposed_reroutes: string[];
  max_diagnostic_budget: number;
  estimated_total_cost: number;
  created_at: string;
  limitations: string[];
}

export interface InvestigationEvent {
  event_id: string;
  investigation_id: string;
  timestamp: string;
  stage: string;
  agent_name: string;
  event_type: string;
  details: Record<string, any>;
  sequence_number: number;
}

export interface InvestigationSummary {
  investigation_id: string;
  triage_run_id: string;
  agent_mode: AgentMode;
  model_identifier: string;
  status: InvestigationStatus;
  started_at: string;
  completed_at: string;
  hypotheses_count: number;
  top_hypothesis?: string;
  top_hypothesis_confidence?: number;
  diagnostic_candidates_count: number;
  top_candidate_tool?: string;
  tool_calls_count: number;
  errors: string[];
}
```

---

## 5. Layer 4 Pydantic Schemas

### `MitigationActionType`, `ValidationStatus`, `CandidateEvaluationStatus`
```python
class MitigationActionType(str, Enum):
    REROUTE = "REROUTE"
    RATE_LIMIT = "RATE_LIMIT"
    SHED_LOAD = "SHED_LOAD"
    TOPOLOGY_ISOLATION = "TOPOLOGY_ISOLATION"

class ValidationStatus(str, Enum):
    VALID = "VALID"
    INVALID_SOURCE_TARGET = "INVALID_SOURCE_TARGET"
    NODE_NOT_FOUND = "NODE_NOT_FOUND"
    EDGE_NOT_FOUND = "EDGE_NOT_FOUND"
    EDGE_DOWN = "EDGE_DOWN"
    CYCLE_DETECTED = "CYCLE_DETECTED"
    DISCONNECTED_PATH = "DISCONNECTED_PATH"
    INCOMPLETE_CONSTRAINTS = "INCOMPLETE_CONSTRAINTS"

class CandidateEvaluationStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    SLO_LATENCY_BREACH = "SLO_LATENCY_BREACH"
    CAPACITY_OVERLOAD = "CAPACITY_OVERLOAD"
    FRAGILE_UNDER_UNCERTAINTY = "FRAGILE_UNDER_UNCERTAINTY"
    INVALID_PATH = "INVALID_PATH"
    INSUFFICIENT_MODEL_DATA = "INSUFFICIENT_MODEL_DATA"
    EVALUATION_ERROR = "EVALUATION_ERROR"
```

### `CandidateAction` & `PathValidationResult`
```python
class CandidateAction(BaseModel):
    candidate_id: str
    action_type: MitigationActionType = MitigationActionType.REROUTE
    flow_id: str
    source_node: str
    target_node: str
    proposed_path: List[str]
    parameters: Dict[str, Any] = Field(default_factory=dict)
    rationale: str
    proposed_by: str = "agent_b_planner"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PathValidationResult(BaseModel):
    candidate_id: str
    is_valid: bool
    status: ValidationStatus
    errors: List[str] = Field(default_factory=list)
    validated_path: List[str] = Field(default_factory=list)
    validated_edge_ids: List[str] = Field(default_factory=list)
```

### `SimulationPrediction` & `CandidateComparison`
```python
class SimulationPrediction(BaseModel):
    is_feasible: bool
    predicted_path_latency_ms: float
    max_link_utilization: float
    bottleneck_edge_id: Optional[str] = None
    all_link_results: List[LinkSimulationResult] = Field(default_factory=list)
    slo_latency_target_ms: float
    slo_latency_satisfied: bool
    slo_utilization_target: float
    slo_utilization_satisfied: bool
    model_assumptions: Dict[str, Any] = Field(default_factory=dict)

class CandidateComparison(BaseModel):
    candidate_id: str
    baseline_latency_ms: float
    simulated_latency_ms: float
    latency_delta_ms: float
    baseline_max_utilization: float
    simulated_max_utilization: float
    utilization_delta: float
    newly_overloaded_edges: List[str] = Field(default_factory=list)
    impacted_flows: List[str] = Field(default_factory=list)
    tradeoff_summary: str
```

### `Counterexample` & `CandidateEvaluation`
```python
class Counterexample(BaseModel):
    counterexample_id: str
    candidate_id: str
    parameter_variations: Dict[str, float]
    violated_constraint: str
    observed_value: float
    threshold_value: float
    margin_breach: float
    description: str

class CandidateEvaluation(BaseModel):
    candidate: CandidateAction
    validation: PathValidationResult
    nominal_prediction: Optional[SimulationPrediction] = None
    comparison_to_baseline: Optional[CandidateComparison] = None
    counterexamples: List[Counterexample] = Field(default_factory=list)
    sampled_robustness_score: float = 0.0
    evaluation_status: CandidateEvaluationStatus
    gate_decision: GateDecision
    reference_evaluation: Optional[ReferenceEvaluationResult] = None
```

### `MitigationEvaluationReport` & `MitigationEvaluationSummary`
```python
class MitigationEvaluationReport(BaseModel):
    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: EvaluationLifecycleStatus
    created_at: datetime
    evaluated_candidates: List[CandidateEvaluation]
    gate_verdict: GateDecision
    selected_candidate_id: Optional[str] = None
    gate_justification: str
    total_simulations_executed: int
    evaluation_duration_ms: float
    data_limitations: List[str]

class MitigationEvaluationSummary(BaseModel):
    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: EvaluationLifecycleStatus
    created_at: datetime
    completed_at: Optional[datetime] = None
    total_candidates: int
    compliant_candidates: int
    gate_verdict: GateDecision
    selected_candidate_id: Optional[str] = None
    gate_justification: str
    total_simulations_executed: int
    evaluation_duration_ms: float
```

---

## 6. Layer 4 TypeScript Interfaces

```typescript
export type MitigationActionType = 'REROUTE' | 'RATE_LIMIT' | 'SHED_LOAD' | 'TOPOLOGY_ISOLATION';

export type ValidationStatus =
  | 'VALID'
  | 'INVALID_SOURCE_TARGET'
  | 'NODE_NOT_FOUND'
  | 'EDGE_NOT_FOUND'
  | 'EDGE_DOWN'
  | 'CYCLE_DETECTED'
  | 'DISCONNECTED_PATH'
  | 'INCOMPLETE_CONSTRAINTS';

export type CandidateEvaluationStatus =
  | 'COMPLIANT'
  | 'SLO_LATENCY_BREACH'
  | 'CAPACITY_OVERLOAD'
  | 'FRAGILE_UNDER_UNCERTAINTY'
  | 'INVALID_PATH'
  | 'INSUFFICIENT_MODEL_DATA'
  | 'EVALUATION_ERROR';

export type ReferenceEvaluationStatus =
  | 'VERIFIED_SAFE'
  | 'UNSAFE_ACCEPTANCE'
  | 'INCORRECT_ABSTENTION'
  | 'CONVERGED_GROUND_TRUTH'
  | 'REFERENCE_NOT_AVAILABLE';

export interface CandidateAction {
  candidate_id: string;
  action_type: MitigationActionType;
  flow_id: string;
  source_node: string;
  target_node: string;
  proposed_path: string[];
  parameters: Record<string, any>;
  rationale: string;
  proposed_by: string;
  created_at: string;
}

export interface PathValidationResult {
  candidate_id: string;
  is_valid: bool;
  status: ValidationStatus;
  errors: string[];
  validated_path: string[];
  validated_edge_ids: string[];
}

export interface LinkSimulationResult {
  edge_id: string;
  source: string;
  target: string;
  capacity_mbps: number;
  allocated_load_mbps: number;
  utilization: number;
  base_latency_ms: number;
  queueing_delay_ms: number;
  total_latency_ms: number;
  is_overloaded: bool;
  is_bottleneck: bool;
}

export interface SimulationPrediction {
  is_feasible: bool;
  predicted_path_latency_ms: number;
  max_link_utilization: number;
  bottleneck_edge_id?: string;
  all_link_results: LinkSimulationResult[];
  slo_latency_target_ms: number;
  slo_latency_satisfied: bool;
  slo_utilization_target: number;
  slo_utilization_satisfied: bool;
  model_assumptions: Record<string, any>;
}

export interface CandidateComparison {
  candidate_id: string;
  baseline_latency_ms: number;
  simulated_latency_ms: number;
  latency_delta_ms: number;
  baseline_max_utilization: number;
  simulated_max_utilization: number;
  utilization_delta: number;
  newly_overloaded_edges: string[];
  impacted_flows: string[];
  tradeoff_summary: string;
}

export interface Counterexample {
  counterexample_id: string;
  candidate_id: string;
  parameter_variations: Record<string, number>;
  violated_constraint: string;
  observed_value: number;
  threshold_value: number;
  margin_breach: number;
  description: string;
}

export interface ReferenceEvaluationResult {
  candidate_id: string;
  reference_status: ReferenceEvaluationStatus;
  true_ground_truth_latency_ms?: number;
  true_max_utilization?: number;
  true_bottleneck_edge?: string;
  is_reference_safe: bool;
  ground_truth_source: string;
  evaluation_notes: string;
}

export interface CandidateEvaluation {
  candidate: CandidateAction;
  validation: PathValidationResult;
  nominal_prediction?: SimulationPrediction;
  comparison_to_baseline?: CandidateComparison;
  counterexamples: Counterexample[];
  sampled_robustness_score: number;
  evaluation_status: CandidateEvaluationStatus;
  gate_decision: GateDecision;
  reference_evaluation?: ReferenceEvaluationResult;
}

export interface MitigationEvaluationReport {
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  status: EvaluationLifecycleStatus;
  created_at: string;
  evaluated_candidates: CandidateEvaluation[];
  gate_verdict: GateDecision;
  selected_candidate_id?: string;
  gate_justification: string;
  total_simulations_executed: number;
  evaluation_duration_ms: number;
  data_limitations: string[];
}

export interface MitigationEvaluationSummary {
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  status: EvaluationLifecycleStatus;
  created_at: string;
  completed_at?: string;
  total_candidates: number;
  compliant_candidates: number;
  gate_verdict: GateDecision;
  selected_candidate_id?: string;
  gate_justification: string;
  total_simulations_executed: number;
  evaluation_duration_ms: number;
}
```

---

## 7. Layer 5 Pydantic Schemas (`fidelitygate/adaptive/models.py`)

```python
class MeasurementErrorType(str, Enum):
    GAUSSIAN = "GAUSSIAN"
    BOUNDED_UNIFORM = "BOUNDED_UNIFORM"
    TRUNCATED_GAUSSIAN = "TRUNCATED_GAUSSIAN"
    DETERMINISTIC_BOUND = "DETERMINISTIC_BOUND"

class ObservationMode(str, Enum):
    PUBLIC_REPLAY = "PUBLIC_REPLAY"
    SYNTHETIC_SIMULATION = "SYNTHETIC_SIMULATION"
    CALIBRATED_HARDWARE = "CALIBRATED_HARDWARE"
    UNAVAILABLE = "UNAVAILABLE"

class MeasurementModel(BaseModel):
    tool_id: str
    target_parameter: str
    physical_unit: str
    error_type: MeasurementErrorType
    nominal_error_bound: float
    standard_deviation: float
    cost_usd: float
    duration_ms: float
    supported_topologies: List[str]

class DiagnosticObservation(BaseModel):
    observation_id: str
    tool_id: str
    target_entity: str
    target_parameter: str
    measured_value: float
    physical_unit: str
    error_bound: float
    confidence_interval: Tuple[float, float]
    observation_mode: ObservationMode
    is_public_replay: bool
    provenance_reference: str
    timestamp: str

class UncertaintyInterval(BaseModel):
    parameter_name: str
    target_entity: str
    lower_bound: float
    upper_bound: float
    physical_unit: str
    width: float

class UncertaintyUpdate(BaseModel):
    parameter_name: str
    target_entity: str
    prior_interval: UncertaintyInterval
    measurement_interval: UncertaintyInterval
    posterior_interval: UncertaintyInterval
    reduction_ratio: float
    is_consistent: bool
    inconsistency_reason: Optional[str]

class DiagnosticCandidateEvaluation(BaseModel):
    diagnostic_id: str
    tool_name: str
    target_entity: str
    target_parameter: str
    addressed_counterexample_id: Optional[str]
    current_uncertainty_width: float
    affected_constraints: List[str]
    estimated_cost: float
    expected_uncertainty_reduction: float
    decision_relevance_score: float
    priority_score: float
    is_eligible: bool
    rejection_reason: Optional[str]

class DiagnosticExecutionRecord(BaseModel):
    execution_id: str
    cycle_number: int
    diagnostic_id: str
    target_entity: str
    target_parameter: str
    observation: DiagnosticObservation
    update: UncertaintyUpdate
    cost_usd: float
    executed_at: str

class AdaptiveCycleResult(BaseModel):
    cycle_number: int
    selected_diagnostic_id: str
    target_parameter: str
    addressed_counterexample_id: Optional[str]
    observation: DiagnosticObservation
    uncertainty_update: UncertaintyUpdate
    simulations_executed: int
    gate_decision_before: GateDecision
    gate_decision_after: GateDecision
    decision_transition: str
    duration_ms: float

class AdaptiveRunStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BUDGET_EXHAUSTED = "BUDGET_EXHAUSTED"
    INCONSISTENCY_DETECTED = "INCONSISTENCY_DETECTED"
    ABSTAINED = "ABSTAINED"
    FAILED = "FAILED"

class AdaptiveInvestigationRequest(BaseModel):
    evaluation_id: str
    max_cycles: int = Field(default=2, ge=1, le=5)
    simulation_budget_per_cycle: int = Field(default=25, ge=5, le=50)
    total_simulation_budget: int = Field(default=100, ge=10, le=200)
    diagnostic_cost_budget_usd: float = Field(default=0.05, ge=0.0, le=1.0)
    deterministic_seed: int = 42

class AdaptiveInvestigationSummary(BaseModel):
    adaptive_run_id: str
    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: AdaptiveRunStatus
    created_at: str
    completed_at: Optional[str]
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
    adaptive_run_id: str
    evaluation_id: str
    investigation_id: str
    scenario_id: str
    status: AdaptiveRunStatus
    created_at: str
    completed_at: str
    initial_gate_decision: GateDecision
    final_gate_decision: GateDecision
    selected_candidate_id: str
    cycles: List[AdaptiveCycleResult]
    diagnostic_executions: List[DiagnosticExecutionRecord]
    uncertainty_updates: List[UncertaintyUpdate]
    total_diagnostic_cost_usd: float
    total_simulations_consumed: int
    total_duration_ms: float
    termination_reason: str
    audit_events: List[AdaptiveEvent]
```

---

## 8. Layer 5 TypeScript Client Types (`src/types/index.ts`)

```typescript
export type MeasurementErrorType =
  | 'GAUSSIAN'
  | 'BOUNDED_UNIFORM'
  | 'TRUNCATED_GAUSSIAN'
  | 'DETERMINISTIC_BOUND';

export type ObservationMode =
  | 'PUBLIC_REPLAY'
  | 'SYNTHETIC_SIMULATION'
  | 'CALIBRATED_HARDWARE'
  | 'UNAVAILABLE';

export type AdaptiveRunStatus =
  | 'INITIALIZED'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'BUDGET_EXHAUSTED'
  | 'INCONSISTENCY_DETECTED'
  | 'ABSTAINED'
  | 'FAILED';

export interface MeasurementModel {
  tool_id: string;
  target_parameter: string;
  physical_unit: string;
  error_type: MeasurementErrorType;
  nominal_error_bound: number;
  standard_deviation: number;
  cost_usd: number;
  duration_ms: number;
  supported_topologies: string[];
}

export interface DiagnosticObservation {
  observation_id: string;
  tool_id: string;
  target_entity: string;
  target_parameter: string;
  measured_value: number;
  physical_unit: string;
  error_bound: number;
  confidence_interval: [number, number];
  observation_mode: ObservationMode;
  is_public_replay: boolean;
  provenance_reference: string;
  timestamp: string;
}

export interface UncertaintyInterval {
  parameter_name: string;
  target_entity: string;
  lower_bound: number;
  upper_bound: number;
  physical_unit: string;
  width: number;
}

export interface UncertaintyUpdate {
  parameter_name: string;
  target_entity: string;
  prior_interval: UncertaintyInterval;
  measurement_interval: UncertaintyInterval;
  posterior_interval: UncertaintyInterval;
  reduction_ratio: number;
  is_consistent: boolean;
  inconsistency_reason?: string;
}

export interface DiagnosticCandidateEvaluation {
  diagnostic_id: string;
  tool_name: string;
  target_entity: string;
  target_parameter: string;
  addressed_counterexample_id?: string;
  current_uncertainty_width: number;
  affected_constraints: string[];
  estimated_cost: number;
  expected_uncertainty_reduction: number;
  decision_relevance_score: number;
  priority_score: number;
  is_eligible: boolean;
  rejection_reason?: string;
}

export interface DiagnosticExecutionRecord {
  execution_id: string;
  cycle_number: number;
  diagnostic_id: string;
  target_entity: string;
  target_parameter: string;
  observation: DiagnosticObservation;
  update: UncertaintyUpdate;
  cost_usd: number;
  executed_at: string;
}

export interface AdaptiveCycleResult {
  cycle_number: number;
  selected_diagnostic_id: string;
  target_parameter: string;
  addressed_counterexample_id?: string;
  observation: DiagnosticObservation;
  uncertainty_update: UncertaintyUpdate;
  simulations_executed: number;
  gate_decision_before: GateDecision;
  gate_decision_after: GateDecision;
  decision_transition: string;
  duration_ms: number;
}

export interface AdaptiveInvestigationSummary {
  adaptive_run_id: string;
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  status: AdaptiveRunStatus;
  created_at: string;
  completed_at?: string;
  initial_gate_decision: GateDecision;
  final_gate_decision: GateDecision;
  decision_changed: boolean;
  candidate_changed: boolean;
  total_cycles_executed: number;
  diagnostics_executed_count: number;
  total_simulations_consumed: number;
  total_diagnostic_cost_usd: number;
  total_duration_ms: number;
  termination_reason: string;
}

export interface AdaptiveInvestigationReport {
  adaptive_run_id: string;
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  status: AdaptiveRunStatus;
  created_at: string;
  completed_at: string;
  initial_gate_decision: GateDecision;
  final_gate_decision: GateDecision;
  selected_candidate_id: string;
  cycles: AdaptiveCycleResult[];
  diagnostic_executions: DiagnosticExecutionRecord[];
  uncertainty_updates: UncertaintyUpdate[];
  total_diagnostic_cost_usd: number;
  total_simulations_consumed: number;
  total_duration_ms: number;
  termination_reason: string;
  audit_events: Array<{
    event_id: string;
    sequence_number: number;
    timestamp: string;
    stage: string;
    event_type: string;
    details: Record<string, any>;
  }>;
}
```

---

## 9. Layer 6: Explainable AI (XAI) & Decision Attribution Schemas

### Python Pydantic Schemas (`fidelitygate/xai/models.py`)

```python
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field
from fidelitygate.evaluation.models import GateDecision

class RuleStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    NOT_EVALUATED = "NOT_EVALUATED"

class GateRuleExplanation(BaseModel):
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
    parameter_name: str
    unit: str
    nominal_value: float
    perturbations: List[Dict[str, Any]]
    latency_elasticity: float
    utilization_elasticity: float
    sensitivity_rank: int
    is_critical_bottleneck: bool = False

class LocalSensitivityReport(BaseModel):
    candidate_id: str
    scenario_id: str
    evaluated_parameters: List[ParameterSensitivity]
    most_sensitive_parameter: str
    bottleneck_edge: str
    counterfactual_edge_perturbation: Dict[str, Any]
    methodology_disclosure: str

class DecisionExplanation(BaseModel):
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
    created_at: str
    post_hoc_reference: Optional[Dict[str, Any]] = None

class ExplanationRequest(BaseModel):
    run_id: Optional[str] = None
    evaluation_id: Optional[str] = None
    adaptive_run_id: Optional[str] = None
    scenario_id: Optional[str] = None
    compute_sensitivity: bool = True
    llm_rephrase: bool = False

class ExplanationSummary(BaseModel):
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
```

### TypeScript Contracts (`src/types/index.ts`)

```typescript
export type RuleStatus = 'PASSED' | 'FAILED' | 'UNKNOWN' | 'NOT_EVALUATED';

export interface GateRuleExplanation {
  rule_id: string;
  rule_name: string;
  target_metric: string;
  observed_value?: number | null;
  unit: string;
  threshold_condition: string;
  threshold_value?: number | null;
  comparison_symbol: string;
  status: RuleStatus;
  is_mandatory: boolean;
  supporting_evidence_ref: string;
  explanation: string;
}

export interface CounterexampleExplanation {
  counterexample_id: string;
  candidate_id: string;
  violated_constraint: string;
  nominal_latency_ms: number;
  nominal_utilization: number;
  perturbed_latency_ms: number;
  perturbed_utilization: number;
  slo_latency_ms: number;
  violation_margin_ms: number;
  exact_parameter_vector: Record<string, number>;
  primary_failure_cause: string;
  simulation_event_id?: string | null;
  explanation: string;
}

export interface ProvenanceItem {
  observation_id: string;
  source_dataset: string;
  source_file: string;
  entity_id: string;
  metric_name: string;
  value: number;
  unit: string;
  timestamp: string;
  label_origin: string;
  data_quality_status: string;
  relationship_descriptor: string;
  is_causal_claim: boolean;
  evidence_url?: string | null;
}

export interface UncertaintyExplanation {
  cycle_number: number;
  tool_id: string;
  tool_name: string;
  target_parameter: string;
  target_entity: string;
  relevance_rationale: string;
  addressed_counterexample_id?: string | null;
  raw_measured_value?: number | null;
  raw_unit?: string | null;
  raw_error_bound?: number | null;
  parameter_measured_value: number;
  parameter_unit: string;
  parameter_error_bound: number;
  prior_interval: [number, number];
  measurement_interval: [number, number];
  posterior_interval?: [number, number] | null;
  width_reduction_pct: number;
  is_consistent: boolean;
  unrelated_dimensions_preserved: string[];
  subsequent_gate_impact: string;
}

export interface ParameterPerturbation {
  perturbation_pct: number;
  parameter_value: number;
  resulting_latency_ms: number;
  resulting_utilization: number;
  latency_delta_ms: number;
  utilization_delta: number;
}

export interface ParameterSensitivity {
  parameter_name: string;
  unit: string;
  nominal_value: number;
  perturbations: ParameterPerturbation[];
  latency_elasticity: number;
  utilization_elasticity: number;
  sensitivity_rank: number;
  is_critical_bottleneck: boolean;
}

export interface LocalSensitivityReport {
  candidate_id: string;
  scenario_id: string;
  evaluated_parameters: ParameterSensitivity[];
  most_sensitive_parameter: string;
  bottleneck_edge: string;
  counterfactual_edge_perturbation: Record<string, any>;
  methodology_disclosure: string;
}

export interface DecisionExplanation {
  explanation_id: string;
  run_id: string;
  scenario_id: string;
  candidate_id?: string | null;
  data_mode: string;
  agent_mode: string;
  summary: string;
  decision: GateDecisionType;
  decision_rationale: string;
  evidence_items: ProvenanceItem[];
  supporting_findings: string[];
  counterexample_summary?: CounterexampleExplanation | null;
  measurement_summary?: UncertaintyExplanation | null;
  uncertainty_changes: UncertaintyExplanation[];
  constraint_results: GateRuleExplanation[];
  sensitivity_results?: LocalSensitivityReport | null;
  limitations: string[];
  unresolved_questions: string[];
  model_version: string;
  policy_version: string;
  created_at: string;
  post_hoc_reference?: Record<string, any> | null;
}
```

---

## 7. Layer 7 Contracts: Workflow Orchestration & Human Authorization

### `WorkflowStage`
```python
class WorkflowStage(str, Enum):
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
```

### `WorkflowStatus`
```python
class WorkflowStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED_BY_HUMAN = "REJECTED_BY_HUMAN"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
```

### `ApprovalDecision` & `OverallImpact`
```python
class ApprovalDecision(str, Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"

class OverallImpact(str, Enum):
    IMPROVED = "IMPROVED"
    NEUTRAL = "NEUTRAL"
    DEGRADED = "DEGRADED"
    REGRESSED = "REGRESSED"
```

### `WorkflowEvent`
```python
class WorkflowEvent(BaseModel):
    event_id: str
    workflow_run_id: str
    sequence_number: int
    stage: WorkflowStage
    event_type: str
    timestamp: str
    input_artifact_refs: List[str] = []
    output_artifact_refs: List[str] = []
    details: Dict[str, Any] = {}
```

### `HumanApprovalRecord`
```python
class HumanApprovalRecord(BaseModel):
    approval_id: str
    workflow_run_id: str
    candidate_id: str
    gate_verdict: GateDecision
    explanation_id: str
    evidence_version: str
    decision: ApprovalDecision
    reviewer_id: str
    reviewer_comment: Optional[str] = None
    timestamp: str
    is_stale: bool = False
    idempotency_key: Optional[str] = None
```

### `OverallImpact`
```python
class OverallImpact(str, Enum):
    IMPROVED = "IMPROVED"
    REGRESSED = "REGRESSED"
    MIXED = "MIXED"
    UNCHANGED = "UNCHANGED"
    DEGRADED = "DEGRADED"
    NEUTRAL = "NEUTRAL"
```

### `InterventionOutcomeReport`
```python
class InterventionOutcomeReport(BaseModel):
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
    units: Dict[str, str] = {
        "latency": "ms",
        "utilization": "ratio",
        "capacity_violations": "count",
        "slo_violations": "count",
    }
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
    assumptions_and_limitations: List[str] = []
    created_at: str
```

---



## 8. Canonical Identifier Namespaces & Resolution Invariants

### A. Identifier Namespaces

To prevent accidental cross-domain lookups, data corruption, and runtime crashes, each pipeline entity belongs to an exclusive identifier namespace:

| Entity Domain | Table Name | Canonical ID Format | Example |
| :--- | :--- | :--- | :--- |
| **Legacy Test Run** | `runs` | Auto-increment integer | `209`, `211` |
| **Ingestion Run** | `ingestion_runs` | `ing-<hex8>` | `ing-f2189c69` |
| **Triage Run** | `triage_runs` | `trg-<hex8>` | `trg-63c67858` |
| **Investigation Run** | `investigation_runs` | `inv-<hex8>` | `inv-1248ea0e` |
| **Mitigation Evaluation** | `mitigation_evaluations` | `eval-<hex8>` | `eval-gather-123`, `eval-922d1287` |
| **Adaptive Investigation** | `adaptive_investigations` | `adapt-<hex8>` | `adapt-4438aaad`, `adapt-deec9c67` |
| **Decision Explanation** | `explanations` | `expl-<hex8>` | `expl-dde21f93` |
| **End-to-End Workflow** | `workflow_runs` | `wf-<hex8>` | `wf-01e0244c` |

> [!CAUTION]
> **Namespace Integrity Invariant**: Under no circumstances should integer run IDs from the legacy `runs` table (e.g. `209`) be fabricated into `eval-209` or `adapt-209`. Prefixes are bound to SQLite primary keys and must be resolved through their authoritative storage tables.

### B. Canonical Resolution & HTTP Status Codes for Explanations

1. **`POST /api/v1/explanations`**:
   - `evaluation_id`: If provided, looked up in `mitigation_evaluations`. Returns **HTTP 404** if not found.
   - `adaptive_run_id`: If provided, looked up in `adaptive_investigations`. Returns **HTTP 404** if not found.
   - `scenario_id`: If provided without run IDs, resolves latest completed run for that specific scenario. Returns **HTTP 404** if no completed evaluations match. Never silently switches to another scenario.
   - Missing/Empty payload or literal `"None"`: Returns **HTTP 400 Bad Request** (`Must provide at least one of 'evaluation_id', 'adaptive_run_id', 'run_id', or 'scenario_id'.`).
   - Success: Returns **HTTP 201 Created** with full `DecisionExplanation` where `constraint_results`, `evidence_items`, and `uncertainty_changes` are guaranteed non-null lists.

2. **`GET /api/v1/explanations`**:
   - Returns `List[ExplanationSummary]` for catalog listings.
   - Each item contains aggregate counters (`rule_pass_count`, `rule_fail_count`) but omits verbose rule and provenance lists.

3. **`GET /api/v1/explanations/{explanation_id}`** (and Next.js proxy `?id={explanation_id}`):
   - Returns full `DecisionExplanation` including the complete `constraint_results` array.
   - Returns **HTTP 404** if `explanation_id` is not found.

---

## 9. Layer 8A: Shared Run Context Interface (SelectedRunContextType)

`	ypescript
export interface SelectedRunContextType {
  selectedWorkflowRunId: string | null;
  selectedWorkflow: WorkflowRunSummary | null;
  scenarioId: string;
  workflowStatus: WorkflowStatus | null;
  currentStage: WorkflowStage | null;
  gateVerdict: GateDecisionType | null;
  selectedCandidateId: string | null;
  triageRunId: string | null;
  investigationId: string | null;
  evaluationId: string | null;
  adaptiveRunId: string | null;
  explanationId: string | null;
  approvalId: string | null;
  outcomeId: string | null;
  lastRefreshedAt: string | null;
  isStale: boolean;
  isLoading: boolean;
  error: string | null;
  workflowEvents: WorkflowEvent[];
  approvalRecord: HumanApprovalRecord | null;
  outcomeReport: InterventionOutcomeReport | null;
  
  selectWorkflowRun: (runId: string) => Promise<void>;
  setWorkflowSummary: (summary: WorkflowRunSummary) => void;
  refreshSelectedWorkflow: () => Promise<void>;
  clearSelectedWorkflow: () => void;
}
`


---

## 10. Layer 8C & Hardening: Auto Demo Context & Step Contracts

```typescript
export interface AutoDemoContext {
  activeStepIndex: number;
  currentStep: AutoDemoStep;
  totalSteps: number;
  isModalOpen: boolean;
  isFloatingBarVisible: boolean;
  isDwellPaused: boolean;
  dwellRemainingMs: number;
  dwellProgressPercent: number;
  modalRemainingSeconds: number;
  statusHeadline: string;
  workflowStatus: string | null;
  scenarioId: string | null;
  gateVerdict: string | null;
  isAwaitingApproval: boolean;
  isCompleted: boolean;
  isAbstained: boolean;
  isRejected: boolean;

  // Navigation actions
  startDemo: () => void;
  stopDemo: () => void;
  confirmModalStep: () => void;
  skipModalStep: () => void;
  pauseDwell: () => void;
  resumeDwell: () => void;
  nextStep: () => void;
  prevStep: () => void;
}

export interface AutoDemoStep {
  id: string;
  tabKey: WorkspaceTab;
  title: string;
  stageName: string;
  badge: string;
  modalHeadline: string;
  modalDescription: (ctx: AutoDemoStepContext) => string;
  highlights: string[];
  keyEvidence: (ctx: AutoDemoStepContext) => Array<{ label: string; value: string }>;
  nextTabName?: string;
}
```
