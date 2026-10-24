# FidelityGate — Uncertainty-Aware Decision Assurance Platform

> **"Make every network decision earn its confidence."**

**Primary Domain:** IT Infrastructure  
**Business Use Case:** Human-approved network-reroute assurance during a traffic surge  
**Core Principle:** Agents investigate and recommend. Deterministic software calculates and enforces. An independent evaluator measures. A human authorizes consequential actions.

FidelityGate is a decision-assurance platform for digital-twin network operations and enterprise SD-WAN infrastructure. Rather than relying on naive nominal telemetry or trusting unconstrained AI reroute recommendations, FidelityGate explores multidimensional parameter uncertainty, exposes adversarial counterexamples, gathers targeted diagnostic evidence (with explicit measurement error), and enforces zero-drift deterministic verification before consequential network interventions.

---

## 1. System Architecture & Implementation State

FidelityGate is structured as a modular monolith pairing a high-performance **Next.js 14 App Router** frontend with a canonical **FastAPI / Python** research and ingestion core.

### Current Implementation State: Layers 1, 2, 3, 4, 5, 6, and 7 (Full MVP Complete)

#### Layer 1: Backend Foundation, Trustworthy Data Ingestion, Validation, and Provenance
- **Canonical REST Backend (`fidelitygate/api/app.py`)**: FastAPI application providing health/readiness probes, source manifest catalogs, and bounded ingestion execution.
- **Cisco Telemetry Adapter (`fidelitygate/ingestion/cisco_adapter.py`)**: Streaming parser and validator for real-world Cisco Innovation Edge telemetry (87 YANG telemetry metrics, nanosecond timestamp normalization, strict physical unit preservation).
- **Bounded Ingestion Pipeline (`fidelitygate/ingestion/pipeline.py`)**: Enforces path containment (blocking directory traversals), SHA-256 chunked hashing, and idempotency caching.
- **Quarantine Manager (`fidelitygate/ingestion/quarantine.py`)**: Isolates corrupted or malformed rows to prevent downstream model contamination while preserving raw records for human review.
- **Data Mode Separation**: Strictly tags records as `PUBLIC_DATA`, `REPLAY`, `SYNTHETIC_FIXTURE`, `SYNTHETIC_FAULT_INJECTION`, `SIMULATED`, or `UNKNOWN`.

#### Layer 2: Explainable Anomaly Triage and Evidence Correlation
- **Deterministic Anomaly Detectors (`fidelitygate/triage/detectors/`)**:
  - `RobustStatisticalDetector`: Computes robust deviation scores via $0.6745 \cdot (x - m) / \text{MAD}$. Strictly handles invariant zero-MAD baselines (`score = None`, step evaluation, division-by-zero protection). Computes first-difference rates for cumulative counters with counter-reset handling.
  - `StepChangeDetector`: Evaluates relative and absolute step jumps with non-zero denominator protection.
  - `SourceEventCaseDetector`: Parses Cisco experiment case tables (`casedata.txt`), converts PDT timestamps to UTC, and correlates target devices with strict provenance separation (`LabelOrigin.SOURCE_DEFINED`).
- **Deterministic Evidence Correlation (`fidelitygate/triage/correlation.py`)**: Multi-metric entity clustering (`co_occurring_metric_cluster`), 60s temporal proximity clustering (`temporally_associated`), non-causal descriptors, and evidence deduplication.
- **Investigation Context Builder (`fidelitygate/triage/context_builder.py`)**: Assembles bounded `InvestigationContext` (`max_context_evidence = 50`), baseline comparisons, recommended diagnostic categories, and explicit data limitations for downstream Layer 3 agents.
- **Triage API & CLI**: Exposes `/api/v1/triage/*` endpoints and standalone runner `scripts/run_triage.py`.

#### Layer 3: Bounded Agentic Investigation, Tool Use and Diagnostic Planning
- **Bounded Specialist Agents (`fidelitygate/investigation/`)**:
  - **Agent A (Anomaly Investigator)**: Formulates structured, evidence-linked hypotheses (`Hypothesis`), enforces non-causal descriptors, clearly differentiates source-defined case labels (`LabelOrigin.SOURCE_DEFINED`) from inferred anomalies (`LabelOrigin.STATISTICAL_DETECTOR`), and reports `INSUFFICIENT_EVIDENCE` when observations are absent or ambiguous.
  - **Agent B (Diagnostic & Mitigation Planner)**: Evaluates allowlisted diagnostic catalog (`DIAGNOSTIC_TOOLS`), ranks candidate probes by expected uncertainty reduction vs. cost, proposes candidate reroute mitigations (e.g. `R-reroute-alt1`) for digital-twin evaluation, and strictly enforces probe/time budgets.
