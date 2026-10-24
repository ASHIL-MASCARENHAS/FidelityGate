# FidelityGate — Evaluation Protocol

## 1. Baselines Compared

We evaluate four distinct operational approaches under identical test distributions:

1. **Nominal-Only**: Agent trusts the default digital-twin simulation. Makes decisions solely on nominal prediction without considering parameter uncertainty.
2. **Fixed Safety Margin**: Adds a static $+25\%$ buffer to nominal predictions ($1.25 \times L_{\text{nominal}} \le \text{SLO}$).
3. **Non-Adaptive Uncertainty Sweep**: Executes a blind grid sweep (25 evaluations) across the full uncertainty set without active diagnostic probing. Fails closed if any point breaches.
4. **Adaptive FidelityGate**: Counterexample-guided workflow. Identifies critical perturbation mode, calls targeted diagnostic tool with explicit error bounds, and re-evaluates under collapsed posterior uncertainty.

---

## 2. Benchmark Scenarios & Ground-Truth Test Cases
- `WAN-042`: WAN congestion & reroute burst ($\text{Cap} = 1000$ Mbps, $\text{Load} = 760$ Mbps, $\text{SLO} = 45$ ms).
- `FIBER-017`: Fiber latency calibration drift ($\text{Cap} = 900$ Mbps, $\text{Load} = 690$ Mbps, $\text{SLO} = 40$ ms).
- `BURST-006`: Hidden traffic burst ($\text{Cap} = 800$ Mbps, $\text{Load} = 730$ Mbps, $\text{SLO} = 35$ ms).

10 controlled evaluation trials with varied physical ground-truth drifts ($\alpha^* \in [1.00, 1.55]$, $\beta^* \in [1.00, 1.22]$).

---

## 3. Metrics Evaluated
- **Unsafe Acceptance Rate (%)**: Candidate route accepted by the gate, but violated the SLO in physical reality (Goal: 0.0%).
- **False Abstention Rate (%)**: Candidate route rejected by the gate, but would have safely met the SLO in physical reality (Goal: minimal).
- **Overall Decision Accuracy (%)**: Percentage of decisions matching true physical ground truth.
- **Diagnostic Calls & Cost ($)**: Total financial cost incurred by active network telemetry probes.
- **Execution Latency (ms)**: Total compute and diagnostic time to reach a final verdict.

---

## 4. Layer 4 Candidate Mitigation Evaluation Protocol

### A. Independent Reference Evaluator Protocol
The reference evaluator measures proposed candidate interventions against true, hidden ground truth. To prevent scientific data leakage:
1. **Strict Offline Boundary**: Reference evaluation executes strictly after candidate evaluation, simulation, and gate decision have been computed and committed.
2. **Agent & Candidate Isolation**: The reference evaluator is never exposed to Agent A, Agent B, or the candidate parameter search.
3. **Public Replay vs. Synthetic Distinction**:
   - For real public telemetry (e.g. Cisco Innovation Edge), no verified ground truth exists for future network interventions. The reference evaluator truthfully returns `ReferenceEvaluationStatus.REFERENCE_NOT_AVAILABLE`.
   - For calibrated benchmark scenarios (`wan_congestion`, `fiber_drift`, `traffic_burst`), hidden reference parameters (e.g. actual propagation delay $\alpha^*$, true cross-traffic $\beta^*$) are queried to classify outcomes into `VERIFIED_SAFE`, `UNSAFE_ACCEPTANCE`, or `INCORRECT_ABSTENTION`.

### B. Candidate Path Validation Protocol
Before running numerical simulations, candidate proposals are validated against canonical network graph invariants:
- **Allowlist Verification**: Action type must be in approved enum (`REROUTE`, etc.).
- **Endpoint Match**: First node matches flow source; last node matches flow destination.
- **Directed Edge Existence**: All consecutive node pairs $(u, v)$ must correspond to valid edges in topology.
- **Operational Status Check**: Traversed edges must be operational (`is_up = True`).
- **Acyclic Check**: Forwarding loops and self-loops are rejected (`CYCLE_DETECTED`).
- **Positive Capacity**: Incomplete or zero-capacity edges fail closed (`INCOMPLETE_CONSTRAINTS`).

### C. Bounded Uncertainty Sweep Protocol
- Bounded to maximum $N \le 50$ iterations (default: 25) to prevent unbounded execution latency.
- Tests multi-parameter variations: traffic burst factors ($0.9$ to $1.3$), link degradation ($0.8$ to $1.1$), and cross-traffic ($0.8$ to $1.25$).
- Records minimal adversarial counterexamples highlighting the exact constraint breach and margin.
- Yields deterministic sampled robustness score $\hat{R} = 1 - \hat{r}$.

### D. Gate Authority Protocol
- The deterministic decision gate retains final authority.
- No LLM, agent, or explanation layer can override gate verdicts.
- Invalid paths, down links, and overloaded flows fail closed to `GateDecision.ABSTAIN`.

---

## 5. Layer 7 Workflow Orchestration & Human Authorization Evaluation Protocol

