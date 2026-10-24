'use client';

import React, { useState } from 'react';
import { X, Check, AlertOctagon, Info, UserCheck, RefreshCw } from 'lucide-react';
import { playConfirmation, playTick } from '@/lib/sound';

interface HumanApprovalModalProps {
  isOpen: boolean;
  onClose: () => void;
  workflowRunId?: string | null;
  candidateId?: string | null;
  scenarioName?: string;
  nominalLatency?: number;
  worstLatency?: number;
  sloThreshold?: number;
  gateVerdict?: string;
  soundEnabled?: boolean;
  onApprove?: () => Promise<void> | void;
  onReject?: () => Promise<void> | void;
}

export function HumanApprovalModal({
  isOpen,
  onClose,
  workflowRunId,
  candidateId,
  scenarioName = 'WAN-042 · Traffic Surge Reroute',
  nominalLatency = 18.0,
  worstLatency = 48.6,
  sloThreshold = 45.0,
  gateVerdict = 'GATHER_EVIDENCE',
  soundEnabled = false,
  onApprove,
  onReject,
}: HumanApprovalModalProps) {
  const [approvalState, setApprovalState] = useState<'pending' | 'approved' | 'rejected'>('pending');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  if (!isOpen) return null;

  const handleApprove = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      if (onApprove) {
        await onApprove();
      }
      playConfirmation(soundEnabled);
      setApprovalState('approved');
    } catch (err: any) {
      setSubmitError(err.message || 'Authorization failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleReject = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      if (onReject) {
        await onReject();
      }
      playTick(soundEnabled);
      setApprovalState('rejected');
    } catch (err: any) {
      setSubmitError(err.message || 'Rejection failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const isGateAbstain = gateVerdict === 'ABSTAIN';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in">
      <div className="editorial-card w-full max-w-xl p-6 sm:p-8 bg-paper dark:bg-surface-dark border border-hairline dark:border-hairline-dark rounded-2xl shadow-2xl relative overflow-hidden">
        {/* Top glowing accent line */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-500 via-cobalt to-indigo-500" />

        {/* Modal Header */}
        <div className="flex items-start justify-between pb-4 border-b border-hairline dark:border-hairline-dark">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt">
              <UserCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-ink dark:text-ink-dark">
                Human-in-the-Loop Action Authorization
              </h3>
              <p className="text-xs text-muted-fg dark:text-muted-dark">
                Consequential Network Intervention Gate {workflowRunId ? `· Run ${workflowRunId}` : ''}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-surface dark:hover:bg-surface-dark transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Target Scenario & Evidence Details */}
        <div className="py-5 space-y-4">
          <div className="p-3.5 rounded-xl bg-surface dark:bg-surface-dark/60 border border-hairline dark:border-hairline-dark space-y-2">
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-muted-fg dark:text-muted-dark">Target Scenario:</span>
              <span className="font-bold text-ink dark:text-ink-dark">{scenarioName}</span>
            </div>
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-muted-fg dark:text-muted-dark">Proposed Candidate:</span>
              <span className="font-bold text-cobalt">{candidateId || 'R-reroute-alt1 (Alternate Path)'}</span>
            </div>
            <div className="flex justify-between items-center text-xs font-mono">
              <span className="text-muted-fg dark:text-muted-dark">Deterministic Gate Verdict:</span>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                  gateVerdict === 'ACCEPT'
                    ? 'bg-emerald-verdict-subtle text-emerald-verdict border border-emerald-verdict/30'
                    : gateVerdict === 'GATHER_EVIDENCE'
                    ? 'bg-amber-warning-subtle text-amber-warning border border-amber-warning/30'
                    : 'bg-rose-abstain-subtle text-rose-abstain border border-rose-abstain/30'
                }`}
              >
                {gateVerdict}
              </span>
            </div>
          </div>

          {/* Metric Comparison */}
          <div className="grid grid-cols-3 gap-2.5 text-center font-mono text-xs">
            <div className="p-2.5 rounded-lg border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50">
              <span className="text-[11px] text-muted-fg dark:text-muted-dark uppercase block">Nominal RTT</span>
              <span className="text-sm font-bold text-emerald-verdict block mt-0.5">{nominalLatency.toFixed(1)} ms</span>
            </div>
            <div className="p-2.5 rounded-lg border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50">
              <span className="text-[11px] text-muted-fg dark:text-muted-dark uppercase block">Worst Burst RTT</span>
              <span className="text-sm font-bold text-amber-warning block mt-0.5">{worstLatency.toFixed(1)} ms</span>
            </div>
            <div className="p-2.5 rounded-lg border border-hairline dark:border-hairline-dark bg-surface/50 dark:bg-surface-dark/50">
              <span className="text-[11px] text-muted-fg dark:text-muted-dark uppercase block">SLO Contract</span>
              <span className="text-sm font-bold text-ink dark:text-ink-dark block mt-0.5">{sloThreshold.toFixed(1)} ms</span>
            </div>
          </div>

          {submitError && (
            <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs font-mono text-rose-600 dark:text-rose-400">
              {submitError}
            </div>
          )}

          {/* Invariant Warning */}
          <div className="p-3.5 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-ink dark:text-ink-dark flex items-start space-x-2.5">
            <AlertOctagon className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <span className="font-bold text-amber-700 dark:text-amber-400 block font-mono">
                Responsible AI &amp; Gate Invariant Notice
              </span>
              <p className="text-[11px] text-muted-fg dark:text-muted-dark leading-snug">
                FidelityGate strictly forbids autonomous alteration of network routes. An operator can authorize or reject an evaluated candidate, but <strong>cannot override a mathematical gate ABSTAIN</strong>.
              </p>
            </div>
          </div>

          {/* Execution Environment Disclaimer */}
          <div className="text-[11px] font-mono text-muted-fg dark:text-muted-dark flex items-center space-x-1.5 px-1">
            <Info className="w-3.5 h-3.5 text-cobalt shrink-0" />
            <span>Execution Environment: <strong>Offline Digital-Twin Simulator</strong> (Isolated simulation).</span>
          </div>
        </div>

        {/* Modal Action Buttons */}
        <div className="pt-4 border-t border-hairline dark:border-hairline-dark flex items-center justify-between">
          {approvalState === 'pending' ? (
            <>
              <button
                onClick={handleReject}
                disabled={isSubmitting}
                className="px-4 py-2.5 rounded-xl border border-rose-500/30 text-rose-600 dark:text-rose-400 hover:bg-rose-500/10 text-xs font-mono font-medium transition-all disabled:opacity-50"
              >
                Reject &amp; Fail Closed
              </button>

              <div className="flex items-center space-x-3">
                <button
                  onClick={onClose}
                  disabled={isSubmitting}
                  className="px-4 py-2.5 rounded-xl border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark text-xs font-mono transition-all"
                >
                  Cancel
                </button>
                <button
                  onClick={handleApprove}
                  disabled={isSubmitting || isGateAbstain}
                  className={`px-5 py-2.5 rounded-xl text-xs font-mono font-bold tracking-tight shadow-md transition-all active:scale-95 flex items-center space-x-1.5 ${
                    isGateAbstain
                      ? 'bg-muted-fg/20 text-muted-fg cursor-not-allowed'
                      : 'bg-cobalt hover:bg-cobalt-hover text-white'
                  }`}
                  title={isGateAbstain ? 'Cannot authorize an intervention with gate ABSTAIN' : 'Authorize Intervention'}
                >
                  {isSubmitting ? (
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  ) : (
                    <Check className="w-3.5 h-3.5" />
                  )}
                  <span>{isSubmitting ? 'Recording...' : 'Authorize Intervention'}</span>
                </button>
              </div>
            </>
          ) : approvalState === 'approved' ? (
            <div className="w-full flex items-center justify-between p-2 rounded-xl bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-400 text-xs font-mono">
              <span className="flex items-center space-x-2">
                <Check className="w-4 h-4" />
                <span>Intervention Authorized by Operator · Recorded to SQLite Audit Trail</span>
              </span>
              <button
                onClick={onClose}
                className="px-3 py-1 rounded-lg bg-emerald-600 text-white text-[11px] font-bold"
              >
                Done
              </button>
            </div>
          ) : (
            <div className="w-full flex items-center justify-between p-2 rounded-xl bg-rose-500/15 border border-rose-500/30 text-rose-700 dark:text-rose-400 text-xs font-mono">
              <span className="flex items-center space-x-2">
                <AlertOctagon className="w-4 h-4" />
                <span>Intervention Rejected · Safely Halted</span>
              </span>
              <button
                onClick={onClose}
                className="px-3 py-1 rounded-lg bg-rose-600 text-white text-[11px] font-bold"
              >
                Close
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default HumanApprovalModal;
