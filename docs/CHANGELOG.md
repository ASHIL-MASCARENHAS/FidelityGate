# FidelityGate — Changelog

All notable changes to this project are documented in this file per `DOCUMENTATION_AND_CHANGELOG_RULES.md`.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Final Frontend Refinement: Enterprise UX, Interactive Network Globe & In-App User Guide

### Added
- **Interactive Three.js 3D Network Globe (`src/components/landing/InteractiveNetworkGlobe.tsx`)**:
  - 3D dark spherical core ($R = 2.0$) with electric-cyan atmospheric glow shell ($R = 2.04$).
  - 4,312 realistically positioned continental landmass dots sampled at 3° resolution and filtered by an inland geographical polygon model.
  - 10 real-world strategic network hubs (Frankfurt, London, New York, Silicon Valley, Tokyo, Singapore, Zurich, São Paulo, Sydney, Mumbai).
  - Curved 3D Bézier great-circle connection arcs with animated travelling cyan and blue signal packet streams.
  - Interactive mouse and touch drag rotation with inertia damping (`lerp(current, target, 0.05)`), gentle auto-rotation when idle, and `prefers-reduced-motion` compliance.
  - Accessible WebGL fallback and an explicit scientific integrity footnote badge: *"Illustrative Network Simulation · Illustrative Topology Arcs"*.
- **Atmospheric Pure CSS Mesh Gradients (`src/app/globals.css`, `tailwind.config.ts`)**:
  - High-performance, GPU-accelerated fixed-attachment radial gradient layering (`.dark-mesh-bg`, `.workspace-mesh-bg`, `.light-mesh-bg`) with deep navy ground (`#08111F`), elevated surfaces (`#0D1B2A`, `#111F34`), hairline borders (`#22334A`), and restrained electric cyan (`#55D9F4`) and cobalt (`#4169F5`) accents.
  - High-contrast dual-theme semantic token system (`paper`, `surface`, `ink`, `muted`, `cobalt`, `cyan`, `hairline`, `amber`, `emerald`, `rose`) eliminating washed-out grays and ensuring WCAG AA contrast.
- **In-App User Guide (`src/components/guide/UserGuide.tsx`, `src/components/workspace/WorkspaceApp.tsx`)**:
  - Replaced the generic raw markdown file list in the workspace with an interactive 12-section User Guide.
  - Detailed technical modules covering Start Guide, Workflow Execution, Anomaly Triage & Robust MAD, Candidate Evaluation & Twin Simulation, Bounded Counterexample Sweeps, Adaptive Diagnostics & Error Models, Explainable AI & Attribution, Human Authorization Boundary, Safe Fallbacks, and Architecture Invariants.
  - **Hackathon Judging Criteria Alignment**: Explicitly maps platform capabilities to the 5 competition criteria: Reusability, Governance & Responsibility, ROI/Business Value, MVP Readiness, and Originality & Innovation.
  - **Interactive 6-Step Demo Walkthrough**: Includes step-by-step guidance and direct one-click tab jump buttons navigating operators between Workflow, Explainable AI, Topology, and User Guide views.

### Refined
- **Minimal, Bold Hero Section (`src/components/landing/HeroSection.tsx`, `Navbar.tsx`)**:
  - Simplified landing page hero around the dominant product title **FidelityGate**, eliminating verbose marketing claims and dense paragraphs.
  - Added clear operating rule callout: *"Agents investigate and recommend. Deterministic software calculates and enforces. Explanations expose the evidence. A human authorizes consequential actions."*
  - Streamlined primary CTA ("Explore the platform"), secondary CTA ("How it works"), and compact technical capability tags.
  - Integrated the Three.js Interactive Network Globe seamlessly into the hero grid.
- **Navbar & Navigation Consistency**:
  - Connected the Navbar "User Guide" link directly to the workspace User Guide tab.
  - Added `guide` tab into `WorkspaceApp.tsx` navigation bar with `BookOpen` icon, smooth Framer Motion transitions, and preserved backward compatibility with legacy `docs` routes.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 8A: Shared Run Context, Cross-Tab Integration & Fallback Removal

### Added
- **Shared Canonical Run Context (`src/context/WorkflowRunContext.tsx`)**:
  - Created `WorkflowRunProvider` and `useWorkflowRun()` managing canonical `selectedWorkflow`, `workflowEvents`, `approvalRecord`, and `outcomeReport`.
  - Added race condition prevention (`activeFetchIdRef`) ensuring sequential artifact fetching.
  - Linked `triage_run_id`, `investigation_id`, `evaluation_id`, `adaptive_run_id`, `explanation_id`, `approval_id`, and `outcome_id` to all child components.
- **CLI Bridge Workflow Commands (`fidelitygate/cli.py`)**:
  - Added `get-workflow-events` CLI command printing sequenced stage transition events as JSON.
  - Enhanced `list-workflows` to flexibly support `--limit <n>` flags.
  - Enhanced `approve-workflow` to parse both flagged (`--decision`, `--reviewer`, `--comment`) and positional arguments.
- **Dedicated Layer 8A Test Suite (`tests/test_layer8a_integration.py`)**:
  - `test_canonical_workflow_persistence`: Authoritative SQLite persistence of full workflow runs.
  - `test_artifact_id_namespaces_and_distinction`: Strict uniqueness and non-interchangeability of phase IDs (`trg-`, `inv-`, `eval-`, `adapt-`, `expl-`).
  - `test_cli_bridge_parity`: Verification of CLI bridge output structure for workflow events and approvals.
  - `test_stale_artifacts_isolation`: Guarantees new runs start with empty approval/outcome records.
  - `test_human_rejection_halts_workflow`: Terminal rejection leaves outcome empty and fails closed.

### Fixed & Removed
- **Removed Misleading In-Memory Fallbacks**:
  - Deleted `generateLocalFallbackInvestigation` in `WorkspaceApp.tsx`.
  - Removed unprompted `useEffect([selectedKey])` auto-investigations on scenario change.
  - Removed `Math.random()` and 2-second interval in `FidelityMonitoringRecharts.tsx`; distribution metrics now derive from real SQLite runs.
  - Removed fake benchmark fallback rows in `EvaluationLab.tsx`.
  - Removed fake hardcoded runs (1042, 1041) in `RunHistory.tsx` and `WorkspaceApp.tsx`.
  - Removed hardcoded fallback counts (`|| 8`, `|| 5`, `|| 2`, `'86.7%'`, `'18.0 ms'`) in `DecisionWorkspace.tsx`.
  - Replaced hardcoded `'42 MB'` memory in `SettingsDiagnostics.tsx` with live `/api/diagnostics` consumption.
  - Clarified radial network topology node coordinates as display-only geometric layout and labeled Rive canvas buttons as illustrative motion previews.
- **Integrated All Workspace Tabs**:
  - `WorkflowOrchestrationPanel`: Synchronizes active workflow with shared context on run creation and approval.
  - `DecisionWorkspace`: Displays canonical evaluation ID, candidate ID, and gate verdict from shared run.
  - `DecisionExplanationPanel`: Direct fetching via `GET /api/v1/explanations/{id}` with honest empty state.
  - `ExecutionTraceView`: Directly consumes real sequenced `workflowEvents`.
  - `RunHistory`: "Load in Workspace" selects run in shared context and switches to workflow inspection.
  - `HumanApprovalModal`: Bound to real workflow ID and candidate ID, triggering backend approval mutations.

## 2026-10-24 — P0 Outcome Integrity, Dynamic Simulation Verification & Full-Workflow Audit