### A. State Machine Invariants
1. **Monotonic Audit Event Sequencing**:
   - Every stage transition generates a `WorkflowEvent` where `sequence_number` strictly increments ($1, 2, \dots, N$).
   - Sequence gaps, regressions, or duplicate IDs fail automated verification.
2. **Terminal State Integrity**:
   - Rejection by human transitions status directly to `REJECTED_BY_HUMAN` and terminates without invoking simulation adapters.
   - Stage requests with missing or corrupt scenarios fail closed during `VALIDATING` stage.

### B. Human Authorization Boundary Verification
1. **Gate Precedence Security Check**:
   - Submitting `ApprovalDecision.APPROVED` for a workflow in gate `ABSTAIN` must raise an explicit exception and remain rejected.
2. **Stale Approval Invalidation**:
   - Approvals referencing outdated evidence versions or stale candidate paths must be rejected by `SimulationActionAdapter`.
3. **Idempotency**:
   - Duplicate approval submissions carrying identical idempotency keys must return identical records without creating duplicate executions.

### C. Digital-Twin Intervention Safety
1. **Isolated Execution Guarantee**:
   - Intervention execution mode must be strictly verified as `ISOLATED_DIGITAL_TWIN`.
   - The test harness verifies zero external socket, SSH, or NETCONF commands are issued to real network routers.
2. **Constraint Regression Detection**:
   - If an intervention causes higher latency or new capacity breaches, `OverallImpact` must be accurately reported as `DEGRADED` or `REGRESSED`.

---

## 6. Outcome Integrity, Sensitivity, and Reproducibility Protocol

### A. Reproducibility Protocol (`test_outcome_reproducibility`)
- **Objective**: Verify that identical deterministic inputs $(S, C, G_0, \theta)$ produce identical numerical simulation outputs, while persisting distinct workflow and outcome records.
- **Verification Rule**:
  - `wf1.workflow_run_id != wf2.workflow_run_id`
  - `out1.outcome_id != out2.outcome_id`
  - All metrics match exactly: $L_{\text{pre}}$, $L_{\text{post}}$, $\Delta L$, $\% \Delta L$, $\rho_{\text{pre}}$, $\rho_{\text{post}}$, $V_{\text{cap}}$, $V_{\text{slo}}$, $\text{bottleneck\_edge}$, $\text{OverallImpact}$.
  - Proves that identical numbers in demonstration runs stem from deterministic physics, not hardcoded strings.

### B. Candidate Sensitivity Protocol (`test_outcome_candidate_sensitivity`)
- **Objective**: Verify that varying the candidate route within the same scenario produces physically distinct metrics.
- **Verification Rule**:
  - Candidate A ($R\text{-alt1}$ via `spine2`): bypasses congestion ($26.55 \to 23.00$ ms, $\rho: 76.0\% \to 50.0\%$, `IMPROVED`).
  - Candidate B ($R\text{-nominal}$ via `spine1`): retains nominal route ($26.55 \to 26.55$ ms, $\rho: 76.0\% \to 76.0\%$, `UNCHANGED`).
  - Metrics must dynamically diverge according to graph physics.

### C. Scenario Sensitivity Protocol (`test_outcome_scenario_sensitivity`)
- **Objective**: Verify that different supported benchmark scenarios produce condition-specific baseline and post-action metrics.
- **Verification Rule**:
  - `wan_congestion`: $L_{\text{pre}} = 26.55$ ms, $L_{\text{post}} = 23.00$ ms, $\Delta L = -3.55$ ms ($-13.37\%$), $\rho: 76.0\% \to 50.0\%$.
  - `fiber_drift`: $L_{\text{pre}} = 35.83$ ms, $L_{\text{post}} = 32.85$ ms, $\Delta L = -2.98$ ms ($-8.32\%$), $\rho: 76.7\% \to 76.7\%$.
  - `traffic_burst`: Gate evaluates `ABSTAIN`; workflow halts cleanly at gate review without generating an executed outcome.

### D. Constraint Regression Protocol (`test_outcome_constraint_regression`)
- **Objective**: Verify that an action lowering target-flow latency but overloading an edge is never classified as an unconditional improvement.
- **Verification Rule**:
  - Candidate routes 400 Mbps flow across a 200 Mbps link with low base latency.
  - Latency is reduced, but post-action capacity breaches exceed baseline ($V_{\text{post, cap}} > V_{\text{pre, cap}}$).
  - Outcome must report $V_{\text{post, cap}} > 0$ and classify impact strictly as `REGRESSED`.

### E. Invalid Action Fail-Closed Protocol (`test_outcome_invalid_action_fails_closed`)
- **Objective**: Verify that physically impossible or disconnected candidate paths fail closed before simulation.
- **Verification Rule**:
  - Candidate proposing a nonexistent node (e.g. `spine_nonexistent_99`) or disconnected hop (e.g. `leaf1` $\to$ `leaf6` directly) is evaluated by `CandidatePathValidator`.
  - `SimulationActionAdapter` raises `ValueError` before invoking simulator.
  - Zero outcome reports or execution records are generated.