- **Allowlisted Tool Registry (`fidelitygate/investigation/tools.py`)**: Strict permission model allowlisting safe read-only queries (`read_observation`, `get_case_metadata`, `query_metric_window`, `inspect_topology`, `list_diagnostic_catalog`, `propose_candidate_reroute`) and restricting active network probes (`execute_diagnostic_probe`) to orchestrator authority. Completely isolates reference evaluator ground truth.
- **Robust LLM Adapter (`fidelitygate/investigation/llm_adapter.py`)**: Single bounded schema repair attempt on malformed model responses, proactive quota-exhaustion tracking (`HTTP 429` locks out future retries), safe timeout handling, and truthful labelling of fallback modes (`DETERMINISTIC_PLANNER` / `DETERMINISTIC_BASELINE`).
- **Orchestration & Audit Persistence (`fidelitygate/investigation/orchestrator.py`)**: Orchestrates agent workflows, enforces monotonic event sequencing, and persists investigation runs, hypotheses, diagnostic plans, and events in SQLite.
- **Investigation API & CLI**: Exposes 6 `/api/v1/investigations/*` endpoints and standalone runner `scripts/run_investigation.py`.

#### Layer 4: Candidate Mitigation Evaluation, Digital-Twin Simulation and SLO Verification
- **Candidate Path Validator (`fidelitygate/evaluation/validator.py`)**: Validates candidate paths against canonical topology graphs, verifying source/target endpoints, edge existence, link operational status (`UP`/`DOWN`), flow requirements, absence of self-loops/cycles, and positive link capacities. Rejects invalid proposals before numerical simulation.
- **Deterministic Digital-Twin Simulator (`fidelitygate/evaluation/simulator.py`)**: Evaluates network interventions through multi-commodity fluid traffic allocation ($B_e = b_e + \sum_k q_k x_{ke}$), link utilization computation ($\rho_e = B_e / C_e$), convex queueing delay approximation ($Q(\rho) = 0.15 \rho / \max(1-\rho, 0.05)$), bottleneck edge isolation, and before/after latency and utilization differential comparisons.
- **Bounded Uncertainty Sweeper (`fidelitygate/evaluation/uncertainty_evaluator.py`)**: Tests candidate robustness across multidimensional parameter variations (traffic surge $\pm 30\%$, capacity degradation $\pm 20\%$, cross-traffic $\pm 25\%$) within a bounded budget ($N \le 50$, default 25). Identifies minimal adversarial counterexamples and margin breaches.
- **Independent Reference Evaluator (`fidelitygate/evaluation/reference_evaluator.py`)**: Evaluates candidates against hidden reference ground truth strictly post-hoc. Kept isolated from candidate search and agent inspection; returns `REFERENCE_NOT_AVAILABLE` for ungrounded public replay traces.
- **Mitigation Evaluation Engine (`fidelitygate/evaluation/engine.py`)**: Orchestrates candidate extraction from Layer 3 diagnostic plans, validation, simulation, uncertainty sweeps, deterministic gate verdicts (`ACCEPT`, `GATHER_EVIDENCE`, `ABSTAIN`), and SQLite audit persistence.
- **Mitigation API & CLI**: Exposes 5 REST endpoints under `/api/v1/mitigation-evaluations/*` and standalone CLI runner `scripts/run_mitigation_evaluation.py`.

#### Layer 5: Counterexample-Guided Adaptive Diagnostics and Measurement-Driven Re-evaluation
- **Counterexample-Driven Diagnostic Selector (`fidelitygate/adaptive/selector.py`)**: Targets the specific parameter responsible for the minimal adversarial counterexample discovered by Layer 4 sweeps. Evaluates allowlisted diagnostics, ranks eligible probes by decision-relevance score ($S = 100 \cdot \Delta w / c$), filters out unsupported parameters, detects repetition, and enforces cost budget caps.
- **Bounded Measurement-Error Models (`fidelitygate/adaptive/measurement_registry.py`)**: Implements declared observation models ($y = h_d(\theta_{\text{true}}) + \epsilon$) with physical units, calibrated noise scales, and reproducible PRNG seeding. Strictly marks public telemetry replays as `UNAVAILABLE` rather than fabricating synthetic measurements as real observations.
- **Mathematically Rigorous Uncertainty Updater (`fidelitygate/adaptive/uncertainty_updater.py`)**: Computes validated parameter updates via bounded interval intersection ($[\theta_{\min}, \theta_{\max}] \cap [y - \delta, y + \delta]$). Detects empty-intersection inconsistencies and fails closed to `ABSTAIN`. Updates target parameter bounds while strictly preserving unrelated dimensions.
- **Adaptive Investigation Orchestration Engine (`fidelitygate/adaptive/engine.py`)**: Executes bounded adaptive loops (maximum 2 cycles by default, total simulation budget $\le 100$), skips unnecessary diagnostics for initial `ACCEPT` decisions, short-circuits on non-informative probes or empty intersections, triggers Layer 4 digital-twin re-simulation and sweep re-evaluation, and decides updated gate verdicts.
- **Full Audit Trace & Event Persistence (`fidelitygate/storage.py`)**: Records adaptive runs, diagnostic executions, interval updates, and monotonically sequenced lifecycle events (`RECEIVED`, `DIAGNOSTIC_SELECTION`, `MEASUREMENT`, `UNCERTAINTY_UPDATE`, `REEVALUATION`, `GATE_REVIEW`).
- **Adaptive API & CLI**: Exposes 5 REST endpoints under `/api/v1/adaptive-investigations/*` and standalone CLI runner `scripts/run_adaptive_investigation.py`.