### Fixed
- **Root Cause of Repeated Demonstration Outcomes**:
  - Identified that repeated identical numbers ($26.55 \to 23.00$ ms, $-3.55$ ms, $76.0\% \to 50.0\%$, $0$ breaches, `IMPROVED`) were mathematically valid deterministic outputs produced by running the identical scenario (`wan_congestion`) with the identical candidate ($R\text{-reroute-alt1}$) under the deterministic fluid queueing simulator.
  - Aligned frontend scenario dropdown in `WorkflowOrchestrationPanel.tsx` with actual supported backend scenarios (`wan_congestion`, `fiber_drift`, `traffic_burst`, `cisco_bgp_clear`), replacing non-existent topologies (`cisco_transceiver`, `packet_drop_burst`) that caused validation failure and forced users into `wan_congestion`.
  - Added canonical topology for `cisco_bgp_clear` in `fidelitygate/evaluation/topologies.py` and `fidelitygate/scenarios.py`.
- **Eliminated Hardcoded Strings and Fallbacks**:
  - Removed hardcoded fallback bottleneck link `"cr01.lon-cr01.par"` in `fidelitygate/workflow/simulation_adapter.py`. Bottleneck link is now dynamically derived as the link with maximum candidate utilization.
  - Removed hardcoded display fallback `'R-alt1 (cr01.lon -> cr01.par -> cr01.fra)'` in `WorkflowOrchestrationPanel.tsx`.
  - Removed hardcoded green presentation strings (`"All edges compliant"`, `"SLA contract satisfied"`). UI now dynamically renders warning/breach badges if capacity violations or SLO violations exceed zero.
  - Removed fallback candidate in `fidelitygate/workflow/orchestrator.py` that created dummy nodes on missing evaluation.
- **Network-Wide Metric Scope & Precise Formulation**:
  - In `fidelitygate/workflow/simulation_adapter.py`: Capacity violations are now calculated across all links in the topology ($V_{\text{cap}} = \sum_{e \in E} \mathbf{1}(\rho_e > 1.00)$) before and after action.
  - SLO violations are now evaluated across all traffic flows in the topology ($V_{\text{slo}} = \sum_{f \in F} \mathbf{1}(L_f > \text{SLO}_f)$) before and after action.
  - Peak edge utilization is evaluated across the exact same set of links before and after.
  - Added `CandidatePathValidator` check in `SimulationActionAdapter.execute_intervention` to fail closed if a candidate path has disconnected hops or missing nodes.
  - Added `MIXED` and `UNCHANGED` to `OverallImpact` in `models.py` and `src/types/index.ts`.
  - Added traceability metadata (`baseline_evaluation_id`, `post_action_evaluation_id`, `model_version`, `metric_status`, `units`) to `InterventionOutcomeReport`.
  - Fixed attribute names in `orchestrator.py` for `adapt_summary.diagnostics_executed_count` and `adapt_summary.total_diagnostic_cost_usd`.

### Added
- **Dedicated Outcome Integrity Test Suite (`tests/test_outcome_integrity.py`)**:
  - `test_outcome_reproducibility`: Same scenario/candidate produces exact deterministic numbers while maintaining distinct workflow and outcome IDs.
  - `test_outcome_candidate_sensitivity`: Candidates $R\text{-alt1}$ vs $R\text{-nominal}$ produce physically distinct metrics ($23.00$ ms vs $26.55$ ms, $50.0\%$ vs $76.0\%$, `IMPROVED` vs `UNCHANGED`).
  - `test_outcome_scenario_sensitivity`: Scenarios `wan_congestion` vs `fiber_drift` produce distinct metrics ($26.55 \to 23.00$ ms vs $35.83 \to 32.85$ ms).
  - `test_outcome_constraint_regression`: Action improving target flow latency but creating link overload reports capacity breaches and classifies strictly as `REGRESSED`.
  - `test_outcome_invalid_action_fails_closed`: Disconnected/unknown node candidate paths raise `ValueError` before simulation.
  - `test_outcome_reporter_integrity_checks`: `OutcomeReporter` validates against false `IMPROVED` claims when violations increase.
- **Full Verification Script (`scripts/verify_outcome_integrity.py`)**:
  - Live multi-run audit verifying reproducibility, sensitivity, gate abstention, and contract parity.
- **Repository Automated Tests**:
  - Expanded from 152 to **158 passing tests (100% pass rate)**.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — P0 XAI Runtime & Data-Contract Repair

### Fixed
- **Frontend TypeError in `DecisionExplanationPanel.tsx`**:
  - Eliminated runtime crash (`Cannot read properties of undefined (reading 'length')`) at `Gate Rules ({explanation.constraint_results.length})`.
  - Removed faulty client-side fallback in `fetchExplanation` that previously requested `/api/v1/explanations?limit=1` and stored a lightweight `ExplanationSummary` missing detailed arrays into component state.
  - Added `normalizeExplanation` data boundary defensively ensuring `constraint_results`, `evidence_items`, `uncertainty_changes`, `limitations`, `unresolved_questions`, and `supporting_findings` are always valid arrays.
  - Implemented comprehensive rendering states for Loading, Error (with interactive "Retry Synthesis" button), Empty, and all 5 explanation tabs.
- **Identifier Fabrication & Namespace Pollution**:
  - In `src/components/workspace/DecisionWorkspace.tsx`: Stopped prepending `'eval-'` to integer run IDs (`eval-${investigationResult.run_id}`).
  - In `src/components/workspace/WorkspaceApp.tsx`: Stopped passing integer run IDs as `adaptiveRunId`.
  - Fixed TypeScript narrowing conflict on `adaptiveResult.run_id`.
- **FastAPI Request Validation & HTTP Status Codes**:
  - Added `StorageResourceNotFoundError` mapping explicit missing `evaluation_id`, `adaptive_run_id`, or `scenario_id` to **HTTP 404 Not Found**.
  - Mapped requests missing all source identifiers and scenarios to **HTTP 400 Bad Request**.
  - Sanitized incoming strings (`"None"`, `"undefined"`, `""`) to Python `None`.
  - Prevented silent scenario switching when an unknown `scenario_id` is passed.
- **Next.js Proxy Routes**:
  - In `src/app/api/v1/explanations/route.ts` and `src/app/api/explanations/route.ts`: Updated `GET` handler to route requests with `?id=` or `?explanation_id=` directly to FastAPI detail endpoint `/api/v1/explanations/{id}`.
  - Added dedicated dynamic routes `src/app/api/v1/explanations/[id]/route.ts` and `src/app/api/explanations/[id]/route.ts`.
  - Preserved and forwarded exact HTTP status codes from FastAPI rather than defaulting to 500 on non-200 responses.

### Added
- **Automated Regression Tests**:
  - Added 6 new regression tests in `tests/test_xai_explanations.py` covering:
    - Test 14: Nonexistent `evaluation_id` returns 404.
    - Test 15: Nonexistent `adaptive_run_id` returns 404.
    - Test 16: Nonexistent `scenario_id` returns 404 without silent fallback.
    - Test 17: Missing identifiers / literal `"None"` returns 400.
    - Test 18: Canonical contract structure and guaranteed array presence.
    - Test 19: List vs detail contract parity.
  - Repository automated tests expanded from 146 to 152 passing tests (100%).

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 7 Implementation: End-to-End Workflow Orchestration, Human Authorization, Outcome Reporting & Live Full-Stack Verification

