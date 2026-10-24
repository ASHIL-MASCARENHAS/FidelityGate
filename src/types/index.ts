export type GateDecisionType = 'ACCEPT' | 'GATHER_EVIDENCE' | 'ABSTAIN';
export type GateDecision = GateDecisionType;

export interface Scenario {
  scenario_id: string;
  name: string;
  description: string;
  nominal_latency_ms: number;
  capacity_mbps: number;
  offered_load_mbps: number;
  slo_latency_ms: number;
  latency_multiplier_min: number;
  latency_multiplier_max: number;
  stability_threshold: number;
}

export interface SweepPoint {
  sample: number;
  latency_factor: number;
  load_factor: number;
  latency_ms: number;
  utilization: number;
  violated: boolean;
}

export interface SweepReport {
  evaluations: number;
  nominal_latency_ms: number;
  worst_latency_ms: number;
  peak_utilization: number;
  stability_score: number;
  violations: number;
  sensitivity: Record<string, number>;
}

export interface GateReport {
  decision: GateDecisionType;
  reason: string;
  report: SweepReport;
  posterior_latency_ms?: number;
}

export interface Counterexample {
  is_fragile: boolean;
  violating_latency_ms: number;
  critical_parameter: string;
  perturbation_factor: number;
  explanation: string;
}

export interface DiagnosticObservation {
  tool_id: string;
  tool_name: string;
  measured_value: number;
  unit: string;
  declared_error_bound: number;
  confidence_interval: [number, number];
  cost_usd: number;
  execution_time_ms: number;
  summary: string;
}

export interface ExecutionEvent {
  step_num: number;
  phase: string;
  actor: string;
  timestamp_offset_ms: number;
  duration_ms?: number;
  action: string;
  status: 'PASS' | 'WARNING' | 'ACTIVE' | 'MEASURED' | 'ACCEPT' | 'ABSTAIN';
  details: Record<string, any>;
}

export interface InvestigationResult {
  run_id: number;
  scenario: Scenario;
  gate: GateReport;
  sweep_points?: SweepPoint[];
  counterexample?: Counterexample;
  diagnostic_observation?: DiagnosticObservation;
  execution_trace?: ExecutionEvent[];
}

export interface BaselineMetrics {
  name: string;
  question: string;
  unsafe_acceptances?: number;
  false_abstentions?: number;
  correct_decisions?: number;
  avg_evaluations: number;
  diagnostic_calls?: number;
  avg_latency_ms: number;
  avg_cost_usd: number;
  unsafe_acceptance_pct: number;
  false_abstention_pct: number;
  accuracy_pct: number;
}

export interface RunHistoryItem {
  id: number;
  created_at: string;
  scenario_id: string;
  scenario_name: string;
  decision: GateDecisionType;
  reason: string;
  report: SweepReport;
}

export interface SiteTopologyNode {
  id: string;
  name: string;
  type: 'onPrem' | 'virtualOffice' | 'remoteAccess' | 'hostedCloud';
  color: string;
  r: number;
  angle: number;
  status: 'healthy' | 'warning' | 'error';
  latency: number;
  capacity: string;
  scenarioKey?: string;
  counterexample?: string;
}

export type RunRecord = RunHistoryItem;

export interface DiagnosticInfo {
  environment?: {
    nodeVersion?: string;
    platform?: string;
    uptimeSeconds?: number;
    memoryUsage?: { rss: number; heapTotal: number; heapUsed: number };
  };
  database?: {
    exists?: boolean;
    path?: string;
    sizeBytes?: number;
    runsCount?: number;
  };
  safety_controls?: {
    llm_api_configured?: boolean;
    offline_only?: boolean;
    read_only_infrastructure?: boolean;
    fail_closed?: boolean;
  };
}

// ==========================================
// Layer 1: Canonical Data Ingestion & Provenance Contracts
// ==========================================

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

