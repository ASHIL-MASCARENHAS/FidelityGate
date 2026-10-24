import React, { useState } from 'react';
import { Play, ShieldCheck, AlertTriangle, XCircle, Sliders, Activity, Info, Network, BarChart3, RefreshCw, Sparkles, Zap } from 'lucide-react';
import Twin3DViewer from './Twin3DViewer';
import SplineTwinCenterpiece from './SplineTwinCenterpiece';
import UncertaintyChart from './UncertaintyChart';
import TraceTimeline from './TraceTimeline';

export default function DecisionWorkspace({
  scenarios = {},
  selectedKey,
  setSelectedKey,
  evaluations,
  setEvaluations,
  onRunInvestigation,
  investigationResult,
  loading
}) {
  const [twinViewMode, setTwinViewMode] = useState('spline_centerpiece'); // 'spline_centerpiece' or 'fleet_topology'

  const currentScenario = scenarios[selectedKey] || {
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
  const decision = gate?.decision || 'GATHER_EVIDENCE';
  const reason = gate?.reason || 'Nominal prediction passes, but uncertainty variations breach the SLO; gather diagnostics.';
  const runId = investigationResult?.run_id || 1;
  const points = investigationResult?.sweep_points || [];

  // Theme styling based on decision
  const isAccept = decision === 'ACCEPT';
  const isEvidence = decision === 'GATHER_EVIDENCE';
  const isAbstain = decision === 'ABSTAIN';

  const decisionColor = isAccept ? 'text-[#39d3a4]' : isEvidence ? 'text-[#f3b64b]' : 'text-[#ff667d]';
  const decisionBorder = isAccept ? 'border-[#39d3a4]/50' : isEvidence ? 'border-[#f3b64b]/50' : 'border-[#ff667d]/50';
  const decisionBg = isAccept ? 'bg-[#39d3a4]/10' : isEvidence ? 'bg-[#f3b64b]/10' : 'bg-[#ff667d]/10';
  const decisionGlow = isAccept ? 'shadow-[0_0_30px_rgba(57,211,164,0.15)]' : isEvidence ? 'shadow-[0_0_30px_rgba(243,182,75,0.15)]' : 'shadow-[0_0_30px_rgba(255,102,125,0.15)]';

  const deltaLatency = report ? report.worst_latency_ms - report.nominal_latency_ms : 0;

  return (
    <div className="space-y-6">
      {/* Top Configuration & Policy Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Investigation Setup (Span 2) */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl relative overflow-hidden">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2.5">
              <div className="p-2 rounded-xl bg-cyan-950/60 border border-cyan-700/50 text-cyan-400">
                <Sliders className="w-4 h-4" />
              </div>
              <div>
                <h2 className="text-base font-bold text-white tracking-tight">Investigation Setup</h2>
                <p className="text-xs text-slate-400">Configure twin uncertainty boundaries and sweep parameters</p>
              </div>
            </div>
            <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-slate-900 border border-slate-700 text-cyan-300">
              Deterministic Engine
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5 mb-5">
            {/* Scenario Selector */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono font-medium text-slate-300 flex items-center justify-between">
                <span>TARGET SCENARIO</span>
                <span className="text-cyan-400 font-semibold">{currentScenario.scenario_id}</span>
              </label>
              <select
                value={selectedKey}
                onChange={(e) => setSelectedKey(e.target.value)}
                className="w-full bg-[#0a1220] border border-slate-700/80 rounded-xl px-3.5 py-2.5 text-xs font-medium text-slate-100 focus:outline-none focus:border-cyan-500 transition-colors cursor-pointer"
              >
                {Object.keys(scenarios).map((key) => (
                  <option key={key} value={key}>
                    {scenarios[key].scenario_id} · {scenarios[key].name}
                  </option>
                ))}
              </select>
              <p className="text-[11px] text-slate-400 leading-relaxed italic pt-1">
                {currentScenario.description}
              </p>
            </div>

            {/* Evaluations Slider */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-xs font-mono">
                <span className="text-slate-300">UNCERTAINTY SWEEP EVALUATIONS</span>
                <span className="bg-cyan-950 text-cyan-300 border border-cyan-800 px-2 py-0.5 rounded font-bold text-xs">
                  {evaluations} samples
                </span>
              </div>
              <input
                type="range"
                min="5"
                max="100"
                step="5"
                value={evaluations}
                onChange={(e) => setEvaluations(Number(e.target.value))}
                className="w-full h-2 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-cyan-400"
              />
              <div className="flex justify-between text-[10px] font-mono text-slate-500">
                <span>5 (Fast check)</span>
                <span>25 (Standard)</span>
                <span>50 (Rigorous)</span>
                <span>100 (Deep envelope)</span>
              </div>
            </div>
          </div>

          {/* Scenario Constraint Badges */}
          <div className="grid grid-cols-3 gap-3 p-3 rounded-xl bg-[#09111c] border border-slate-800/80 text-[11px] font-mono mb-5">
            <div>
              <span className="text-slate-500 block">Link Capacity</span>
              <span className="text-slate-200 font-bold">{currentScenario.capacity_mbps} Mbps</span>
            </div>
            <div>
              <span className="text-slate-500 block">Offered Load</span>
              <span className="text-slate-200 font-bold">{currentScenario.offered_load_mbps} Mbps</span>
            </div>
            <div>
              <span className="text-slate-500 block">SLO Latency Bound</span>
              <span className="text-amber-300 font-bold">{currentScenario.slo_latency_ms} ms</span>
            </div>
          </div>

          {/* Run Button */}
          <button
            onClick={() => onRunInvestigation(selectedKey, evaluations)}
            disabled={loading}
            className="w-full py-3 px-5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase tracking-wider flex items-center justify-center space-x-2.5 shadow-[0_0_20px_rgba(84,214,232,0.3)] transition-all disabled:opacity-50 disabled:cursor-not-allowed group active:scale-[0.99]"
          >
            {loading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                <span>Evaluating Deterministic Uncertainty Envelope…</span>
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-slate-950 group-hover:scale-110 transition-transform" />
                <span>Run Bounded Investigation</span>
              </>
            )}
          </button>
        </div>

        {/* Right Column: Gate Policy Card */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-3">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-mono font-bold tracking-wider text-white uppercase">
                Deterministic Gate Policy
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Zero-drift deterministic boundary rules governing candidate network intervention acceptance:
            </p>

            <div className="space-y-3">
              <div className="p-3 rounded-xl bg-emerald-950/20 border border-emerald-800/40">
                <div className="flex items-center space-x-2 text-xs font-bold text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#34d399]" />
                  <span>ACCEPT</span>
                </div>
                <p className="text-[11px] text-slate-300 mt-1">
                  All evaluated variations stay within latency SLO and satisfy stability threshold.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-amber-950/20 border border-amber-800/40">
                <div className="flex items-center space-x-2 text-xs font-bold text-amber-400">
                  <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_6px_#fbbf24]" />
                  <span>GATHER_EVIDENCE</span>
                </div>
                <p className="text-[11px] text-slate-300 mt-1">
                  Nominal latency passes SLO, but uncertainty variations breach bounds. Requires live telemetry.
                </p>
              </div>

              <div className="p-3 rounded-xl bg-rose-950/20 border border-rose-800/40">
                <div className="flex items-center space-x-2 text-xs font-bold text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-400 shadow-[0_0_6px_#f43f5e]" />
                  <span>ABSTAIN</span>
                </div>
                <p className="text-[11px] text-slate-300 mt-1">
                  Candidate cannot be justified within configured uncertainty envelope; fail closed.
                </p>
              </div>
            </div>
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono text-slate-400">
            <span>Stability Threshold:</span>
            <span className="text-cyan-400 font-bold">{(currentScenario.stability_threshold * 100).toFixed(0)}% Minimum</span>
          </div>
        </div>
      </div>

      {/* Decision Assessment Hero Banner */}
      <div className={`p-6 rounded-2xl border ${decisionBorder} ${decisionBg} ${decisionGlow} transition-all`}>
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-3">
              <span className="text-xs font-mono font-bold tracking-widest text-slate-400 uppercase">
                FIDELITY GATE OUTCOME · RUN #{runId}
              </span>
              <span className={`text-[11px] font-mono font-semibold px-2.5 py-0.5 rounded-full border ${decisionBorder} ${decisionColor}`}>
                {decision.replace('_', ' ')}
              </span>
            </div>
            <h2 className={`text-2xl md:text-3xl font-black tracking-tight ${decisionColor}`}>
              {decision.replace('_', ' ')}
            </h2>
            <p className="text-sm text-slate-200/90 max-w-3xl leading-relaxed">
              {reason}
            </p>
          </div>

          <div className="flex-shrink-0 flex items-center space-x-3">
            <div className="text-right font-mono">
              <span className="text-[10px] text-slate-400 uppercase block">Stability Confidence</span>
              <span className="text-xl font-extrabold text-white">
                {report ? (report.stability_score * 100).toFixed(1) : '86.7'}%
              </span>
            </div>
            <div className={`w-12 h-12 rounded-2xl border ${decisionBorder} ${decisionBg} flex items-center justify-center`}>
              {isAccept ? (
                <ShieldCheck className="w-6 h-6 text-emerald-400" />
              ) : isEvidence ? (
                <AlertTriangle className="w-6 h-6 text-amber-400" />
              ) : (
                <XCircle className="w-6 h-6 text-rose-400" />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 4 Core Metrics Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Nominal Latency */}
        <div className="glass-card p-4 rounded-xl">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">Nominal Latency</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-black text-white font-mono">
              {report ? report.nominal_latency_ms.toFixed(1) : '18.0'}
              <span className="text-sm font-normal text-slate-400 ml-1">ms</span>
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
              Base
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block font-mono">Normal twin baseline</span>
        </div>

        {/* Worst Sweep Latency */}
        <div className="glass-card p-4 rounded-xl">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">Worst Sweep Latency</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-black text-amber-300 font-mono">
              {report ? report.worst_latency_ms.toFixed(1) : '49.6'}
              <span className="text-sm font-normal text-slate-400 ml-1">ms</span>
            </span>
            <span className={`text-[11px] font-mono font-bold px-2 py-0.5 rounded ${deltaLatency > 0 ? 'bg-amber-950 text-amber-300 border border-amber-800' : 'bg-emerald-950 text-emerald-300'}`}>
              +{deltaLatency.toFixed(1)} ms
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block font-mono">Peak sweep deviation</span>
        </div>

        {/* Peak Utilization */}
        <div className="glass-card p-4 rounded-xl">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">Peak Utilization</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-black text-white font-mono">
              {report ? (report.peak_utilization * 100).toFixed(1) : '87.4'}
              <span className="text-sm font-normal text-slate-400 ml-1">%</span>
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800">
              Capacity
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block font-mono">Max buffer queue load</span>
        </div>

        {/* Decision Stability */}
        <div className="glass-card p-4 rounded-xl">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-wider block">Decision Stability</span>
          <div className="mt-2 flex items-baseline justify-between">
            <span className="text-2xl font-black text-emerald-400 font-mono">
              {report ? (report.stability_score * 100).toFixed(1) : '86.7'}
              <span className="text-sm font-normal text-slate-400 ml-1">%</span>
            </span>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700">
              {report ? report.violations : 2} Violations
            </span>
          </div>
          <span className="text-[11px] text-slate-500 mt-1 block font-mono">Threshold: {(currentScenario.stability_threshold * 100).toFixed(0)}%</span>
        </div>
      </div>

      {/* Visualizers Row: 3D Twin & Uncertainty Sweep */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center space-x-2">
              <Zap className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
                Twin-System 3D Centerpiece
              </h3>
            </div>
            
            {/* View Mode Toggle: Spline 3D vs Fleet Topology */}
            <div className="flex items-center space-x-1 bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-[10px] font-mono">
              <button
                onClick={() => setTwinViewMode('spline_centerpiece')}
                className={`px-2 py-1 rounded-md transition-all ${
                  twinViewMode === 'spline_centerpiece'
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                Spline 3D Twin (2 Nodes & Signal)
              </button>
              <button
                onClick={() => setTwinViewMode('fleet_topology')}
                className={`px-2 py-1 rounded-md transition-all ${
                  twinViewMode === 'fleet_topology'
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold'
                    : 'text-slate-400 hover:text-white'
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
              <BarChart3 className="w-4 h-4 text-cyan-400" />
              <h3 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
                Uncertainty Envelope & SLO Boundary
              </h3>
            </div>
            <span className="text-[10px] font-mono text-slate-400">
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
    </div>
  );
}
