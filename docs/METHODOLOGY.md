# FidelityGate — Methodology & Mathematical Framework

This document details the scientific methodology governing data ingestion, quality validation, provenance tracking, and the mathematical formulations for decision assurance in FidelityGate.

---

## 1. Layer 1: Ingestion, Validation & Provenance Methodology

### A. Raw Provenance & Lineage Preservation
The ingestion layer maintains end-to-end auditability from raw public datasets down to individual normalized observations:
- **Cryptographic Fingerprint**: Every raw file receives a SHA-256 hash computed in 64 KB binary chunks prior to processing.
- **Lineage Tuples**: Every normalized observation carries an immutable `provenance` dictionary:
  ```json
  {
    "source_file": "bgpclear_sample_1000.csv",
    "source_row_index": 2,
    "source_checksum": "aed9f23075ff1fcf...",
    "raw_timestamp": "1501867007675000000",
    "ingestion_id": "ing-f2189c69"
  }
  ```
- **Non-destructive Ingestion**: Original raw files are stored in `data/raw/` unmodified. Normalized outputs reside in `data/processed/`.

### B. Timestamp Validation & Timezone Rigor
- Cisco IOS-XR timestamps represent nanosecond epochs ($10^{-9}$ seconds).
- Validated values are converted to UTC seconds ($t_{\text{sec}} = t_{\text{nano}} / 10^9$) and rendered as ISO-8601 strings (`YYYY-MM-DDTHH:MM:SS.ffffff+00:00`).
- Unparseable, corrupted, or non-numeric timestamps are set to `None` and recorded as `TIMESTAMP_PARSING_FAILURE` warnings.
- Sequence Monotonicity: Telemetry streams per `(Producer, entity_id)` are monitored. If $t_k < t_{k-1}$, a `MONOTONICITY_VIOLATION` is flagged to prevent out-of-order state reconstruction in future layers.

### C. Physical Unit Integrity & Unknown Field Handling
- Units are attached **strictly** when documented in Cisco's official telemetry header specification (e.g. `bytes-received` $\to$ `bytes`, `input-data-rate` $\to$ `bits/sec`, `bandwidth` $\to$ `kbps`, CPU $\to$ `percent`).
- Where units are not declared in the publisher's specification (e.g. `input-drops`), the `unit` field is explicitly set to `None` (unknown).
- Units and metrics are never inferred, guessed, or imputed.

### D. Data Quality Rules & Quarantine Strategy
Records are classified into three dispositions:
1. **ACCEPTED**: Valid headers, parseable numeric metrics, plausible timestamps.
2. **ACCEPTED_WITH_WARNING**: Minor non-fatal anomalies (duplicate event signatures, timestamp jitter, unassigned units).
3. **QUARANTINED**: Severe defects (corrupt non-numeric characters in numeric counters, NaN/Inf floats, unparseable lines). Quarantined records are isolated to `data/quarantine/{ingestion_id}_quarantine.jsonl` with row index, raw payload, and defect category for human operator review without contaminating model inputs.
4. **REJECTED**: Unapproved paths, directory traversals, or empty files reject the entire ingestion run.

### E. Explicit Separation of Data Modes
To ensure scientific validity and avoid data leakage:
- `PUBLIC_DATA`: Directly sourced from real public network traces (Cisco Innovation Edge).
- `REPLAY`: Public observations played through simulation time.
- `SYNTHETIC_FIXTURE`: Artificial records for unit tests.
- `SYNTHETIC_FAULT_INJECTION`: Known injected perturbation schedules.
- `SIMULATED`: Posterior outputs from mathematical twin models.
- `UNKNOWN`: Unverified lineage.

---

## 2. Layer 2: Anomaly Triage & Evidence Correlation Methodology

### A. Robust Statistical Deviation (MAD)
For continuous telemetry gauges (e.g. CPU utilization, memory buffers, queue depths), anomalies are triaged using Median Absolute Deviation (MAD), which is resilient to extreme outliers:

