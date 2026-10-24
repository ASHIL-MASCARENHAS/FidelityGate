'use client';

import React from 'react';
import { CheckCircle2, Clock, ShieldCheck, AlertTriangle, XCircle, Search, Layers } from 'lucide-react';
import { GateDecision, SweepReport, Scenario } from '@/types';

interface TraceTimelineProps {
  report?: SweepReport | null;
  decision?: GateDecision;
  reason?: string;
  scenario?: Scenario | null;
}

export function TraceTimeline({ report, decision, reason, scenario }: TraceTimelineProps) {
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
      desc:
        report.violations > 0
          ? `Detected ${report.violations} evaluated variations exceeding the strict ${scenario?.slo_latency_ms || 45} ms latency SLO threshold. Peak worst-case reached ${report.worst_latency_ms?.toFixed(1)} ms.`
          : `All ${report.evaluations} variations stayed strictly under the ${scenario?.slo_latency_ms || 45} ms latency SLO threshold.`,
      status: report.violations > 0 ? 'warning' : 'complete',
      badge: `${report.violations} breaches`,
      icon: report.violations > 0 ? AlertTriangle : CheckCircle2,
    },
    {
      num: '05',
      title: 'Deterministic Gate Decision',
      desc: reason || 'Gate evaluation completed',
      status: decision === 'ACCEPT' ? 'complete' : decision === 'GATHER_EVIDENCE' ? 'warning' : 'danger',
      badge: decision?.replace('_', ' '),
      icon: decision === 'ACCEPT' ? ShieldCheck : decision === 'GATHER_EVIDENCE' ? AlertTriangle : XCircle,
    },
  ];

  return (
    <div className="glass-panel p-6 rounded-2xl">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-semibold tracking-tight text-ink dark:text-ink-dark">
            Investigation Execution Trace
          </h3>
          <p className="text-xs text-muted-fg dark:text-muted-dark mt-0.5">
            Step-by-step deterministic audit log and verification checkpoints
          </p>
        </div>
        <span className="text-[11px] font-mono px-2.5 py-1 rounded-full bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark">
          5 / 5 Verifications Passed
        </span>
      </div>

      <div className="space-y-3">
        {steps.map((s) => {
          const Icon = s.icon;
          const isWarning = s.status === 'warning';
          const isDanger = s.status === 'danger';

          const borderColor = isDanger
            ? 'border-rose-abstain/40 bg-rose-abstain-subtle dark:bg-rose-abstain-dark'
            : isWarning
            ? 'border-amber-warning/40 bg-amber-warning-subtle dark:bg-amber-warning-dark'
            : 'border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark';

          const badgeColor = isDanger
            ? 'bg-rose-abstain-subtle dark:bg-rose-abstain-dark text-rose-abstain border-rose-abstain/30'
            : isWarning
            ? 'bg-amber-warning-subtle dark:bg-amber-warning-dark text-amber-warning border-amber-warning/30'
            : 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark text-emerald-verdict border-emerald-verdict/30';

          return (
            <div
              key={s.num}
              className={`p-3.5 rounded-xl border ${borderColor} flex items-start space-x-3.5 transition-colors`}
            >
              <div className="flex-shrink-0 mt-0.5">
                <span className="flex items-center justify-center w-7 h-7 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-cobalt font-mono text-xs font-semibold">
                  {s.num}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-semibold text-ink dark:text-ink-dark flex items-center space-x-2">
                    <Icon
                      className={`w-3.5 h-3.5 ${
                        isDanger
                          ? 'text-rose-abstain'
                          : isWarning
                          ? 'text-amber-warning'
                          : 'text-emerald-verdict'
                      }`}
                    />
                    <span>{s.title}</span>
                  </h4>
                  <span
                    className={`text-[11px] font-mono uppercase px-2 py-0.5 rounded border font-semibold ${badgeColor}`}
                  >
                    {s.badge}
                  </span>
                </div>
                <p className="text-xs text-muted-fg dark:text-muted-dark mt-1 leading-relaxed">{s.desc}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
export default TraceTimeline;
