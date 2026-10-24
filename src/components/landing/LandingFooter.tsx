'use client';

import React from 'react';
import { ArrowUpRight, ShieldCheck, Terminal, FileText, GitBranch, ArrowRight } from 'lucide-react';
import { playTick } from '@/lib/sound';

interface LandingFooterProps {
  soundEnabled: boolean;
  onOpenWorkspace: (tab?: string) => void;
}

export function LandingFooter({ soundEnabled, onOpenWorkspace }: LandingFooterProps) {
  return (
    <footer className="border-t border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark transition-colors">
      {/* Final Confident CTA Banner */}
      <div className="max-w-7xl mx-auto px-6 py-16 border-b border-hairline dark:border-hairline-dark">
        <div className="editorial-card p-8 md:p-14 bg-gradient-to-br from-surface to-paper dark:from-surface-dark dark:to-paper-dark relative overflow-hidden flex flex-col md:flex-row md:items-center justify-between gap-8">
          <div className="max-w-2xl space-y-4">
            <span className="t-eyebrow text-cobalt flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-cobalt animate-ping" />
              <span>Deterministic Assurance Platform</span>
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-ink dark:text-ink-dark leading-tight">
              Turn uncertainty into evidence. Turn evidence into defensible decisions.
            </h2>
            <p className="text-sm md:text-base text-muted-fg dark:text-muted-dark leading-relaxed">
              Explore the engineering workspace with live interactive topologies, counterexample sweeps, and the fail-closed deterministic decision gate.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 flex-shrink-0">
            <button
              onClick={() => {
                playTick(soundEnabled);
                onOpenWorkspace('decision');
              }}
              className="inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white text-sm font-semibold tracking-tight transition-all shadow-fine active:scale-[0.98]"
            >
              <span>Explore Platform</span>
              <ArrowUpRight className="w-4 h-4" />
            </button>
            <button
              onClick={() => {
                playTick(soundEnabled);
                onOpenWorkspace('evaluation');
              }}
              className="inline-flex items-center justify-center space-x-2 px-6 py-3.5 rounded-xl border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark hover:border-cobalt/50 text-ink dark:text-ink-dark text-sm font-semibold tracking-tight transition-all shadow-fine"
            >
              <span>View Baseline Benchmarks</span>
              <ArrowRight className="w-4 h-4 text-muted-fg dark:text-muted-dark" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Footer Links & Architecture Contracts */}
      <div className="max-w-7xl mx-auto px-6 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand & Mission Column */}
          <div className="space-y-4 md:col-span-1">
            <div className="flex items-center space-x-2.5">
              <div className="w-7 h-7 rounded-lg bg-cobalt flex items-center justify-center text-white shadow-fine">
                <span className="font-mono text-xs font-bold">◈</span>
              </div>
              <span className="font-extrabold text-base tracking-tight text-ink dark:text-ink-dark">
                FidelityGate
              </span>
            </div>
            <p className="text-xs text-muted-fg dark:text-muted-dark leading-relaxed">
              Uncertainty-aware decision assurance for enterprise digital-twin network routing systems.
            </p>
            <div className="inline-flex items-center space-x-2 text-[11px] font-mono text-emerald-verdict bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark px-2 py-0.5 rounded">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-verdict" />
              <span>Engine Status: Online & Deterministic</span>
            </div>
          </div>

          {/* Navigation Column */}
          <div className="space-y-3">
            <h4 className="t-panel-title">
              Engineering Views
            </h4>
            <ul className="space-y-2 text-xs text-muted-fg dark:text-muted-dark font-medium">
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('overview');
                  }}
                  className="hover:text-cobalt transition-colors"
                >
                  Overview Dashboard
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('decision');
                  }}
                  className="hover:text-cobalt transition-colors"
                >
                  Decision Workspace
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('trace');
                  }}
                  className="hover:text-cobalt transition-colors"
                >
                  Execution Trace (AgentOps)
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('evaluation');
                  }}
                  className="hover:text-cobalt transition-colors"
                >
                  Evaluation Lab (4-Way Baselines)
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('history');
                  }}
                  className="hover:text-cobalt transition-colors"
                >
                  Persistent Run History
                </button>
              </li>
            </ul>
          </div>

          {/* Technical Documentation Column */}
          <div className="space-y-3">
            <h4 className="t-panel-title">
              Project Contracts
            </h4>
            <ul className="space-y-2 text-xs text-muted-fg dark:text-muted-dark">
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('docs');
                  }}
                  className="hover:text-cobalt transition-colors flex items-center space-x-1"
                >
                  <FileText className="w-3 h-3" />
                  <span>ARCHITECTURE.md</span>
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('docs');
                  }}
                  className="hover:text-cobalt transition-colors flex items-center space-x-1"
                >
                  <FileText className="w-3 h-3" />
                  <span>CONTRACTS.md</span>
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('docs');
                  }}
                  className="hover:text-cobalt transition-colors flex items-center space-x-1"
                >
                  <FileText className="w-3 h-3" />
                  <span>METHODOLOGY.md</span>
                </button>
              </li>
              <li>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    onOpenWorkspace('docs');
                  }}
                  className="hover:text-cobalt transition-colors flex items-center space-x-1"
                >
                  <FileText className="w-3 h-3" />
                  <span>EVALUATION_PROTOCOL.md</span>
                </button>
              </li>
            </ul>
          </div>

          {/* Operational Guarantees Column */}
          <div className="space-y-3">
            <h4 className="t-panel-title">
              System Invariants
            </h4>
            <div className="space-y-2 text-xs text-muted-fg dark:text-muted-dark">
              <div className="p-2.5 rounded bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                <span className="text-ink dark:text-ink-dark font-bold block">Fail-Closed Semantics</span>
                <span className="text-[11px]">Zero false accepts under active uncertainty breach</span>
              </div>
              <div className="p-2.5 rounded bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark">
                <span className="text-ink dark:text-ink-dark font-bold block">Zero External Phone-Home</span>
                <span className="text-[11px]">Fully air-gapped deterministic Python / Next.js engine</span>
              </div>
            </div>
          </div>
        </div>

        {/* Bottom Baseline Bar */}
        <div className="pt-8 mt-8 border-t border-hairline dark:border-hairline-dark flex flex-col sm:flex-row items-center justify-between text-xs text-muted-fg dark:text-muted-dark gap-4">
          <div className="flex items-center space-x-3">
            <span>&copy; {new Date().getFullYear()} FidelityGate Project.</span>
            <span>All rights reserved.</span>
          </div>
          <div className="flex items-center space-x-4">
            <span className="flex items-center space-x-1">
              <ShieldCheck className="w-3.5 h-3.5 text-cobalt" />
              <span>WCAG 2.2 AA Compliant</span>
            </span>
            <span>Next.js 14 &middot; Strict TypeScript</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