$$\text{median} = m = \text{median}(X)$$

$$\text{MAD} = \text{median}(|x_i - m|)$$

$$\text{robust\_score} = 0.6745 \cdot \frac{x - m}{\text{MAD}}$$

The factor $0.6745 \approx \Phi^{-1}(0.75)$ normalizes the MAD to be asymptotically equivalent to standard deviation $\sigma$ for Gaussian distributions.

#### Zero-MAD Fallback Handling
In steady-state IT infrastructure telemetry, counters and drop gauges often remain constant at zero across 90%+ of observations. In such invariant series, $\text{MAD} = 0$.
- **Division by Zero Protection**: If $\text{MAD} < 10^{-9}$, dividing by MAD is mathematically invalid.
- **Epistemic Honesty**: The robust score is explicitly marked unavailable (`deviation_score = None`).
- **Step Difference Fallback**: An absolute step difference $|x - m|$ is evaluated against metric thresholds.
- **Limitation Tagging**: Every generated finding explicitly notes `"MAD was zero (invariant baseline); robust score unavailable, evaluated via step difference"`.

### B. Monotonic Cumulative Counter Deltas
Counters such as `bytes-received` and `total-number-of-drop-packets` accumulate over time:
- **First Differences**: Rates are calculated as $\Delta x / \Delta t = (x_k - x_{k-1}) / (t_k - t_{k-1})$.
- **Counter Resets**: When $x_k < x_{k-1}$ (due to device reload or 32/64-bit integer rollover), the delta is **never** interpreted as a negative transmission rate. Instead, the sample is tagged as a counter reset event and excluded from the rate window.

### C. Severity Categorization & Confidence Decoupling
FidelityGate strictly decouples **Severity** (impact on infrastructure) from **Confidence** (epistemic quality of evidence):

1. **Severity Scoring (`PriorityScorer.calculate_severity`)**:
   - `CRITICAL`: Forwarding plane packet drop surges ($\ge 1000$ drops), high CPU ($\ge 80\%$), or $|z| \ge 7.0$ on core devices (`spine`, `dr01`, `dr02`).
   - `HIGH`: $|z| \ge 4.5$, packet drops $\ge 100$, or step jumps $\ge 100\%$.
   - `MEDIUM`: $|z| \ge 3.0$ or moderate deviations.
   - `LOW`: $|z| < 3.0$ or minor blips.

2. **Confidence Scoring (`PriorityScorer.calculate_confidence`)**:
   - Scales with baseline sample size: $\text{base} = \min(0.50 + 0.015 \cdot N, 0.88)$ for statistical detections, $0.95$ for verified source case metadata.
   - Penalized for data quality defects: $-0.20$ for `SUSPECT`, $-0.30$ for `UNKNOWN`.
   - Penalized for undocumented units: $-0.10$.
   - Penalized for zero-MAD fallbacks: $-0.15$.

### D. Deterministic Correlation & Non-Causal Descriptors
The correlation engine links findings into multi-perspective investigation contexts:
- **Rule 1 (Entity Co-occurrence)**: Multiple deviating metrics on the same device within the run are clustered as `co_occurring_metric_cluster`.
- **Rule 2 (Temporal Association)**: Findings on different devices within $\Delta t \le 60\text{ s}$ are linked as `temporally_associated`.
- **Rule 3 (Non-Causal Language Invariant)**: Without complete physical topology wiring, routing tables, and active diagnostic verification, claiming "Device A caused packet loss on Device B" is unscientific. FidelityGate strictly enforces non-causal descriptors: *"temporally associated"*, *"co-occurring metric cluster"*, *"candidate relationship"*.

---

## 3. Layer 4: Candidate Mitigation Evaluation & Digital-Twin Simulation Methodology