export interface RawObservation {
  raw_record_id: string;
  source_dataset: string;
  source_file: string;
  source_row_index: number;
  original_timestamp?: string;
  original_field_name: string;
  original_value: string;
  original_unit?: string;
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

export interface IngestionRequest {
  source_id?: string;
  relative_path: string;
  dataset_version?: string;
  scenario_id?: string;
  force_reingest?: boolean;
}

export interface IngestionSummary {
  ingestion_id: string;
  dataset_id: string;
  status: string;
  source_file: string;
  source_checksum: string;
  source_row_count: number;
  accepted_count: number;
  quarantined_count: number;
  started_at: string;
  completed_at: string;
}

// ==========================================
// Layer 2: Triage & Correlation Interfaces
// ==========================================

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

export interface CorrelationReport {
  correlation_id: string;
  triage_run_id: string;
  time_window: { start?: string; end?: string };
  affected_entities: string[];
  finding_ids: string[];
  evidence_ids: string[];
  supported_relationships: Array<{
    relationship_type: 'co_occurring_metric_cluster' | 'temporally_associated';
    description: string;
    entity_id?: string;
    entity_ids?: string[];
    finding_ids: string[];
    metrics?: string[];
    delta_seconds?: number;
  }>;
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

// ==========================================
// Layer 3: Agentic Investigation & Planning Interfaces
// ==========================================

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

export interface InvestigationRequest {
  triage_run_id: string;
  scenario_id?: string;
  force_agent_mode?: AgentMode;
  max_tool_calls?: number;
  max_diagnostics?: number;
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

// ==========================================
// Layer 4: Mitigation Evaluation & Simulation Interfaces
// ==========================================

export type MitigationActionType = 'REROUTE_FLOW' | 'LOAD_BALANCE' | 'TRAFFIC_SHAPING';
export type ValidationStatus =
  | 'VALID'
  | 'INVALID_NODE'
  | 'INVALID_EDGE'
  | 'LINK_DOWN'
  | 'CYCLE_DETECTED'
  | 'FLOW_MISMATCH'
  | 'INVALID_ACTION_TYPE'
  | 'INCOMPLETE_CONSTRAINTS'
  | 'NO_VALID_CANDIDATE';

export type CandidateEvaluationStatus =
  | 'COMPLIANT'
  | 'FRAGILE'
  | 'INFEASIBLE'
  | 'INVALID_PATH'
  | 'MODEL_DATA_INSUFFICIENT'
  | 'FAILED';

export type ReferenceEvaluationStatus =
  | 'VERIFIED_SAFE'
  | 'VERIFIED_BREACH'
  | 'REFERENCE_NOT_AVAILABLE'
  | 'UNVERIFIED';

export interface TopologyNode {
  node_id: string;
  node_type: string;
  status: 'UP' | 'DOWN';
}

export interface TopologyEdge {
  edge_id: string;
  source: string;
  target: string;
  capacity_mbps: number;
  base_latency_ms: number;
  background_load_mbps: number;
  status: 'UP' | 'DOWN';
}

export interface TrafficFlow {
  flow_id: string;
  name: string;
  source: string;
  destination: string;
  demand_mbps: number;
  slo_latency_ms: number;
  nominal_path: string[];
}

export interface NetworkTopology {
  scenario_id: string;
  name: string;
  nodes: Record<string, TopologyNode>;
  edges: Record<string, TopologyEdge>;
  flows: Record<string, TrafficFlow>;
}

export interface CandidateAction {
  candidate_id: string;
  action_type: MitigationActionType;
  flow_id: string;
  source_node: string;
  destination_node: string;
  path: string[];
  rationale?: string;
  supporting_evidence_ids?: string[];
  originating_investigation_id?: string;
}

export interface PathValidationResult {
  is_valid: boolean;
  status: ValidationStatus;
  reasons: string[];
  validated_path: string[];
  hop_count: number;
  edges_traversed: string[];
}

export interface LinkSimulationResult {
  edge_id: string;
  source: string;
  target: string;
  load_mbps: number;
  capacity_mbps: number;
  utilization: number;
  delay_ms: number;
  is_overloaded: boolean;
}

export interface SimulationPrediction {
  flow_id: string;
  latency_ms: number;
  slo_latency_ms: number;
  peak_utilization: number;
  is_connected: boolean;
  capacity_violated: boolean;
  slo_violated: boolean;
  bottleneck_edge_id?: string;
  link_results: LinkSimulationResult[];
  model_version: string;
  assumptions: string[];
}

export interface CandidateComparison {
  baseline_latency_ms: number;
  candidate_latency_ms: number;
  latency_change_ms: number;
  latency_change_pct?: number;
  baseline_peak_utilization: number;
  candidate_peak_utilization: number;
  peak_utilization_change: number;
  newly_overloaded_edges: string[];
  shared_flow_impacts: Array<Record<string, any>>;
  all_flows_compliant: boolean;
  comparison_supported: boolean;
  notes: string[];
}

export interface ReferenceEvaluationResult {
  reference_status: ReferenceEvaluationStatus;
  true_latency_ms?: number;
  true_peak_utilization?: number;
  ground_truth_safe?: boolean;
  assumptions_difference?: string;
  notes: string[];
}

export interface CandidateEvaluation {
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  candidate_id: string;
  action: CandidateAction;
  validation: PathValidationResult;
  nominal_prediction?: SimulationPrediction;
  uncertainty_report?: SweepReport;
  counterexample?: Counterexample;
  comparison?: CandidateComparison;
  gate_report?: GateReport;
  reference_evaluation?: ReferenceEvaluationResult;
  status: CandidateEvaluationStatus;
  explanation_facts: Record<string, any>;
  limitations: string[];
}

export interface EvaluationEvent {
  event_id: string;
  evaluation_id: string;
  timestamp: string;
  stage: string;
  actor: string;
  event_type: string;
  details: Record<string, any>;
  sequence_number: number;
}

export interface MitigationEvaluationRequest {
  investigation_id: string;
  scenario_id?: string;
  candidate_actions?: CandidateAction[];
  evaluation_budget?: number;
  include_reference_eval?: boolean;
}

export interface MitigationEvaluationSummary {
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  status: string;
  gate_verdict: GateDecisionType;
  candidates_count: number;
  evaluated_count: number;
  compliant_count: number;
  selected_candidate_id?: string;
  created_at: string;
  duration_ms: number;
}

export interface MitigationEvaluationReport {
  evaluation_id: string;
  investigation_id: string;
  plan_id?: string;
  scenario_id: string;
  scenario_version: string;
  model_version: string;
  policy_version: string;
  candidate_evaluations: CandidateEvaluation[];
  selected_candidate_id?: string;
  gate_verdict: GateDecisionType;
  gate_justification: string;
  total_simulations: number;
  duration_ms: number;
  created_at: string;
  data_mode: DataMode;
  reference_evaluation_status: string;
  limitations: string[];
}

// ==========================================
// Layer 5: Counterexample-Guided Adaptive Diagnostics Contracts
// ==========================================

export type MeasurementErrorType =
  | 'BOUNDED_ABSOLUTE'
  | 'BOUNDED_RELATIVE'
  | 'GAUSSIAN_TRUNCATED'
  | 'DISCRETE_INTERVAL';

export type ObservationMode =
  | 'PUBLIC_TELEMETRY_OBSERVED'
  | 'REPLAY'
  | 'SYNTHETIC_DIAGNOSTIC_MEASUREMENT'
  | 'UNAVAILABLE';

export type AdaptiveRunStatus =
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'COMPLETED'
  | 'BUDGET_EXHAUSTED'
  | 'INCONSISTENCY_DETECTED'
  | 'ABSTAINED'
  | 'FAILED';

export interface MeasurementModel {
  tool_id: string;
  tool_name: string;
  target_entity: string;
  target_parameter: string;
  unit: string;
  error_type: MeasurementErrorType;
  error_bound: number;
  cost_usd: number;
  latency_ms: number;
  sampling_behavior: string;
  repeatability_config: string;
  description: string;
  limitations: string[];
}

export interface DiagnosticObservation {
  observation_id: string;
  tool_id: string;
  tool_name: string;
  target_entity: string;
  target_parameter: string;
  measured_value: number;
  unit: string;
  declared_error_bound: number;
  confidence_interval: [number, number];
  observation_mode: ObservationMode;
  source_provenance: Record<string, any>;
  timestamp: string;
  is_valid: boolean;
  limitations: string[];
}

export interface UncertaintyInterval {
  parameter_name: string;
  unit: string;
  min_value: number;
  max_value: number;
  nominal_value: number;
  confidence_level: number;
  is_bounded: boolean;
}

export interface UncertaintyUpdate {
  update_id: string;
  parameter_name: string;
  target_entity: string;
  prior_interval: UncertaintyInterval;
  measurement_interval: [number, number];
  posterior_interval?: UncertaintyInterval;
  is_consistent: boolean;
  update_method: string;
  justification: string;
  assumptions: string[];
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
  measurement_model: MeasurementModel;
  cost_usd: number;
  latency_ms: number;
  status: string;
}

export interface AdaptiveCycleResult {
  cycle_number: number;
  selected_diagnostic_id: string;
  observation: DiagnosticObservation;
  uncertainty_update: UncertaintyUpdate;
  previous_gate_decision: GateDecisionType;
  new_gate_decision: GateDecisionType;
  decision_changed: boolean;
  simulations_consumed: number;
  gate_justification: string;
}

export interface AdaptiveInvestigationRequest {
  evaluation_id: string;
  max_cycles?: number;
  simulation_budget_per_cycle?: number;
  total_simulation_budget?: number;
  diagnostic_cost_budget_usd?: number;
  deterministic_seed?: number;
}

export interface AdaptiveInvestigationSummary {
  adaptive_run_id: string;
  evaluation_id: string;
  investigation_id: string;
  scenario_id: string;
  status: AdaptiveRunStatus;
  created_at: string;
  completed_at?: string;
  initial_gate_decision: GateDecisionType;
  final_gate_decision: GateDecisionType;
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
  completed_at?: string;
  initial_gate_decision: GateDecisionType;
  final_gate_decision: GateDecisionType;
  initial_candidate_id?: string;
  final_candidate_id?: string;
  initial_uncertainty: Record<string, UncertaintyInterval>;
  final_uncertainty: Record<string, UncertaintyInterval>;
  cycles: AdaptiveCycleResult[];
  diagnostic_executions: DiagnosticExecutionRecord[];
  uncertainty_updates: UncertaintyUpdate[];
  total_simulations_consumed: number;
  total_diagnostic_cost_usd: number;
  execution_duration_ms: number;
  reference_evaluation_status?: ReferenceEvaluationStatus;
  termination_reason: string;
  limitations: string[];
  warnings: string[];
}

export interface AdaptiveEvent {
  event_id: string;
  adaptive_run_id: string;
  timestamp: string;
  cycle_number: number;
  stage: string;
  actor: string;
  event_type: string;
  details: Record<string, any>;
  sequence_number: number;
}

// ==========================================
// Layer 6: Explainable AI (XAI) & Decision Attribution Contracts
// ==========================================

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

export interface ExplanationRequest {
  run_id?: string | null;
  evaluation_id?: string | null;
  adaptive_run_id?: string | null;
  scenario_id?: string | null;
  compute_sensitivity?: boolean;
  llm_rephrase?: boolean;
}

export interface ExplanationSummary {
  explanation_id: string;
  run_id: string;
  scenario_id: string;
  candidate_id?: string | null;
  decision: GateDecisionType;
  summary: string;
  rule_pass_count: number;
  rule_fail_count: number;
  has_counterexample: boolean;
  diagnostics_count: number;
  created_at: string;
}

// ==========================================
// Layer 7: End-to-End Workflow & Human Approval
// ==========================================

export type WorkflowStage =
  | 'RECEIVED'
  | 'VALIDATING'
  | 'TRIAGE'
  | 'INVESTIGATION'
  | 'CANDIDATE_EVALUATION'
  | 'COUNTEREXAMPLE_ANALYSIS'
  | 'ADAPTIVE_DIAGNOSTICS'
  | 'REEVALUATION'
  | 'EXPLANATION'
  | 'GATE_REVIEW'
  | 'AWAITING_HUMAN_APPROVAL'
  | 'SIMULATED_ACTION'
  | 'OUTCOME_REPORTED';

export type WorkflowStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'AWAITING_APPROVAL'
  | 'APPROVED'
  | 'REJECTED_BY_HUMAN'
  | 'CHANGES_REQUESTED'
  | 'COMPLETED'
  | 'FAILED'
  | 'CANCELLED';

export type ApprovalDecision = 'APPROVED' | 'REJECTED' | 'CHANGES_REQUESTED';

export type OverallImpact = 'IMPROVED' | 'REGRESSED' | 'MIXED' | 'UNCHANGED' | 'NEUTRAL' | 'DEGRADED';

export interface WorkflowEvent {
  event_id: string;
  workflow_run_id: string;
  sequence_number: number;
  stage: WorkflowStage;
  event_type: string;
  timestamp: string;
  input_artifact_refs: string[];
  output_artifact_refs: string[];
  details: Record<string, any>;
}

export interface HumanApprovalRecord {
  approval_id: string;
  workflow_run_id: string;
  candidate_id: string;
  gate_verdict: GateDecisionType;
  explanation_id: string;
  evidence_version: string;
  decision: ApprovalDecision;
  reviewer_id: string;
  reviewer_comment?: string | null;
  timestamp: string;
  is_stale: boolean;
  idempotency_key?: string | null;
}

export interface SimulatedInterventionRecord {
  intervention_id: string;
  workflow_run_id: string;
  approval_id: string;
  candidate_id: string;
  flow_id: string;
  reroute_path: string[];
  simulated_at: string;
  environment_isolation_mode: string;
  execution_duration_ms: number;
}

export interface InterventionOutcomeReport {
  outcome_id: string;
  workflow_run_id: string;
  scenario_id: string;
  candidate_id: string;
  approval_id: string;
  execution_id: string;
  baseline_evaluation_id?: string | null;
  post_action_evaluation_id?: string | null;
  model_version?: string;
  metric_status?: string;
  units?: Record<string, string>;
  pre_action_latency_ms: number;
  post_action_latency_ms: number;
  latency_delta_ms: number;
  latency_reduction_pct: number;
  pre_action_peak_utilization: number;
  post_action_peak_utilization: number;
  pre_action_slo_violations: number;
  post_action_slo_violations: number;
  pre_action_capacity_violations: number;
  post_action_capacity_violations: number;
  affected_flows: string[];
  bottleneck_link: string;
  overall_impact: OverallImpact;
  reference_evaluation_status?: string;
  is_reference_safe?: boolean | null;
  assumptions_and_limitations: string[];
  created_at: string;
}

export interface WorkflowRunSummary {
  workflow_run_id: string;
  scenario_id: string;
  created_at?: string;
  updated_at?: string;
  started_at?: string;
  completed_at?: string | null;
  current_stage: WorkflowStage;
  status: WorkflowStatus;
  triage_run_id?: string | null;
  investigation_id?: string | null;
  evaluation_id?: string | null;
  adaptive_run_id?: string | null;
  gate_verdict?: GateDecisionType | null;
  selected_candidate_id?: string | null;
  explanation_id?: string | null;
  approval_id?: string | null;
  approval_status?: ApprovalDecision | null;
  outcome_id?: string | null;
  overall_impact?: OverallImpact | null;
  event_count?: number;
  termination_reason?: string | null;
  duration_ms?: number | null;
}

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

export interface WorkflowRunRequest {
  scenario_id: string;
  reviewer_id?: string;
  auto_approve_for_testing?: boolean;
  candidate_id?: string | null;
  triage_run_id?: string | null;
  investigation_id?: string | null;
  evaluation_id?: string | null;
}

export interface ApprovalRequest {
  decision: ApprovalDecision;
  reviewer_id: string;
  reviewer_comment?: string | null;
  idempotency_key?: string | null;
}