#### Layer 6: Evidence-Based Explainable AI (XAI), Decision Attribution & Sensitivity Analysis
- **Deterministic Gate Rule Explainer (`fidelitygate/xai/rule_explainer.py`)**: Rule-by-rule evaluation of all 5 mandatory gate predicates (`RULE-CONN-01` Connectivity, `RULE-CAP-02` Capacity, `RULE-SLO-03` Latency SLO, `RULE-ROB-04` Robustness Score $\ge 0.90$, `RULE-CE-05` Zero Counterexamples) with exact numerical observed values, comparison symbols, units, thresholds, and evidence references.
- **Counterexample Replay Explainer (`fidelitygate/xai/counterexample_explainer.py`)**: Preserves exact perturbation vectors (e.g. `{'fiber_latency_calibration_drift': 1.25}`), nominal vs perturbed metrics, breach margins ($+3.5$ ms vs 45.0 ms SLO), and failure cause.
- **Diagnostic Measurement & Unit Conversion Explainer (`fidelitygate/xai/measurement_explainer.py`)**: Mathematically inverts physical probe delays ($20.993$ ms $\pm 1.5$ ms) to parameter confidence intervals ($1.0496 \pm 0.0750$ factor), documents $70.0\%$ uncertainty width reduction via interval intersection, and verifies that orthogonal dimensions remain preserved.
- **Local Sensitivity & Counterfactual Analyzer (`fidelitygate/xai/sensitivity_analyzer.py`)**: Evaluates deterministic one-at-a-time (OAT) parameter variations ($\pm 10\%, \pm 20\%$) and computes elasticity gradients using `NetworkSimulator`. Performs bottleneck edge counterfactual perturbations (+15% load). Includes explicit disclosure: local sensitivity measures simulator gradients, not real-world causality.
- **Authoritative Zero-Hallucination Summary Generator (`fidelitygate/xai/summary_generator.py`)**: Synthesizes structured facts into concise plain-language summaries with explicit knowledge limitations and human authorization disclosures.
- **XAI API & CLI**: Exposes 5 REST endpoints under `/api/v1/explanations/*`, standalone CLI runner `scripts/run_explanation.py`, and CLI subcommands (`explain-decision`, `get-explanation`, `list-explanations`).
- **Interactive Next.js UI Integration**: Implements `DecisionExplanationPanel.tsx`, dedicated "Explainable AI" tab in `WorkspaceApp.tsx`, and inline XAI attribution card in `DecisionWorkspace.tsx`.


#### Layer 8B: Premium Enterprise UX, Interactive Network Globe & In-App User Guide
- **Interactive 3D Network Globe (`src/components/landing/InteractiveNetworkGlobe.tsx`)**: Three.js visualization featuring a dark core (R = 2.0), electric cyan atmosphere (R = 2.04), 4,312 continental landmass dots sampled at 3° resolution, 10 global network hubs, curved 3D Bézier connection arcs, and animated traveling signal packets. Features mouse/touch drag rotation, inertia damping, auto-rotation, prefers-reduced-motion compliance, 2D fallback, and illustrative simulation disclaimer badge.
- **Pure CSS Atmospheric Mesh Gradients (`src/app/globals.css`, `tailwind.config.ts`)**: GPU-accelerated fixed-attachment radial gradients (`.dark-mesh-bg`, `.workspace-mesh-bg`, `.light-mesh-bg`) utilizing deep navy ground (`#08111F`), elevated navy (`#0D1B2A`, `#111F34`), dark borders (`#22334A`), and restrained cyan/cobalt accents, rendering at 60 FPS without heavy canvas libraries.
- **High-Contrast Dual-Theme System**: Semantic token system across Light mode (`#F7F8FA`, `#FFFFFF`, `#111827`, `#657387`) and Dark mode (`#08111F`, `#0D1B2A`, `#111F34`, `#F2F5FA`, `#9AA9BD`) ensuring WCAG AA contrast.
- **In-App User Guide (`src/components/guide/UserGuide.tsx`, `WorkspaceApp.tsx`)**: Replaced raw markdown file lists with an interactive 12-section user guide covering operational workflows, diagnostic error models, deterministic gate rules, 5 hackathon judging criteria (Reusability, Governance & Responsibility, ROI/Business Value, MVP Readiness, Originality & Innovation), and an interactive 6-step demo walkthrough with direct tab jump buttons.

