import React, { useState } from 'react';
import { Clock, Play, Layers, ShieldCheck, AlertTriangle, XCircle, Search, Radio, Cpu, ChevronRight, FileText, Activity } from 'lucide-react';

export default function ExecutionTraceView({
  executionTrace = [],
  counterexample = null,
  diagnosticObservation = null,
  gateVerdict = null,
  scenario = null,
  onRunAdaptive,
  loading = false
}) {
  const [selectedSpan, setSelectedSpan] = useState(null);

  // Default mock trace if no adaptive run has occurred yet
  const defaultTrace = [
    {
      step_num: 1,
      phase: "AGENT_INVESTIGATION",
      actor: "LLM_Agent",
      timestamp_offset_ms: 12,
      duration_ms: 26,
      action: "Select candidate network route and evaluate nominal digital-twin prediction",
      status: "PASS",
      details: {
        route_id: `R-${scenario?.scenario_id || 'WAN-042'}`,
        nominal_latency_ms: scenario?.nominal_latency_ms || 18.0,
        slo_target_ms: scenario?.slo_latency_ms || 45.0,
        nominal_compliant: true
      }
    },
    {
      step_num: 2,
      phase: "COUNTEREXAMPLE_SEARCH",
      actor: "Counterexample_Engine",
      timestamp_offset_ms: 38,
      duration_ms: 16,
      action: "Search uncertainty envelope for minimal violating perturbation",
      status: "WARNING",
      details: {
        is_fragile: true,
        violating_latency_ms: 45.5,
        critical_parameter: "traffic_load_burst",
        perturbation_factor: 1.198,
        explanation: "A plausible 19.8% traffic burst causes buffer queueing delay (45.5 ms) to breach the 45.0 ms SLO."
      }
    },
    {
      step_num: 3,
      phase: "TARGETED_DIAGNOSTIC_CHOICE",
      actor: "LLM_Agent",
      timestamp_offset_ms: 54,
      duration_ms: 24,
      action: "Agent selects targeted diagnostic tool 'SNMP v3 Interface Queue Telemetry' based on counterexample sensitivity",
      status: "ACTIVE",
      details: {
        selected_tool_id: "snmp_interface_poll",
        tool_name: "SNMP v3 Interface Queue Telemetry",
        target_parameter: "traffic_load_burst",
        declared_error_bound: "±15.0 Mbps",
        cost_usd: 0.002,
        reason: "Collapses uncertainty around traffic_load_burst identified in step 2"
      }
    },
    {
      step_num: 4,
      phase: "MEASUREMENT_ACQUISITION",
      actor: "Diagnostic_Probe",
      timestamp_offset_ms: 78,
      duration_ms: 17,
      action: "Execute physical diagnostic probe and capture measurement observation with declared error",
      status: "MEASURED",
      details: {
        measured_value: 798.0,
        unit: "Mbps",
        declared_error_bound: 15.0,
        confidence_interval: [783.0, 813.0],
        observation_summary: "Polled interface traffic load at 798.0 Mbps (declared error ±15.0 Mbps, 95% CI: [783.0, 813.0 Mbps])."
      }
    },
    {
      step_num: 5,
      phase: "GATE_RE_EVALUATION",
      actor: "Deterministic_Gate",
      timestamp_offset_ms: 95,
      duration_ms: 12,
      action: "Independent gate evaluation under posterior uncertainty",
      status: "ACCEPT",
      details: {
        final_decision: "ACCEPT",
        posterior_latency_ms: 28.68,
        final_reason: "Diagnostic measurement (798.0 Mbps) confirms actual operating state (28.7 ms) satisfies 45.0 ms SLO within measurement error bounds."
      }
    }
  ];

  const traceEvents = executionTrace.length > 0 ? executionTrace : defaultTrace;

  const totalDuration = traceEvents.reduce((acc, ev) => Math.max(acc, (ev.timestamp_offset_ms || 0) + (ev.duration_ms || 15)), 0);

  return (
    <div className="space-y-6">
      {/* Header with AgentOps KPI Banner */}
      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div>
            <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">
              <Clock className="w-4 h-4" />
              <span>AgentOps Execution Trace</span>
            </div>
            <h2 className="text-xl font-extrabold text-white tracking-tight">Adaptive Counterexample-Guided Trace</h2>
            <p className="text-xs text-slate-400">
              Chronological span execution showing candidate investigation, counterexample exposure, targeted diagnostic probing, and final gate verdict.
            </p>
          </div>

          <button
            onClick={onRunAdaptive}
            disabled={loading}
            className="py-2.5 px-5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs uppercase tracking-wider flex items-center space-x-2 shadow-[0_0_15px_rgba(84,214,232,0.3)] transition-all disabled:opacity-50"
          >
            <Play className={`w-3.5 h-3.5 fill-slate-950 ${loading ? 'animate-spin' : ''}`} />
            <span>{loading ? 'Executing Agent Loop…' : 'Run Adaptive Trace'}</span>
          </button>
        </div>

        {/* KPI Telemetry Header (Matching Page 9 in Strategy Brief) */}
        <div className="grid grid-cols-2 md:grid-cols-6 gap-3 p-4 rounded-xl bg-[#09111c] border border-slate-800 font-mono text-xs">
          <div>
            <span className="text-slate-500 text-[10px] block uppercase">Duration</span>
            <span className="text-lg font-black text-white">{totalDuration} ms</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] block uppercase">Trace Spans</span>
            <span className="text-lg font-black text-cyan-300">{traceEvents.length}</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] block uppercase">LLM Decisions</span>
            <span className="text-lg font-black text-white">2</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] block uppercase">Tool Calls</span>
            <span className="text-lg font-black text-emerald-400">1</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] block uppercase">SLO Failures</span>
            <span className="text-lg font-black text-emerald-400">0</span>
          </div>
          <div>
            <span className="text-slate-500 text-[10px] block uppercase">Audit Cost</span>
            <span className="text-lg font-black text-amber-300">$0.002</span>
          </div>
        </div>
      </div>

      {/* Flamegraph / Span Timeline */}
      <div className="glass-panel p-6 rounded-2xl space-y-4">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-mono font-bold text-white uppercase tracking-wider">
              Chronological Span Waterfall
            </h3>
          </div>
          <div className="flex items-center space-x-3 text-[11px] font-mono text-slate-400">
            <span>0 ms</span>
            <span>25 ms</span>
            <span>50 ms</span>
            <span>75 ms</span>
            <span>{totalDuration} ms</span>
          </div>
        </div>

        {/* Spans List */}
        <div className="space-y-3 font-mono">
          {traceEvents.map((ev, idx) => {
            const isWarning = ev.status === 'WARNING';
            const isAccept = ev.status === 'ACCEPT' || ev.status === 'PASS';
            const isMeasured = ev.status === 'MEASURED' || ev.status === 'ACTIVE';

            const barColor = isWarning
              ? 'bg-amber-500'
              : isAccept
              ? 'bg-emerald-400'
              : 'bg-cyan-400';

            const leftPct = Math.min(85, ((ev.timestamp_offset_ms || (idx * 20)) / (totalDuration || 100)) * 85);
            const widthPct = Math.max(12, ((ev.duration_ms || 18) / (totalDuration || 100)) * 60);

            return (
              <div
                key={ev.step_num || idx}
                onClick={() => setSelectedSpan(ev)}
                className="p-3 rounded-xl bg-slate-900/70 border border-slate-800 hover:border-cyan-500/60 hover:bg-slate-850/80 transition-all cursor-pointer group"
              >
                <div className="flex items-center justify-between text-xs mb-1.5">
                  <div className="flex items-center space-x-2 font-bold text-white">
                    <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-300 text-[10px]">
                      0{ev.step_num}
                    </span>
                    <span className="text-slate-300 font-sans">{ev.action}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-[11px]">
                    <span className="text-slate-400">{ev.actor}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isWarning
                          ? 'bg-amber-950 text-amber-300 border border-amber-800'
                          : isAccept
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                      }`}
                    >
                      {ev.status}
                    </span>
                  </div>
                </div>

                {/* Waterfall Bar */}
                <div className="w-full h-3 rounded-full bg-slate-950 overflow-hidden relative">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${barColor}`}
                    style={{ marginLeft: `${leftPct}%`, width: `${widthPct}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Detail Drawer Modal for Selected Span */}
      {selectedSpan && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0b1424] border border-cyan-800/80 rounded-2xl max-w-xl w-full p-6 shadow-2xl animate-in zoom-in-95 duration-150">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
              <div>
                <span className="text-xs font-mono text-cyan-400 font-bold uppercase">
                  Span Inspector · Step #{selectedSpan.step_num}
                </span>
                <h4 className="text-base font-bold text-white">{selectedSpan.phase}</h4>
              </div>
              <button
                onClick={() => setSelectedSpan(null)}
                className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 text-slate-400 hover:text-white flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            <p className="text-xs text-slate-300 mb-4 leading-relaxed">{selectedSpan.action}</p>

            <div className="p-3 rounded-xl bg-slate-900/90 border border-slate-800 mb-4">
              <span className="text-[10px] font-mono text-slate-400 uppercase block mb-1">Observation & Parameters</span>
              <pre className="text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-48">
                {JSON.stringify(selectedSpan.details, null, 2)}
              </pre>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setSelectedSpan(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold font-sans"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