### Added
- **Layer 7 Workflow Package (`fidelitygate/workflow/`)**:
  - `models.py`: Strongly typed Pydantic contracts for end-to-end orchestration: `WorkflowStage` (13 stages), `WorkflowStatus` (9 lifecycle states), `ApprovalDecision` (`APPROVED`, `REJECTED`, `CHANGES_REQUESTED`), `OverallImpact` (`IMPROVED`, `NEUTRAL`, `DEGRADED`, `REGRESSED`), `WorkflowEvent`, `HumanApprovalRecord`, `SimulatedInterventionRecord`, `InterventionOutcomeReport`, `WorkflowRunSummary`, `WorkflowRunRequest`, `ApprovalRequest`.
  - `orchestrator.py`: `EndToEndWorkflowOrchestrator` managing the 13-stage deterministic state machine (`RECEIVED → VALIDATING → TRIAGE → INVESTIGATION → CANDIDATE_EVALUATION → COUNTEREXAMPLE_ANALYSIS → ADAPTIVE_DIAGNOSTICS → REEVALUATION → EXPLANATION → GATE_REVIEW → AWAITING_HUMAN_APPROVAL → SIMULATED_ACTION → OUTCOME_REPORTED`). Enforces monotonically sequenced audit trails and fail-closed transitions.
  - `simulation_adapter.py`: `SimulationActionAdapter` executing candidate reroutes in strictly isolated digital-twin environments (`ISOLATED_DIGITAL_TWIN`). Enforces safety boundaries: rejects stale authorizations, prevents execution of unapproved candidates, and ensures real router interfaces are never touched.
  - `outcome.py`: `OutcomeReporter` computing pre vs post intervention delta analysis (latency shift, percentage reduction, peak edge utilization change, headroom gain, and post-action constraint compliance).
  - `__init__.py`: Exported workflow package components with lazy orchestrator loader to prevent circular import locks.
- **SQLite Persistence Extension (`fidelitygate/storage.py`)**:
  - Added 4 ACID tables: `workflow_runs`, `workflow_events`, `workflow_approvals`, and `workflow_outcomes`.
  - Implemented complete CRUD methods: `save_workflow_run`, `get_workflow_run`, `list_workflow_runs`, `save_workflow_event`, `get_workflow_events`, `save_approval`, `get_approval`, `get_approval_by_workflow`, `save_outcome`, `get_outcome`, `get_outcome_by_workflow`.
- **FastAPI Layer 7 Workflow Endpoints (`fidelitygate/api/app.py`)**:
  - `POST /api/v1/workflows`: Initiate end-to-end workflow run.
  - `GET /api/v1/workflows`: List recent workflow summaries.
  - `GET /api/v1/workflows/{id}`: Fetch single workflow status and stage.
  - `GET /api/v1/workflows/{id}/events`: Monotonically sequenced audit trail.
  - `POST /api/v1/workflows/{id}/approval`: Submit human authorization/rejection.
  - `GET /api/v1/workflows/{id}/approval`: Fetch recorded authorization record.
  - `GET /api/v1/workflows/{id}/outcome`: Fetch post-intervention outcome report.
  - `GET /api/v1/workflows/outcomes/latest`: Fetch most recent outcome report.
- **CLI Subcommands & Standalone Runner**:
  - CLI subcommands in `fidelitygate/cli.py`: `run-workflow`, `get-workflow`, `list-workflows`, `approve-workflow`, `get-workflow-outcome`.
  - Standalone script `scripts/run_workflow.py` supporting `--scenario`, `--reviewer`, `--auto-approve`, `--reject`, and `--output-json`.
  - Standalone verification script `scripts/verify_layer7_live.py`.
- **Next.js Frontend Integration**:
  - Created `WorkflowOrchestrationPanel.tsx` in `src/components/workspace/`.
  - Added dedicated "Workflow & Approval" tab in `WorkspaceApp.tsx` navigation with `UserCheck` icon.
  - Added Next.js API route handlers under `src/app/api/v1/workflows/*` with proxying to FastAPI and CLI fallback.
  - Updated TypeScript definitions in `src/types/index.ts`.
- **Automated Test Suite**:
  - Added `tests/test_workflow_orchestration.py` with 12 comprehensive unit and integration tests (100% pass rate).
  - Total repository tests expanded from 133 to 146 passed (100%).

### Fixed
- **Pre-Flight Layer 6 Response Equivalence Discrepancy**:
  - Unified default scenario resolution across `ExplanationEngine` and CLI (`engine.py`, `cli.py`, `api/app.py`).
  - Added `force_regenerate: bool = False` to `ExplanationRequest`.
  - Updated Next.js API proxy `src/app/api/v1/explanations/route.ts` to directly proxy to FastAPI before falling back to CLI.
  - Added regression test `test_13_controlled_run_equivalence` to `tests/test_xai_explanations.py`.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — P0 Runtime Repair & Layer 6 Full-Stack Live Verification

### Fixed
- **JSX Compilation Repair in `DecisionWorkspace.tsx`**:
  - Identified root cause of Next.js frontend compilation failure (`Unexpected token div. Expected jsx identifier`): multiple duplicate `<DecisionExplanationPanel />` blocks were mistakenly inserted across 5 separate locations (range slider container, two branches of the `twinViewMode` ternary, inside the `UncertaintyChart` container, and duplicate at file bottom).
  - Cleaned up `src/components/workspace/DecisionWorkspace.tsx`, preserving a single, properly structured mounting of `<DecisionExplanationPanel />` immediately below `<TraceTimeline />`.
- **Node 20 Typeless Package Warning**:
  - Added `"type": "module"` to `package.json` so `node start-dev.js` and other native ES module scripts run without `MODULE_TYPELESS_PACKAGE_JSON` warnings.
- **Webpack Build Cache Lock**:
  - Cleared stale `.next` cache directory resolving Webpack file renaming `ENOENT` issues.

### Verified
- **Full Stack Health & Compilation**:
  - `npx tsc --noEmit`: 0 TypeScript errors.
  - `npm run lint`: 0 ESLint warnings or errors.
  - `npm run build`: 17 of 17 static and dynamic routes compiled successfully.
  - `python -m pytest -v`: 133 of 133 tests passed in 31.58s.
  - `node start-dev.js`: Starts FastAPI backend (`http://127.0.0.1:8000`) and Next.js frontend (`http://localhost:3000`) without errors or typeless warnings.
- **Live Endpoint Verification**:
  - `GET http://127.0.0.1:8000/api/v1/health` -> 200 OK.
  - `GET http://127.0.0.1:8000/docs` -> 200 OK.
  - `GET http://localhost:3000/` -> 200 OK (98,836 bytes).
  - `GET http://localhost:3000/workspace` -> 200 OK (51,729 bytes).
  - `POST http://127.0.0.1:8000/api/v1/explanations` -> 200 OK.
  - `POST http://localhost:3000/api/v1/explanations` -> 200 OK.
- **Verification Script**:
  - Added `scripts/verify_xai_stack.py` demonstrating end-to-end multi-layer consistency and NISTIR 8312 summary generation.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 6 Implementation: Evidence-Based Explainable AI (XAI), Decision Attribution and End-to-End Demo Verification