### A. Candidate Path Invariants & Topological Validation
Before any numerical evaluation, proposed candidate mitigations undergo rigorous structural validation (`CandidatePathValidator`):
1. **Action Type Allowlist**: Enforces approved mitigation actions (`REROUTE`, `RATE_LIMIT`, `SHED_LOAD`, `TOPOLOGY_ISOLATION`).
2. **Endpoint Consistency**: Path start node must equal flow source; path end node must equal flow destination.
3. **Topological Adjacency**: Every consecutive pair of nodes $(u, v)$ in the proposed path must correspond to a directed edge $e = (u, v) \in E$ in the canonical topology graph $G = (V, E)$.
4. **Operational Status**: Every traversed link must have `is_up = True`. If any link is administratively down or experiencing physical fault, the path is rejected as `EDGE_DOWN`.
5. **Acyclic Invariant**: The path must contain no repeating nodes (preventing forwarding loops and cycles).
6. **Positive Capacity**: Every link must have strictly positive transmission capacity ($C_e > 0$). Edges with zero capacity trigger `INCOMPLETE_CONSTRAINTS`.

Any candidate failing validation is immediately marked `INVALID_PATH` and fails closed with a deterministic `GateDecision.ABSTAIN`.

### B. Multi-Commodity Traffic Allocation & Convex Queueing Delay
In an enterprise WAN or datacenter fabric, link congestion arises from both existing background traffic and concurrent rerouted flows. FidelityGate computes link-level loads via multi-commodity fluid flow allocation:

$$B_e = b_e + \sum_{k \in \mathcal{K}} q_k \cdot x_{ke}$$

Where:
- $b_e$ is the background load on edge $e$ (Mbps).
- $\mathcal{K}$ is the set of all active traffic flows.
- $q_k$ is the demand of flow $k$ (Mbps).
- $x_{ke} \in \{0, 1\}$ indicates whether flow $k$ traverses edge $e$.

The link utilization is defined as:
$$\rho_e = \frac{B_e}{C_e}$$

If $\rho_e \ge 1.0$, the link is overloaded; the simulation marks the route infeasible ($D = \infty$). When $\rho_e < 1.0$, queueing delay is computed via a convex $M/M/1$-inspired queueing approximation:

$$Q(\rho_e) = \frac{0.15 \cdot \rho_e}{\max(1.0 - \rho_e, 0.05)}$$

Total link latency combining physical propagation delay $d_e$ and buffer queueing:
$$D_e = d_e \cdot \left(1.0 + Q(\rho_e)\right)$$

Total candidate path latency:
$$D(\text{Path}) = \sum_{e \in \text{Path}} D_e$$

### C. Bottleneck Isolation & Differential Impact Analysis
The digital twin identifies the critical bottleneck edge:
$$e^* = \operatorname{argmax}_{e \in \text{Path}} \rho_e$$

It computes before/after differentials comparing baseline routing to candidate mitigation:
- $\Delta \text{Latency} = D_{\text{simulated}} - D_{\text{baseline}}$
- $\Delta \text{Utilization} = \max_e \rho_{e,\text{simulated}} - \max_e \rho_{e,\text{baseline}}$
- Newly overloaded edges: $\{e \in E : \rho_{e,\text{baseline}} < 1.0 \wedge \rho_{e,\text{simulated}} \ge 1.0\}$
- Impacted concurrent flows sharing any edges with the rerouted path.

### D. Bounded Uncertainty Sweeper & Counterexample Search
Candidate routes that appear feasible under nominal conditions may violate SLOs under real-world traffic bursts or fiber degradation. The uncertainty sweeper tests the candidate across a bounded parameter envelope $\Theta$:
- Traffic surge factor: $\theta_{\text{traffic}} \in [0.9, 1.3]$
- Link capacity degradation: $\theta_{\text{capacity}} \in [0.8, 1.1]$
- Cross-traffic variation: $\theta_{\text{cross}} \in [0.8, 1.25]$

The sweep is strictly bounded to $N \le 50$ iterations (default 25).
If any parameter sample $\theta$ causes $D(\text{Path}, \theta) > \text{SLO}_{\text{latency}}$ or $\max_e \rho_e(\theta) > \text{SLO}_{\text{utilization}}$, a `Counterexample` is generated recording:
- Parameter vector $\theta$
- Violated constraint
- Observed value vs. threshold value
- Margin breach magnitude: $|V_{\text{observed}} - V_{\text{threshold}}|$