#### Layer 7: End-to-End Workflow Orchestration, Human Authorization Boundary, and Outcome Reporting
- **Master 13-Stage Workflow State Machine (`fidelitygate/workflow/orchestrator.py`)**: End-to-end orchestration across the complete operational lifecycle: `RECEIVED → VALIDATING → TRIAGE → INVESTIGATION → CANDIDATE_EVALUATION → COUNTEREXAMPLE_ANALYSIS → ADAPTIVE_DIAGNOSTICS → REEVALUATION → EXPLANATION → GATE_REVIEW → AWAITING_HUMAN_APPROVAL → SIMULATED_ACTION → OUTCOME_REPORTED`. Employs monotonically sequenced audit events ($1 \dots N$).
- **Strict Human Authorization Boundary (`fidelitygate/workflow/simulation_adapter.py`)**: Enforces safety invariants: Human operators cannot override gate `ABSTAIN` decisions (violating mandatory safety constraints fails closed); human rejection halts execution cleanly; authorizations require fresh evidence tokens (`fidelitygate-v1.0`); duplicate authorizations are idempotent.
- **Isolated Digital-Twin Intervention Execution (`fidelitygate/workflow/simulation_adapter.py`)**: Interventions are simulated strictly in `ISOLATED_DIGITAL_TWIN` mode, guaranteeing zero unintended real-world router reconfiguration.
- **Dynamic Outcome Reporting & Integrity Audit (`fidelitygate/workflow/outcome.py`, `simulation_adapter.py`)**: Computes mathematically rigorous before/after comparative metrics from actual network state:
  - Latency Shift: $L_{\text{after}} - L_{\text{before}}$ and relative percentage $100 \cdot (L_{\text{after}} - L_{\text{before}}) / L_{\text{before}}$.
  - Peak Edge Utilization: evaluates the identical set of network links before and after ($100 \cdot \max_e \rho_e$).
  - Dynamic Bottleneck Link: identifies the link with maximum candidate utilization (e.g. `e_leaf1_spine2`), eliminating hardcoded fallback strings.
  - Network-Wide Constraint Breaches: counts all links violating capacity and all flows violating latency SLOs across the entire topology.
  - Documented Impact Classification: `IMPROVED`, `REGRESSED`, `MIXED`, `UNCHANGED`. Any action introducing a new capacity or SLO breach is classified as `REGRESSED` even if target flow latency improves.
  - Provenance & Traceability: records baseline and post-action evaluation IDs, model version (`fidelitygate-v1.0`), affected flow lists, and units.
- **Interactive Next.js Control Panel (`src/components/workspace/WorkflowOrchestrationPanel.tsx`)**: Dedicated "Workflow & Approval" dashboard tab with real-time stage progression visualization, operator authorization form, dynamic outcome metrics cards (with conditional styling for breaches), and audit event stream.
- **Layer 7 REST API & CLI**: Exposes 8 REST endpoints under `/api/v1/workflows/*`, CLI subcommands, standalone runner `scripts/run_workflow.py`, and live verification script `scripts/verify_outcome_integrity.py`.

#### Layer 8: Shared Run Context, Enterprise UX, In-App User Guide & Guided Auto Demo Mode
- **Shared Run Context (`src/context/WorkflowRunContext.tsx`)**: Establishes a single authoritative source of truth for the active workflow run (`selectedWorkflowRunId`, `selectedWorkflow`, `workflowEvents`, `approvalRecord`, `outcomeReport`). Eliminates misleading in-memory fallbacks, unprompted auto-investigations, and hardcoded mock metrics.
- **Enterprise UX & 3D Interactive Network Globe (`src/components/landing/`)**: Features an interactive Three.js network globe with 4,312 continental landmass dots, 10 global network hubs, curved 3D Bézier arcs, traveling signal packets, atmospheric pure CSS mesh gradients (`.dark-mesh-bg`, `.workspace-mesh-bg`), and a high-contrast dual-theme semantic token system.
- **Interactive In-App User Guide (`src/components/guide/UserGuide.tsx`)**: 12 structured interactive sections covering technical modules, Hackathon Judging Criteria Alignment (Reusability, Governance & Responsibility, ROI/Business Value, MVP Readiness, Originality & Innovation), and an interactive 6-step demo walkthrough with direct tab jump buttons.
- **Guided Auto Demo Mode (`src/hooks/useAutoDemo.ts`, `src/components/demo/`)**:
  - **Prominent Tab Navigation Control**: Dedicated "Auto Demo" button (`Play` / `Square` icons) integrated directly into the workspace tab bar with live active indicator (`Demo Running`).
  - **Status-Aware Transition Popups (`AutoDemoModal.tsx`)**: Displays an orienting dialog before each tab switch announcing real persisted workflow status, 1-2 lines explaining what the target tab proves, and Continue/Skip/Stop controls with auto-advance countdown.
  - **Floating Viewing Dwell Bar (`AutoDemoFloatingControl.tsx`)**: 5-second dwell interval on each tab with step counter (e.g. `Step 2 of 8: Workflow & Approval`), Pause/Resume, Next, and Stop controls.
  - **Strict Human Approval Boundary Safety**: Automatically pauses at Stage 11 (`AWAITING_HUMAN_APPROVAL`); never auto-authorizes or triggers consequential mutations. Resumes seamlessly once an operator authorizes manually.
  - **Honest Status Reporting**: Reflects exact runtime truth—`ABSTAIN`, `GATHER_EVIDENCE`, `REJECTED_BY_HUMAN`, missing explanations, or completed outcomes without fabrication.
  - **Keyboard Navigation**: Press <kbd>Esc</kbd> to exit, <kbd>Space</kbd> to pause/resume, and <kbd>Enter</kbd> to continue.

---

## 2. Directory Structure