### Added
- **Layer 6 Explainable AI Package (`fidelitygate/xai/`)**:
  - `models.py`: Strongly typed Pydantic contracts: `RuleStatus`, `ExplanationMode`, `GateRuleExplanation`, `CounterexampleExplanation`, `ProvenanceItem`, `UncertaintyExplanation`, `ParameterSensitivity`, `LocalSensitivityReport`, `DecisionExplanation`, `ExplanationRequest`, `ExplanationSummary`.
  - `rule_explainer.py`: `GateRuleExplainer` implementing deterministic evaluation of 5 mandatory gate rules (`RULE-CONN-01` Connectivity, `RULE-CAP-02` Capacity, `RULE-SLO-03` Latency SLO, `RULE-ROB-04` Robustness Margin $\ge 0.90$, `RULE-CE-05` Counterexample Freedom) with exact numerical observed values, comparison symbols, units, thresholds, and evidence references.
  - `counterexample_explainer.py`: `CounterexampleExplainer` preserving exact parameter vectors, nominal vs perturbed metrics, breach margins, and adversarial failure analysis.
  - `measurement_explainer.py`: `MeasurementExplainer` explaining physical-to-parameter mathematical inversion, bounded interval intersection ($[0.85, 1.35] \to [0.9746, 1.1246]$), uncertainty width reductions ($70.0\%$), and dimensionality preservation.
  - `sensitivity_analyzer.py`: `SensitivityAnalyzer` evaluating deterministic one-at-a-time (OAT) parameter variations ($\pm 10\%, \pm 20\%$) and computing elasticity gradients using `NetworkSimulator`. Performs bottleneck link counterfactual perturbations. Includes explicit methodology disclosure.
  - `summary_generator.py`: `DecisionSummaryGenerator` synthesizing structured facts into plain-language summaries with explicit zero-hallucination guardrails and human authorization scope notices.
  - `engine.py`: `ExplanationEngine` orchestrating cross-layer explanation synthesis across Layers 1–5 artifacts.
- **Section 3 Mathematical Correction (Layer 5 Audit Finding)**:
  - Corrected dimensional mismatch between physical probe delay ($y_{\text{raw}} \in \text{ms}$) and digital-twin simulator parameter ($\theta \in \text{factor}$, nominal 1.0).
  - Implemented base-scale observation model $y_{\text{raw}} = D_{\text{base}} \cdot \theta + \epsilon$ and physical inversion $\hat{\theta} = y_{\text{raw}} / D_{\text{base}}$, $\delta_{\text{param}} = \delta_{\text{raw}} / D_{\text{base}}$ in `fidelitygate/adaptive/measurement_registry.py` and `fidelitygate/adaptive/engine.py`.
  - Added strict unit consistency check in `fidelitygate/adaptive/uncertainty_updater.py`.
- **SQLite Persistence Extension (`fidelitygate/storage.py`)**:
  - Added `explanations` table storing structured `DecisionExplanation` JSON.
  - Implemented methods: `save_explanation`, `get_explanation`, `get_explanation_by_run`, `list_explanations`.
- **FastAPI Layer 6 Endpoints (`fidelitygate/api/app.py`)**:
  - `POST /api/v1/explanations`: Generate authoritative evidence-based DecisionExplanation.
  - `GET /api/v1/explanations`: List past explanation summaries.
  - `GET /api/v1/explanations/{id}`: Single explanation lookup.
  - `GET /api/v1/explanations/{id}/rules`: Rule-by-rule predicate breakdown.
  - `GET /api/v1/explanations/{id}/sensitivity`: Sensitivity report.
- **CLI Subcommands & Runners**:
  - `scripts/run_explanation.py`: Standalone CLI runner with formatted terminal breakdown of rules, counterexamples, diagnostics, sensitivity, and provenance.
  - `fidelitygate/cli.py`: Added CLI subcommands `explain-decision`, `get-explanation`, `list-explanations`.
- **Next.js Frontend Integration (`src/components/xai/`, `src/app/api/`)**:
  - Created `DecisionExplanationPanel.tsx` with tabs for Gate Rules, Counterexamples, Measurements, Sensitivity Gradients, and Evidence Provenance.
  - Added dedicated "Explainable AI" tab in `WorkspaceApp.tsx`.
  - Embedded `DecisionExplanationPanel` into `DecisionWorkspace.tsx`.
  - Added Next.js API routes `/api/v1/explanations` and `/api/explanations`.
  - P0 audit: Removed silent fake-success fallback paths and explicitly labeled fallback modes (`DEMO FIXTURE: DETERMINISTIC_LOCAL_BASELINE` and `DEMO FIXTURE: REPLAY TRACE`).
- **Automated Test Suite (`tests/test_xai_explanations.py`)**:
  - 12 comprehensive tests covering all Layer 6 requirements.
  - Entire repository suite: 133 of 133 tests passing (100%).
  - Next.js production build: 17 of 17 routes compiled cleanly with 0 ESLint warnings.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 5 Implementation: Counterexample-Guided Adaptive Diagnostics, Measurement Models and Decision Re-evaluation

### Added
- **Layer 5 Adaptive Diagnostics Package (`fidelitygate/adaptive/`)**:
  - `models.py`: Strongly typed Pydantic contracts: `MeasurementErrorType`, `ObservationMode`, `MeasurementModel`, `DiagnosticObservation`, `UncertaintyInterval`, `UncertaintyUpdate`, `DiagnosticCandidateEvaluation`, `DiagnosticExecutionRecord`, `AdaptiveCycleResult`, `AdaptiveRunStatus`, `AdaptiveInvestigationRequest`, `AdaptiveInvestigationSummary`, `AdaptiveInvestigationReport`, `AdaptiveEvent`.
  - `measurement_registry.py`: Allowlisted registry of measurement models (`active_rtt_probe`, `snmp_interface_poll`, `passive_telemetry_flow`), reproducible PRNG seeded noise simulation, and explicit `ObservationMode.UNAVAILABLE` handling for public telemetry replay (zero synthetic fabrication).
  - `uncertainty_updater.py`: Mathematically rigorous bounded interval intersection updater ($[\theta_{\min}, \theta_{\max}] \cap [y - \delta, y + \delta]$), empty-intersection inconsistency detection, and multi-parameter state updating that strictly preserves unrelated dimensions.
  - `selector.py`: `AdaptiveDiagnosticSelector` evaluating Layer 4 counterexamples, uncertainty widths, diagnostic costs, and remaining budgets under a deterministic ranking policy ($S = 100 \cdot \Delta w / c$).
  - `engine.py`: `AdaptiveInvestigationEngine` orchestrating cycle management (max 2 cycles), initial `ACCEPT` short-circuiting (preventing redundant probes), structural `ABSTAIN` short-circuiting, measurement execution, uncertainty update, Layer 4 simulation and sweep re-evaluation, decision-gate re-review, and persistence.
- **SQLite Persistence Extension (`fidelitygate/storage.py`)**:
  - Added tables: `adaptive_investigations`, `adaptive_reports`, `diagnostic_executions`, `uncertainty_updates`, `adaptive_events`.
  - Added query and persistence methods: `save_adaptive_investigation`, `get_adaptive_summary`, `list_adaptive_summaries`, `get_adaptive_report`, `get_adaptive_diagnostics`, `get_adaptive_events`.
- **FastAPI Layer 5 Endpoints (`fidelitygate/api/app.py`)**:
  - `POST /api/v1/adaptive-investigations`: Trigger counterexample-guided adaptive diagnostics loop and re-evaluation.
  - `GET /api/v1/adaptive-investigations`: List past adaptive investigation summaries.
  - `GET /api/v1/adaptive-investigations/{id}`: Single adaptive run summary and decision transitions lookup.
  - `GET /api/v1/adaptive-investigations/{id}/report`: Full detailed `AdaptiveInvestigationReport`.
  - `GET /api/v1/adaptive-investigations/{id}/events`: Monotonically sequenced audit events recorded during adaptive execution.
- **CLI Subcommands & Runners**:
  - `scripts/run_adaptive_investigation.py`: Standalone CLI runner with summary formatting, cycle breakdowns, and JSON export.
  - `fidelitygate/cli.py`: Added CLI commands `run-adaptive-investigation`, `get-adaptive-investigation`, `list-adaptive-investigations`.