The sampled robustness score is:
$$\hat{R} = 1.0 - \hat{r} = 1.0 - \frac{\sum_{i=1}^N v_i}{N}$$
Where $v_i = 1$ if iteration $i$ violated any constraint, else $0$.

### E. Independent Reference Evaluator Protocol
To maintain scientific validity:
1. **Public Replay Traces**: Public telemetry (e.g. Cisco Innovation Edge) does not include hidden ground-truth physical topologies or true future network states. Evaluating against imaginary ground truth would be scientifically fraudulent. For public replay data, the evaluator explicitly returns `ReferenceEvaluationStatus.REFERENCE_NOT_AVAILABLE`.
2. **Controlled Benchmark Scenarios**: Synthetic benchmark scenarios (e.g. `wan_congestion`) possess declared hidden ground truth (actual physical fiber latency, true link capacity). The reference evaluator computes ground truth performance **strictly post-hoc** and completely out-of-band.
3. **Agent Isolation**: Neither Agent A nor Agent B can access the reference evaluator; it is not exposed in the `ToolRegistry`.

### F. Deterministic Gate Decision Rules
The decision gate enforces fail-closed safety:
1. **ACCEPT**:
   $$\text{Validation} = \text{VALID} \quad \wedge \quad D_{\text{nominal}} \le \text{SLO} \quad \wedge \quad \rho_{\max} \le \text{SLO}_{\text{util}} \quad \wedge \quad \hat{R} \ge 0.80 \quad \wedge \quad |\text{Counterexamples}| = 0$$
2. **GATHER_EVIDENCE**:
   $$\text{Validation} = \text{VALID} \quad \wedge \quad D_{\text{nominal}} \le \text{SLO} \quad \wedge \quad (|\text{Counterexamples}| > 0 \vee \hat{R} < 0.80)$$
   *(Fragile under parameter variations; targeted diagnostic probe required).*
3. **ABSTAIN**:
   $$\text{Validation} \ne \text{VALID} \quad \vee \quad D_{\text{nominal}} > \text{SLO} \quad \vee \quad \rho_{\max} \ge 1.0 \quad \vee \quad \text{No Feasible Candidate}$$
   *(Zero-compromise fail-closed default).*

---

## 4. Layer 3: Agentic Investigation & Diagnostic Planning Methodology

### Separation of Empirical Observation vs Inferred Hypothesis
Layer 3 strictly maintains epistemic humility and provenance integrity:
1. **Source-Defined Ground Truth (`LabelOrigin.SOURCE_DEFINED`)**:
   - Ingested directly from official experiment logs (e.g. Cisco `casedata.txt`).
   - Carries high prior confidence ($0.95$) and marks hypotheses as `is_source_confirmed = True`.
2. **Detector Inferences (`LabelOrigin.STATISTICAL_DETECTOR` / `RULE_BASED`)**:
   - Statistically observed deviations computed via robust MAD scores.
   - Confidence strictly bounded by sample size, deviation magnitude, and data freshness ($\le 0.85$).
3. **Non-Causal Language Governance**:
   - Agents are forbidden from claiming unverified physical causality (e.g. "Device X caused network outage").
   - Telemetry relationships are strictly phrased using descriptive, empirical correlations ("co-occurring with", "temporally associated within 60s", "candidate finding").
4. **Insufficient Evidence Handling**:
   - If telemetry exhibits zero findings or missing entity contexts, Agent A halts and returns `InvestigationStatus.INSUFFICIENT_EVIDENCE` rather than fabricating speculative hypotheses.

### Diagnostic Probe Ranking & Utility Optimization
Agent B selects diagnostic candidates from an allowlisted catalog (`DIAGNOSTIC_TOOLS`) by maximizing marginal uncertainty reduction relative to resource cost:

