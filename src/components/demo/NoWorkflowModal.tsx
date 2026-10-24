'use client';

import React from 'react';
import { AlertCircle, ArrowRight, History, Play, X, UserCheck } from 'lucide-react';
import { playTick, playConfirmation } from '@/lib/sound';

interface NoWorkflowModalProps {
  isOpen: boolean;
  onGoToWorkflow: () => void;
  onGoToHistory: () => void;
  onClose: () => void;
  soundEnabled?: boolean;
}

export function NoWorkflowModal({
  isOpen,
  onGoToWorkflow,
  onGoToHistory,
  onClose,
  soundEnabled = false,
}: NoWorkflowModalProps) {
  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="no-workflow-title"
    >
      <div className="w-full max-w-lg p-6 bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark rounded-2xl shadow-elevation relative overflow-hidden text-ink dark:text-ink-dark space-y-5">
        {/* Top glowing accent hairline */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-amber-500 via-cobalt to-cyan-400" />

        {/* Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-amber-warning-subtle dark:bg-amber-warning-dark flex items-center justify-center text-amber-warning shrink-0">
              <AlertCircle className="w-5 h-5" />
            </div>
            <div>
              <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-amber-warning">
                Workflow Selection Required
              </span>
              <h3 id="no-workflow-title" className="text-base sm:text-lg font-bold text-ink dark:text-ink-dark tracking-tight mt-0.5">
                No Active Workflow Selected
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

        {/* Explanation */}
        <div className="space-y-3 text-xs sm:text-sm text-muted-fg dark:text-muted-dark leading-relaxed">
          <p>
            To experience the <strong>Auto Demo</strong> with genuine evidence and real verification artifacts, a workflow run must be active or loaded.
          </p>
          <p>
            FidelityGate never manufactures synthetic metrics or simulates fake agent actions. The guided tour navigates through actual persisted states (such as candidate evaluation, counterexample search, gate verdicts, and isolated twin outcome reports).
          </p>
        </div>

        {/* Direct Action Routes */}
        <div className="p-4 rounded-xl border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-ink dark:text-ink-dark block">
            Choose an Option:
          </span>

          <div className="flex flex-col sm:flex-row gap-2.5">
            <button
              onClick={() => {
                playConfirmation(soundEnabled);
                onGoToWorkflow();
              }}
              className="flex-1 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white text-xs font-semibold shadow-fine transition-all active:scale-95"
            >
              <UserCheck className="w-4 h-4" />
              <span>Go to Workflow &amp; Approval</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>

            <button
              onClick={() => {
                playTick(soundEnabled);
                onGoToHistory();
              }}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark hover:border-cobalt text-ink dark:text-ink-dark text-xs font-semibold transition-all active:scale-95"
            >
              <History className="w-4 h-4 text-muted-fg" />
              <span>Select from Audit Runs</span>
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="pt-2 flex justify-end border-t border-hairline dark:border-hairline-dark">
          <button
            onClick={() => {
              playTick(soundEnabled);
              onClose();
            }}
            className="px-4 py-1.5 rounded-lg text-xs font-medium text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}