```
├── data/
│   ├── raw/cisco_telemetry/     # Approved raw telemetry datasets (baseline, anomaly)
│   ├── processed/               # Normalized observations (.jsonl)
│   ├── manifests/               # DatasetSourceManifest JSON records
│   ├── reports/                 # IngestionReport JSON records
│   └── quarantine/              # Quarantined malformed rows for audit review
├── docs/                        # Architecture, contracts, datasets, and methodology
│   ├── ARCHITECTURE.md          # System architecture and ingestion pipeline flow
│   ├── CONTRACTS.md             # Pydantic schemas and TypeScript client types
│   ├── CURRENT_STATUS.md        # Real-time implementation and verification status
│   ├── DATASETS.md              # Dataset catalog, field mapping, and limitations
│   ├── DECISIONS.md             # Architecture Decision Records (ADRs)
│   ├── HANDOFF.md               # Session handoff notes and next layer roadmap
│   ├── METHODOLOGY.md           # Normalization rules, unit integrity, math formulation
│   └── TEST_REPORT.md           # Automated test execution results
├── fidelitygate/                # Authoritative Python modular monolith
│   ├── api/app.py               # Canonical FastAPI REST backend (:8000)
│   ├── ingestion/               # Layer 1 Ingestion, validation, and quarantine engine
│   ├── triage/                  # Layer 2 Anomaly triage, correlation, and context builder
│   ├── investigation/           # Layer 3 Bounded agentic investigation & diagnostic planning
│   │   ├── models.py            # Typed investigation contracts (Hypothesis, DiagnosticPlan, Events)
│   │   ├── tools.py             # Strict allowlisted ToolRegistry with permission enforcement
│   │   ├── llm_adapter.py       # Quota-aware LLM adapter with bounded single repair attempt
│   │   ├── investigator.py      # Agent A: Anomaly Investigator
│   │   ├── planner.py           # Agent B: Diagnostic & Mitigation Planner
│   │   └── orchestrator.py      # State machine orchestrator & event bus
│   ├── evaluation/              # Layer 4 Candidate mitigation evaluation & digital-twin simulation
│   │   ├── models.py            # Typed evaluation contracts (CandidateAction, SimulationPrediction, Reports)
│   │   ├── topologies.py        # Canonical scenario topologies (wan_congestion, fiber_drift, traffic_burst)
│   │   ├── validator.py         # Path & topology topological validator
│   │   ├── simulator.py         # Multi-commodity digital-twin queueing simulator
│   │   ├── uncertainty_evaluator.py # Bounded uncertainty sweeper & counterexample extractor
│   │   ├── reference_evaluator.py   # Isolated offline reference evaluator
│   │   └── engine.py            # Mitigation evaluation orchestrator & gate decider
│   ├── adaptive/                # Layer 5 Counterexample-guided adaptive diagnostics & re-evaluation
│   │   ├── models.py            # Typed adaptive contracts (DiagnosticObservation, UncertaintyUpdate, Reports)
│   │   ├── measurement_registry.py # Allowlisted measurement error models & observation simulators
│   │   ├── uncertainty_updater.py  # Bounded interval intersection & inconsistency detection
│   │   ├── selector.py          # Decision-relevance diagnostic selector & ranking policy
│   │   └── engine.py            # Adaptive investigation loop orchestrator & persistence
│   ├── xai/                     # Layer 6 Evidence-based explainable AI & sensitivity analysis
│   │   ├── models.py            # Typed XAI contracts (GateRuleExplanation, CounterexampleExplanation, etc.)
│   │   ├── rule_explainer.py    # 5-predicate deterministic gate rule evaluator
│   │   ├── counterexample_explainer.py # Exact perturbation vector & margin breach explainer
│   │   ├── measurement_explainer.py # Physical-to-parameter inversion & interval update explainer
│   │   ├── sensitivity_analyzer.py  # Deterministic OAT sensitivity gradients & counterfactuals
│   │   ├── summary_generator.py # Zero-hallucination deterministic summary generator
│   │   └── engine.py            # Cross-layer ExplanationEngine & SQLite persistence
│   ├── workflow/                # Layer 7 End-to-end orchestration & human approval
│   │   ├── models.py            # Typed workflow contracts (WorkflowStage, ApprovalDecision, OutcomeReport)
│   │   ├── orchestrator.py      # Master 13-stage deterministic state machine orchestrator
│   │   ├── simulation_adapter.py# Isolated twin simulation executor & authorization boundary
│   │   └── outcome.py           # Pre vs post comparative outcome evaluator & reporter
│   ├── config.py                # Central Pydantic settings configuration
│   ├── storage.py               # SQLite ACID persistence engine (ingestions, triage, investigations, evaluations, adaptive, explanations, workflows)
│   ├── scenarios.py             # Registered network benchmark scenarios
│   ├── twin.py                  # Convex M/M/1 queueing delay twin model
│   ├── uncertainty.py           # Multidimensional parameter sweep engine
│   ├── counterexample.py        # Counterexample search engine
│   ├── diagnostics.py           # Diagnostic probe registry & error models
│   ├── decision_gate.py         # Deterministic gate policy
│   ├── baseline_evaluator.py    # 4-way scientific baseline comparison
│   └── cli.py                   # Python CLI command bridge
├── scripts/
│   ├── download_datasets.py     # Reproducible Cisco telemetry downloader
│   ├── ingest_dataset.py        # CLI ingestion runner
│   ├── validate_dataset.py      # Dry-run validation tool
│   ├── prepare_sample_subsets.py# Sample subset extractor
│   ├── run_triage.py            # Layer 2 triage execution runner
│   ├── run_investigation.py     # Layer 3 agentic investigation runner
│   ├── run_mitigation_evaluation.py # Layer 4 mitigation evaluation & digital-twin runner
│   ├── run_adaptive_investigation.py # Layer 5 adaptive diagnostic & re-evaluation runner
│   ├── run_explanation.py       # Layer 6 evidence-based XAI decision attribution runner
│   ├── run_workflow.py          # Layer 7 end-to-end workflow runner (pause at gate / auto-approve)
│   └── verify_layer7_live.py    # Layer 7 live full-stack automated verification script
├── src/                         # Next.js 14 App Router frontend (:3000)
│   ├── app/                     # Pages and API route handlers (18 static & dynamic routes)
│   ├── components/              # Workspace, Landing, Topology, Trace, XAI, Workflow, and Demo components
│   │   ├── demo/                # AutoDemoModal, AutoDemoFloatingControl, NoWorkflowModal, CompletionModal
│   │   ├── guide/               # Interactive 12-section in-app User Guide
│   │   ├── landing/             # HeroSection, InteractiveNetworkGlobe 3D Three.js visualizer
│   │   ├── xai/                 # DecisionExplanationPanel interactive XAI audit interface
│   │   └── workspace/           # WorkflowOrchestrationPanel, DecisionWorkspace, Nexus Core
│   └── types/index.ts           # Authoritative TypeScript client contracts
│   ├── config/autoDemoSteps.ts  # Data-driven configuration for 8 workspace demo tabs
│   ├── hooks/useAutoDemo.ts     # Guided tour state machine and dwell interval manager
│   └── context/                 # Canonical WorkflowRunContext shared state provider
├── tests/                       # Pytest automated test suite (171 unit & integration tests)
│   ├── fixtures/                # Offline test fixtures (valid, malformed, empty)
│   ├── test_auto_demo_mode.py   # Comprehensive 8-point Auto Demo mode test suite
│   ├── test_layer8a_integration.py # Comprehensive 5-point Shared Context test suite
│   ├── test_ingestion_pipeline.py # Comprehensive 16-point Layer 1 test suite
│   ├── test_anomaly_triage.py   # Comprehensive 22-point Layer 2 test suite
│   ├── test_agentic_investigation.py # Comprehensive 22-point Layer 3 test suite
│   ├── test_candidate_evaluation.py # Comprehensive 26-point Layer 4 test suite
│   ├── test_adaptive_investigation.py # Comprehensive 24-point Layer 5 test suite
│   ├── test_xai_explanations.py # Comprehensive 19-point Layer 6 test suite
│   ├── test_workflow_orchestration.py # Comprehensive 12-point Layer 7 test suite
│   └── test_outcome_integrity.py # Comprehensive 6-point Outcome Integrity & Sensitivity test suite
├── start-dev.js                 # Unified full-stack development launcher
└── requirements.txt             # Python backend dependencies
```