$$\text{PriorityRank}(d) = \operatorname{argmax}_d \left[ \frac{\Delta \text{Uncertainty}(d)}{\text{Cost}(d)} \right]$$

Subject to:
$$\sum_{d \in \text{Plan}} \text{Cost}(d) \le \text{MaxBudget}, \quad |\text{Plan}| \le \text{MaxDiagnostics}$$

### LLM Reliability & Truthful Fallback Discipline
1. **Single Bounded Repair**: If an LLM response fails Pydantic schema validation or includes non-allowlisted tool calls, exactly one corrective retry is attempted with explicit schema feedback. If it fails again, the agent immediately defaults to `DETERMINISTIC_BASELINE`.
2. **Quota Latching**: On receiving HTTP 429 or quota-exhausted errors, `quota_exhausted = True` is latched for the lifespan of the agent instance to prevent cascade retries and latency degradation.
3. **Audit Trail Truthfulness**: Execution modes are permanently recorded as `AgentMode.DETERMINISTIC_PLANNER` or `AgentMode.DETERMINISTIC_BASELINE`. Fallbacks are never misrepresented as live LLM outputs in reports, UI headers, or SQLite records.

---

## 5. Layer 4: Candidate Mitigation Evaluation & Digital-Twin Simulation Methodology

### Multi-Commodity Fluid Allocation & Utilization
For a directed network topology $G = (V, E)$, background flow on link $e$ is $b_e$. For candidate reroutes and active flows $k \in \mathcal{K}$ with demand $q_k$ and path indicator $x_{ke} \in \{0, 1\}$:
$$B_e = b_e + \sum_{k \in \mathcal{K}} q_k x_{ke}$$
Link utilization is defined by:
$$\rho_e = \frac{B_e}{C_e}$$
where $C_e$ is the nominal link capacity in Mbps. If $\exists e \in \text{Path}: \rho_e \ge 1.0$, the candidate is marked `INFEASIBLE` with infinite delay.

### Convex Queueing Delay Approximation
For operational links where $\rho_e < 1.0$, queueing delay increases nonlinearly as utilization approaches capacity:
$$Q(\rho_e) = \frac{0.15 \cdot \rho_e}{\max(1.0 - \rho_e, 0.05)}$$
Total link delay is $D_e = d_e \cdot (1.0 + Q(\rho_e))$, where $d_e$ is the base physical propagation delay in milliseconds. Total path transit delay is:
$$D(\text{Path}) = \sum_{e \in \text{Path}} D_e$$

### Bounded Parameter Sweeps & Counterexample Search
Candidate robustness is tested by sampling $N \le 50$ parameter variations within a declared uncertainty envelope $\Theta$:
$$\Theta = \left\{ \theta_{\text{traffic}} \in [0.9, 1.3], \; \theta_{\text{capacity}} \in [0.8, 1.1], \; \theta_{\text{cross}} \in [0.8, 1.25] \right\}$$
For each variation $\theta^{(i)}$, constraints are evaluated. If any constraint fails:
$$v_i = \mathbb{I}\left( D(\text{Path}, \theta^{(i)}) > \text{SLO}_{\text{lat}} \;\lor\; \max_e \rho_e(\theta^{(i)}) > \text{SLO}_{\text{util}} \right)$$
The sampled violation rate is $\hat{r} = \frac{1}{N} \sum_{i=1}^N v_i$, and the sampled robustness score is $\hat{R} = 1 - \hat{r}$. The parameter perturbation minimizing margin distance is extracted as the minimal counterexample.

---

## 6. Layer 5: Counterexample-Guided Adaptive Diagnostics & Interval Intersection

### Decision-Relevance Diagnostic Selection
When a counterexample highlights parameter $\theta_j$ with prior interval $[\theta_{\min, j}, \theta_{\max, j}]$, the selector evaluates eligible probes whose nominal error bound satisfies $\delta_d < (\theta_{\max, j} - \theta_{\min, j}) / 2$.
Probes are prioritized by the decision-relevance score:
$$S(d) = 100.0 \cdot \frac{(\theta_{\max, j} - \theta_{\min, j}) - 2\delta_d}{c_d}$$
where $c_d$ is the operational probe cost in USD. Probes that have already been executed in the current investigation are filtered out to prevent redundant expenditures.

