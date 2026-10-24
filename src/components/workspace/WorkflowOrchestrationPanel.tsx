'use client';

import React, { useState, useEffect } from 'react';
import {
  Play,
  ShieldCheck,
  AlertTriangle,
  XCircle,
  Clock,
  UserCheck,
  ArrowRight,
  RefreshCw,
  CheckCircle2,
  AlertOctagon,
  FileCheck,
  Activity,
  Layers,
  ChevronRight,
  Sliders,
  Info,
} from 'lucide-react';
import {
  WorkflowRunSummary,
  WorkflowEvent,
  HumanApprovalRecord,
  InterventionOutcomeReport,
  WorkflowStage,
  WorkflowStatus,
  ApprovalDecision,
  OverallImpact,
} from '@/types';
import { playTick, playConfirmation } from '@/lib/sound';
import { useWorkflowRun } from '@/context/WorkflowRunContext';

interface WorkflowOrchestrationPanelProps {
  scenarioKey?: string;
  soundEnabled?: boolean;
}

const STAGES_ORDER: WorkflowStage[] = [
  'RECEIVED',
  'VALIDATING',
  'TRIAGE',
  'INVESTIGATION',
  'CANDIDATE_EVALUATION',
  'COUNTEREXAMPLE_ANALYSIS',
  'ADAPTIVE_DIAGNOSTICS',
  'REEVALUATION',
  'EXPLANATION',
  'GATE_REVIEW',
  'AWAITING_HUMAN_APPROVAL',
  'SIMULATED_ACTION',
  'OUTCOME_REPORTED',
];