---

## 3. Quick Start & Startup Commands

### Prerequisites
- Node.js 18+ & npm
- Python 3.11+ & pip

### 1. Installation
```bash
# 1. Install frontend dependencies
npm install

# 2. Install backend dependencies
pip install -r requirements.txt
```

### 2. Dataset Acquisition & Ingestion
```bash
# Download Cisco Innovation Edge baseline and anomaly datasets
python scripts/download_datasets.py --dataset all

# Extract calibrated 1,000-row sample subsets for rapid verification
python scripts/prepare_sample_subsets.py

# Ingest baseline telemetry into FidelityGate
python scripts/ingest_dataset.py --file data/raw/cisco_telemetry/0/baseline_sample_1000.csv --source-id cisco-ie-telemetry-baseline

# Ingest BGP clear anomaly telemetry into FidelityGate
python scripts/ingest_dataset.py --file data/raw/cisco_telemetry/3/bgpclear_sample_1000.csv --source-id cisco-ie-telemetry-bgpclear

# Execute Layer 2 Anomaly Triage & Evidence Correlation
python scripts/run_triage.py --ingestion-id ing-f2189c69 --case-file data/raw/cisco_telemetry/3/bgpclear_casedata.txt --output-json data/reports/triage_bgpclear.json

# Execute Layer 3 Bounded Agentic Investigation & Diagnostic Planning
python scripts/run_investigation.py --triage-run-id trg-63c67858 --scenario-id wan_congestion --output-json data/reports/investigation_bgpclear.json

# Execute Layer 4 Candidate Mitigation Evaluation & Digital-Twin Simulation
python scripts/run_mitigation_evaluation.py --investigation-id inv-1248ea0e --scenario-id wan_congestion --include-reference --output-json data/reports/mitigation_bgpclear.json

# Execute Layer 5 Counterexample-Guided Adaptive Diagnostics & Re-evaluation
python scripts/run_adaptive_investigation.py --evaluation-id eval-9e86b738 --output-json data/reports/adaptive_report.json

# Execute Layer 6 Evidence-Based Explainable AI & Decision Attribution
python scripts/run_explanation.py --output-json data/reports/explanation_report.json

# Execute Layer 7 End-to-End Workflow & Human Authorization
python scripts/run_workflow.py --scenario wan_congestion

# Run Live Full-Stack Verification (FastAPI :8000 & Next.js :3000)
python scripts/verify_layer7_live.py
```