### Bounded Measurement-Error Model
Measurements follow a declared physical model:
$$y = h_d(\theta^*) + \epsilon, \quad \epsilon \sim \text{TruncNormal}(0, \sigma_d^2, [-\delta_d, +\delta_d])$$
The acquired measurement defines an empirical confidence interval $[y - \delta_d, y + \delta_d]$.
For public telemetry replay where physical probing is impossible, the registry returns `ObservationMode.UNAVAILABLE`, preventing fabricated synthetic readings from masquerading as real telemetry.

### Interval Intersection & Inconsistency Detection
The posterior parameter interval is determined by rigorous set intersection:
$$[\theta'_{\min, j}, \theta'_{\max, j}] = [\theta_{\min, j}, \theta_{\max, j}] \cap [y - \delta_d, y + \delta_d] = \left[ \max(\theta_{\min, j}, y - \delta_d), \; \min(\theta_{\max, j}, y + \delta_d) \right]$$
**Empty-Intersection Property:**
If $\theta'_{\min, j} > \theta'_{\max, j}$, the measurement contradicts prior knowledge or model assumptions. The engine marks `INCONSISTENCY_DETECTED` and immediately fails closed to `ABSTAIN`.

### Multi-Parameter Invariant
Updating parameter $j$ strictly preserves the intervals of all other parameters $k \neq j$:
$$[\theta'_{\min, k}, \theta'_{\max, k}] = [\theta_{\min, k}, \theta_{\max, k}] \quad \forall k \neq j$$
Diagnostic measurement of link latency never silently modifies traffic surge bounds or capacity estimates.

---

## 7. Layer 6: Evidence-Based Explainable AI (XAI) & Sensitivity Methodology

### Mathematical Inversion of Physical Observations
A critical audit finding identified during Layer 5 verification was dimensional mismatch: physical diagnostic probes report delay in milliseconds (e.g. $y_{\text{raw}} \in \text{ms}$, error $\delta_{\text{raw}} = 1.5$ ms), whereas digital-twin simulator parameter $\theta_{\text{drift}}$ is dimensionless (unit `"factor"`, nominal $1.0$).

To prevent dimensional corruption, the observation model explicitly scales physical delays by candidate path base propagation delay $D_{\text{base}}$:
$$y_{\text{raw}} = D_{\text{base}} \cdot \theta^* + \epsilon_{\text{raw}}, \quad \epsilon_{\text{raw}} \in [-\delta_{\text{raw}}, +\delta_{\text{raw}}]$$
The observation is mathematically inverted into the target parameter space:
$$\hat{\theta} = \frac{y_{\text{raw}}}{D_{\text{base}}}, \quad \delta_{\text{param}} = \frac{\delta_{\text{raw}}}{D_{\text{base}}}$$
For candidate path base latency $D_{\text{base}} = 20.0$ ms and raw delay measurement $y_{\text{raw}} = 20.993 \pm 1.5$ ms:
$$\hat{\theta} = \frac{20.993}{20.0} = 1.0496 \text{ factor}, \quad \delta_{\text{param}} = \frac{1.5}{20.0} = 0.0750 \text{ factor}$$
Parameter measurement interval: $[0.9746, 1.1246]$ factor.
Intersecting with prior $[0.85, 1.35]$ yields posterior $[0.9746, 1.1246]$ factor ($70.0\%$ uncertainty width reduction), maintaining strict dimensional consistency. If units mismatch, the updater rejects the observation.

