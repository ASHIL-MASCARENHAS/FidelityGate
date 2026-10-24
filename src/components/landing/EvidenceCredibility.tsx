'use client';

import React from 'react';
import {
  ShieldAlert,
  SlidersHorizontal,
  GitBranch,
  CheckCircle,
  BarChart2,
  Database,
  ArrowUpRight,
} from 'lucide-react';
import { playTick } from '@/lib/sound';

interface EvidenceCredibilityProps {
  soundEnabled: boolean;
  onOpenWorkspace: () => void;
}

export function EvidenceCredibility({ soundEnabled, onOpenWorkspace }: EvidenceCredibilityProps) {
  const pillars = [
    {
      id: 'counterexample',
      title: 'Counterexample Evidence',
      badge: 'Convex Non-Linearity',
      icon: ShieldAlert,
      tagline: 'Adversarial uncertainty exploration',
      description:
        'Standard systems evaluate only nominal average-case states. FidelityGate deliberately solves for the worst-case parameter combination across load, queuing delay, and packet burst envelopes.',
      evidenceMetric: '48.6 ms counterexample',
      evidenceSub: 'Discovered at +19% traffic load burst',
      formula: 'T(ρ) = T_0 / (1 - ρ) + q_depth / C',
    },
    {
      id: 'uncertainty',
      title: 'Measurement Uncertainty',
      badge: 'Stochastic Intervals',
      icon: SlidersHorizontal,
      tagline: 'Telemetry noise & jitter modeling',
      description:
        'Telemetry is never exact. Our Bayesian and bounded error models incorporate probe timestamp jitter, packet loss variance, and collector latency so decisions are never based on false precision.',
      evidenceMetric: '± 2.4 ms noise bound',
      evidenceSub: '95% empirical confidence intervals',
      formula: 'Confidence Envelope = μ ± z · (σ / √n)',
    },
    {
      id: 'provenance',
      title: 'Diagnostic Provenance',
      badge: 'Audit Lineage',
      icon: GitBranch,
      tagline: 'Traceable diagnostic execution graph',
      description:
        'Every routing recommendation and gate outcome is bound to an unbroken execution trace. Engineers can inspect exactly which agent actions, eBPF probes, and link telemetry supported the verdict.',
      evidenceMetric: '5 Trace Events / Run',
      evidenceSub: 'Deterministic timestamped receipts',
      formula: 'Hash-linked execution trace DAG',
    },
    {
      id: 'gate',
      title: 'Deterministic Gate Outcomes',
      badge: 'Zero Drift',
      icon: CheckCircle,
      tagline: 'Mathematical fail-closed state machine',
      description:
        'The decision gate contains no non-deterministic heuristic shortcuts. Decisions fail closed into ACCEPT, GATHER_EVIDENCE, or ABSTAIN with mathematically verifiable stability scores.',
      evidenceMetric: 'Zero False Accepts',
      evidenceSub: 'Enforced safety invariant',
      formula: 'Decision = f(SLO, Stability, Uncertainty)',
    },
    {
      id: 'baseline',
      title: 'Comparison with Baselines',
      badge: 'Empirical Rigor',
      icon: BarChart2,
      tagline: 'Defensible multi-scenario validation',
      description:
        'Continuously benchmarked against industry standard nominal-only heuristics, static +25% safety margins, and exhaustive non-adaptive sweeps across real topologies.',
      evidenceMetric: '100% Safety Guarantee',
      evidenceSub: '40% fewer probes than brute force',
      formula: '4-Way Baseline Comparison Matrix',
    },
    {
      id: 'history',
      title: 'Reproducible Execution History',
      badge: 'SQLite Persistence',
      icon: Database,
      tagline: 'Persistent local audit trail',
      description:
        'All scenario parameters, sampled points, gate verdicts, and sensitivity analyses are stored in local SQLite storage, enabling forensic inspection and audit compliance.',
      evidenceMetric: 'Persistent Runs',
      evidenceSub: 'Local SQLite audit database',
      formula: 'schema: run_id, scenario, gate, points',
    },
  ];

  return (
    <section id="evidence" className="py-16 md:py-20 border-t border-hairline dark:border-hairline-dark">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-16 gap-6">
          <div className="max-w-3xl">
            <span className="t-eyebrow text-cobalt block mb-3">
              Engineering Defensibility
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-ink dark:text-ink-dark leading-tight mb-4">
              What makes a network decision defensible?
            </h2>
            <p className="text-base text-muted-fg dark:text-muted-dark leading-relaxed">
              When millions of dollars in enterprise SLAs rely on automated traffic interventions, decisions cannot rest on probabilistic guesses or superficial dashboards. Every recommendation requires mathematical proof.
            </p>
          </div>

          <button
            onClick={() => {
              playTick(soundEnabled);
              onOpenWorkspace();
            }}
            className="self-start md:self-end inline-flex items-center space-x-2 px-4 py-2.5 rounded-lg border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark text-xs font-semibold text-ink dark:text-ink-dark hover:border-cobalt/50 transition-colors shadow-fine"
          >
            <span>Inspect Evidence in Workspace</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-cobalt" />
          </button>
        </div>

        {/* 6-Pillar Evidence Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {pillars.map((pillar) => {
            const Icon = pillar.icon;
            return (
              <div
                key={pillar.id}
                className="editorial-card p-6 flex flex-col justify-between space-y-6 group"
              >
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-9 h-9 rounded-lg bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt group-hover:scale-105 transition-transform">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark">
                      {pillar.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-base font-bold text-ink dark:text-ink-dark tracking-tight">
                      {pillar.title}
                    </h3>
                    <p className="text-xs text-cobalt font-medium mt-0.5 font-mono">
                      {pillar.tagline}
                    </p>
                  </div>

                  <p className="text-xs text-muted-fg dark:text-muted-dark leading-relaxed">
                    {pillar.description}
                  </p>
                </div>

                <div className="pt-4 border-t border-hairline dark:border-hairline-dark space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-muted-fg dark:text-muted-dark">Empirical Record:</span>
                    <span className="font-mono font-bold text-ink dark:text-ink-dark">
                      {pillar.evidenceMetric}
                    </span>
                  </div>
                  <div className="flex items-center justify-between text-[11px] text-muted-fg dark:text-muted-dark font-mono">
                    <span>{pillar.evidenceSub}</span>
                  </div>
                  <div className="p-2 rounded bg-paper dark:bg-paper-dark/60 text-[11px] font-mono text-muted-fg dark:text-muted-dark truncate">
                    <code>{pillar.formula}</code>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