### 3. Start the Full-Stack Application
```bash
# Starts canonical FastAPI backend (:8000) and Next.js frontend (:3000) simultaneously:
node start-dev.js
```
- **Next.js Frontend**: [http://localhost:3000](http://localhost:3000)
- **Engineering Workspace**: [http://localhost:3000/workspace](http://localhost:3000/workspace)
- **FastAPI Canonical Backend**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

Alternatively, start services independently:
```bash
# Start FastAPI backend only
python -m uvicorn fidelitygate.api.app:app --host 127.0.0.1 --port 8000

# Start Next.js frontend only
npm run dev
```

---

## 4. API Endpoints (Layers 1–7)

### Data Ingestion Endpoints (Layer 1)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /api/v1/health` | `GET` | System health check (database connection, storage, environment) |
| `GET /api/v1/sources` | `GET` | List registered dataset source manifests |
| `GET /api/v1/sources/{source_id}` | `GET` | Query specific dataset source manifest and SHA-256 checksum |
| `POST /api/v1/ingestions` | `POST` | Execute ingestion pipeline on a registered source file |
| `GET /api/v1/ingestions` | `GET` | Query list of recent ingestion summaries |
| `GET /api/v1/ingestions/{id}` | `GET` | Query single ingestion run status and row counts |
| `GET /api/v1/ingestions/{id}/report` | `GET` | Retrieve full detailed audit report with quality issues |
| `GET /api/v1/ingestions/{id}/quarantine` | `GET` | Inspect quarantined malformed rows |

### Anomaly Triage & Correlation Endpoints (Layer 2)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/triage` | `POST` | Execute anomaly triage and correlation on ingested telemetry |
| `GET /api/v1/triage` | `GET` | List recent anomaly triage execution summaries |
| `GET /api/v1/triage/{id}` | `GET` | Query summary metrics for a specific triage run |
| `GET /api/v1/triage/{id}/findings` | `GET` | Query candidate anomaly findings identified during triage |
| `GET /api/v1/triage/{id}/correlation` | `GET` | Retrieve deterministic correlation report linking findings and evidence |
| `GET /api/v1/triage/{id}/context` | `GET` | Retrieve typed InvestigationContext for downstream Layer 3 agents |

### Agentic Investigation & Diagnostic Planning Endpoints (Layer 3)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/investigations` | `POST` | Run bounded agentic investigation & diagnostic planning from triage context |
| `GET /api/v1/investigations` | `GET` | List recent agentic investigation execution summaries |
| `GET /api/v1/investigations/{id}` | `GET` | Query single investigation run summary and execution status |
| `GET /api/v1/investigations/{id}/report` | `GET` | Retrieve full InvestigationReport including hypotheses and confidence |
| `GET /api/v1/investigations/{id}/plan` | `GET` | Retrieve DiagnosticPlan with ranked candidate probes and reroute proposals |
| `GET /api/v1/investigations/{id}/events` | `GET` | Query monotonically sequenced audit events recorded during investigation |

### Candidate Mitigation Evaluation & Digital-Twin Endpoints (Layer 4)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/mitigation-evaluations` | `POST` | Evaluate proposed candidate reroutes via digital twin and bounded uncertainty sweeps |
| `GET /api/v1/mitigation-evaluations` | `GET` | List recent candidate mitigation evaluation summaries |
| `GET /api/v1/mitigation-evaluations/{id}` | `GET` | Query single mitigation evaluation summary and gate decision |
| `GET /api/v1/mitigation-evaluations/{id}/candidates` | `GET` | Query detailed validation, simulation, and counterexample results for evaluated candidates |
| `GET /api/v1/mitigation-evaluations/{id}/report` | `GET` | Retrieve full MitigationEvaluationReport including comparisons and gate justification |
| `GET /api/v1/mitigation-evaluations/{id}/events` | `GET` | Query monotonically sequenced audit events recorded during simulation and gate evaluation |

### Adaptive Diagnostics & Re-evaluation Endpoints (Layer 5)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/adaptive-investigations` | `POST` | Launch counterexample-guided adaptive diagnostic loop and digital-twin re-evaluation |
| `GET /api/v1/adaptive-investigations` | `GET` | List recent adaptive investigation summaries |
| `GET /api/v1/adaptive-investigations/{id}` | `GET` | Query single adaptive investigation summary and decision transitions |
| `GET /api/v1/adaptive-investigations/{id}/report` | `GET` | Retrieve full AdaptiveInvestigationReport with cycle-by-cycle interval updates |
| `GET /api/v1/adaptive-investigations/{id}/events` | `GET` | Query monotonically sequenced audit events recorded during adaptive execution |

### Explainable AI & Decision Attribution Endpoints (Layer 6)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/explanations` | `POST` | Generate authoritative evidence-based DecisionExplanation |
| `GET /api/v1/explanations` | `GET` | List recent explanation summaries |
| `GET /api/v1/explanations/{id}` | `GET` | Retrieve single DecisionExplanation by ID |
| `GET /api/v1/explanations/{id}/rules` | `GET` | Retrieve rule-by-rule gate predicates and observed evaluations |
| `GET /api/v1/explanations/{id}/sensitivity` | `GET` | Retrieve local sensitivity gradients and counterfactual edge perturbations |

### End-to-End Workflow & Human Approval Endpoints (Layer 7)
| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `POST /api/v1/workflows` | `POST` | Initiate 13-stage workflow run (pauses at human approval boundary by default) |
| `GET /api/v1/workflows` | `GET` | List recent workflow execution summaries |
| `GET /api/v1/workflows/{id}` | `GET` | Query workflow run summary, current stage, and gate status |
| `GET /api/v1/workflows/{id}/events` | `GET` | Retrieve monotonically sequenced audit events trail |
| `POST /api/v1/workflows/{id}/approval` | `POST` | Record human authorization, rejection, or changes requested |
| `GET /api/v1/workflows/{id}/approval` | `GET` | Fetch recorded human approval record for workflow run |
| `GET /api/v1/workflows/{id}/outcome` | `GET` | Retrieve comparative pre vs post intervention outcome report |
| `GET /api/v1/workflows/outcomes/latest` | `GET` | Fetch most recent intervention outcome report |

---

## 5. Verification & Test Suite

Run the complete backend automated test suite:
```bash
python -m pytest -v
```
*Current Result: 171 of 171 tests passing (100% pass rate).*
- 8 tests in `tests/test_auto_demo_mode.py` (Auto Demo state machine, 8 workspace tabs, awaiting approval boundary, completed outcome reporting, terminal abstention / operator rejection precedence, honest missing explanation fallback, SQLite DB run retrieval, empty context safety).
- 5 tests in `tests/test_layer8a_integration.py` (Canonical workflow persistence, distinct artifact ID namespaces, CLI bridge parity, stale artifact isolation, human rejection halts).
- 6 tests in `tests/test_outcome_integrity.py` (Post-intervention outcome reproducibility, candidate sensitivity, scenario sensitivity, constraint regressions, fail-closed invalid actions, outcome reporter checks).
- 19 tests in `tests/test_xai_explanations.py` (Layer 6 evidence-based XAI, 5 gate predicates, counterexample vectors, physical unit inversion, sensitivity gradients, controlled run equivalence, 404/400 validation, contract structure).
- 12 tests in `tests/test_workflow_orchestration.py` (Layer 7 master 13-stage state machine, human approval boundary, stale approval rejection, duplicate idempotency, monotonic events, isolated twin execution, constraint regression, outcome reporting).
- 24 tests in `tests/test_adaptive_investigation.py` (Layer 5 adaptive diagnostics, allowlisted registry, measurement-error models, interval intersection, inconsistency detection, cycle budget limits, simulation budgets).
- 26 tests in `tests/test_candidate_evaluation.py` (Layer 4 mitigation evaluation, path validation, digital-twin fluid simulation, convex queueing delay, bottleneck identification, sweeps, counterexamples).
- 22 tests in `tests/test_agentic_investigation.py` (Layer 3 bounded agent workflows, Agent A hypotheses, Agent B diagnostic ranking, allowlisted tool registry, quota exhaustion tracking, deterministic fallback).
- 22 tests in `tests/test_anomaly_triage.py` (Layer 2 triage, robust MAD, invariant series fallback, step change, case metadata, temporal/entity correlation, non-causal descriptors).
- 16 tests in `tests/test_ingestion_pipeline.py` (Layer 1 ingestion, checksums, idempotency, path safety, quarantine, data modes).
- 11 tests in legacy test modules (CLI, baseline evaluator, decision gate, uncertainty sweeps).

Verify Next.js production build:
```bash
npm run build
```
*Current Result: 18 of 18 static/dynamic pages and route handlers compiled cleanly with 0 errors.*

Check code style and linting:
```bash
npm run lint
```
*Current Result: 0 ESLint warnings or errors.*

---

## 6. Environment Configuration (`.env.example`)

```ini
# Frontend & App URLs
NEXT_PUBLIC_APP_URL=http://localhost:3000
NEXT_PUBLIC_DEMO_MODE=true

# Canonical Backend & Ingestion Engine
BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
APP_ENV=development
DEBUG=false
DATA_ROOT=data
MAX_FILE_SIZE_MB=100

# Persistence & Storage
DATABASE_PATH=fidelitygate.db
PYTHON_EXEC_PATH=python

# Layer 3 Agent & LLM Configuration
LLM_PROVIDER=DETERMINISTIC_BASELINE
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
AGENT_A_MAX_TOOL_CALLS=5
AGENT_B_MAX_DIAGNOSTICS=2
AGENT_TIMEOUT_SECONDS=10.0
AGENT_MAX_REPAIR_ATTEMPTS=1
```

---

## 7. Troubleshooting

- **`ModuleNotFoundError: No module named 'fidelitygate'`**:  
  Ensure `PYTHONPATH` includes the project root: `set PYTHONPATH=.` (Windows PowerShell: `$env:PYTHONPATH="."`) or invoke via `python -m pytest`.
- **Port Conflict on 8000 or 3000**:  
  Update `BACKEND_PORT` in `.env` or pass `--port` to uvicorn / `next dev -p <port>`.
- **Unsafe Path Error (`IngestionSecurityError`)**:  
  Ingestion files must reside inside `data/raw/` or project fixtures. Paths with `..` or absolute external paths are rejected by design.
- **Large Dataset Ingestion Memory**:  
  Full `.csv.gz` files containing 500,000+ rows should be processed using `scripts/ingest_dataset.py` with streaming sinks or sample subsets created via `scripts/prepare_sample_subsets.py`.