- **TypeScript Contracts (`src/types/index.ts`)**:
  - Added Layer 5 TypeScript interfaces mirroring Pydantic models for frontend consumption.
- **Automated Test Suite (`tests/test_adaptive_investigation.py`)**:
  - 24 comprehensive tests covering all Layer 5 requirements:
    1. Diagnostic ranking addresses actual counterexample
    2. Irrelevant diagnostics excluded
    3. Diagnostics requiring unsupported parameters excluded
    4. Same diagnostic not repeated without justification
    5. Valid bounded-error measurement produces justified interval update
    6. Unrelated parameter interval remains unchanged
    7. Inconsistent measurement intervals rejected (fail-closed)
    8. Measurement error and units validated
    9. Malformed measurement output handled safely
    10. Synthetic diagnostic noise reproducible with fixed seed
    11. Public replay observations never relabelled as synthetic
    12. Hidden reference truth not exposed
    13. Diagnostic measurement can cause genuine re-evaluation
    14. Diagnostic not altering decision reported honestly
    15. Accept result does not trigger unnecessary diagnostics
    16. Gather evidence triggers measurement only when useful
    17. Irrecoverable abstain condition remains abstention
    18. Justified measurement followed by accept transition
    19. Inconsistency fails closed to ABSTAIN
    20. Two-cycle limit strictly enforced
    21. Simulation budget enforced
    22. Persistence survives database restart
    23. FastAPI adaptive endpoints verification
    24. Monotonically sequenced audit events recorded

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 4 Implementation: Candidate Mitigation Evaluation, Digital-Twin Simulation and SLO Verification

### Added
- **Layer 4 Evaluation Package (`fidelitygate/evaluation/`)**:
  - `models.py`: Strongly typed Pydantic schemas for `MitigationActionType`, `ValidationStatus`, `CandidateEvaluationStatus`, `ReferenceEvaluationStatus`, `TopologyNode`, `TopologyEdge`, `TrafficFlow`, `NetworkTopology`, `CandidateAction`, `PathValidationResult`, `LinkSimulationResult`, `SimulationPrediction`, `CandidateComparison`, `Counterexample`, `ReferenceEvaluationResult`, `CandidateEvaluation`, `EvaluationEvent`, `MitigationEvaluationRequest`, `MitigationEvaluationSummary`, `MitigationEvaluationReport`.
  - `topologies.py`: Canonical topologies for scenarios (`wan_congestion`, `fiber_drift`, `traffic_burst`) with verified capacities, base latencies, and initial background flows.
  - `validator.py`: `CandidatePathValidator` enforcing structural path invariants: action allowlist, flow endpoint matching, node/edge existence in canonical topology, operational status checks (`is_up = True`), acyclic paths (rejecting cycles and loops), and positive capacities ($C_e > 0$). Invalid proposals fail closed with `GateDecision.ABSTAIN`.
  - `simulator.py`: `NetworkSimulator` evaluating network interventions via multi-commodity fluid traffic allocation ($B_e = b_e + \sum_k q_k x_{ke}$), link utilization calculation ($\rho_e = B_e / C_e$), convex queueing delay approximation ($Q(\rho) = 0.15 \rho / \max(1-\rho, 0.05)$), path transit latency calculation, bottleneck edge isolation, and differential before/after comparisons with shared concurrent flow impact tracking.
  - `uncertainty_evaluator.py`: `CandidateUncertaintyEvaluator` executing bounded parameter sweeps ($N \le 50$, default 25) across traffic surge, capacity degradation, and cross-traffic variations. Extracts minimal adversarial counterexamples with exact constraint breaches and calculates sampled robustness scores $\hat{R} = 1 - \hat{r}$.
  - `reference_evaluator.py`: `IndependentReferenceEvaluator` evaluating candidates against hidden reference ground truth strictly post-hoc. Kept completely isolated from candidate search and agent tool registries; returns `REFERENCE_NOT_AVAILABLE` for ungrounded public telemetry traces.
  - `engine.py`: `MitigationEvaluationEngine` orchestrating candidate resolution from Layer 3 diagnostic plans, validation, digital-twin simulation, uncertainty sweeps, deterministic decision gate enforcement, and audit persistence.
- **SQLite Persistence Extension (`fidelitygate/storage.py`)**:
  - Added tables: `mitigation_evaluations`, `candidate_evaluations`, `mitigation_reports`, `evaluation_events`.
  - Added query and persistence methods: `save_mitigation_evaluation`, `get_mitigation_summary`, `list_mitigation_summaries`, `get_mitigation_report`, `get_candidate_evaluations`, `get_evaluation_events`.
- **FastAPI Layer 4 Endpoints (`fidelitygate/api/app.py`)**:
  - `POST /api/v1/mitigation-evaluations`: Trigger candidate mitigation evaluation and simulation.
  - `GET /api/v1/mitigation-evaluations`: List past mitigation evaluation summaries.
  - `GET /api/v1/mitigation-evaluations/{id}`: Single evaluation summary and gate decision lookup.
  - `GET /api/v1/mitigation-evaluations/{id}/candidates`: Evaluated candidate details, comparisons, and counterexamples.
  - `GET /api/v1/mitigation-evaluations/{id}/report`: Full detailed `MitigationEvaluationReport`.
  - `GET /api/v1/mitigation-evaluations/{id}/events`: Monotonically sequenced audit events recorded during evaluation.
- **CLI Subcommands & Runners**:
  - `scripts/run_mitigation_evaluation.py`: Standalone CLI runner with summary formatting, candidate path trace, before/after metrics, counterexample inspection, and JSON export.
  - `fidelitygate/cli.py`: Added CLI commands `evaluate-mitigation`, `get-mitigation-evaluation`, `list-mitigation-evaluations`.
- **TypeScript Contracts (`src/types/index.ts`)**:
  - Added Layer 4 TypeScript interfaces mirroring Pydantic models for frontend consumption.
- **Automated Test Suite (`tests/test_candidate_evaluation.py`)**:
  - 26 comprehensive tests covering all Layer 4 requirements:
    1. Valid candidate passes structural validation
    2. Action type not in allowlist rejected
    3. Endpoint mismatch rejected
    4. Nonexistent node rejected
    5. Nonexistent edge rejected
    6. Edge down rejected (`EDGE_DOWN`)
    7. Cycles and loops rejected (`CYCLE_DETECTED`)
    8. Incomplete constraints (zero capacity) fails closed
    9. Multi-commodity fluid load allocation
    10. Overloaded link marks route infeasible
    11. Convex queueing delay increases with utilization
    12. Bottleneck edge correctly identified
    13. Differential impact and shared concurrent flows evaluated
    14. Bounded uncertainty sweep enforces maximum $N \le 50$
    15. Uncertainty sweep extracts minimal counterexample
    16. Sampled robustness score calculation
    17. Independent reference evaluator isolation
    18. Reference not available for public replay data
    19. Gate decision ACCEPT when compliant and robust
    20. Gate decision GATHER_EVIDENCE when parameter breaches occur
    21. Gate decision ABSTAIN when nominal prediction fails
    22. Fail-closed policy: invalid candidate never receives ACCEPT
    23. Monotonically sequenced audit events recorded
    24. Persistence survives database restart
    25. Schema contract conformance
    26. FastAPI mitigation evaluation REST endpoints verification

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 3 Implementation: Bounded Agentic Investigation, Tool Use and Diagnostic Planning

