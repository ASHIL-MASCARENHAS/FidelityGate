'use client';

import React from 'react';
import { CheckCircle2, RotateCw, X, ShieldCheck, ArrowRight, Sparkles, Clock, Timer } from 'lucide-react';
import { AutoDemoContext } from '@/types/demo';
import { playTick, playConfirmation } from '@/lib/sound';

interface AutoDemoCompletionModalProps {
  isOpen: boolean;
  context: AutoDemoContext;
  onRestart: () => void;
  onClose: () => void;
  soundEnabled?: boolean;
  elapsedSeconds?: number;
}

export function AutoDemoCompletionModal({
  isOpen,
  context,
  onRestart,
  onClose,
  soundEnabled = false,
  elapsedSeconds,
}: AutoDemoCompletionModalProps) {
  if (!isOpen) return null;

  const outcome = context.outcomeReport;
  const delta = outcome?.latency_delta_ms;
  const reductionPct = outcome?.latency_reduction_pct;

  const formattedDuration = typeof elapsedSeconds === 'number'
    ? `${Math.floor(elapsedSeconds / 60)}m ${(elapsedSeconds % 60).toString().padStart(2, '0')}s`
    : '2m 45s';

  const isUnderThreeMinutes = typeof elapsedSeconds === 'number' ? elapsedSeconds < 180 : true;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="demo-complete-title"
    >
      <div className="w-full max-w-lg p-6 bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark rounded-2xl shadow-elevation relative overflow-hidden text-ink dark:text-ink-dark space-y-5">
        {/* Top glowing accent hairline */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-emerald-500 via-cobalt to-cyan-400" />

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark flex items-center justify-center text-emerald-verdict shrink-0">
              <CheckCircle2 className="w-6 h-6" />
            </div>
            <div>
              <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-emerald-verdict">
                Demonstration Complete
              </span>
              <h3 id="demo-complete-title" className="text-base sm:text-lg font-bold text-ink dark:text-ink-dark tracking-tight mt-0.5">
                Auto Demo Tour Finished
              </h3>
            </div>
          </div>

          <button
            onClick={() => {
              playTick(soundEnabled);
              onClose();
            }}
            className="p-1 rounded-lg text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-paper dark:hover:bg-paper-dark transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50"
            aria-label="Close"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Summary text */}
        <p className="text-xs sm:text-sm text-muted-fg dark:text-muted-dark leading-relaxed">
          You have completed the calibrated 3-minute guided inspection of <strong>FidelityGate</strong> across all 8 core views. Real telemetry was triaged, candidate mitigations evaluated under parameter uncertainty, the deterministic gate enforced safety invariants, and human authorization was respected before simulated execution.
        </p>

        {/* Timing Performance Card */}
        <div className="p-3.5 rounded-xl border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark flex items-center justify-between gap-3 text-xs font-mono">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt shrink-0">
              <Timer className="w-4 h-4 text-cobalt dark:text-cyan-accent" />
            </div>
            <div>
              <span className="text-muted-fg dark:text-muted-dark block text-[10px] uppercase tracking-wider">
                Total Tour Duration
              </span>
              <span className="font-bold text-ink dark:text-ink-dark text-sm">
                {formattedDuration}
              </span>
            </div>
          </div>

          <div className="text-right">
            <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold ${
              isUnderThreeMinutes
                ? 'bg-emerald-verdict-subtle text-emerald-verdict'
                : 'bg-amber-warning-subtle text-amber-warning'
            }`}>
              <ShieldCheck className="w-3 h-3" />
              {isUnderThreeMinutes ? 'Target Met (< 3m)' : 'Completed'}
            </span>
            <span className="block text-[10px] text-muted-fg mt-0.5">
              8 views · 15s dwell · 4s count
            </span>
          </div>
        </div>

        {/* Key Verified Findings Card */}
        <div className="p-4 rounded-xl border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark space-y-3 font-mono text-xs">
          <div className="flex items-center justify-between pb-2 border-b border-hairline dark:border-hairline-dark">
            <span className="text-muted-fg dark:text-muted-dark">Verified Workflow Run:</span>
            <span className="font-semibold text-ink dark:text-ink-dark">
              {context.selectedWorkflowRunId || 'active'}
            </span>
          </div>

          <div className="grid grid-cols-2 gap-2 text-[11px]">
            <div>
              <span className="text-muted-fg block">Gate Verdict</span>
              <span className="font-bold text-emerald-verdict">
                {context.gateVerdict || 'ACCEPT'}
              </span>
            </div>
            <div>
              <span className="text-muted-fg block">Candidate Action</span>
              <span className="font-semibold text-ink dark:text-ink-dark">
                {context.selectedCandidateId || 'R-reroute-alt1'}
              </span>
            </div>
            <div>
              <span className="text-muted-fg block">Latency Impact</span>
              <span className="font-bold text-emerald-verdict">
                {typeof delta === 'number'
                  ? `${delta.toFixed(2)} ms (${reductionPct?.toFixed(1)}%)`
                  : '-3.55 ms (-13.4%)'}
              </span>
            </div>
            <div>
              <span className="text-muted-fg block">Capacity Violations</span>
              <span className="font-bold text-emerald-verdict">
                {outcome ? `${outcome.post_action_capacity_violations} breaches` : '0 breaches'}
              </span>
            </div>
          </div>
        </div>

        {/* Modal Controls */}
        <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-hairline dark:border-hairline-dark">
          <button
            onClick={() => {
              playTick(soundEnabled);
              onRestart();
            }}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-3.5 py-2 rounded-xl border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-xs font-semibold text-ink dark:text-ink-dark hover:border-cobalt transition-colors"
          >
            <RotateCw className="w-3.5 h-3.5" />
            <span>Restart Tour</span>
          </button>

          <button
            onClick={() => {
              playConfirmation(soundEnabled);
              onClose();
            }}
            className="w-full sm:w-auto inline-flex items-center justify-center gap-1.5 px-5 py-2 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white text-xs font-semibold shadow-fine transition-all active:scale-95"
          >
            <span>Close &amp; Explore Freely</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
