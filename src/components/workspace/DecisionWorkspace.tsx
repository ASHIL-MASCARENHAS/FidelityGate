'use client';

import React, { useState } from 'react';
import {
  Play,
  ShieldCheck,
  AlertTriangle,
  XCircle,
  Sliders,
  RefreshCw,
  Zap,
  BarChart3,
} from 'lucide-react';
import { Twin3DViewer } from './Twin3DViewer';
import { SplineTwinCenterpiece } from './SplineTwinCenterpiece';
import { UncertaintyChart } from './UncertaintyChart';
import { TraceTimeline } from './TraceTimeline';
import { DecisionExplanationPanel } from '@/components/xai/DecisionExplanationPanel';
import { GateDecision, InvestigationResult, Scenario } from '@/types';
import { playTick, playConfirmation } from '@/lib/sound';
import { useWorkflowRun } from '@/context/WorkflowRunContext';

interface DecisionWorkspaceProps {
  scenarios?: Record<string, Scenario>;
  selectedKey: string;
  setSelectedKey: (key: string) => void;
  evaluations: number;
  setEvaluations: (n: number) => void;
  onRunInvestigation: (key: string, evals: number) => void;
  investigationResult?: InvestigationResult | null;
  loading: boolean;
  soundEnabled?: boolean;
}

