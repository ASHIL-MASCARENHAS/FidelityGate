'use client';

import React, { useState } from 'react';
import {
  LayoutDashboard,
  Layers,
  Clock,
  Cpu,
  LineChart,
  Waves,
  History,
  FileText,
  Settings,
  ArrowUpRight,
  ChevronRight,
  CheckCircle2,
  Sparkles,
} from 'lucide-react';
import { playTick, playConfirmation } from '@/lib/sound';

interface ServicesShowcaseProps {
  soundEnabled: boolean;
  onOpenWorkspace: (tab: string) => void;
}

export function ServicesShowcase({ soundEnabled, onOpenWorkspace }: ServicesShowcaseProps) {
  const [filterCategory, setFilterCategory] = useState<'all' | 'insights' | 'assurance'>('all');
  const [hoveredService, setHoveredService] = useState<string | null>(null);

  const services = [
    {
      id: 'overview',
      targetTab: 'overview',
      category: 'insights',
      name: 'Overview Dashboard',
      badge: 'Fleet Telemetry',
      badgeColor: 'bg-cobalt-subtle text-cobalt dark:bg-cobalt-subtle-dark',
      icon: LayoutDashboard,
      subtitle: 'Global fleet-wide health & scenario triage',
      description:
        'Unified pane-of-glass monitoring branch PoPs, SD-WAN egress gateways, real-time traffic surges, and active counterexample breach alerts across enterprise topologies.',
      metricLabel: 'Fleet Observability',
      metricValue: '99.99% Uptime',
      metricSub: 'Active telemetry ingestion across 10 global regions',
      keyFeatures: [
        'Multi-scenario traffic congestion triage',
        'Instant sensitivity trigger to diagnostic traces',
        'Fleet-wide SLO breach warning banner',
      ],
    },
    {
      id: 'decision',
      targetTab: 'decision',
      category: 'insights',
      name: 'Decision Workspace',
      badge: 'Topology & Twin',
      badgeColor: 'bg-cobalt text-white shadow-fine',
      icon: Layers,
      subtitle: 'Digital-twin simulation under non-linear uncertainty',
      description:
        'Interactive 3D digital-twin routing engine. Systematically perturbs link load factors, exposes non-linear buffer overflow counterexamples, and submits evidence to the deterministic gate.',
      metricLabel: 'Decision Assurance',
      metricValue: 'Zero-Drift Gate',
      metricSub: 'M/M/1 non-linear queueing physics model',
      keyFeatures: [
        'Interactive Spline 3D twin & fleet topology',
        'Uncertainty sweep slider (5 to 100 sample points)',
        'Fail-closed gate verdict: ACCEPT, GATHER_EVIDENCE, ABSTAIN',
      ],
    },
    {
      id: 'trace',
      targetTab: 'trace',
      category: 'insights',
      name: 'Execution Trace',
      badge: 'AgentOps Waterfall',
      badgeColor: 'bg-emerald-verdict-subtle text-emerald-verdict dark:bg-emerald-verdict-dark',
      icon: Clock,
      subtitle: 'Traceable diagnostic execution graph',
      description:
        'Chronological span waterfall providing unbroken provenance for every decision: agent hypothesis, adversarial sweep, targeted diagnostic selection, physical probe dispatch, and gate verdict.',
      metricLabel: 'Trace Duration',
      metricValue: '110 ms Spans',
      metricSub: 'Cryptographically linked execution DAG',
      keyFeatures: [
        'Detailed span inspector with input/output payloads',
        'SNMP v3 & eBPF targeted probe telemetry',
        'Complete audit cost and decision accounting',
      ],
    },
    {
      id: 'evaluation',
      targetTab: 'evaluation',
      category: 'insights',
      name: 'Evaluation Lab',
      badge: '4-Way Baselines',
      badgeColor: 'bg-amber-warning-subtle text-amber-warning dark:bg-amber-warning-dark',
      icon: Cpu,
      subtitle: 'Empirical benchmarking against industry baselines',
      description:
        'Scientific validation harness proving mathematical differentiation against Nominal-Only, Fixed Safety Margin (+25%), and Exhaustive Non-Adaptive Sweeps (25x).',
      metricLabel: 'Safety Advantage',
      metricValue: '100% Safety',
      metricSub: 'Eliminates 20% to 40% unsafe acceptances',
      keyFeatures: [
        'Recharts comparative bar charts & latency curves',
        'False abstention vs. unsafe acceptance trade-off',
        'One-click multi-scenario batch benchmark runner',
      ],
    },
    {
      id: 'monitoring',
      targetTab: 'monitoring',
      category: 'insights',
      name: 'Telemetry Monitoring',
      badge: 'Telemetry & Jitter',
      badgeColor: 'bg-cobalt-subtle text-cobalt dark:bg-cobalt-subtle-dark',
      icon: LineChart,
      subtitle: 'Continuous queue dispersion & latency histograms',
      description:
        'Recharts-powered real-time telemetry analytics visualizing queue depth variance, link buffer congestion curves, and empirical confidence intervals across operational runs.',
      metricLabel: 'Measurement Bounding',
      metricValue: '±2.4 ms Jitter',
      metricSub: '95% empirical confidence interval modeling',
      keyFeatures: [
        'Queue delay dispersion over load factors',
        'Multi-run trend monitoring across SQLite history',
        'Dynamic threshold overlays for contractual SLO bounds',
      ],
    },
    {
      id: 'motion',
      targetTab: 'motion',
      category: 'insights',
      name: 'Motion & Sync',
      badge: 'Rive Signals',
      badgeColor: 'bg-paper text-ink dark:bg-paper-dark dark:text-ink-dark border border-hairline dark:border-hairline-dark',
      icon: Waves,
      subtitle: 'Real-time vector state-machine telemetry sync',
      description:
        'Interactive state-machine visualizer driven by Rive runtime animation logic. Translates mathematical gate states into responsive visual feedback and heartbeat pulses.',
      metricLabel: 'Vector Motion',
      metricValue: '60 FPS Canvas',
      metricSub: 'Accessible reduced-motion fallback',
      keyFeatures: [
        'Synchronized signal pulse across digital twin nodes',
        'Dynamic colorway reflecting gate verdict changes',
        'Zero layout shifts with hardware acceleration',
      ],
    },
    {
      id: 'history',
      targetTab: 'history',
      category: 'assurance',
      name: 'Audit Trail (Runs)',
      badge: 'SQLite Persistence',
      badgeColor: 'bg-emerald-verdict-subtle text-emerald-verdict dark:bg-emerald-verdict-dark',
      icon: History,
      subtitle: 'Immutable forensic execution ledger',
      description:
        'Persistent SQLite database storing every investigation run, scenario seed, sample evaluation, and mathematical gate verdict for audit compliance and historical reproducibility.',
      metricLabel: 'Local Ledger',
      metricValue: 'Immutable SQLite',
      metricSub: 'Tamper-resistant receipts stored in fidelitygate.db',
      keyFeatures: [
        'Multi-column search and decision verdict filtering',
        'One-click copyable raw JSON payload inspector',
        'Zero external cloud database dependencies',
      ],
    },
    {
      id: 'docs',
      targetTab: 'docs',
      category: 'assurance',
      name: 'Docs & Contracts',
      badge: 'Canonical Contracts',
      badgeColor: 'bg-cobalt-subtle text-cobalt dark:bg-cobalt-subtle-dark',
      icon: FileText,
      subtitle: 'Canonical engineering documentation & ADRs',
      description:
        'Living project context surviving agent and engineer handoffs. Comprehensive architectural contracts, Pydantic schemas, REST endpoint definitions, and queueing mathematics.',
      metricLabel: 'Documentation',
      metricValue: '8 Canonical Files',
      metricSub: 'ARCHITECTURE.md, CONTRACTS.md, METHODOLOGY.md',
      keyFeatures: [
        'Formal Pydantic and TypeScript schema parity',
        'Convex M/M/1 queueing mathematical proofs',
        'ADR records covering safety invariants and database choices',
      ],
    },
    {
      id: 'settings',
      targetTab: 'settings',
      category: 'assurance',
      name: 'Settings & Diag',
      badge: 'Controls & Safety',
      badgeColor: 'bg-paper text-ink dark:bg-paper-dark dark:text-ink-dark border border-hairline dark:border-hairline-dark',
      icon: Settings,
      subtitle: 'Operational constraints & air-gapped safeguards',
      description:
        'Engineering control room exposing light/dark color tokens, synthesized Web Audio tick feedback, WCAG 2.2 AA motion preferences, and host environment diagnostics.',
      metricLabel: 'Safety Invariants',
      metricValue: 'Fail-Closed',
      metricSub: 'Zero external phone-home calls; fully offline',
      keyFeatures: [
        'Web Audio API sound toggle with live test click',
        'WCAG 2.2 AA reduced motion sensitivity controls',
        'Node.js memory RSS, uptime, and database diagnostics',
      ],
    },
  ];

  const filteredServices = services.filter((s) => {
    if (filterCategory === 'all') return true;
    return s.category === filterCategory;
  });

  const handleServiceClick = (targetTab: string) => {
    playConfirmation(soundEnabled);
    onOpenWorkspace(targetTab);
  };

  return (
    <section id="services" className="py-16 md:py-20 border-t border-hairline dark:border-hairline-dark relative overflow-hidden">
      {/* Background ambient radial glow */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[500px] bg-gradient-to-tr from-cobalt-subtle/20 via-transparent to-cobalt-subtle/10 dark:from-cobalt-subtle-dark/20 pointer-events-none blur-3xl" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        {/* BilloDesign Section Header */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-10 gap-6">
          <div className="max-w-3xl">
            <div className="flex items-center space-x-2 mb-3">
              <span className="pulse-dot-parent">
                <span className="pulse-dot-back" />
                <span className="pulse-dot-front" />
              </span>
              <span className="t-eyebrow text-cobalt">
                SERVICES & PLATFORM MODULES
              </span>
            </div>
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight text-ink dark:text-ink-dark leading-[1.1] mb-4">
              Engineered for absolute certainty. <br />
              <span className="text-cobalt">Explore all 9 core services.</span>
            </h2>
            <p className="text-[15px] text-muted-fg dark:text-muted-dark leading-relaxed max-w-xl">
              Inspired by the precision of BilloDesign, every service in FidelityGate pairs minimal editorial craft with authoritative digital-twin queueing algorithms and zero-drift verification.
            </p>
          </div>

          {/* Billo Filter Pills */}
          <div className="flex items-center space-x-1 bg-surface dark:bg-surface-dark p-1.5 rounded-xl border border-hairline dark:border-hairline-dark shadow-fine self-start md:self-end">
            <button
              onClick={() => {
                playTick(soundEnabled);
                setFilterCategory('all');
              }}
              className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                filterCategory === 'all'
                  ? 'bg-cobalt text-white shadow-fine'
                  : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              All Services ({services.length})
            </button>
            <button
              onClick={() => {
                playTick(soundEnabled);
                setFilterCategory('insights');
              }}
              className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                filterCategory === 'insights'
                  ? 'bg-cobalt text-white shadow-fine'
                  : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              Insights (6)
            </button>
            <button
              onClick={() => {
                playTick(soundEnabled);
                setFilterCategory('assurance');
              }}
              className={`px-3.5 py-1.5 rounded-lg text-[13px] font-medium transition-colors ${
                filterCategory === 'assurance'
                  ? 'bg-cobalt text-white shadow-fine'
                  : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              Assurance (3)
            </button>
          </div>
        </div>

        {/* 9 Services Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredServices.map((service) => {
            const Icon = service.icon;
            const isHovered = hoveredService === service.id;

            return (
              <div
                key={service.id}
                onMouseEnter={() => {
                  setHoveredService(service.id);
                  playTick(soundEnabled);
                }}
                onMouseLeave={() => setHoveredService(null)}
                className="billo-card p-6 flex flex-col justify-between space-y-5 group cursor-pointer"
                onClick={() => handleServiceClick(service.targetTab)}
              >
                {/* Card Top: Icon, Badge, and Title */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="w-12 h-12 rounded-xl bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt group-hover:scale-105 transition-transform shadow-fine border border-cobalt/20">
                      <Icon className="w-5 h-5" />
                    </div>
                    <span
                      className={`t-eyebrow px-2.5 py-1 rounded-full ${service.badgeColor}`}
                    >
                      {service.badge}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-ink dark:text-ink-dark tracking-[-0.015em] group-hover:text-cobalt transition-colors">
                      {service.name}
                    </h3>
                    <p className="text-[13px] text-cobalt font-medium mt-1 leading-snug">
                      {service.subtitle}
                    </p>
                  </div>

                  <p className="text-[13px] text-muted-fg dark:text-muted-dark leading-relaxed">
                    {service.description}
                  </p>

                  {/* Bullet features */}
                  <div className="space-y-1.5 pt-1">
                    {service.keyFeatures.map((feat, idx) => (
                      <div key={idx} className="flex items-start gap-2 text-xs text-ink dark:text-ink-dark leading-relaxed">
                        <span className="w-1 h-1 mt-[7px] rounded-full bg-cobalt flex-shrink-0" />
                        <span className="text-muted-fg dark:text-muted-dark group-hover:text-ink dark:group-hover:text-ink-dark transition-colors">
                          {feat}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Card Bottom: Metrics & Direct Workspace Launcher */}
                <div className="pt-4 border-t border-hairline dark:border-hairline-dark space-y-3">
                  <div className="flex items-baseline justify-between gap-3">
                    <span className="text-xs text-muted-fg dark:text-muted-dark">
                      {service.metricLabel}
                    </span>
                    <span className="t-metric text-xs font-semibold text-ink dark:text-ink-dark">
                      {service.metricValue}
                    </span>
                  </div>
                  <div className="text-xs text-muted-fg dark:text-muted-dark truncate">
                    {service.metricSub}
                  </div>

                  {/* Action Link */}
                  <div className="pt-1 flex items-center justify-between text-xs font-semibold text-cobalt group-hover:underline">
                    <span className="flex items-center space-x-1.5">
                      <span>Launch in Workspace</span>
                      <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                    </span>
                    <ArrowUpRight className="w-4 h-4 opacity-70 group-hover:opacity-100 transition-opacity" />
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
export default ServicesShowcase;