### Deterministic Gate Predicate Verification
Gate explanations evaluate 5 deterministic, mandatory predicates:
1. **Connectivity**: $\text{is\_valid} == \text{True} \land \text{down\_links} == \emptyset \land \text{cycles} == \emptyset$.
2. **Capacity Compliance**: $\max_{e} \rho_e \le 1.00$.
3. **Transit Latency SLO**: $D(\text{Path}) \le \text{SLO}_{\text{lat}}$ (nominal simulation).
4. **Sampled Robustness Score**: $\hat{R} \ge 0.90$ across uncertainty envelope variations.
5. **Counterexample Freedom**: $C_{\text{active}} == 0$ active adversarial breaches.

### Local One-At-A-Time (OAT) Sensitivity Gradients
Parameter response gradients are computed by perturbing parameters individually at $\pm 10\%, \pm 20\%$ around nominal values using `NetworkSimulator`:
$$\text{Elasticity}_{\text{lat}}(\theta) = \frac{\Delta D(\text{Path}) / D_{\text{nominal}}}{\Delta \theta / \theta_{\text{nominal}}}$$
$$\text{Elasticity}_{\text{util}}(\theta) = \frac{\Delta \rho_{\max} / \rho_{\text{nominal}}}{\Delta \theta / \theta_{\text{nominal}}}$$
**Methodology Disclosure**: Local sensitivity measures mathematical simulator gradients under isolated parameter variation. It does not establish physical real-world causality.

### NISTIR 8312 Principle Mapping
1. **Explanation**: Quantitative, rule-by-rule predicate audit with exact thresholds and observed values.
2. **Meaningful**: Layered representations (plain-language executive summary, structured JSON, interactive UI panel).
3. **Explanation Accuracy**: Strictly derived from executed simulation runs, counterexamples, and physical observations.
4. **Knowledge Limits**: Explicitly documents simulator queueing assumptions, telemetry gaps, and non-causal evidence descriptors.

---

## 8. Layer 7: End-to-End Workflow Orchestration & Human Authorization

### Master State Machine Lifecycle
The end-to-end operational lifecycle follows an immutable 13-stage sequence:
$$\text{RECEIVED} \to \text{VALIDATING} \to \text{TRIAGE} \to \text{INVESTIGATION} \to \text{CANDIDATE\_EVALUATION} \to \text{COUNTEREXAMPLE\_ANALYSIS} \to \text{ADAPTIVE\_DIAGNOSTICS} \to \text{REEVALUATION} \to \text{EXPLANATION} \to \text{GATE\_REVIEW} \to \text{AWAITING\_HUMAN\_APPROVAL} \to \text{SIMULATED\_ACTION} \to \text{OUTCOME\_REPORTED}$$

1. **Monotonically Sequenced Audit Trail**: Every stage transition records a persistent `WorkflowEvent` with sequence number $k = 1, 2, \dots, N$.
2. **Terminal Alternatives**:
   - `REJECTED_BY_HUMAN`: Operator halts workflow; no intervention executed.
   - `CHANGES_REQUESTED`: Operator requests alternative candidate or diagnostic probe.
   - `FAILED`: Validation or operational constraint fails closed.

### Human-in-the-Loop Authorization Boundary Invariants
1. **Gate Precedence Invariant**: A human operator cannot override a deterministic gate `ABSTAIN`. Interventions that violate mandatory safety predicates ($\max \rho_e > 1.00$ or active counterexamples) strictly fail closed.
2. **Evidence Currency Invariant**: Authorization records carry an `evidence_version` token (`fidelitygate-v1.0`). If new telemetry arrives or the candidate is modified, previous approvals are invalidated as stale (`is_stale = True`).
3. **Fail-Closed Execution**: Unapproved candidates cannot execute. Any attempt to invoke intervention adapters without an active `APPROVED` record raises a fatal security exception.

### Isolated Digital-Twin Simulation Adapter
1. Interventions are executed exclusively via `SimulationActionAdapter` in `ISOLATED_DIGITAL_TWIN` mode.
2. The adapter calls `NetworkSimulator.compare_candidate_to_baseline` to calculate exact before vs after network states.
3. No real-world physical router interfaces, BGP routing tables, or SDN control planes are reconfigured.

