# FidelityGate — Architecture Decision Records (ADR)

## ADR-001: Preserve Domain Calculations in Python
- **Context**: The existing simulation math, Pydantic contracts, and queueing models were written in Python.
- **Decision**: Keep all computational simulation, uncertainty sweeping, counterexample search, and gate decisions in Python rather than porting to TypeScript.
- **Rationale**: Python provides superior numerical stability, NumPy vectorization, and deterministic reproducibility. A thin subprocess/API bridge between Express/Next.js and Python isolates concerns cleanly.

## ADR-002: Bounded Diagnostic Tool Error Model
- **Context**: Real diagnostics (ping, SNMP, traceroute) have inherent measurement jitter and inaccuracy.
- **Decision**: Every diagnostic tool explicitly declares its error bound ($\pm \delta$) and produces a 95% confidence interval $[y - \delta, y + \delta]$.
- **Rationale**: Prevents the agent from assuming point-estimate perfection. The deterministic gate re-evaluates against the worst-case boundary of the narrowed measurement interval.

## ADR-003: Decoupling Spline 3D Presentation from Core Simulation
- **Context**: Hackathon rubric demands genuine agentic workflow, not decorative animation masquerading as the network data model.
- **Decision**: Spline/Three.js 3D twin centerpiece is strictly a visual enhancement with a toggle to fleet network topology. It never executes simulation math.
- **Rationale**: Ensures the system remains 100% functional, responsive, and trustworthy even if WebGL is disabled or unavailable.

## ADR-004: Four-Way Baseline Comparison
- **Context**: Proving value over simple baselines is essential for technical credibility.
- **Decision**: Compare Nominal-Only, Fixed Safety Margin (+25%), Non-Adaptive Sweep (25x), and Adaptive FidelityGate across identical trials.
- **Rationale**: Directly demonstrates the trade-off: eliminating unsafe acceptances while avoiding false abstentions and minimizing compute/probe cost.