### Added
- **Layer 3 Package Structure (`fidelitygate/investigation/`)**:
  - `models.py`: Strongly typed Pydantic models for `AgentMode`, `InvestigationStatus`, `HypothesisType`, `Hypothesis`, `InvestigationReport`, `DiagnosticCandidate`, `PlanStatus`, `DiagnosticPlan`, `InvestigationEvent`, `InvestigationRequest`, `InvestigationSummary`.
  - `tools.py`: Strict allowlisted `ToolRegistry` supporting:
    - `read_observation`: Retrieve individual normalized telemetry observation.
    - `get_case_metadata`: Retrieve experiment case file timing and device metadata.
    - `query_metric_window`: Entity-scoped time-series observations query.
    - `inspect_topology`: Declared scenario topology inspection.
    - `list_diagnostic_catalog`: Allowlisted diagnostic probe catalog inspection.
    - `propose_candidate_reroute`: Declarative mitigation registration for subsequent twin evaluation.
    - Orchestrator-restricted `execute_diagnostic_probe` with error bounds.
    - Complete exclusion and isolation of reference evaluator ground truth.
  - `llm_adapter.py`: `LLMAdapter` with quota-exhaustion tracking (`quota_exhausted = True` on HTTP 429), safe timeout handling, single bounded repair attempt on schema invalidity, and transparent fallback labelling (`DETERMINISTIC_PLANNER` / `DETERMINISTIC_BASELINE`).
  - `investigator.py`: `AnomalyInvestigatorAgent` (Agent A) consuming Layer 2 `InvestigationContext`, formulating evidence-linked hypotheses, enforcing non-causal descriptors, differentiating source-defined case events (`LabelOrigin.SOURCE_DEFINED`) from inferred anomalies (`LabelOrigin.STATISTICAL_DETECTOR`), and returning `INSUFFICIENT_EVIDENCE` when data is missing.
  - `planner.py`: `DiagnosticPlannerAgent` (Agent B) evaluating diagnostic catalog, computing uncertainty reduction vs. cost ranking, selecting candidate probes within budgets, and proposing candidate network reroute mitigations.
  - `orchestrator.py`: `InvestigationOrchestrator` managing end-to-end execution, enforcing monotonic stage progression, monotonically sequenced audit events, and persistence.
- **SQLite Persistence Extension (`fidelitygate/storage.py`)**:
  - Added tables: `investigation_runs`, `hypotheses`, `diagnostic_plans`, `investigation_events`.
  - Added persistence & query methods: `save_investigation_run`, `get_investigation_summary`, `list_investigation_summaries`, `get_investigation_report`, `get_diagnostic_plan`, `get_investigation_events`.
- **FastAPI Layer 3 Endpoints (`fidelitygate/api/app.py`)**:
  - `POST /api/v1/investigations`: Trigger bounded agentic investigation.
  - `GET /api/v1/investigations`: List past investigation runs.
  - `GET /api/v1/investigations/{id}`: Single run summary lookup.
  - `GET /api/v1/investigations/{id}/report`: Full investigation report.
  - `GET /api/v1/investigations/{id}/plan`: Diagnostic and mitigation plan.
  - `GET /api/v1/investigations/{id}/events`: Monotonically sequenced audit trace events.
- **CLI Subcommands & Runners**:
  - `scripts/run_investigation.py`: Standalone CLI runner with summary statistics, hypotheses, diagnostic plan, and JSON export.
  - `fidelitygate/cli.py`: Added CLI commands `investigate-agent`, `get-investigation`, `list-investigations`.
- **Automated Test Suite (`tests/test_agentic_investigation.py`)**:
  - 22 comprehensive tests covering all Layer 3 requirements:
    1. Valid context reaches Agent A
    2. Evidence IDs resolve against context
    3. Distinguish source-defined vs inferred detector labels
    4. Agent A insufficient evidence handling
    5. Contradictory evidence preserved in report
    6. Agent B receives investigation report
    7. Agent B selects allowlisted candidates
    8. Unknown tools rejected
    9. Malformed tool arguments rejected
    10. Fabricated evidence IDs filtered
    11. Bounded repair attempt (max 1 retry)
    12. Timeout handled safely without hanging
    13. Quota exhaustion disables retries
    14. Deterministic fallback labelled accurately
    15. Live LLM never fabricated
    16. Diagnostic budgets enforced
    17. Repeatable reads idempotent
    18. Reference evaluator isolated from tools
    19. Persistence survives database restart
    20. Gate remains deterministic authority
    21. Schema contract conformance
    22. FastAPI investigation endpoints validation

### Changed
- **`fidelitygate/config.py`**: Added Layer 3 settings (`LLM_PROVIDER`, `LLM_API_KEY`, budgets, timeouts).
- **`fidelitygate/schemas.py`**: Re-exported Layer 3 models.
- **`src/types/index.ts`**: Added Layer 2 and Layer 3 TypeScript interfaces.
- **`docs/*`**: Updated `README.md`, `ARCHITECTURE.md`, `CONTRACTS.md`, `METHODOLOGY.md`, `CURRENT_STATUS.md`, `TEST_REPORT.md`, `DECISIONS.md`, `HANDOFF.md`.

### Verification
- `python -m pytest -v`: **PASS** — 71 of 71 tests passing (22 Layer 3 tests + 22 Layer 2 tests + 16 Layer 1 tests + 11 legacy tests).
- `npm run build`: **PASS** — 15 of 15 Next.js static/dynamic pages compiled cleanly.
- `npm run lint`: **PASS** — 0 errors, 0 warnings.
- Real investigation execution on Cisco BGP clear anomaly triage context (`trg-63c67858`):
  - Formulated 2 hypotheses: `BGP_SESSION_FLAP` on `0/RP0/CPU0` (95% conf, source-confirmed) and `FORWARDING_DROP_SURGE` on `0/RP0/CPU0` (73% conf, statistical).
  - Selected 1 diagnostic candidate: `snmp_interface_poll` on `0/RP0/CPU0` informing `bottleneck_capacity_mbps` with $0.10 cost and 60% expected uncertainty reduction.
  - Generated and persisted 4 audit events.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 2 Implementation: Explainable Anomaly Triage and Evidence Correlation

### Added
- **Layer 2 Package Structure (`fidelitygate/triage/`)**:
  - `models.py`: Strongly typed Pydantic models for `FindingSeverity`, `FindingStatus`, `LabelOrigin`, `EvidenceType`, `EvidenceItem`, `AnomalyFinding`, `CorrelationReport`, `InvestigationContext`, `TriageRunRequest`, `TriageRunSummary`.
  - `priority.py`: `PriorityScorer` for transparent severity assignment and epistemic confidence calculation decoupled from severity.
  - `detectors/base.py`: Abstract `BaseDetector` defining uniform detector interface.
  - `detectors/statistical.py`: `RobustStatisticalDetector` implementing robust MAD score $0.6745 \cdot (x - m) / \text{MAD}$ with zero-MAD invariant series fallback (`score = None`, step difference evaluation, divide-by-zero protection), and monotonic counter delta rate calculation with counter reset handling.
  - `detectors/change.py`: `StepChangeDetector` evaluating relative and absolute step jumps with non-zero denominator checks.
  - `detectors/event_case.py`: `SourceEventCaseDetector` parsing PDT-to-UTC experiment case tables (`casedata.txt`) and mapping target devices with strict provenance separation (`LabelOrigin.SOURCE_DEFINED`).
  - `correlation.py`: `EvidenceCorrelationEngine` implementing deterministic multi-metric entity clustering (`co_occurring_metric_cluster`), temporal proximity clustering (`temporally_associated`), non-causal descriptors, and evidence deduplication.
  - `context_builder.py`: `InvestigationContextBuilder` assembling bounded `InvestigationContext` (`max_context_evidence = 50`), baseline comparisons, recommended diagnostic categories, and explicit data limitations.
  - `engine.py`: `AnomalyTriageEngine` orchestrating streaming observation scans, multi-detector execution, evidence correlation, and context creation.