### Comparative Outcome Reporting & Metric Precision

Pre-action baseline state is compared against post-action simulated state using exact mathematical formulations:

1. **Target Flow Latency Shift**:
   $$\Delta L = L_{\text{after}} - L_{\text{before}} \quad [\text{ms}]$$
   $$\% \Delta L = \frac{L_{\text{after}} - L_{\text{before}}}{L_{\text{before}}} \times 100\% \quad (L_{\text{before}} > 0)$$

2. **Edge Utilization (Ratio vs. Percentage)**:
   Link utilization $\rho_e = \frac{B_e}{C_e}$ is stored as an exact dimensionless ratio $\rho \in [0, \infty)$ and displayed in presentation layers as $100 \cdot \rho\,\%$.
   $$\rho_{\text{peak}} = \max_{e \in E} \rho_e, \quad \Delta \rho_{\text{peak}} = \rho_{\text{peak, post}} - \rho_{\text{peak, pre}}$$
   Peak utilization is evaluated strictly across the identical documented set of topology edges $E$ before and after the intervention.

3. **Network-Wide Capacity Violations**:
   $$V_{\text{cap}} = \sum_{e \in E} \mathbf{1}(\text{load}_e > C_e \lor \rho_e > 1.00)$$
   Evaluates all relevant links in the network graph, ensuring that congestion shifting onto adjacent links is surfaced immediately.

4. **Network-Wide SLO Violations**:
   $$V_{\text{slo}} = \sum_{f \in F} \mathbf{1}(L_f > \text{SLO}_f)$$
   Evaluates all relevant traffic flows in the scenario topology. A lower latency on the target flow does not constitute an improvement if it forces another flow into an SLO breach.

5. **Dynamic Bottleneck Edge**:
   $$\text{bottleneck\_edge} = \begin{cases}
   e \in E_{\text{newly\_overloaded}} & \text{if } E_{\text{newly\_overloaded}} \neq \emptyset \\
   \arg\max_{e \in E} \rho_{e, \text{post}} & \text{otherwise}
   \end{cases}$$
   Dynamically computed from post-action link load distribution; never hardcoded to fallback strings.

6. **Impact Classification Invariant**:
   $$\text{OverallImpact} = \begin{cases}
   \text{REGRESSED} & \text{if } V_{\text{post, cap}} > V_{\text{pre, cap}} \lor V_{\text{post, slo}} > V_{\text{pre, slo}} \lor E_{\text{newly\_overloaded}} \neq \emptyset \\
   \text{UNCHANGED} & \text{if } \Delta L = 0.00 \land \Delta \rho_{\text{peak}} = 0.0000 \land \Delta V = 0 \\
   \text{IMPROVED} & \text{if } \Delta L < 0 \land \Delta \rho_{\text{peak}} \le 0 \land V_{\text{post, cap}} = 0 \land V_{\text{post, slo}} = 0 \\
   \text{MIXED} & \text{if } (\Delta L < 0 \land \Delta \rho_{\text{peak}} > 0) \lor (\Delta L > 0 \land \Delta \rho_{\text{peak}} < 0) \\
   \text{DEGRADED} & \text{if } \Delta L > 0 \land \Delta \rho_{\text{peak}} \ge 0 \\
   \text{NEUTRAL} & \text{otherwise}
   \end{cases}$$

### Deterministic Reproducibility Principle

FidelityGate enforces strict deterministic simulation reproducibility:
- For identical inputs $(S, C, G_0, \theta, \mathcal{M})$, the digital twin must produce identical numerical results across repeated runs.
- Random jitter or stochastic noise is never injected to artificially vary numbers on the dashboard.
- Identical outputs in repeated runs are mathematically valid when inputs are identical; distinct workflow and outcome IDs maintain unique audit traceability.
- Sensitivity is demonstrated across distinct candidates (e.g. $R\text{-alt1}$ vs. $R\text{-nominal}$) and distinct scenarios (`wan_congestion`, `fiber_drift`, `traffic_burst`).