export function WorkflowOrchestrationPanel({
  scenarioKey = 'wan_congestion',
  soundEnabled = false,
}: WorkflowOrchestrationPanelProps) {
  const {
    selectedWorkflow,
    selectedWorkflowRunId,
    selectWorkflowRun,
    setWorkflowSummary,
    refreshSelectedWorkflow,
    workflowEvents: contextEvents,
    approvalRecord: contextApproval,
    outcomeReport: contextOutcome,
  } = useWorkflowRun();

  const [selectedScenario, setSelectedScenario] = useState<string>(scenarioKey);
  const [reviewerId, setReviewerId] = useState<string>('operator-alice');
  const [reviewerComment, setReviewerComment] = useState<string>('');
  
  const [loading, setLoading] = useState<boolean>(false);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [activeWorkflow, setActiveWorkflow] = useState<WorkflowRunSummary | null>(selectedWorkflow);
  const [events, setEvents] = useState<WorkflowEvent[]>(contextEvents);
  const [approval, setApproval] = useState<HumanApprovalRecord | null>(contextApproval);
  const [outcome, setOutcome] = useState<InterventionOutcomeReport | null>(contextOutcome);
  const [recentWorkflows, setRecentWorkflows] = useState<WorkflowRunSummary[]>([]);

  // Synchronize with canonical WorkflowRunContext if activeWorkflow differs
  useEffect(() => {
    if (selectedWorkflow) {
      setActiveWorkflow(selectedWorkflow);
      setEvents(contextEvents);
      setApproval(contextApproval);
      setOutcome(contextOutcome);
    }
  }, [selectedWorkflow, contextEvents, contextApproval, contextOutcome]);

  // Fetch recent workflows on mount
  useEffect(() => {
    loadRecentWorkflows();
  }, []);

  const loadRecentWorkflows = async () => {
    try {
      const res = await fetch('/api/v1/workflows?limit=10');
      if (res.ok) {
        const data = await res.json();
        setRecentWorkflows(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      // ignore
    }
  };

  const loadWorkflowDetails = async (wfId: string) => {
    try {
      // Select canonical run across all workspace tabs
      selectWorkflowRun(wfId);

      // 1. Summary
      const resSum = await fetch(`/api/v1/workflows/${wfId}`);
      if (resSum.ok) {
        const sumData = await resSum.json();
        setActiveWorkflow(sumData);
      }

      // 2. Events
      const resEvents = await fetch(`/api/v1/workflows/${wfId}/events`);
      if (resEvents.ok) {
        const evData = await resEvents.json();
        setEvents(Array.isArray(evData) ? evData : []);
      }

      // 3. Approval
      const resAppr = await fetch(`/api/v1/workflows/${wfId}/approval`);
      if (resAppr.ok) {
        const apprData = await resAppr.json();
        setApproval(apprData);
      } else {
        setApproval(null);
      }

      // 4. Outcome
      const resOut = await fetch(`/api/v1/workflows/${wfId}/outcome`);
      if (resOut.ok) {
        const outData = await resOut.json();
        setOutcome(outData);
      } else {
        setOutcome(null);
      }
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleInitiateWorkflow = async (autoApprove: boolean = false) => {
    setLoading(true);
    setError(null);
    playConfirmation(soundEnabled);

    try {
      const res = await fetch('/api/v1/workflows', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario_id: selectedScenario,
          reviewer_id: reviewerId,
          auto_approve_for_testing: autoApprove,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error || 'Failed to initiate workflow');
      }

      const summary: WorkflowRunSummary = await res.json();
      setActiveWorkflow(summary);
      setWorkflowSummary(summary);
      await loadWorkflowDetails(summary.workflow_run_id);
      await loadRecentWorkflows();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDecisionAction = async (decision: ApprovalDecision) => {
    if (!activeWorkflow) return;
    setActionLoading(true);
    setError(null);
    playTick(soundEnabled);

    try {
      const res = await fetch(`/api/v1/workflows/${activeWorkflow.workflow_run_id}/approval`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          decision,
          reviewer_id: reviewerId,
          reviewer_comment: reviewerComment || `Operator decided ${decision} via dashboard.`,
        }),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error || `Failed to record ${decision}`);
      }

      // Reload full state and sync shared run context
      await loadWorkflowDetails(activeWorkflow.workflow_run_id);
      await refreshSelectedWorkflow();
      await loadRecentWorkflows();
    } catch (err: any) {
      setError(err.message);
    } finally {
      setActionLoading(false);
    }
  };

  // Determine stage progression index
  const currentStageIndex = activeWorkflow
    ? STAGES_ORDER.indexOf(activeWorkflow.current_stage)
    : -1;

  const isGateAbstain = activeWorkflow?.gate_verdict === 'ABSTAIN';
  const isAwaitingApproval = activeWorkflow?.status === 'AWAITING_APPROVAL';
  const isCompleted = activeWorkflow?.status === 'COMPLETED';

  return (
    <div className="space-y-6">
      {/* Header & Control Bar */}
      <div className="editorial-card p-6 relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Layers className="w-5 h-5 text-cobalt" />
              <h2 className="text-lg font-bold text-ink dark:text-ink-dark tracking-tight">
                Layer 7: End-to-End Workflow Orchestrator & Human Authorization
              </h2>
            </div>
            <p className="text-xs text-muted-fg dark:text-muted-dark max-w-2xl">
              Deterministic 13-stage pipeline enforcing strict separation between agentic investigation, 
              counterexample-guided verification, human authorization boundary, and isolated twin simulation.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value)}
              className="text-xs font-mono px-3 py-2 rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-ink dark:text-ink-dark"
            >
              <option value="wan_congestion">WAN Congestion Surge (wan_congestion)</option>
              <option value="fiber_drift">Fiber Latency Calibration Drift (fiber_drift)</option>
              <option value="traffic_burst">Hidden Traffic Burst Spikes (traffic_burst)</option>
              <option value="cisco_bgp_clear">Cisco BGP Clear Telemetry Replay (cisco_bgp_clear)</option>
            </select>

            <button
              onClick={() => handleInitiateWorkflow(false)}
              disabled={loading}
              className="px-4 py-2 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white text-xs font-mono font-bold flex items-center space-x-2 shadow-fine transition-all disabled:opacity-50"
            >
              {loading ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Play className="w-4 h-4 fill-white" />
              )}
              <span>Initiate Workflow (Pause at Gate)</span>
            </button>

            <button
              onClick={() => handleInitiateWorkflow(true)}
              disabled={loading}
              className="px-4 py-2 rounded-xl border border-hairline dark:border-hairline-dark hover:bg-surface dark:hover:bg-surface-dark text-xs font-mono font-semibold text-muted-fg dark:text-muted-dark transition-all disabled:opacity-50"
            >
              Auto-Approve Test Run
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs font-mono text-rose-600 dark:text-rose-400 flex items-center space-x-2">
            <XCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
      </div>

      {/* 13-Stage Visual Pipeline State Machine */}
      <div className="editorial-card p-6">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cobalt" />
            <h3 className="t-panel-title">End-to-End State Machine Execution</h3>
          </div>
          {activeWorkflow && (
            <span className="text-[11px] font-mono px-2.5 py-0.5 rounded-full bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-cobalt">
              Run: {activeWorkflow.workflow_run_id} ({activeWorkflow.status})
            </span>
          )}
        </div>

        <div className="overflow-x-auto pb-2">
          <div className="flex items-center min-w-[900px] justify-between text-center">
            {STAGES_ORDER.map((stage, idx) => {
              const isPast = currentStageIndex > idx;
              const isCurrent = currentStageIndex === idx;
              const isFuture = currentStageIndex < idx;

              let circleClass = 'bg-surface dark:bg-surface-dark text-muted-fg border-hairline dark:border-hairline-dark';
              let textClass = 'text-muted-fg dark:text-muted-dark';

              if (isPast) {
                circleClass = 'bg-emerald-500 text-white border-emerald-500';
                textClass = 'text-emerald-700 dark:text-emerald-400 font-semibold';
              } else if (isCurrent) {
                circleClass = 'bg-cobalt text-white border-cobalt ring-2 ring-cobalt/30 animate-pulse';
                textClass = 'text-cobalt font-bold';
              }

              return (
                <React.Fragment key={stage}>
                  <div className="flex flex-col items-center flex-1 max-w-[90px]">
                    <div
                      className={`w-7 h-7 rounded-full border flex items-center justify-center text-xs font-mono transition-all ${circleClass}`}
                    >
                      {isPast ? <CheckCircle2 className="w-4 h-4" /> : idx + 1}
                    </div>
                    <span className={`text-[10px] mt-1.5 leading-tight font-mono truncate w-full ${textClass}`}>
                      {stage.replace(/_/g, ' ')}
                    </span>
                  </div>
                  {idx < STAGES_ORDER.length - 1 && (
                    <div
                      className={`h-0.5 flex-1 transition-all ${
                        isPast ? 'bg-emerald-500' : 'bg-hairline dark:bg-hairline-dark'
                      }`}
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>
      </div>

      {/* Main Grid: Human Approval Boundary (Left) & Outcome Report (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Human Authorization Boundary */}
        <div className="editorial-card p-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-hairline dark:border-hairline-dark">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt">
                  <UserCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="t-panel-title">Human Authorization Boundary</h3>
                  <p className="text-[11px] text-muted-fg dark:text-muted-dark">
                    Strict isolation: No autonomous network alterations permitted
                  </p>
                </div>
              </div>

              {activeWorkflow?.gate_verdict && (
                <span
                  className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded-full ${
                    activeWorkflow.gate_verdict === 'ACCEPT'
                      ? 'bg-emerald-verdict-subtle text-emerald-verdict border border-emerald-verdict/30'
                      : activeWorkflow.gate_verdict === 'GATHER_EVIDENCE'
                      ? 'bg-amber-warning-subtle text-amber-warning border border-amber-warning/30'
                      : 'bg-rose-abstain-subtle text-rose-abstain border border-rose-abstain/30'
                  }`}
                >
                  Gate: {activeWorkflow.gate_verdict}
                </span>
              )}
            </div>

            {/* Target Intervention Context */}
            <div className="p-3.5 rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark space-y-2 text-xs font-mono">
              <div className="flex justify-between">
                <span className="text-muted-fg dark:text-muted-dark">Selected Candidate:</span>
                <span className="font-bold text-ink dark:text-ink-dark">
                  {activeWorkflow?.selected_candidate_id || (activeWorkflow ? 'None Proposed' : 'Pending Initialization')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-fg dark:text-muted-dark">XAI Explanation Ref:</span>
                <span className="text-cobalt">
                  {activeWorkflow?.explanation_id || 'expl-pending'}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-fg dark:text-muted-dark">Evidence Currency:</span>
                <span className="text-emerald-verdict font-semibold">fidelitygate-v1.0 (Fresh)</span>
              </div>
            </div>

            {/* Invariant Warning */}
            <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-ink dark:text-ink-dark space-y-1">
              <div className="flex items-center space-x-2 font-bold text-amber-700 dark:text-amber-400 font-mono">
                <AlertOctagon className="w-4 h-4 shrink-0" />
                <span>Deterministic Gate Precedence Invariant</span>
              </div>
              <p className="text-[11px] text-muted-fg dark:text-muted-dark leading-relaxed">
                Human authorization is required to execute a proposed reroute, but a human operator 
                <strong> cannot override a gate ABSTAIN</strong>. Interventions violating mandatory safety invariants fail closed.
              </p>
            </div>

            {/* Reviewer Inputs */}
            <div className="space-y-3 pt-2">
              <div>
                <label className="text-[11px] font-mono text-muted-fg dark:text-muted-dark block mb-1">
                  Operator / Reviewer Identity
                </label>
                <input
                  type="text"
                  value={reviewerId}
                  onChange={(e) => setReviewerId(e.target.value)}
                  className="w-full text-xs font-mono px-3 py-2 rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-ink dark:text-ink-dark"
                  placeholder="e.g. netops-senior-alice"
                />
              </div>

              <div>
                <label className="text-[11px] font-mono text-muted-fg dark:text-muted-dark block mb-1">
                  Authorization Audit Comments
                </label>
                <input
                  type="text"
                  value={reviewerComment}
                  onChange={(e) => setReviewerComment(e.target.value)}
                  className="w-full text-xs font-mono px-3 py-2 rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-ink dark:text-ink-dark"
                  placeholder="e.g. Authorized for off-peak maintenance window."
                />
              </div>
            </div>
          </div>

          {/* Action Decision Buttons */}
          <div className="pt-5 mt-5 border-t border-hairline dark:border-hairline-dark">
            {isAwaitingApproval ? (
              <div className="flex flex-col sm:flex-row gap-2.5">
                <button
                  onClick={() => handleDecisionAction('APPROVED')}
                  disabled={actionLoading || isGateAbstain}
                  className={`flex-1 py-2.5 px-4 rounded-xl text-xs font-mono font-bold flex items-center justify-center space-x-1.5 transition-all shadow-md ${
                    isGateAbstain
                      ? 'bg-muted-fg/20 text-muted-fg cursor-not-allowed'
                      : 'bg-cobalt hover:bg-cobalt-hover text-white active:scale-95'
                  }`}
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Authorize Intervention</span>
                </button>

                <button
                  onClick={() => handleDecisionAction('REJECTED')}
                  disabled={actionLoading}
                  className="py-2.5 px-3 rounded-xl border border-rose-500/30 text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 text-xs font-mono font-medium transition-all"
                >
                  Reject & Halt
                </button>

                <button
                  onClick={() => handleDecisionAction('CHANGES_REQUESTED')}
                  disabled={actionLoading}
                  className="py-2.5 px-3 rounded-xl border border-amber-500/30 text-amber-600 dark:text-amber-400 hover:bg-amber-500/10 text-xs font-mono font-medium transition-all"
                >
                  Request Changes
                </button>
              </div>
            ) : approval ? (
              <div className="p-3 rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark flex items-center justify-between text-xs font-mono">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-verdict" />
                  <span className="font-bold text-ink dark:text-ink-dark">
                    Recorded Decision: {approval.decision}
                  </span>
                </div>
                <span className="text-[11px] text-muted-fg dark:text-muted-dark">
                  by {approval.reviewer_id}
                </span>
              </div>
            ) : (
              <div className="text-center py-2 text-xs font-mono text-muted-fg dark:text-muted-dark">
                Initiate a workflow to pause at human approval boundary.
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Comparative Outcome Report */}
        <div className="editorial-card p-6 flex flex-col justify-between">
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-hairline dark:border-hairline-dark">
              <div className="flex items-center space-x-2.5">
                <div className="w-8 h-8 rounded-xl bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark flex items-center justify-center text-emerald-verdict">
                  <FileCheck className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="t-panel-title">Post-Intervention Outcome Report</h3>
                  <p className="text-[11px] text-muted-fg dark:text-muted-dark">
                    Comparative twin simulation: Baseline vs Candidate Intervention
                  </p>
                </div>
              </div>

              {outcome && (
                <span
                  className={`text-[11px] font-mono font-bold px-2.5 py-1 rounded-full ${
                    outcome.overall_impact === 'IMPROVED'
                      ? 'bg-emerald-verdict-subtle text-emerald-verdict border border-emerald-verdict/30'
                      : outcome.overall_impact === 'MIXED'
                      ? 'bg-amber-warning-subtle text-amber-warning border border-amber-warning/30'
                      : outcome.overall_impact === 'UNCHANGED' || outcome.overall_impact === 'NEUTRAL'
                      ? 'bg-cobalt-subtle text-cobalt border border-cobalt/30'
                      : 'bg-rose-abstain-subtle text-rose-abstain border border-rose-abstain/30'
                  }`}
                >
                  Impact: {outcome.overall_impact}
                </span>
              )}
            </div>

            {outcome ? (
              <div className="space-y-4">
                {/* 2x2 Metric Comparison Grid */}
                <div className="grid grid-cols-2 gap-3 font-mono text-xs">
                  {/* Latency Comparison */}
                  <div className="p-3 rounded-xl border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50 space-y-1">
                    <span className="text-[10px] uppercase text-muted-fg dark:text-muted-dark block">
                      RTT Latency Shift
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-sm line-through text-muted-fg">
                        {outcome.pre_action_latency_ms.toFixed(2)} ms
                      </span>
                      <ArrowRight className="w-3 h-3 text-muted-fg inline" />
                      <span className={`text-base font-bold ${
                        outcome.latency_delta_ms < 0 ? 'text-emerald-verdict' : outcome.latency_delta_ms > 0 ? 'text-rose-abstain' : 'text-cobalt'
                      }`}>
                        {outcome.post_action_latency_ms.toFixed(2)} ms
                      </span>
                    </div>
                    <span className={`text-[11px] font-bold block ${
                      outcome.latency_delta_ms < 0 ? 'text-emerald-verdict' : outcome.latency_delta_ms > 0 ? 'text-rose-abstain' : 'text-muted-fg'
                    }`}>
                      {outcome.latency_delta_ms < 0
                        ? `${Math.abs(outcome.latency_delta_ms).toFixed(2)} ms reduction (${Math.abs(outcome.latency_reduction_pct).toFixed(1)}%)`
                        : outcome.latency_delta_ms > 0
                        ? `+${outcome.latency_delta_ms.toFixed(2)} ms increase (+${Math.abs(outcome.latency_reduction_pct).toFixed(1)}%)`
                        : '0.00 ms (0.0% unchanged)'}
                    </span>
                  </div>

                  {/* Utilization Comparison */}
                  <div className="p-3 rounded-xl border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50 space-y-1">
                    <span className="text-[10px] uppercase text-muted-fg dark:text-muted-dark block">
                      Peak Edge Utilization
                    </span>
                    <div className="flex items-baseline space-x-2">
                      <span className="text-sm line-through text-muted-fg">
                        {(outcome.pre_action_peak_utilization * 100).toFixed(1)}%
                      </span>
                      <ArrowRight className="w-3 h-3 text-muted-fg inline" />
                      <span className={`text-base font-bold ${
                        outcome.post_action_peak_utilization > 1.0 ? 'text-rose-abstain' : 'text-cobalt'
                      }`}>
                        {(outcome.post_action_peak_utilization * 100).toFixed(1)}%
                      </span>
                    </div>
                    <span className={`text-[11px] font-bold block ${
                      outcome.post_action_peak_utilization < outcome.pre_action_peak_utilization
                        ? 'text-cobalt'
                        : outcome.post_action_peak_utilization > outcome.pre_action_peak_utilization
                        ? 'text-amber-warning'
                        : 'text-muted-fg'
                    }`}>
                      {outcome.post_action_peak_utilization < outcome.pre_action_peak_utilization
                        ? `${((outcome.pre_action_peak_utilization - outcome.post_action_peak_utilization) * 100).toFixed(1)}% headroom gain`
                        : outcome.post_action_peak_utilization > outcome.pre_action_peak_utilization
                        ? `${((outcome.post_action_peak_utilization - outcome.pre_action_peak_utilization) * 100).toFixed(1)}% load increase`
                        : '0.0% utilization delta'}
                    </span>
                    <span className="text-[10px] text-muted-fg dark:text-muted-dark block truncate">
                      Bottleneck: {outcome.bottleneck_link}
                    </span>
                  </div>

                  {/* Capacity Violations */}
                  <div className="p-3 rounded-xl border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50 space-y-1">
                    <span className="text-[10px] uppercase text-muted-fg dark:text-muted-dark block">
                      Capacity Violations
                    </span>
                    <span className={`text-base font-bold block ${
                      outcome.post_action_capacity_violations > 0 ? 'text-rose-abstain' : 'text-ink dark:text-ink-dark'
                    }`}>
                      {outcome.post_action_capacity_violations} breaches
                    </span>
                    <span className={`text-[11px] font-semibold ${
                      outcome.post_action_capacity_violations === 0 ? 'text-emerald-verdict' : 'text-rose-abstain'
                    }`}>
                      {outcome.post_action_capacity_violations === 0
                        ? 'All edges compliant (0 breaches)'
                        : `${outcome.post_action_capacity_violations} link(s) breach capacity constraint`}
                    </span>
                  </div>

                  {/* SLO Violations */}
                  <div className="p-3 rounded-xl border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50 space-y-1">
                    <span className="text-[10px] uppercase text-muted-fg dark:text-muted-dark block">
                      SLO Budget Violations
                    </span>
                    <span className={`text-base font-bold block ${
                      outcome.post_action_slo_violations > 0 ? 'text-rose-abstain' : 'text-ink dark:text-ink-dark'
                    }`}>
                      {outcome.post_action_slo_violations} breaches
                    </span>
                    <span className={`text-[11px] font-semibold ${
                      outcome.post_action_slo_violations === 0 ? 'text-emerald-verdict' : 'text-rose-abstain'
                    }`}>
                      {outcome.post_action_slo_violations === 0
                        ? 'SLA contract satisfied (0 breaches)'
                        : `${outcome.post_action_slo_violations} flow(s) exceed latency contract`}
                    </span>
                  </div>
                </div>

                {/* Audit Linkage & Provenance */}
                <div className="p-3 rounded-xl bg-surface/30 dark:bg-surface-dark/30 border border-hairline dark:border-hairline-dark grid grid-cols-2 gap-2 text-[10px] font-mono text-muted-fg dark:text-muted-dark">
                  <div>
                    <span className="block font-semibold text-ink dark:text-ink-dark">Outcome ID:</span>
                    <span className="truncate block">{outcome.outcome_id}</span>
                  </div>
                  <div>
                    <span className="block font-semibold text-ink dark:text-ink-dark">Model Version:</span>
                    <span className="truncate block">{outcome.model_version || 'fidelitygate-v1.0'}</span>
                  </div>
                  <div>
                    <span className="block font-semibold text-ink dark:text-ink-dark">Affected Flows ({outcome.affected_flows?.length || 0}):</span>
                    <span className="truncate block">{outcome.affected_flows?.join(', ') || 'none'}</span>
                  </div>
                  <div>
                    <span className="block font-semibold text-ink dark:text-ink-dark">Execution Twin ID:</span>
                    <span className="truncate block">{outcome.execution_id}</span>
                  </div>
                </div>

                {/* Executive Summary & Boundaries */}
                <div className="p-3 rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark space-y-2">
                  <span className="text-[11px] font-bold text-ink dark:text-ink-dark font-mono block">
                    Intervention Assessment & Boundaries
                  </span>
                  <p className="text-xs text-muted-fg dark:text-muted-dark leading-relaxed font-mono">
                    Intervention {outcome.candidate_id} on {outcome.scenario_id} produced {outcome.overall_impact} outcome with {outcome.post_action_capacity_violations} capacity and {outcome.post_action_slo_violations} SLO breaches.
                  </p>
                  {outcome.assumptions_and_limitations?.length > 0 && (
                    <ul className="text-[10px] text-muted-fg dark:text-muted-dark space-y-1 font-mono list-disc list-inside">
                      {outcome.assumptions_and_limitations.map((lim, i) => (
                        <li key={i}>{lim}</li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>
            ) : (
              <div className="py-12 text-center text-xs font-mono text-muted-fg dark:text-muted-dark border border-dashed border-hairline dark:border-hairline-dark rounded-xl">
                Outcome report generated after operator authorization and digital-twin execution.
              </div>
            )}
          </div>

          {/* Operational Boundaries Disclaimer */}
          <div className="pt-4 mt-4 border-t border-hairline dark:border-hairline-dark flex items-start space-x-2 text-[11px] font-mono text-muted-fg dark:text-muted-dark">
            <Info className="w-3.5 h-3.5 text-cobalt shrink-0 mt-0.5" />
            <span>
              <strong>Environment Isolation:</strong> Simulation executed strictly in offline digital twin. 
              No physical router configuration changes made.
            </span>
          </div>
        </div>
      </div>

      {/* Monotonically Sequenced Audit Events Trail */}
      {events.length > 0 && (
        <div className="editorial-card p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Clock className="w-4 h-4 text-cobalt" />
              <h3 className="t-panel-title">Monotonically Sequenced Audit Trail</h3>
            </div>
            <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">
              {events.length} Persisted Audit Events
            </span>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
            {events.map((ev) => (
              <div
                key={ev.event_id}
                className="p-2.5 rounded-lg bg-surface/50 dark:bg-surface-dark/50 border border-hairline dark:border-hairline-dark flex items-center justify-between text-xs font-mono"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-cobalt font-bold w-6 text-center">
                    #{ev.sequence_number}
                  </span>
                  <span className="px-2 py-0.5 rounded bg-surface dark:bg-surface-dark text-[11px] border border-hairline dark:border-hairline-dark text-muted-fg">
                    {ev.stage}
                  </span>
                  <span className="font-semibold text-ink dark:text-ink-dark">
                    {ev.event_type}
                  </span>
                </div>
                <span className="text-[10px] text-muted-fg dark:text-muted-dark">
                  {new Date(ev.timestamp).toLocaleTimeString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default WorkflowOrchestrationPanel;