export function DecisionWorkspace({
  scenarios = {},
  selectedKey,
  setSelectedKey,
  evaluations,
  setEvaluations,
  onRunInvestigation,
  investigationResult,
  loading,
  soundEnabled = false,
}: DecisionWorkspaceProps) {
  const {
    selectedWorkflow,
    evaluationId: contextEvalId,
    explanationId: contextExplId,
    adaptiveRunId: contextAdaptId,
    gateVerdict: contextGateVerdict,
    selectedCandidateId,
  } = useWorkflowRun();

  const [twinViewMode, setTwinViewMode] = useState<'spline_centerpiece' | 'fleet_topology'>(
    'spline_centerpiece'
  );

  const currentScenario: Scenario = scenarios[selectedKey] || {
    scenario_id: 'WAN-042',
    name: 'WAN congestion / reroute',
    description: 'Illustrative branch-to-core traffic burst with a proposed reroute.',
    nominal_latency_ms: 18,
    capacity_mbps: 1000,
    offered_load_mbps: 760,
    slo_latency_ms: 45,
    latency_multiplier_min: 0.85,
    latency_multiplier_max: 1.35,
    stability_threshold: 0.9,
  };

  const gate = investigationResult?.gate;
  const report = gate?.report;
  const decision: GateDecision = (contextGateVerdict as GateDecision) || gate?.decision || 'GATHER_EVIDENCE';
  const reason =
    selectedWorkflow?.termination_reason ||
    gate?.reason ||
    'Nominal prediction passes, but uncertainty variations breach the SLO; gather diagnostics.';
  const runId = selectedWorkflow?.workflow_run_id || (investigationResult?.run_id ? `RUN #${investigationResult.run_id}` : 'CANONICAL');
  const points = investigationResult?.sweep_points || [];

  // Theme styling based on decision
  const isAccept = decision === 'ACCEPT';
  const isEvidence = decision === 'GATHER_EVIDENCE';

  const decisionColor = isAccept
    ? 'text-emerald-verdict'
    : isEvidence
    ? 'text-amber-warning'
    : 'text-rose-abstain';

  const decisionBorder = isAccept
    ? 'border-emerald-verdict/40'
    : isEvidence
    ? 'border-amber-warning/40'
    : 'border-rose-abstain/40';

  const decisionBg = isAccept
    ? 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark'
    : isEvidence
    ? 'bg-amber-warning-subtle dark:bg-amber-warning-dark'
    : 'bg-rose-abstain-subtle dark:bg-rose-abstain-dark';

  const deltaLatency = report ? report.worst_latency_ms - report.nominal_latency_ms : 0;

  const handleRunClick = () => {
    playConfirmation(soundEnabled);
    onRunInvestigation(selectedKey, evaluations);
  };

  return (
    <div className="space-y-6">
      {/* Top Configuration & Policy Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Investigation Setup (Span 2) */}
        <div className="lg:col-span-2 editorial-card p-6 relative overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-lg bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt">
                <Sliders className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-bold text-ink dark:text-ink-dark tracking-tight">
                  Investigation Setup
                </h2>
                <p className="text-xs text-muted-fg dark:text-muted-dark">
                  Configure digital-twin uncertainty boundaries and sweep parameters
                </p>
              </div>
            </div>
            <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark">
              Deterministic Gate
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
            {/* Scenario Selector */}
            <div className="space-y-1.5">
              <label className="t-label font-medium text-ink dark:text-ink-dark flex items-center justify-between">
                <span>TARGET SCENARIO</span>
                <span className="text-cobalt font-semibold">{currentScenario.scenario_id}</span>
              </label>
              <select
                value={selectedKey}
                onChange={(e) => {
                  playTick(soundEnabled);
                  setSelectedKey(e.target.value);
                }}
                className="w-full bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark rounded-lg px-3.5 py-2.5 text-xs font-medium text-ink dark:text-ink-dark focus:outline-none focus:border-cobalt transition-colors cursor-pointer"
              >
                {Object.keys(scenarios).map((key) => (
                  <option key={key} value={key}>
                    {scenarios[key].scenario_id} · {scenarios[key].name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-muted-fg dark:text-muted-dark leading-relaxed italic pt-1">
                {currentScenario.description}
              </p>
            </div>

            {/* Evaluations Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-ink dark:text-ink-dark">UNCERTAINTY SWEEP EVALUATIONS</span>
                <span className="bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt px-2 py-0.5 rounded font-bold text-xs border border-cobalt/30">
                  {evaluations} samples
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="100"
                step="5"
                value={evaluations}
                onChange={(e) => {
                  playTick(soundEnabled);
                  setEvaluations(Number(e.target.value));
                }}
                className="w-full h-2 bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-[11px] font-mono text-muted-fg dark:text-muted-dark">
                <span>5 (Fast check)</span>
                <span>25 (Standard)</span>
                <span>50 (Rigorous)</span>
                <span>100 (Deep envelope)</span>
              </div>
            </div>
          </div>

          {/* Scenario Constraint Badges */}
          <div className="grid grid-cols-3 gap-3 p-3 rounded-lg bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark text-[11px] font-mono mb-5">
            <div>
              <span className="text-muted-fg dark:text-muted-dark block">Link Capacity</span>
              <span className="text-ink dark:text-ink-dark font-bold">{currentScenario.capacity_mbps} Mbps</span>
            </div>
            <div>
              <span className="text-muted-fg dark:text-muted-dark block">Offered Load</span>
              <span className="text-ink dark:text-ink-dark font-bold">{currentScenario.offered_load_mbps} Mbps</span>
            </div>
            <div>
              <span className="text-muted-fg dark:text-muted-dark block">SLO Latency Bound</span>
              <span className="text-amber-warning font-bold">{currentScenario.slo_latency_ms} ms</span>
            </div>
          </div>

          {/* Run Button */}
          <button
            onClick={handleRunClick}
            disabled={loading}
            className="w-full py-3 px-5 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white font-semibold text-xs uppercase tracking-wider flex items-center justify-center space-x-2.5 shadow-fine transition-all disabled:opacity-50 disabled:cursor-not-allowed group active:scale-[0.99]"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-white" />
                <span>Evaluating Deterministic Uncertainty Envelope…</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-white group-hover:scale-105 transition-transform" />
                <span>Run Bounded Investigation</span>
              </>
            )}
          </button>
        </div>

        {/* Right Column: Gate Policy Card */}
        <div className="editorial-card p-6 flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-cobalt" />
              <h3 className="t-panel-title">
                Deterministic Gate Policy
              </h3>
            </div>
            <p className="text-xs text-muted-fg dark:text-muted-dark mb-4 leading-relaxed">
              Zero-drift deterministic boundary rules governing candidate network intervention acceptance:
            </p>

            <div className="space-y-3">
              <div className="p-3 rounded-lg bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark border border-emerald-verdict/30">
                <div className="flex items-center space-x-2 text-xs font-bold text-emerald-verdict">
                  <span className="w-2 h-2 rounded-full bg-emerald-verdict" />
                  <span>ACCEPT</span>
                </div>
                <p className="text-[11px] text-muted-fg dark:text-muted-dark mt-1">
                  All evaluated variations stay within latency SLO and satisfy stability threshold.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-amber-warning-subtle dark:bg-amber-warning-dark border border-amber-warning/30">
                <div className="flex items-center space-x-2 text-xs font-bold text-amber-warning">
                  <span className="w-2 h-2 rounded-full bg-amber-warning" />
                  <span>GATHER_EVIDENCE</span>
                </div>
                <p className="text-[11px] text-muted-fg dark:text-muted-dark mt-1">
                  Nominal latency passes SLO, but uncertainty variations breach bounds. Requires live telemetry.
                </p>
              </div>

              <div className="p-3 rounded-lg bg-rose-abstain-subtle dark:bg-rose-abstain-dark border border-rose-abstain/30">
                <div className="flex items-center space-x-2 text-xs font-bold text-rose-abstain">
                  <span className="w-2 h-2 rounded-full bg-rose-abstain" />
                  <span>ABSTAIN</span>
                </div>
                <p className="text-[11px] text-muted-fg dark:text-muted-dark mt-1">
                  Candidate cannot be justified within configured uncertainty envelope; fail closed.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-hairline dark:border-hairline-dark flex items-center justify-between text-[11px] font-mono text-muted-fg dark:text-muted-dark">
            <span>Stability Threshold:</span>
            <span className="text-cobalt font-bold">
              {(currentScenario.stability_threshold * 100).toFixed(0)}% Minimum
            </span>
          </div>
        </div>
      </div>

      {/* Decision Assessment Hero Banner */}
      <div className={`p-6 rounded-xl border ${decisionBorder} ${decisionBg} shadow-fine transition-all`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <span className="t-eyebrow">
                FIDELITY GATE OUTCOME · {runId}
              </span>
              <span
                className={`text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full border ${decisionBorder} ${decisionColor}`}
              >
                {decision.replace('_', ' ')}
              </span>
            </div>
            <h2 className={`text-2xl md:text-3xl font-bold tracking-tight ${decisionColor}`}>
              {decision.replace('_', ' ')}
            </h2>
            <p className="text-xs sm:text-sm text-ink dark:text-ink-dark max-w-3xl leading-relaxed">
              {reason}
            </p>
          </div>

          <div className="flex-shrink-0 flex items-center space-x-3">
            <div className="text-right font-mono">
              <span className="text-[11px] text-muted-fg dark:text-muted-dark uppercase block">Stability Confidence</span>
              <span className="text-xl font-semibold text-ink dark:text-ink-dark">
                {report ? `${(report.stability_score * 100).toFixed(1)}%` : '—'}
              </span>
            </div>
            <div className={`w-12 h-12 rounded-xl border ${decisionBorder} ${decisionBg} flex items-center justify-center`}>
              {isAccept ? (
                <ShieldCheck className="w-6 h-6 text-emerald-verdict" />
              ) : isEvidence ? (
                <AlertTriangle className="w-6 h-6 text-amber-warning" />
              ) : (
                <XCircle className="w-6 h-6 text-rose-abstain" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 4 Core Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Nominal Latency */}
        <div className="editorial-card p-4">
          <span className="t-eyebrow block">
            Nominal Latency
          </span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-semibold text-ink dark:text-ink-dark t-metric">
              {report ? report.nominal_latency_ms.toFixed(1) : currentScenario.nominal_latency_ms.toFixed(1)}
              <span className="text-sm font-normal text-muted-fg dark:text-muted-dark ml-1">ms</span>
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt border border-cobalt/20">
              Base
            </span>
          </div>
          <span className="text-[11px] text-muted-fg dark:text-muted-dark mt-1 block">Normal twin baseline</span>
        </div>

        {/* Worst Sweep Latency */}
        <div className="editorial-card p-4">
          <span className="t-eyebrow block">
            Worst Sweep Latency
          </span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-semibold text-amber-warning t-metric">
              {report ? report.worst_latency_ms.toFixed(1) : (currentScenario.nominal_latency_ms * currentScenario.latency_multiplier_max).toFixed(1)}
              <span className="text-sm font-normal text-muted-fg dark:text-muted-dark ml-1">ms</span>
            </span>
            <span
              className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${
                deltaLatency > 0
                  ? 'bg-amber-warning-subtle dark:bg-amber-warning-dark text-amber-warning border border-amber-warning/30'
                  : 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark text-emerald-verdict'
              }`}
            >
              +{deltaLatency.toFixed(1)} ms
            </span>
          </div>
          <span className="text-[11px] text-muted-fg dark:text-muted-dark mt-1 block">Peak sweep deviation</span>
        </div>

        {/* Peak Utilization */}
        <div className="editorial-card p-4">
          <span className="t-eyebrow block">
            Peak Utilization
          </span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-semibold text-ink dark:text-ink-dark t-metric">
              {report ? (report.peak_utilization * 100).toFixed(1) : ((currentScenario.offered_load_mbps / currentScenario.capacity_mbps) * 100).toFixed(1)}
              <span className="text-sm font-normal text-muted-fg dark:text-muted-dark ml-1">%</span>
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark border border-hairline dark:border-hairline-dark">
              Capacity
            </span>
          </div>
          <span className="text-[11px] text-muted-fg dark:text-muted-dark mt-1 block">Max buffer queue load</span>
        </div>

        {/* Decision Stability */}
        <div className="editorial-card p-4">
          <span className="t-eyebrow block">
            Decision Stability
          </span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-black text-emerald-verdict font-mono">
              {report ? (report.stability_score * 100).toFixed(1) : '86.7'}
              <span className="text-sm font-normal text-muted-fg dark:text-muted-dark ml-1">%</span>
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark border border-hairline dark:border-hairline-dark">
              {report ? `${report.violations} Breaches` : '0 Breaches'}
            </span>
          </div>
          <span className="text-[11px] text-muted-fg dark:text-muted-dark mt-1 block">
            Threshold: {(currentScenario.stability_threshold * 100).toFixed(0)}%
          </span>
        </div>
      </div>

      {/* Visualizers Row: 3D Twin & Uncertainty Sweep */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cobalt" />
              <h3 className="t-panel-title">
                Twin-System 3D Centerpiece
              </h3>
            </div>

            {/* View Mode Toggle */}
            <div className="flex items-center space-x-1 bg-surface dark:bg-surface-dark p-0.5 rounded-lg border border-hairline dark:border-hairline-dark text-[11px] font-mono">
              <button
                onClick={() => {
                  playTick(soundEnabled);
                  setTwinViewMode('spline_centerpiece');
                }}
                className={`px-2 py-1 rounded-md transition-all ${
                  twinViewMode === 'spline_centerpiece'
                    ? 'bg-cobalt text-white font-bold'
                    : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                Spline 3D Twin
              </button>
              <button
                onClick={() => {
                  playTick(soundEnabled);
                  setTwinViewMode('fleet_topology');
                }}
                className={`px-2 py-1 rounded-md transition-all ${
                  twinViewMode === 'fleet_topology'
                    ? 'bg-cobalt text-white font-bold'
                    : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                Fleet Network 3D
              </button>
            </div>
          </div>

          {twinViewMode === 'spline_centerpiece' ? (
            <SplineTwinCenterpiece
              decision={decision}
              nominalLatency={report ? Math.round(report.nominal_latency_ms) : 18}
              worstLatency={report ? Math.round(report.worst_latency_ms) : 50}
              fidelityScore={report ? Math.round(report.stability_score * 100) : 94}
            />

          ) : (
            <Twin3DViewer
              decision={decision}
              nominalLatency={report ? Math.round(report.nominal_latency_ms) : 18}
              worstLatency={report ? Math.round(report.worst_latency_ms) : 50}
              peakUtil={report ? Math.round(report.peak_utilization * 100) : 87}
            />

          )}
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <BarChart3 className="w-4 h-4 text-cobalt" />
              <h3 className="t-panel-title">
                Uncertainty Envelope & SLO Boundary
              </h3>
            </div>
            <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">
              {points.length} Swept Samples
            </span>
          </div>
          <UncertaintyChart
            points={points}
            slo={currentScenario.slo_latency_ms}
            nominal={report ? report.nominal_latency_ms : 18}
            worst={report ? report.worst_latency_ms : 50}
            violations={report ? report.violations : 2}
            sensitivity={report?.sensitivity}
          />

        </div>
      </div>

      {/* Bottom Row: Investigation Trace */}
      <TraceTimeline
        report={report}
        decision={decision}
        reason={reason}
        scenario={currentScenario}
      />

      {/* Layer 6: Evidence-Based Explainable AI & Decision Attribution */}
      <div className="mt-8 pt-6 border-t border-hairline dark:border-hairline-dark">
        <DecisionExplanationPanel
          scenarioKey={selectedKey}
          evaluationId={
            contextEvalId ||
            (typeof (investigationResult as any)?.evaluation_id === 'string' &&
            (investigationResult as any).evaluation_id.startsWith('eval-')
              ? (investigationResult as any).evaluation_id
              : undefined)
          }
          explanationId={contextExplId || undefined}
          adaptiveRunId={contextAdaptId || undefined}
          workflowRunId={selectedWorkflow?.workflow_run_id}
          loading={loading}
        />
      </div>

    </div>
  );
}
export default DecisionWorkspace;