## ADR-005: BilloDesign and Nexus Core Visual Translation
- **Context**: The project required a substantial redesign matching the visual quality and interactions of [billodesign.webflow.io](https://billodesign.webflow.io/) and the "Nexus Core" engineering workspace reference.
- **Decision**: Implement pure CSS `@property --angle` rotating conic gradient borders, tracked monospace typography, an interactive pointer-responsive Three.js digital-twin focal sphere, and a floating dark application enclosure ("Nexus Core") with global network topology metrics and regional zone tables.
- **Rationale**: Balances experiential storytelling on the landing page with calm, editorial focus in the workspace. Avoids heavy JavaScript animation libraries by leveraging modern CSS GPU-accelerated properties.

## ADR-006: Human-in-the-Loop Action Approval Gate
- **Context**: Autonomous AI routing changes in critical enterprise IT networks introduce severe risk of unintended outages if executed without operator oversight.
- **Decision**: Implement an explicit `HumanApprovalModal` requiring manual authorization before any reroute action is considered approved.
- **Rationale**: Enforces responsible AI governance, clearly displays evidence provenance and worst-case burst projections, and honestly discloses hardware execution boundaries (*Simulation / Pre-Production Validation*).

## ADR-007: Canonical FastAPI Modular Monolith over Competing Servers
- **Context**: The archive contained an Express server (`server/server.js`), Next.js route handlers invoking Python via subprocess, and a target architecture requiring FastAPI.
- **Decision**: Establish FastAPI (`fidelitygate.api.app`) as the single canonical backend REST API on port 8000, while preserving Next.js App Router route handlers on port 3000 as client-facing proxies.
- **Rationale**: Eliminates competing server boundaries, provides native OpenAPI documentation, enforces Pydantic validation on all requests/responses, and keeps the architecture as a simple, maintainable modular monolith without unnecessary infrastructure (no Kafka, Redis, or microservices).

## ADR-008: Streaming Ingestion Sink over In-Memory Model Lists
- **Context**: Real-world Cisco telemetry CSV files contain hundreds of thousands of rows and 87 columns. Pre-allocating millions of Pydantic model instances in an in-memory Python list consumed over 4 GB of RAM.
- **Decision**: Implement a stream-based record sink (`record_sink`) in `CiscoTelemetryAdapter` that writes normalized observations directly to the output `.jsonl` file as rows are parsed, while capping the retained `quality_issues` list in the report at 200 items.
- **Rationale**: Reduces peak memory consumption from gigabytes to constant $O(1)$ memory (~45 MB), enabling the application to ingest full multi-gigabyte production traces smoothly on standard workstations.

## ADR-009: Separation of Public Data Replay and Synthetic Reference Ground Truth
- **Context**: In network operations, public telemetry rarely includes aligned topology, capacities, measurement errors, and counterfactual intervention outcomes for a single network. Mixing synthetic evaluation data with public telemetry confuses what was observed versus what was modeled.
- **Decision**: Define a strict `DataMode` taxonomy (`PUBLIC_DATA`, `REPLAY`, `SYNTHETIC_FIXTURE`, `SYNTHETIC_FAULT_INJECTION`, `SIMULATED`, `UNKNOWN`) and isolate the reference evaluator from agent tools.
- **Rationale**: Protects scientific validity. Public telemetry is ingested truthfully with exact units and provenance; synthetic ground truth remains quarantined in the offline evaluator.

## ADR-010: Safe Path Containment and Ingestion Idempotency
- **Context**: Allowing arbitrary file paths in ingestion APIs opens path traversal vulnerabilities (`../../etc/passwd`). Ingesting identical multi-megabyte files repeatedly wastes compute and disk space.
- **Decision**: Strictly bound file paths to `data/raw/` or approved test fixtures, rejecting any traversal attempt. Implement SHA-256 fingerprinting and query existing successful ingestion runs to provide instantaneous idempotency.
- **Rationale**: Guarantees security and deterministic repeatability across repeated pipeline executions.

## ADR-011: Zero-MAD Invariant Baseline Fallback with Epistemic Limitation Tagging
- **Context**: In IT infrastructure telemetry, counters and drop gauges often remain constant at zero across 90%+ of baseline observations. In such invariant series, Median Absolute Deviation ($\text{MAD}$) equals zero, making division by MAD mathematically undefined.
- **Decision**: When $\text{MAD} < 10^{-9}$, strictly prevent divide-by-zero, mark the robust score unavailable (`deviation_score = None`), evaluate candidate anomalies via step difference from the invariant median, and explicitly append `"MAD was zero (invariant baseline); robust score unavailable, evaluated via step difference"` to the finding's limitations.
- **Rationale**: Prevents division-by-zero exceptions or artificial numerical blow-ups while maintaining complete epistemic transparency with human operators and downstream agents.

## ADR-012: Non-Causal Evidence Correlation over Premature Causal Inference
- **Context**: When a network event occurs (e.g. BGP clear), telemetry shows multiple simultaneous deviations across CPU, interface drops, and FIB unroutable packets. Without complete physical topology wiring, routing tables, and active diagnostic verification, asserting causal links ("Device A caused packet loss on Device B") is scientifically invalid.
- **Decision**: Enforce non-causal descriptors in all correlation outputs (`co_occurring_metric_cluster`, `temporally_associated`, `candidate relationship`) and prohibit causal terms (`root cause`, `caused by`, `leads to`) in deterministic correlation reports.
- **Rationale**: Upholds the core principle: agents investigate and recommend, deterministic code calculates and enforces, and consequential claims require verified proof.

## ADR-013: Bounded Investigation Context for Downstream Agent Memory Safety
- **Context**: Ingesting a 1,000-row telemetry sample produces 22,000 observations, hundreds of candidate findings, and thousands of pairwise correlation associations. Passing thousands of unconstrained evidence records into downstream LLM agent context windows would cause prompt bloat, latency spikes, and memory exhaustion.
- **Decision**: Bound `InvestigationContext` to top 20 candidate findings and top 50 correlated evidence items (`max_context_evidence = 50`), prioritized by transparent severity and confidence scoring.
- **Rationale**: Protects agent context windows and ensures that only the highest-leverage, decision-relevant evidence is presented to Layer 3 agents.

## ADR-014: Two Bounded Specialist Agents with Allowlisted Tool Registry
- **Context**: Unconstrained multi-agent swarms or single omniscient LLM agents with open execution environments introduce nondeterministic behavior, tool hallucination, prompt injection vulnerabilities, and safety hazards in network operations.
- **Decision**: Implement exactly two bounded specialist agent roles coordinated by an orchestrator: Agent A (Anomaly Investigator) and Agent B (Diagnostic & Mitigation Planner). All tool use must resolve against a strictly typed `ToolRegistry` with caller permissions. Agents are restricted to safe read-only queries and declarative candidate proposals.
- **Rationale**: Maintains bounded cognitive responsibility, prevents tool execution attacks (no shell, Python, or raw SQL access), and ensures deterministic auditability.

## ADR-015: Absolute Isolation of Reference Evaluator Ground Truth
- **Context**: The evaluation harness requires access to synthetic ground truth (hidden link capacities, exact fault schedules) to score system accuracy and safety. If agents or simulators access this boundary during investigation, decision assurance becomes circular and invalid.
- **Decision**: The reference evaluator ground truth is strictly excluded from `ToolRegistry` and all agent-accessible contracts. It is evaluated solely offline post-decision by the evaluation harness.
- **Rationale**: Guarantees scientific integrity and prevents leakage of test ground truth into operational decision workflows.

## ADR-016: Truthful Fallback Discipline and Quota Latching
- **Context**: Commercial LLM APIs are subject to transient outages, rate limits (HTTP 429), and quota exhaustion. Falling back silently to heuristics while pretending the decision came from an advanced AI agent is deceptive and violates safety standards.
- **Decision**: When LLM calls fail or quota is exhausted, immediately latch `quota_exhausted = True` to disable retries, fall back to `DETERMINISTIC_PLANNER` / `DETERMINISTIC_BASELINE`, and explicitly record this agent mode in all JSON outputs, SQLite records, and UI displays.
- **Rationale**: Truthfulness is paramount in safety-critical IT infrastructure; operators must know precisely which reasoning mode generated the recommendation.

## ADR-017: Pre-Simulation Candidate Path Validation & Invariant Enforcement
- **Context**: Agent-generated candidate routes can propose nonexistent nodes, invalid edges, reversed directions, down links, or cyclic loops. Running numerical queueing simulations on an invalid route wastes compute and produces meaningless latency numbers.
- **Decision**: Enforce `CandidatePathValidator` prior to digital-twin execution. Any candidate failing structural invariants (endpoint mismatch, nonexistent node/edge, link down, cycle detected, zero capacity) is immediately rejected with an explicit `ValidationStatus` and forced closed to `GateDecision.ABSTAIN`.
- **Rationale**: Fail-closed safety guarantee. Assures mathematical validity, prevents corrupt graphs from reaching numerical solvers, and ensures invalid candidates never receive `ACCEPT`.

## ADR-018: Multi-Commodity Fluid Allocation & Convex Queueing Delay Model
- **Context**: Simulating a single rerouted flow in isolation ignores concurrent background traffic and competing flows that share physical links, leading to false optimism and secondary bottlenecks.
- **Decision**: Implement multi-commodity fluid flow allocation ($B_e = b_e + \sum_k q_k x_{ke}$) and link-by-link convex queueing delay ($Q(\rho) = 0.15 \rho / \max(1-\rho, 0.05)$). If any link exceeds 100% utilization, the candidate is marked infeasible ($D = \infty$).
- **Rationale**: Captures realistic cross-flow contention, isolates the true bottleneck edge, and accurately computes before/after differential impacts on shared infrastructure.

## ADR-019: Bounded Parameter Sweeps & Honest Reference Evaluator Boundary
- **Context**: Real public network telemetry (e.g. Cisco IE) lacks unobserved ground truth for hypothetical future reroutes. Scoring public replay data against an invented reference ground truth would be scientifically dishonest. Furthermore, unconstrained parameter sweeps create denial-of-service latency risks.
- **Decision**: Bound the uncertainty parameter sweep strictly to $N \le 50$ iterations (default 25) with deterministic PRNG reproducibility. In the reference evaluator, return `REFERENCE_NOT_AVAILABLE` for public replay traces, and score against hidden parameters only for synthetic benchmark scenarios with declared ground truth.
- **Rationale**: Enforces strict epistemic honesty, prevents arbitrary benchmark fabrication, and bounds worst-case execution time.

## ADR-020: Counterexample-Guided Diagnostic Selection Policy
- **Context**: Selecting diagnostic network probes at random or executing broad telemetry polls introduces monetary cost, probe latency, and network overhead without guaranteeing decision clarity.
- **Decision**: Drive diagnostic selection strictly from the adversarial counterexample discovered by Layer 4 sweeps. Rank allowlisted probes using a decision-relevance priority score ($S = 100 \cdot \Delta w / c$). Filter out uninformative probes and prevent repetitive probes within the same run.
- **Rationale**: Focuses resource expenditure exclusively on the missing information that caused the candidate to fail verification.

## ADR-021: Bounded Interval Intersection & Fail-Closed Inconsistency Handling
- **Context**: When a diagnostic measurement is acquired with bounded measurement error, updating the parameter interval must be mathematically sound. If the measurement contradicts prior knowledge, accepting it blindly could cause catastrophic routing decisions.
- **Decision**: Update parameter intervals via bounded set intersection ($[\theta_{\min}, \theta_{\max}] \cap [y - \delta, y + \delta]$). If the intersection is empty ($\theta'_{\min} > \theta'_{\max}$), mark `INCONSISTENCY_DETECTED` and immediately fail closed to `ABSTAIN`.
- **Rationale**: Rejects contradictory evidence that indicates sensor failure or unmodelled structural changes, preventing unsafe network interventions.

## ADR-022: Multi-Parameter Dimensionality Preservation & Zero Synthetic Replay Fabrication
- **Context**: Measuring one parameter (e.g. fiber latency) must not alter estimates for independent parameters (e.g. traffic demand or link capacity). Additionally, public replay traces must never fabricate active diagnostic results as real public telemetry.
- **Decision**: Strictly isolate parameter bounds during uncertainty updates. For public replay datasets where active probes cannot be executed, return `ObservationMode.UNAVAILABLE` rather than generating synthetic measurements.
- **Rationale**: Maintains dimensional independence in the uncertainty envelope and guarantees zero-fake telemetry provenance.

## ADR-023: Evidence-Based Deterministic Decision Attribution & Sensitivity Analysis
- **Context**: Operators reviewing high-consequence network reroutes need to understand the exact numerical evidence, mathematical bounds, and rule-by-rule evaluations that led to a decision, rather than relying on another LLM that invents plausible-sounding explanations.
- **Decision**: Implement deterministic rule evaluators (`GateRuleExplainer`), exact counterexample replay (`CounterexampleExplainer`), physical unit inversion (`MeasurementExplainer`), and local sensitivity elasticity analysis (`SensitivityAnalyzer`). Ground all summaries strictly in computed artifacts and NISTIR 8312 explainability principles.
- **Rationale**: Provides verifiable decision attribution without hallucinations, exposes knowledge limits, and complies with enterprise AI governance standards.

## ADR-024: Master 13-Stage Workflow State Machine, Strict Human Authorization Boundary, and Isolated Twin Execution
- **Context**: Integrating anomaly triage, agentic investigation, counterexample search, diagnostic re-evaluation, XAI explanation, and operator approval into an end-to-end IT infrastructure solution requires a deterministic lifecycle to prevent race conditions, bypass of safety gates, or unintended physical changes.
- **Decision**:
  1. Enforce a monotonic 13-stage state machine: `RECEIVED → VALIDATING → TRIAGE → INVESTIGATION → CANDIDATE_EVALUATION → COUNTEREXAMPLE_ANALYSIS → ADAPTIVE_DIAGNOSTICS → REEVALUATION → EXPLANATION → GATE_REVIEW → AWAITING_HUMAN_APPROVAL → SIMULATED_ACTION → OUTCOME_REPORTED`.
  2. Implement a strict human authorization boundary: A human operator cannot override a gate `ABSTAIN` (mandatory safety constraints fail closed). Rejection terminates execution without action. Authorization requires fresh evidence currency (`fidelitygate-v1.0`).
  3. Digital-twin isolation: Candidate interventions execute exclusively inside the simulated digital twin (`ISOLATED_DIGITAL_TWIN`). Real-world physical device modification is strictly prevented.
- **Rationale**: Guarantees system safety, transparency, auditable reproducibility, and complete separation between algorithmic recommendation and human authorization.

## ADR-025: Deterministic Repeated Simulation Outcomes and Input-Sensitive Variation Policy
- **Context**: In manual demonstrations, repeated runs using the `wan_congestion` scenario produced identical outcome metrics (`26.55 ms` $\to$ `23.00 ms`, `-3.55 ms`, `76.0%` $\to$ `50.0%`, `0` breaches, `IMPROVED`). We audited whether this was due to hardcoded fallback fixtures or correct deterministic simulation.
- **Decision**:
  1. **Deterministic Reproducibility**: Under the digital twin's fluid M/M/1 queueing delay model, identical inputs $(S, C, G_0, \theta)$ deterministically yield identical physics. Injecting uncontrolled random noise or fake jitter to make consecutive runs look different is strictly forbidden.
  2. **Audit & Removal of Hardcoded Presentation Fallbacks**: We removed hardcoded strings (`"cr01.lon-cr01.par"` as fallback bottleneck edge, `"All edges compliant"`, `"SLA contract satisfied"`, and dummy London-Frankfurt candidates). The bottleneck link is dynamically selected from candidate link load distributions, and the UI conditionally renders breach counts.
  3. **Multi-Scenario & Candidate Sensitivity**: Supported scenarios in the UI dropdown were aligned with real backend topologies (`wan_congestion`, `fiber_drift`, `traffic_burst`, `cisco_bgp_clear`). Verified that different candidates ($R\text{-alt1}$ vs $R\text{-nominal}$) and different scenarios produce distinct calculated metrics.
  4. **Distinct Audit Identifiers**: Each run persists unique identifiers (`workflow_run_id`, `outcome_id`, `execution_id`) referencing exact source evaluation IDs (`baseline_evaluation_id`, `post_action_evaluation_id`) to ensure distinct traceability without sacrificing mathematical reproducibility.
- **Rationale**: Maintains scientific integrity, reproducible engineering auditability, and zero-deception metrics.

## ADR-026: Canonical Shared Run Context, Cross-Tab Integration & Fallback Elimination
- **Context**: Different workspace tabs previously maintained independent, uncoordinated state. In some views, local mathematical fallbacks (`generateLocalFallbackInvestigation`), randomized mock charts (`Math.random()`), hardcoded dummy runs (1042, 1041), and fake fallback metrics (`|| 2`, `86.7%`) created the risk of misleading operators during audits or presentations.
- **Decision**:
  1. Establish **one canonical persisted workflow run context** (`WorkflowRunProvider`, `useWorkflowRun`) storing authoritative IDs (`workflow_run_id`, `triage_run_id`, `investigation_id`, `evaluation_id`, `adaptive_run_id`, `explanation_id`, `approval_id`, `outcome_id`) and artifacts.
  2. Eliminate all in-memory local mathematical generators and random intervals from the live path. If the backend is offline or no run is active, UI components display honest empty or error states.
  3. Ensure all tabs (Workflow Orchestration, Decision Workspace, Explainable AI, Execution Trace, Metrics, Audit Runs, Human Approval Modal) inspect the identical selected run.
  4. Ensure CLI commands (`get-workflow-events`, `list-workflows`, `approve-workflow`) and Next.js route handlers maintain contract parity with FastAPI.
- **Rationale**: Preserves scientific integrity, zero-deception governance, and ensures that an evaluation or approval in one tab is immediately visible, consistent, and verifiable across every other tab.

## ADR-027: Enterprise Dark-Mesh Gradient, 3D Interactive Network Globe, and In-App User Guide
- **Context**: Hackathon presentation and enterprise UX standards require a refined, restrained aesthetic suitable for infrastructure reliability engineers, with an interactive visual centerpiece, clear light and dark theme contrast, and an integrated user guide replacing raw markdown file lists.
- **Decision**:
  1. **Interactive 3D Network Globe (InteractiveNetworkGlobe.tsx)**: Replaced the abstract rotating focal orb with a Three.js interactive geographic network globe. Features a dark spherical core (radius 2.0), electric-cyan thin atmosphere shell, 4,312 realistically positioned dotted continental landmass points, fine latitude/longitude reference rings, 10 real-world global network hubs (Frankfurt, London, New York, Silicon Valley, Tokyo, Singapore, Zurich, São Paulo, Sydney, Mumbai), curved 3D Bézier connection arcs, and animated cyan travelling signal particles. Supports mouse/touch drag rotation, auto-rotation, prefers-reduced-motion, accessible WebGL fallback, and an explicit illustrative simulation disclaimer badge.
  2. **Pure CSS Atmospheric Mesh Gradients (globals.css)**: Implemented GPU-accelerated fixed-attachment radial gradients (.dark-mesh-bg, .workspace-mesh-bg, .light-mesh-bg) utilizing deep navy ground (#08111F), elevated navy (#0D1B2A), secondary surface (#111F34), dark border (#22334A), and restrained cyan (#55D9F4) and cobalt (#4169F5) glow layers, avoiding heavy external canvas libraries while rendering at 60 FPS.
  3. **High-Contrast Dual-Theme Design Tokens (	ailwind.config.ts, globals.css)**: Built distinct semantic token dictionaries for Light mode (#F7F8FA, #FFFFFF, #111827, #657387) and Dark mode (#08111F, #0D1B2A, #111F34, #F2F5FA, #9AA9BD), ensuring WCAG AA contrast and eliminating washed-out grays.
  4. **In-App User Guide (UserGuide.tsx)**: Replaced the generic raw file list in the workspace with an interactive, section-wise User Guide featuring 12 structured modules: Start Here, Run a Workflow, Investigation & Triage, Candidate Evaluation & Twin Simulation, Bounded Counterexample Sweeps, Adaptive Diagnostics & Error Models, Explainable AI & Decision Attribution, Human Authorization Boundary, Failure Modes & Safe Fallbacks, Architecture Invariants, Hackathon Judging Criteria Alignment (Reusability, Governance & Responsibility, ROI/Business Value, MVP Readiness, Originality & Innovation), and an interactive 6-step demo walkthrough with direct tab jump buttons.
- **Rationale**: Elevates the product to enterprise engineering standards, communicates technical depth through real functionality, and empowers judges to understand and verify the entire system self-guidedly.

## ADR-028: Guided Auto Demo Mode, Status-Aware Transition Popups & Zero-Mutation Boundary
- **Context**: Demonstrating a complex 13-stage decision assurance platform across 8 workspace tabs to evaluators or operators risks cognitive overload if unguided, or skepticism if scripted via synthetic frontend macros that bypass real backend pipelines.
- **Decision**:
  1. **Strictly Grounded in Persisted SQLite Runs**: Auto Demo consumes canonical workflow state from `WorkflowRunContext`. If no workflow is active, it prompts the user (`NoWorkflowModal`) to launch or load one. It never fakes run IDs or outcomes.
  2. **Data-Driven 8-Step Navigation with Pre-Transition Popups**: Before navigating to each tab (`decision` → `workflow` → `xai` → `trace` → `metrics` → `evaluation` → `history` → `guide`), Auto Demo presents an orienting modal (`AutoDemoModal`) summarizing real status (prioritizing `REJECTED_BY_HUMAN` and `ABSTAIN`), giving a concise explanation of what the view demonstrates, and offering Continue, Skip, and Stop controls with auto-advance countdown.
  3. **5-Second Viewing Dwell Bar (`AutoDemoFloatingControl`)**: Upon entering each destination tab, a non-intrusive floating control bar provides a 5-second inspection interval with step counter, dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next Tab (<kbd>Enter</kbd>), and Stop (<kbd>Esc</kbd>).
  4. **Strict Human Boundary Inviolability**: At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses and alerts the operator. It never executes an intervention or signs off on an approval automatically; human authorization remains exclusively with the operator.
- **Rationale**: Provides an effortless, judge-ready presentation experience that clearly conveys the purpose and evidence of each view while preserving zero-deception data integrity and the inviolable human governance boundary.


## ADR-029: Final Hardening, Complete Fallback Identifier Elimination & Strict Dynamic Derivations
- **Context**: During pre-submission verification of the Auto Demo and workspace views, trace and decision cards contained several legacy fallback numbers (`86.7%`, `0 Breaches`, `18`, `50`, `94`, `87`, `2`) and a fallback candidate identifier (`'R-reroute-alt1'`) when context was null. While harmless in nominal scenarios, these fallbacks could mislead an operator or judge if an abnormal workflow or empty context was evaluated.
- **Decision**:
  1. **Complete elimination of fallback candidate IDs**: In `src/config/autoDemoSteps.ts`, `ctx.selectedCandidateId` is evaluated without `'R-reroute-alt1'` fallback. If null, the UI honestly states that no candidate has been selected or generated yet and gives clear instructions on how to run Stage 4 or load a run from SQLite.
  2. **Complete elimination of hardcoded outcome assertions**: In `src/config/autoDemoSteps.ts`, outcome descriptions are strictly dynamically computed from `ctx.outcomeReport` (post-action evaluation ID, latency shift, peak utilization, capacity breach count, SLO breach count, overall impact). If missing, the UI states that the outcome report is not yet recorded.
  3. **Strict dynamic derivations in UI cards**: In `DecisionWorkspace.tsx`, `ExecutionTraceView.tsx`, and `FidelityMonitoringRecharts.tsx`, all fallback magic numbers were replaced by mathematical bounds and empirical evaluations derived directly from `currentScenario`, `points`, and trace failure events.
  4. **Updated TypeScript contracts**: Changed `scenarioId: string` to `scenarioId: string | null` in `src/types/demo.ts` and `src/types/index.ts` to reflect the honest reality of unselected runs.
- **Rationale**: Guarantees absolute epistemic honesty and data integrity across the entire application. Zero fake data, zero simulated successes, zero fallback assumptions.
