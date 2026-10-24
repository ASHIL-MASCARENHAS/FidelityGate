'use client';

import React, { useState } from 'react';
import { Search, Flame, Radio, ShieldCheck, BarChart4, ChevronRight, Check } from 'lucide-react';
import { playTick } from '@/lib/sound';

interface WorkflowSequenceProps {
  soundEnabled: boolean;
  onOpenWorkspace: () => void;
}

export function WorkflowSequence({ soundEnabled, onOpenWorkspace }: WorkflowSequenceProps) {
  const [activeStep, setActiveStep] = useState<number>(0);

  const steps = [
    {
      id: 'investigate',
      number: '01',
      title: 'Investigate',
      tagline: 'Examine scenario & candidate decision',
      description:
        'Parse the proposed routing change, load balance target, or failover path. Ingest topology parameters including interface capacities, offered loads, and contractually binding SLO thresholds.',
      icon: Search,
      badge: 'Topology Ingestion',
      metric: '18.0 ms nominal',
      details: [
        'Reads digital-twin topology parameters',
        'Extracts traffic matrix & peak demand vectors',
        'Validates target latency SLO contracts',
      ],
    },
    {
      id: 'challenge',
      number: '02',
      title: 'Challenge',
      tagline: 'Expose adversarial counterexamples',
      description:
        'Systematically perturb load factors, queue depths, and link delays along non-linear convex queueing functions. Instead of trusting average-case conditions, actively locate fragility regions.',
      icon: Flame,
      badge: 'Adversarial Sweep',
      metric: 'SLO breach at +19% load',
      details: [
        'Convex M/M/1 non-linear queueing search',
        'Explores multi-dimensional uncertainty envelope',
        'Isolates concrete counterexamples that cause SLA breaches',
      ],
    },
    {
      id: 'gather',
      number: '03',
      title: 'Gather Evidence',
      tagline: 'Deploy adaptive telemetry diagnostics',
      description:
        'When uncertainty creates doubt, invoke targeted diagnostic probes. Account for measurement jitter, collector variance, and timestamp skew rather than assuming perfect telemetry precision.',
      icon: Radio,
      badge: 'Uncertainty-Aware Telemetry',
      metric: '±2.4 ms noise interval',
      details: [
        'Active synthetic probes on critical transit hops',
        'eBPF queue depth and packet drop tracking',
        'Measurement-error bounding with explicit confidence intervals',
      ],
    },
    {
      id: 'verify',
      number: '04',
      title: 'Verify',
      tagline: 'Deterministic fail-closed gate',
      description:
        'Submit accumulated evidence to an un-bypasable, zero-drift mathematical decision gate. Decisions are rigorously classified into ACCEPT, GATHER_EVIDENCE, or ABSTAIN.',
      icon: ShieldCheck,
      badge: 'Zero-Drift Decision Gate',
      metric: 'GATHER_EVIDENCE verdict',
      details: [
        'Fail-closed safety guarantees (zero false accepts)',
        'Explicit mathematical proofs for each verdict',
        'Tamper-resistant SQLite run receipts',
      ],
    },
    {
      id: 'evaluate',
      number: '05',
      title: 'Evaluate',
      tagline: 'Benchmark against baseline methods',
      description:
        'Compare FidelityGate against industry defaults: nominal-only approaches that miss hidden failures, fixed-margin (+25%) rules that over-provision, and brute-force sweeps.',
      icon: BarChart4,
      badge: 'Multi-Scenario Benchmarking',
      metric: '100% safety · 68% fewer probes',
      details: [
        'Nominal-only: catastrophic 40% breach rate',
        'Fixed-margin (+25%): 60% false abstention overhead',
        'FidelityGate: 100% safety with optimal diagnostic thrift',
      ],
    },
  ];

  const handleStepSelect = (index: number) => {
    playTick(soundEnabled);
    setActiveStep(index);
  };

  const current = steps[activeStep];
  const StepIcon = current.icon;

  return (
    <section id="workflow" className="py-16 md:py-20 border-t border-hairline dark:border-hairline-dark">
      <div className="max-w-7xl mx-auto px-6">
        {/* Section Header */}
        <div className="max-w-3xl mb-16">
          <span className="t-eyebrow text-cobalt block mb-3">
            Workflow Architecture
          </span>
          <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-ink dark:text-ink-dark leading-tight mb-4">
            How uncertainty becomes defensible decision evidence.
          </h2>
          <p className="text-base text-muted-fg dark:text-muted-dark leading-relaxed">
            A 5-stage closed-loop assurance cycle that protects critical enterprise network infrastructure from silent SLA breaches, cascading routing failures, and unvalidated automated interventions.
          </p>
        </div>

        {/* Step Navigation Pill Bar */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 mb-12">
          {steps.map((step, idx) => {
            const isSelected = activeStep === idx;
            return (
              <button
                key={step.id}
                onClick={() => handleStepSelect(idx)}
                className={`text-left p-3.5 rounded-xl border transition-all text-xs ${
                  isSelected
                    ? 'border-cobalt bg-surface dark:bg-surface-dark shadow-fine ring-1 ring-cobalt/20'
                    : 'border-hairline dark:border-hairline-dark bg-transparent hover:bg-surface/50 dark:hover:bg-surface-dark/50 text-muted-fg dark:text-muted-dark'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="font-mono text-[11px] font-bold text-muted-fg dark:text-muted-dark">
                    {step.number}
                  </span>
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-cobalt" />}
                </div>
                <div
                  className={`font-semibold tracking-tight ${
                    isSelected ? 'text-ink dark:text-ink-dark' : 'text-muted-fg dark:text-muted-dark'
                  }`}
                >
                  {step.title}
                </div>
              </button>
            );
          })}
        </div>

        {/* Step Detail Focus Card */}
        <div className="editorial-card p-6 md:p-10">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
            {/* Step Explanation */}
            <div className="lg:col-span-7 space-y-6">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt shadow-fine">
                  <StepIcon className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center space-x-2">
                    <span className="font-mono text-xs font-bold text-cobalt">STAGE {current.number}</span>
                    <span className="text-muted-fg dark:text-muted-dark">·</span>
                    <span className="text-xs text-muted-fg dark:text-muted-dark">{current.badge}</span>
                  </div>
                  <h3 className="text-2xl font-bold tracking-tight text-ink dark:text-ink-dark mt-0.5">
                    {current.title}: {current.tagline}
                  </h3>
                </div>
              </div>

              <p className="text-sm md:text-base text-muted-fg dark:text-muted-dark leading-relaxed">
                {current.description}
              </p>

              <div className="space-y-2.5 pt-2">
                <span className="t-eyebrow block">
                  Stage Invariants & Verification Guarantees:
                </span>
                {current.details.map((item, i) => (
                  <div key={i} className="flex items-center space-x-2.5 text-xs text-ink dark:text-ink-dark">
                    <div className="w-4 h-4 rounded-full bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt flex-shrink-0">
                      <Check className="w-2.5 h-2.5" />
                    </div>
                    <span>{item}</span>
                  </div>
                ))}
              </div>

              <div className="pt-4 flex items-center space-x-4">
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    setActiveStep((prev) => (prev + 1) % steps.length);
                  }}
                  className="inline-flex items-center space-x-2 text-xs font-semibold text-cobalt hover:underline"
                >
                  <span>Next stage: {steps[(activeStep + 1) % steps.length].title}</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>

            {/* Interactive Stage Visualization Diagram */}
            <div className="lg:col-span-5 bg-paper dark:bg-paper-dark/60 rounded-xl border border-hairline dark:border-hairline-dark p-6 space-y-4">
              <div className="flex items-center justify-between pb-3 border-b border-hairline dark:border-hairline-dark text-xs font-mono">
                <span className="text-muted-fg dark:text-muted-dark">Telemetry Metric:</span>
                <span className="font-bold text-cobalt">{current.metric}</span>
              </div>

              {/* Stage-specific interactive mini-visual */}
              {activeStep === 0 && (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">CANDIDATE INTERVENTION</span>
                    <span className="text-ink dark:text-ink-dark font-bold">WAN-042 Reroute to Spine Alpha</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div className="p-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                      <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Nominal Delay</span>
                      <span className="font-bold text-ink dark:text-ink-dark">18.0 ms</span>
                    </div>
                    <div className="p-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                      <span className="text-muted-fg dark:text-muted-dark block text-[11px]">SLO Bound</span>
                      <span className="font-bold text-emerald-verdict">&le; 45.0 ms</span>
                    </div>
                  </div>
                </div>
              )}

              {activeStep === 1 && (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-amber-warning-subtle dark:bg-amber-warning-dark border border-amber-warning/40">
                    <span className="text-amber-warning block text-[11px] font-bold">COUNTEREXAMPLE LOCATED</span>
                    <span className="text-ink dark:text-ink-dark font-semibold">Load factor = 1.194 &middot; Latency = 48.6 ms</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-[11px]">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Queueing Equation</span>
                    <span className="text-ink dark:text-ink-dark">T = T_0 / (1 - &rho;) &rarr; non-linear spike</span>
                  </div>
                </div>
              )}

              {activeStep === 2 && (
                <div className="space-y-3 font-mono text-xs">
                  <div className="p-3 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">TELEMETRY PROBE #04</span>
                    <span className="text-ink dark:text-ink-dark font-bold">Interface Gi0/0/1 queue depth: 42 pkts</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-[11px]">
                    <span className="text-muted-fg dark:text-muted-dark block text-[11px]">Bounded Noise Interval</span>
                    <span className="text-cobalt font-semibold">[ 46.2 ms ... 51.0 ms ] (95% CI)</span>
                  </div>
                </div>
              )}

              {activeStep === 3 && (
                <div className="space-y-2.5 font-mono text-xs">
                  <div className="p-2.5 rounded-lg bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark border border-emerald-verdict/40 flex items-center justify-between">
                    <span className="font-bold text-emerald-verdict">ACCEPT</span>
                    <span className="text-[11px] text-muted-fg dark:text-muted-dark">Zero SLO breaches</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-amber-warning-subtle dark:bg-amber-warning-dark border border-amber-warning ring-1 ring-amber-warning/30 flex items-center justify-between">
                    <span className="font-bold text-amber-warning">GATHER_EVIDENCE</span>
                    <span className="text-[11px] text-amber-warning font-bold">Active in WAN-042</span>
                  </div>
                  <div className="p-2.5 rounded-lg bg-rose-abstain-subtle dark:bg-rose-abstain-dark border border-rose-abstain/40 flex items-center justify-between">
                    <span className="font-bold text-rose-abstain">ABSTAIN</span>
                    <span className="text-[11px] text-muted-fg dark:text-muted-dark">Nominal SLO breach</span>
                  </div>
                </div>
              )}

              {activeStep === 4 && (
                <div className="space-y-2 font-mono text-[11px]">
                  <div className="flex justify-between p-2 rounded bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark">Nominal Only:</span>
                    <span className="text-rose-abstain font-bold">40% Silent Failure</span>
                  </div>
                  <div className="flex justify-between p-2 rounded bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                    <span className="text-muted-fg dark:text-muted-dark">Fixed Margin (+25%):</span>
                    <span className="text-amber-warning font-bold">60% False Abstain</span>
                  </div>
                  <div className="flex justify-between p-2 rounded bg-cobalt-subtle dark:bg-cobalt-subtle-dark border border-cobalt/30">
                    <span className="text-cobalt font-bold">FidelityGate Adaptive:</span>
                    <span className="text-cobalt font-bold">100% Correct / 0 SLA Breaches</span>
                  </div>
                </div>
              )}

              <button
                onClick={() => {
                  playTick(soundEnabled);
                  onOpenWorkspace();
                }}
                className="w-full py-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark hover:border-cobalt/50 text-xs font-semibold text-ink dark:text-ink-dark transition-colors shadow-fine flex items-center justify-center space-x-1.5"
              >
                <span>Inspect in Engineering Workspace</span>
                <ChevronRight className="w-3.5 h-3.5 text-cobalt" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
