'use client';

import React, { useState } from 'react';
import {
  Layers,
  Clock,
  LineChart,
  ShieldCheck,
  ArrowUpRight,
  CheckCircle2,
  AlertTriangle,
  Play,
  Terminal,
} from 'lucide-react';
import { playTick } from '@/lib/sound';

interface ProductPreviewProps {
  soundEnabled: boolean;
  onOpenWorkspace: (tab?: string) => void;
}

export function ProductPreview({ soundEnabled, onOpenWorkspace }: ProductPreviewProps) {
  const [activeTab, setActiveTab] = useState<'topology' | 'trace' | 'uncertainty' | 'gate'>('topology');

  const tabs = [
    { id: 'topology', label: '1. Network Topology', icon: Layers, targetTab: 'decision' },
    { id: 'trace', label: '2. Execution Trace', icon: Clock, targetTab: 'trace' },
    { id: 'uncertainty', label: '3. Uncertainty Envelope', icon: LineChart, targetTab: 'monitoring' },
    { id: 'gate', label: '4. Deterministic Gate', icon: ShieldCheck, targetTab: 'decision' },
  ];

  const handleTabChange = (tabId: 'topology' | 'trace' | 'uncertainty' | 'gate') => {
    playTick(soundEnabled);
    setActiveTab(tabId);
  };

  return (
    <section id="previews" className="py-16 md:py-20 border-t border-hairline dark:border-hairline-dark">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="max-w-3xl mb-12">
          <span className="t-eyebrow text-cobalt block mb-3">
            Product Previews
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-ink dark:text-ink-dark leading-tight mb-4">
            Engineered for high-stakes operational certainty.
          </h2>
          <p className="text-base text-muted-fg dark:text-muted-dark leading-relaxed">
            Every screen in the engineering workspace shares the same minimal typography, real digital-twin queueing algorithms, and fail-closed deterministic semantics.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex flex-wrap gap-2 mb-8 border-b border-hairline dark:border-hairline-dark pb-4">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isSelected = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => handleTabChange(tab.id as any)}
                className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-xs font-semibold transition-all ${
                  isSelected
                    ? 'bg-cobalt text-white shadow-fine'
                    : 'bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Interactive Preview Surface */}
        <div className="editorial-card p-6 md:p-8 relative">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-hairline dark:border-hairline-dark gap-3 mb-6">
            <div className="flex items-center space-x-2 font-mono text-xs">
              <span className="w-2 h-2 rounded-full bg-emerald-verdict animate-pulse" />
              <span className="text-muted-fg dark:text-muted-dark">LIVE WORKSPACE PREVIEW:</span>
              <span className="text-ink dark:text-ink-dark font-bold uppercase">{activeTab}</span>
            </div>

            <button
              onClick={() => {
                playTick(soundEnabled);
                const current = tabs.find((t) => t.id === activeTab);
                onOpenWorkspace(current?.targetTab || 'decision');
              }}
              className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark hover:border-cobalt/50 text-xs font-semibold text-cobalt transition-colors shadow-fine"
            >
              <span>Launch this view in workspace</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          {/* Tab 1: Topology */}
          {activeTab === 'topology' && (
            <div className="space-y-6 animate-in fade-in duration-200">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark">
                  <span className="t-label block">Candidate Path</span>
                  <span className="text-sm font-bold text-ink dark:text-ink-dark mt-1 block">Frankfurt &rarr; Milan &rarr; Zurich</span>
                  <span className="text-xs text-cobalt font-mono mt-0.5 block">18.4 ms nominal latency</span>
                </div>
                <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark">
                  <span className="t-label block">SLO Constraint</span>
                  <span className="text-sm font-bold text-ink dark:text-ink-dark mt-1 block">&le; 45.0 ms</span>
                  <span className="text-xs text-muted-fg dark:text-muted-dark mt-0.5 block">Enforced contract bound</span>
                </div>
                <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark">
                  <span className="t-label block">Counterexample Breach</span>
                  <span className="text-sm font-bold text-amber-warning mt-1 block">48.6 ms (+19% Burst)</span>
                  <span className="text-xs text-rose-abstain font-mono mt-0.5 block">3.6 ms beyond SLA limit</span>
                </div>
              </div>

              <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark font-mono text-xs space-y-2">
                <div className="flex justify-between text-muted-fg dark:text-muted-dark">
                  <span>Hop 1: Edge Ingress (Frankfurt)</span>
                  <span className="text-ink dark:text-ink-dark font-semibold">Utilization: 76.0% (OK)</span>
                </div>
                <div className="flex justify-between text-muted-fg dark:text-muted-dark">
                  <span>Hop 2: Spine Alpha (Core Transit)</span>
                  <span className="text-amber-warning font-semibold">Utilization: 89.4% [Near non-linear knee]</span>
                </div>
                <div className="flex justify-between text-muted-fg dark:text-muted-dark">
                  <span>Hop 3: Cloud Egress (Zurich)</span>
                  <span className="text-ink dark:text-ink-dark font-semibold">Utilization: 36.8% (OK)</span>
                </div>
              </div>
            </div>
          )}

          {/* Tab 2: Trace */}
          {activeTab === 'trace' && (
            <div className="space-y-3 font-mono text-xs animate-in fade-in duration-200">
              {[
                {
                  step: '01',
                  time: '12:00:00.120',
                  action: 'INGEST_SCENARIO',
                  status: 'SUCCESS',
                  detail: 'Loaded WAN-042: 1,000 Mbps capacity, 760 Mbps offered load, SLO: 45 ms.',
                },
                {
                  step: '02',
                  time: '12:00:00.285',
                  action: 'ADVERSARIAL_SWEEP',
                  status: 'WARNING',
                  detail: 'Convex parameter perturbation: 25 samples evaluated across load factor [0.95...1.15].',
                },
                {
                  step: '03',
                  time: '12:00:00.410',
                  action: 'COUNTEREXAMPLE_EXPOSED',
                  status: 'WARNING',
                  detail: 'Worst-case point located: sample #25 reaches 48.6 ms, breaching 45 ms threshold.',
                },
                {
                  step: '04',
                  time: '12:00:00.640',
                  action: 'DISPATCH_PROBES',
                  status: 'SUCCESS',
                  detail: 'Active synthetic probing deployed to Spine Alpha. Queue depth confirmed at 42 pkts.',
                },
                {
                  step: '05',
                  time: '12:00:00.820',
                  action: 'DETERMINISTIC_GATE',
                  status: 'VERDICT',
                  detail: 'Verdict: GATHER_EVIDENCE. Fail closed. Automated routing shift withheld.',
                },
              ].map((ev) => (
                <div
                  key={ev.step}
                  className="p-3 rounded-lg bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark flex flex-col sm:flex-row sm:items-center justify-between gap-2"
                >
                  <div className="flex items-center space-x-3">
                    <span className="text-muted-fg dark:text-muted-dark font-bold">{ev.step}</span>
                    <span className="text-muted-fg dark:text-muted-dark text-[11px]">{ev.time}</span>
                    <span className="font-bold text-cobalt">{ev.action}</span>
                  </div>
                  <div className="text-muted-fg dark:text-muted-dark text-[11px] truncate max-w-md">
                    {ev.detail}
                  </div>
                  <span
                    className={`text-[11px] font-bold px-2 py-0.5 rounded self-start sm:self-auto ${
                      ev.status === 'WARNING'
                        ? 'bg-amber-warning-subtle dark:bg-amber-warning-dark text-amber-warning'
                        : ev.status === 'VERDICT'
                        ? 'bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt'
                        : 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark text-emerald-verdict'
                    }`}
                  >
                    {ev.status}
                  </span>
                </div>
              ))}
            </div>
          )}

          {/* Tab 3: Uncertainty Envelope */}
          {activeTab === 'uncertainty' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark">
                <div className="flex justify-between items-center mb-4 text-xs font-mono">
                  <span className="text-muted-fg dark:text-muted-dark">SWEEP SAMPLES (25 SAMPLES)</span>
                  <span className="text-rose-abstain font-bold">SLO THRESHOLD: 45.0 ms</span>
                </div>

                {/* Simplified visual bar chart of sample latency distribution */}
                <div className="h-32 flex items-end gap-1.5 pt-4">
                  {[
                    18.0, 18.5, 19.2, 20.1, 21.0, 22.4, 23.8, 25.2, 27.0, 29.1, 31.5, 33.8, 36.2, 38.5, 40.8,
                    42.0, 43.1, 44.0, 44.8, 45.4, 46.2, 47.0, 47.8, 48.2, 48.6,
                  ].map((val, idx) => {
                    const isBreach = val > 45.0;
                    const heightPercent = Math.min((val / 55.0) * 100, 100);
                    return (
                      <div
                        key={idx}
                        className="flex-1 flex flex-col items-center justify-end h-full group relative cursor-pointer"
                      >
                        <div
                          style={{ height: `${heightPercent}%` }}
                          className={`w-full rounded-t transition-all ${
                            isBreach ? 'bg-amber-warning' : 'bg-cobalt/80 hover:bg-cobalt'
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between text-[11px] font-mono text-muted-fg dark:text-muted-dark mt-2 border-t border-hairline dark:border-hairline-dark pt-1">
                  <span>Sample #01 (Nominal 18.0 ms)</span>
                  <span>Sample #19 (Knee 44.8 ms)</span>
                  <span className="text-amber-warning font-bold">Sample #25 (Worst 48.6 ms)</span>
                </div>
              </div>
            </div>
          )}

          {/* Tab 4: Deterministic Gate */}
          {activeTab === 'gate' && (
            <div className="space-y-4 animate-in fade-in duration-200">
              <div className="p-6 rounded-xl border border-amber-warning/50 bg-amber-warning-subtle/50 dark:bg-amber-warning-dark/20 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-lg bg-amber-warning/20 flex items-center justify-center text-amber-warning">
                      <ShieldCheck className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-base font-bold text-ink dark:text-ink-dark">
                        Deterministic Gate Verdict: GATHER_EVIDENCE
                      </h4>
                      <p className="text-xs text-muted-fg dark:text-muted-dark">
                        Rule: Nominal passes (&le;45 ms), but 6 of 25 uncertainty samples violate bound.
                      </p>
                    </div>
                  </div>

                  <span className="font-mono text-xs font-bold px-3 py-1 rounded bg-amber-warning text-white shadow-fine">
                    FAIL-CLOSED
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2 text-xs font-mono">
                  <div className="p-3 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Nominal Delay</span>
                    <span className="font-bold text-ink dark:text-ink-dark">18.0 ms</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Worst Latency</span>
                    <span className="font-bold text-rose-abstain">48.6 ms</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Stability Score</span>
                    <span className="font-bold text-amber-warning">84.0%</span>
                  </div>
                  <div className="p-3 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Violations</span>
                    <span className="font-bold text-ink dark:text-ink-dark">6 / 25 samples</span>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
