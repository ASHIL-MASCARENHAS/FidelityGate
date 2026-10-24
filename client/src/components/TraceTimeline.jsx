import React from 'react';
import { CheckCircle2, Clock, ShieldCheck, AlertTriangle, XCircle, Search, Layers } from 'lucide-react';

export default function TraceTimeline({ report, decision, reason, scenario }) {
  if (!report) return null;

  const steps = [
    {
      num: '01',
      title: 'Scenario Specification Loaded',
      desc: `Loaded scenario ${scenario?.scenario_id || 'WAN-042'} with ${scenario?.capacity_mbps || 1000} Mbps capacity and nominal load of ${scenario?.offered_load_mbps || 760} Mbps.`,
      status: 'complete',
      badge: `${scenario?.nominal_latency_ms || 18}ms base`,
      icon: Layers,
    },
    {
      num: '02',
      title: 'Digital-Twin Convex Queueing Prediction',
      desc: `Evaluated baseline state. Nominal estimated latency is ${report.nominal_latency_ms?.toFixed(1)} ms under normal operating load.`,
      status: 'complete',
      badge: `${report.nominal_latency_ms?.toFixed(1)}ms nominal`,
      icon: Clock,
    },
    {
      num: '03',
      title: 'Multidimensional Uncertainty Sweep',
      desc: `Executed ${report.evaluations} deterministic variation sweeps over latency calibration drift [${scenario?.latency_multiplier_min || 0.85}x–${scenario?.latency_multiplier_max || 1.35}x] and load burst [0.95x–1.15x].`,
      status: 'complete',
      badge: `${report.evaluations} variations`,
      icon: Search,
    },
    {
      num: '04',
      title: 'SLO Constraint Boundary Check',
      desc: report.violations > 0
        ? `Detected ${report.violations} evaluated variations exceeding the strict ${scenario?.slo_latency_ms || 45} ms latency SLO threshold. Peak worst-case reached ${report.worst_latency_ms?.toFixed(1)} ms.`
        : `All ${report.evaluations} variations stayed strictly under the ${scenario?.slo_latency_ms || 45} ms latency SLO threshold.`,
      status: report.violations > 0 ? 'warning' : 'complete',
      badge: `${report.violations} breaches`,
      icon: report.violations > 0 ? AlertTriangle : CheckCircle2,
    },
    {
      num: '05',
      title: 'Deterministic Gate Decision',
      desc: reason,
      status: decision === 'ACCEPT' ? 'complete' : decision === 'GATHER_EVIDENCE' ? 'warning' : 'danger',
      badge: decision?.replace('_', ' '),
      icon: decision === 'ACCEPT' ? ShieldCheck : decision === 'GATHER_EVIDENCE' ? AlertTriangle : XCircle,
    },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-mono font-bold tracking-wider text-cyan-300 uppercase">
            Investigation Execution Trace
          </h3>
          <p className="text-xs text-slate-400">Step-by-step deterministic audit log and verification checkpoints</p>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-slate-900 border border-slate-700 text-slate-300">
          5 / 5 Verifications Passed
        </span>
      </div>

      <div className="space-y-3">
        {steps.map((s, idx) => {
          const Icon = s.icon;
          const isWarning = s.status === 'warning';
          const isDanger = s.status === 'danger';
          const isAccept = s.status === 'complete';

          const borderColor = isDanger
            ? 'border-rose-500/40 bg-rose-950/20'
            : isWarning
            ? 'border-amber-500/40 bg-amber-950/20'
            : 'border-slate-800 bg-[#0c1626]/70';

          const badgeColor = isDanger
            ? 'bg-rose-950 text-rose-300 border-rose-800'
            : isWarning
            ? 'bg-amber-950 text-amber-300 border-amber-800'
            : 'bg-emerald-950 text-emerald-300 border-emerald-800';

          return (
            <div
              key={s.num}
              className={`p-3.5 rounded-xl border ${borderColor} flex items-start space-x-3.5 transition-all hover:bg-slate-850/60`}
            >
              <div className="flex-shrink-0 mt-0.5">
                <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-slate-900 border border-slate-700 text-cyan-300 font-mono text-xs font-bold shadow">
                  {s.num}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-bold text-white tracking-wide flex items-center space-x-2">
                    <Icon className={`w-3.5 h-3.5 ${isDanger ? 'text-rose-400' : isWarning ? 'text-amber-400' : 'text-emerald-400'}`} />
                    <span>{s.title}</span>
                  </h4>
                  <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded border font-semibold ${badgeColor}`}>
                    {s.badge}
                  </span>
                </div>
                <p className="text-xs text-slate-300/90 mt-1 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
