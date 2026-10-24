import { AutoDemoStep, AutoDemoContext } from '@/types/demo';

export const AUTO_DEMO_STEPS: AutoDemoStep[] = [
  // 1. TOPOLOGY / DECISION WORKSPACE
  {
    id: 'decision',
    tabId: 'decision',
    tabLabel: 'Topology',
    title: 'Global Network Topology & Candidate Reroute',
    getHeading: (ctx: AutoDemoContext) => {
      if (ctx.selectedCandidateId) {
        return `Network Topology & Proposed Candidate (${ctx.selectedCandidateId})`;
      }
      return `Global Network Topology & Telemetry (No Candidate Selected)`;
    },
    getDescription: (ctx: AutoDemoContext) => {
      const scenarioName = ctx.scenarioId ? `Scenario: ${ctx.scenarioId}` : 'No active scenario selected';
      if (ctx.selectedCandidateId) {
        return `Active ${scenarioName}. Telemetry ingestion monitors decentralized edge nodes under heavy load. Candidate reroute ${ctx.selectedCandidateId} has been proposed by Agent B for digital-twin validation prior to consequential deployment.`;
      }
      return `Active ${scenarioName}. Candidate reroute is currently unavailable for this workflow run (Stage: ${ctx.currentStage || 'UNINITIALIZED'}). To evaluate candidate mitigations, run an automated investigation or select a completed run from Audit Runs.`;
    },
    getNextPreview: () => 'Next: 13-Stage Workflow Orchestration & Human Authorization Boundary',
    dwellSeconds: 5,
  },

  // 2. WORKFLOW & APPROVAL
  {
    id: 'workflow',
    tabId: 'workflow',
    tabLabel: 'Workflow & Approval',
    title: '13-Stage Workflow & Approval Boundary',
    getHeading: (ctx: AutoDemoContext) => {
      // 1. Check explicit terminal rejection first
      if (ctx.workflowStatus === 'REJECTED_BY_HUMAN') {
        return 'Intervention Halted: Rejected by Human Operator';
      }
      // 2. Check authoritative gate abstention before generic completion
      if (ctx.gateVerdict === 'ABSTAIN') {
        return 'Authoritative Gate Verdict: ABSTAIN (Failed Closed)';
      }
      // 3. Check awaiting human operator authorization
      if (ctx.currentStage === 'AWAITING_HUMAN_APPROVAL' || ctx.workflowStatus === 'AWAITING_APPROVAL') {
        return 'Awaiting Human Operator Authorization';
      }
      // 4. Check completed execution with outcome report
      if (ctx.workflowStatus === 'COMPLETED' || ctx.currentStage === 'OUTCOME_REPORTED') {
        return '13-Stage Workflow Completed & Outcome Reported';
      }
      // 5. Check in-progress automated orchestration
      if (ctx.workflowStatus === 'RUNNING') {
        return `Automated Orchestration in Progress (Stage: ${ctx.currentStage || 'PROCESSING'})`;
      }
      return '13-Stage Operational Workflow State Machine';
    },
    getDescription: (ctx: AutoDemoContext) => {
      if (ctx.workflowStatus === 'REJECTED_BY_HUMAN') {
        return `Human operator rejected candidate reroute. Execution halted cleanly at Stage 11 without touching real or simulated routing tables.`;
      }
      if (ctx.gateVerdict === 'ABSTAIN') {
        return `Mandatory safety constraints were breached during parameter uncertainty sweeps. The candidate is rejected and fails closed without simulated action.`;
      }
      if (ctx.currentStage === 'AWAITING_HUMAN_APPROVAL' || ctx.workflowStatus === 'AWAITING_APPROVAL') {
        return `The deterministic gate evaluated ${ctx.gateVerdict || 'ACCEPT'}. Algorithmic progression has paused at Stage 11. Consequential network changes strictly require manual operator authorization before simulated execution.`;
      }
      if (ctx.workflowStatus === 'COMPLETED' || ctx.currentStage === 'OUTCOME_REPORTED') {
        if (ctx.outcomeReport) {
          const delta = ctx.outcomeReport.latency_delta_ms;
          const deltaStr = typeof delta === 'number'
            ? `${delta > 0 ? '+' : ''}${delta.toFixed(2)} ms (${ctx.outcomeReport.latency_reduction_pct.toFixed(1)}%)`
            : 'latency delta unavailable';
          const peakUtil = typeof ctx.outcomeReport.post_action_peak_utilization === 'number'
            ? `${(ctx.outcomeReport.post_action_peak_utilization * 100).toFixed(1)}%`
            : 'unmeasured';
          const capViolations = typeof ctx.outcomeReport.post_action_capacity_violations === 'number'
            ? `${ctx.outcomeReport.post_action_capacity_violations} capacity breach(es)`
            : 'capacity uncalculated';
          const sloViolations = typeof ctx.outcomeReport.post_action_slo_violations === 'number'
            ? `${ctx.outcomeReport.post_action_slo_violations} SLO breach(es)`
            : 'SLO uncalculated';
          const impact = ctx.outcomeReport.overall_impact || 'EVALUATED';
          return `Monotonic lifecycle completed across all 13 stages. Simulated outcome (Evaluation: ${ctx.outcomeReport.post_action_evaluation_id}): latency delta ${deltaStr}, peak edge utilization ${peakUtil}, ${capViolations}, ${sloViolations}. Overall impact: ${impact}.`;
        }
        return `Monotonic lifecycle completed across all 13 stages. Human authorization was granted and simulated digital-twin intervention reached Stage 13. Outcome report artifact is pending or unavailable.`;
      }
      return `Current Stage: ${ctx.currentStage || 'RECEIVED'}. Monotonic event bus transitions sequentially through validation, triage, agent investigation, simulation, and gate review.`;
    },
    getNextPreview: () => 'Next: Evidence-Based Explainable AI (XAI) & Attribution',
    dwellSeconds: 5,
  },

  // 3. EXPLAINABLE AI
  {
    id: 'xai',
    tabId: 'xai',
    tabLabel: 'Explainable AI',
    title: 'Evidence-Based Explainable AI (XAI)',
    getHeading: (ctx: AutoDemoContext) => {
      if (!ctx.explanationId) {
        return 'Decision Explanation Status (Artifact Unavailable)';
      }
      if (ctx.gateVerdict === 'ACCEPT') {
        return 'Decision Attribution & 5 Gate Predicates Verified';
      }
      if (ctx.gateVerdict === 'ABSTAIN') {
        return 'Counterexample Replay & Constraint Breach Attribution';
      }
      if (ctx.gateVerdict === 'GATHER_EVIDENCE') {
        return 'Adaptive Diagnostics & Measurement Error Inversion';
      }
      return 'Decision Attribution & Sensitivity Analysis';
    },
    getDescription: (ctx: AutoDemoContext) => {
      if (!ctx.explanationId) {
        return `No explanation artifact is currently linked to the selected run (Stage: ${ctx.currentStage || 'IN_PROGRESS'}). Explanations are generated at Stage 9 (EXPLANATION).`;
      }
      return `Artifact: ${ctx.explanationId}. Examines the 5 deterministic gate predicates (connectivity, capacity, latency SLO, robustness >= 0.90, zero counterexamples), exact counterexample perturbation vectors, and local simulator elasticity gradients without LLM hallucination.`;
    },
    getNextPreview: () => 'Next: Monotonically Sequenced Audit Trace (AgentOps)',
    dwellSeconds: 5,
  },

  // 4. EXECUTION TRACE
  {
    id: 'trace',
    tabId: 'trace',
    tabLabel: 'Trace (AgentOps)',
    title: 'Monotonically Sequenced Audit Trace',
    getHeading: (ctx: AutoDemoContext) => {
      const count = ctx.workflowEventsCount || 0;
      if (count > 0) {
        return `Monotonically Sequenced Audit Events (${count} Events)`;
      }
      return 'Execution Trace & Event Timeline (0 Events)';
    },
    getDescription: (ctx: AutoDemoContext) => {
      const count = ctx.workflowEventsCount || 0;
      if (count > 0) {
        return `Immutable audit trail showing ${count} monotonic stage transitions, actor attribution (Ingestion Engine -> Triage Detector -> Agent A -> Agent B -> Simulator -> Human Operator), and exact millisecond timestamp offsets.`;
      }
      return `No audit events recorded for current run context (Stage: ${ctx.currentStage || 'INITIAL'}). Events are recorded monotonically as the workflow progresses.`;
    },
    getNextPreview: () => 'Next: Fidelity & Latency Distribution Metrics',
    dwellSeconds: 5,
  },

  // 5. METRICS
  {
    id: 'metrics',
    tabId: 'metrics',
    tabLabel: 'Metrics',
    title: 'Fidelity & Distribution Metrics',
    getHeading: () => 'Fidelity & Latency Distribution Metrics',
    getDescription: (ctx: AutoDemoContext) => {
      if (ctx.outcomeReport) {
        return `Latency & utilization distributions derived from actual SQLite audit records. Active run outcome: ${ctx.outcomeReport.post_action_latency_ms.toFixed(2)} ms latency (shift: ${ctx.outcomeReport.latency_delta_ms > 0 ? '+' : ''}${ctx.outcomeReport.latency_delta_ms.toFixed(2)} ms) with ${(ctx.outcomeReport.post_action_peak_utilization * 100).toFixed(1)}% peak utilization.`;
      }
      return `Nominal versus worst-case behavior across recorded runs. Visualizes latency distributions, stability metrics, and SLA threshold margins derived directly from persisted runs.`;
    },
    getNextPreview: () => 'Next: 4-Way Baseline Benchmarks in Evaluation Lab',
    dwellSeconds: 5,
  },

  // 6. EVALUATION LAB
  {
    id: 'evaluation',
    tabId: 'evaluation',
    tabLabel: 'Evaluation Lab',
    title: '4-Way Scientific Baseline Benchmarks',
    getHeading: () => '4-Way Baseline Benchmarks & Scientific Rigor',
    getDescription: (ctx: AutoDemoContext) => {
      const candidateInfo = ctx.selectedCandidateId ? `Active Candidate: ${ctx.selectedCandidateId}. ` : '';
      return `${candidateInfo}Empirical benchmark comparing FidelityGate against 3 standard policies: Nominal-Only (eliminates unsafe acceptances), Fixed Safety Margin (+25%, avoids false abstentions), and Non-Adaptive Sweeps (minimizes probe and simulation costs).`;
    },
    getNextPreview: () => 'Next: Immutable Audit Runs & Historical Forensics',
    dwellSeconds: 5,
  },

  // 7. AUDIT RUNS
  {
    id: 'history',
    tabId: 'history',
    tabLabel: 'Audit Runs',
    title: 'Immutable Audit Runs & Persistence',
    getHeading: (ctx: AutoDemoContext) => {
      if (ctx.selectedWorkflowRunId) {
        return `Immutable Audit Trail (Selected: ${ctx.selectedWorkflowRunId})`;
      }
      return 'Immutable Audit Runs (No Run Selected)';
    },
    getDescription: (ctx: AutoDemoContext) => {
      if (ctx.selectedWorkflowRunId) {
        return `Complete historical record of all executed workflows, gate decisions, and outcome identifiers persisted immutably in SQLite. Run ${ctx.selectedWorkflowRunId} is currently loaded into the workspace context.`;
      }
      return `Complete historical record of all executed workflows, gate decisions, and outcome identifiers persisted immutably in SQLite. Select a run to inspect its artifacts across all tabs.`;
    },
    getNextPreview: () => 'Next: Platform Architecture & Hackathon Judging Alignment',
    dwellSeconds: 5,
  },

  // 8. USER GUIDE
  {
    id: 'guide',
    tabId: 'guide',
    tabLabel: 'User Guide',
    title: 'Platform Guide & Hackathon Judging Alignment',
    getHeading: () => 'Platform Architecture & Judging Criteria Alignment',
    getDescription: () => {
      return `Comprehensive 12-section technical guide detailing system architecture, failure recovery invariants, and the 5 Hackathon Judging Criteria: Reusability, Governance & Responsibility, ROI/Business Value, MVP Readiness, and Originality & Innovation.`;
    },
    getNextPreview: () => 'Conclusion of Guided Auto Demo',
    dwellSeconds: 5,
  },
];