- **SQLite Persistence Extension (`fidelitygate/storage.py`)**:
  - Added tables: `triage_runs`, `anomaly_findings`, `evidence_items`, `correlation_reports`, `investigation_contexts`.
  - Implemented query and persistence methods: `save_triage_run`, `get_triage_summary`, `list_triage_summaries`, `get_triage_findings`, `get_triage_correlation`, `get_investigation_context`.
- **FastAPI Layer 2 Endpoints (`fidelitygate/api/app.py`)**:
  - `POST /api/v1/triage`: Trigger deterministic triage run.
  - `GET /api/v1/triage`: List past triage runs.
  - `GET /api/v1/triage/{triage_run_id}`: Triage summary lookup.
  - `GET /api/v1/triage/{triage_run_id}/findings`: Candidate anomaly findings query.
  - `GET /api/v1/triage/{triage_run_id}/correlation`: Correlation report query.
  - `GET /api/v1/triage/{triage_run_id}/context`: Downstream investigation context.
- **CLI Subcommands & Runners**:
  - `scripts/run_triage.py`: Standalone CLI runner with summary statistics and JSON export.
  - `fidelitygate/cli.py`: Added CLI commands `triage`, `get-triage`, `list-triage`.
- **Automated Test Suite (`tests/test_anomaly_triage.py`)**:
  - 22 comprehensive tests covering all Layer 2 requirements:
    1. Valid baseline triage init
    2. Invariant zero-variance series (MAD=0 fallback)
    3. Robust MAD formula on known synthetic vector
    4. Normal fluctuations below z-threshold
    5. Injected spikes triggering findings
    6. Monotonic counters and resets
    7. Missing timestamps/records handling
    8. Truthful preservation of unknown units
    9. Source case metadata parsing
    10. Separation between source-defined and detector labels
    11. Temporal proximity clustering
    12. Multi-metric entity clusters
    13. Enforcement of non-causal descriptors
    14. Evidence deduplication
    15. Lower confidence on ambiguous evidence
    16. Graceful handling of incomplete topology
    17. Bounded investigation context size
    18. Empty/zero anomaly runs
    19. Pydantic schema validation
    20. Isolation of evaluator/reference data
    21. Deterministic reproducibility
    22. FastAPI HTTP endpoints validation

### Changed
- **`fidelitygate/schemas.py`**: Re-exported Layer 2 models for clean monolithic access.
- **`fidelitygate/triage/__init__.py`**: Exported all Layer 2 models, engines, and detectors.
- **`docs/*`**: Updated `README.md`, `ARCHITECTURE.md`, `CONTRACTS.md`, `DATASETS.md`, `METHODOLOGY.md`, `CURRENT_STATUS.md`, `TEST_REPORT.md`, `DECISIONS.md`, `HANDOFF.md`.

### Verification
- `python -m pytest`: **PASS** — 49 of 49 tests passing (22 new Layer 2 tests + 16 Layer 1 tests + 11 legacy tests).
- `npm run build`: **PASS** — 15 of 15 Next.js static/dynamic pages compiled cleanly.
- `npm run lint`: **PASS** — 0 errors, 0 warnings.
- Real anomaly triage on ingested Cisco BGP clear telemetry (`ing-f2189c69`):
  - Total observations scanned: 22,000
  - Candidate anomaly findings: 203 (119 HIGH, 58 MEDIUM, 26 LOW)
  - Correlated evidence items: 389
  - Supported relationships: 6,928
  - Context saved to `data/reports/triage_bgpclear.json` without errors.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-24 — Layer 1 Implementation: Backend Foundation, Data Ingestion, Validation and Provenance

### Added
- **Canonical FastAPI Backend (`fidelitygate/api/app.py`)**:
  - Implemented versioned Layer 1 endpoints:
    - `GET /api/v1/health` (Readiness and connection probe)
    - `GET /api/v1/sources` & `GET /api/v1/sources/{source_id}` (Manifest registry)
    - `POST /api/v1/ingestions` (Pipeline trigger with safe path containment and idempotency)
    - `GET /api/v1/ingestions` & `GET /api/v1/ingestions/{id}` (Execution summaries)
    - `GET /api/v1/ingestions/{id}/report` (Detailed audit report)
    - `GET /api/v1/ingestions/{id}/quarantine` (Malformed record inspector)
  - Interactive OpenAPI docs enabled at `/docs` and `/redoc`.
- **Cisco Innovation Edge Telemetry Adapter (`fidelitygate/ingestion/cisco_adapter.py`)**:
  - Real CSV and CSV.GZ streaming parser for Cisco IOS-XR network telemetry.
  - Mandatory column verification (`name`, `time`, `Producer`).
  - Nanosecond epoch to ISO-8601 UTC timestamp parser with plausible historical range bounds.
  - Streaming record sink preventing high-RAM allocation on multi-gigabyte files.
  - Strict unit preservation (documented physical units attached; undocumented units left as `None`).
  - Quarantine integration for malformed numeric counters.
- **Data Ingestion Pipeline (`fidelitygate/ingestion/pipeline.py`)**:
  - Cryptographic SHA-256 checksumming in 64 KB binary chunks.
  - Path traversal security checks (rejecting `../` and paths outside approved data roots).
  - Ingestion idempotency check avoiding redundant reprocessing of identical files.
  - Automatic manifest generation and output persistence in `data/processed/`, `data/manifests/`, `data/reports/`.
- **Quarantine Manager (`fidelitygate/ingestion/quarantine.py`)**:
  - Isolates invalid or corrupted records to `data/quarantine/{ingestion_id}_quarantine.jsonl` with row index, raw payload, defect category, and reason.
- **Central Application Configuration (`fidelitygate/config.py`)**:
  - Environment-based configuration using `pydantic_settings`.
- **SQLite Storage Extension (`fidelitygate/storage.py`)**:
  - Added tables `dataset_manifests`, `ingestion_runs`, `data_quality_issues`.
  - Preserved backward compatibility for `runs` table.
- **Reproducible Dataset Scripts**:
  - `scripts/download_datasets.py`: Keyless public downloader for Cisco baseline and anomaly sets.
  - `scripts/ingest_dataset.py`: Standalone CLI ingestion runner.
  - `scripts/validate_dataset.py`: Standalone dry-run validator.
  - `scripts/prepare_sample_subsets.py`: Calibrated sample subset extractor.
- **Next.js Route Handlers**:
  - Added Next.js route handlers `/api/v1/health`, `/api/v1/sources`, `/api/v1/ingestions`.
  - Fixed P0 route mismatches: supported `GET` alongside `POST` on `/api/investigate`, and created `/api/adaptive-investigation` to match UI callers.
- **Automated Test Suite (`tests/test_ingestion_pipeline.py`)**:
  - 16 comprehensive automated tests covering all Layer 1 requirements.

### Changed
- **`fidelitygate/cli.py`**: Added CLI commands `health`, `list-sources`, `ingest`, `get-report`, and `list-ingestions`.
- **`src/types/index.ts`**: Added TypeScript interfaces for `DataMode`, `DatasetSourceManifest`, `RawObservation`, `NormalizedObservation`, `DataQualityIssue`, `IngestionReport`, `IngestionRequest`, and `IngestionSummary`.
- **`start-dev.js`**: Unified stack startup to launch canonical FastAPI backend on `:8000` and Next.js frontend on `:3000`.
- **`.env.example`**: Updated with backend host/port, data root, and max file size configurations.
- **`.gitignore`**: Added ignore patterns for large raw `.gz`/`.zip` archives and processed `.jsonl` files.
- **`requirements.txt`**: Added `fastapi`, `uvicorn`, `pydantic-settings`, and `httpx`.

### Verification
- `python -m pytest`: **PASS** — 27 of 27 tests passing (16 new Layer 1 tests + 11 legacy tests).
- `npm run build`: **PASS** — 15 of 15 Next.js static/dynamic pages compiled cleanly.
- `npm run lint`: **PASS** — 0 errors, 0 warnings.
- Real dataset acquisition: Downloaded `cisco-baseline` (17.97 MB) and `cisco-bgpclear` (12.24 MB) with verified SHA-256 digests.
- Real telemetry ingestion: Successfully ingested 1,000-row baseline and 1,000-row anomaly cases producing 22,000 normalized observations each.

---

## 2026-10-24 — Layer 8C: Guided Auto Demo Mode, Transition Popups & Judge-Ready Tour

### Added
- **Central Auto Demo Navigation Bar Control (`src/components/workspace/WorkspaceApp.tsx`)**:
  - Integrated clearly identifiable "Auto Demo" button (`Play` / `Square` icons) in workspace tab header.
  - Stateful active indicator with pulsating cobalt dot and `Demo Running` tag.
  - Linked to `useWorkflowRun()` and `useAutoDemo()`.
- **Status-Aware Transition Popups (`src/components/demo/AutoDemoModal.tsx`)**:
  - Pre-transition modal announcing real persisted workflow status, 1-2 line technical explanation of the target tab, and active workflow ID chip.
  - Visual 4-second auto-advance progress countdown bar.
  - Explicit user controls: Continue (<kbd>Enter</kbd>), Skip, or Stop (<kbd>Esc</kbd>).
  - Priority status evaluation: Rejections (`REJECTED_BY_HUMAN`) and Gate Abstentions (`ABSTAIN`) evaluate before generic stage completion flags.
- **Floating Viewing Dwell Control (`src/components/demo/AutoDemoFloatingControl.tsx`)**:
  - Fixed-bottom glassmorphism pill anchored during the 5-second viewing interval on target tabs.
  - Displays monospace step indicator (e.g. `Step 2 of 8: Workflow & Approval`), live run tag, animated dwell countdown bar, Pause/Resume (<kbd>Space</kbd>), Next, and Stop buttons.
- **Human Approval Boundary Inviolability**:
  - At Stage 11 (`AWAITING_HUMAN_APPROVAL`), Auto Demo unconditionally pauses the tour, alerts the operator, and halts navigation.
  - Never auto-authorizes interventions; preserves the human operator as the sole consequential decision authority. Resumes viewing dynamically once authorized manually.
- **Context-Sensitive Modals (`src/components/demo/NoWorkflowModal.tsx`, `AutoDemoCompletionModal.tsx`)**:
  - `NoWorkflowModal`: Orienting modal shown when Auto Demo is triggered without an active workflow, guiding the operator to run a workflow or load an audit run.
  - `AutoDemoCompletionModal`: Final wrap-up modal summarizing findings across all 8 tabs with options to restart or close.
- **Dedicated Auto Demo Automated Test Suite (`tests/test_auto_demo_mode.py`)**:
  - 8 automated tests passing: step sequences, awaiting approval mapping, completed outcome mapping, abstain honesty, human rejection honesty, missing explanation fallback, SQLite DB retrieval, and empty context safety.
  - Total test suite expanded to **171 passing tests (100% pass rate)**.

## 2026-10-23 — Reference-Matched BilloDesign & Nexus Core Redesign

### Added
- **Signature 3D Pointer-Responsive Network Twin (`FocalNetworkTwin3D.tsx`)**: Three.js WebGL canvas in the landing hero featuring a glossy obsidian core, geodesic cybernetic wireframe, 3 orbital routing rings, moving packet pulses, and smooth pointer tilt damping (`lerp`).
- **Accessible 3D Fallback**: Automatic detection of `prefers-reduced-motion` and WebGL context unavailability, serving an accessible SVG/CSS alternative.
- **BilloDesign 9 Services Showcase (`ServicesShowcase.tsx`)**: Complete responsive card grid implementing all 9 services from the platform sidebar (Overview, Decision Workspace, Execution Trace, Evaluation Lab, Telemetry Monitoring, Motion & Sync, Audit Trail, Docs & Contracts, Settings & Diag) with interactive category filter tabs.
- **Pure CSS Rotating Conic Gradient Borders (`globals.css`)**: Implemented `@property --angle` with a 360° conic gradient (`#315CF5` and `#00AFCD`) for `.billo-card` and `.billo-button`.
- **Triple-Layer Pulsing Beacon (`pulse-dot-*`)**: Micro-indicator for active telemetry sync.
- **Nexus Core Engineering Workspace Shell (`WorkspaceApp.tsx`)**: Redesigned workspace into a floating dark container with global network topology metrics (`ACTIVE NODES: 1,402`, `AVG LATENCY: 18.4 ms`, `THROUGHPUT: 450 GB/s`), regional zone table (`us-east-1`, `eu-central-1`, `ap-northeast-1`), and supported environments bar.
- **Human-in-the-Loop Action Approval Modal (`HumanApprovalModal.tsx`)**: Operator authorization gate requiring manual approval before deploying network reroutes, showing evidence provenance and safety invariants.
- **Web Audio API Micro-Synthesizer (`sound.ts`)**: Synthesized sine/triangle wave audio ticks with toggle and persistent mute default.
- **Direct Workspace Route (`src/app/workspace/page.tsx`)**: Support for direct `/workspace` visits.

### Changed
- **Landing Hero (`HeroSection.tsx`)**: Updated to a 2-column layout pairing tracked monospace typography (`MAKE EVERY NETWORK DECISION. EARN ITS CONFIDENCE.`) with the interactive 3D focal object and live ticker cards.
- **Navigation (`Navbar.tsx`)**: Added `Services (9)` anchor link with smooth scrolling and direct workspace CTA.
- **Root Page Orchestrator (`src/app/page.tsx`)**: Enhanced deep-linking support via `?view=workspace&tab=...` and smooth client transitions.

### Fixed
- Fixed dev server file locks during concurrent production builds by decoupling build steps.
- Fixed layout jitter during tab switches in the engineering workspace using Framer Motion `AnimatePresence`.

### Backend/API Impact
- **Zero API Contract Breaking Changes**: All existing endpoints (`/api/investigate`, `/api/adaptive-investigation`, `/api/baselines`, `/api/runs`, `/api/health`) and Python CLI schemas (`fidelitygate.cli`) remain 100% authoritative and unchanged.
- Deterministic decision gate rules (`ACCEPT`, `GATHER_EVIDENCE`, `ABSTAIN`) strictly preserved.

### Accessibility & Performance Impact
- **Reduced Motion Support**: Fully respects `prefers-reduced-motion: reduce`, disabling 3D continuous camera rotations and CSS border animations.
- **Sound Consent**: Sounds remain completely disabled until the user explicitly enables them in the top navbar.
- **Performance**: Rotating gradient borders are executed on the GPU via CSS `@property` without JavaScript requestAnimationFrame overhead on the main thread.

### Verification
- `npm run build`: **PASS** — Compiled 11 routes with 0 errors and 0 warnings.
- `python -m pytest tests/`: **PASS** — 11 of 11 unit tests passed in 1.74s.
- Browser subagent live smoke test: **PASS** — Verified on `http://localhost:3000` across landing page, 3D focal object, services showcase, dark/light themes, and workspace views.