'use client';

import React, { useEffect } from 'react';
import {
  Play,
  Pause,
  ChevronRight,
  Square,
  Sparkles,
  ShieldCheck,
  UserCheck,
  Clock,
  ArrowRight,
  Info,
  X,
} from 'lucide-react';
import { AutoDemoStep, AutoDemoContext } from '@/types/demo';
import { playTick, playConfirmation } from '@/lib/sound';

interface AutoDemoModalProps {
  isOpen: boolean;
  step: AutoDemoStep;
  stepIndex: number;
  totalSteps: number;
  context: AutoDemoContext;
  countdown: number;
  isPaused: boolean;
  onContinue: () => void;
  onSkip: () => void;
  onStop: () => void;
  onTogglePause: () => void;
  soundEnabled?: boolean;
}

export function AutoDemoModal({
  isOpen,
  step,
  stepIndex,
  totalSteps,
  context,
  countdown,
  isPaused,
  onContinue,
  onSkip,
  onStop,
  onTogglePause,
  soundEnabled = false,
}: AutoDemoModalProps) {
  useEffect(() => {
    if (!isOpen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        e.preventDefault();
        playTick(soundEnabled);
        onStop();
      } else if (e.key === 'Enter') {
        e.preventDefault();
        playConfirmation(soundEnabled);
        onContinue();
      } else if (e.key === ' ') {
        // Toggle pause if not typing in an input
        if (
          document.activeElement?.tagName !== 'INPUT' &&
          document.activeElement?.tagName !== 'TEXTAREA'
        ) {
          e.preventDefault();
          playTick(soundEnabled);
          onTogglePause();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onContinue, onStop, onTogglePause, soundEnabled]);

  if (!isOpen) return null;

  const heading = step.getHeading(context);
  const description = step.getDescription(context);
  const nextPreview = step.getNextPreview(context);

  // Status badge styling based on genuine run status
  const status = context.workflowStatus || 'PENDING';
  const stage = context.currentStage || 'RECEIVED';
  const gateVerdict = context.gateVerdict || 'PENDING';

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby="auto-demo-title"
    >
      <div className="w-full max-w-lg p-6 bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark rounded-2xl shadow-elevation relative overflow-hidden text-ink dark:text-ink-dark space-y-5">
        {/* Top glowing accent hairline */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-cyan-400 via-cobalt to-indigo-500" />

        {/* Modal Header */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt shrink-0">
              <Sparkles className="w-5 h-5 text-cobalt dark:text-cyan-accent" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-cobalt dark:text-cyan-accent">
                  Auto Demo · Step {stepIndex + 1} of {totalSteps}
                </span>
                <span className="text-muted-fg dark:text-muted-dark text-xs">·</span>
                <span className="text-xs font-medium text-muted-fg dark:text-muted-dark">
                  Target: {step.tabLabel}
                </span>
              </div>
              <h3 id="auto-demo-title" className="text-base sm:text-lg font-bold text-ink dark:text-ink-dark tracking-tight mt-0.5">
                {heading}
              </h3>
            </div>
          </div>

          <button
            onClick={() => {
              playTick(soundEnabled);
              onStop();
            }}
            className="p-1 rounded-lg text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-paper dark:hover:bg-paper-dark transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50"
            aria-label="Stop and close Auto Demo"
            title="Stop Demo (Esc)"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Live Run Status Chip */}
        <div className="flex flex-wrap items-center gap-2 px-3 py-2 rounded-xl bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-xs font-mono">
          <span className="text-muted-fg dark:text-muted-dark">Workflow:</span>
          <span className="font-semibold text-ink dark:text-ink-dark">
            {context.selectedWorkflowRunId || 'None'}
          </span>
          <span className="text-muted-fg dark:text-muted-dark">·</span>
          <span className="text-muted-fg dark:text-muted-dark">Stage:</span>
          <span className="font-semibold text-cobalt dark:text-cyan-accent">
            {stage}
          </span>
          <span className="text-muted-fg dark:text-muted-dark">·</span>
          <span className="text-muted-fg dark:text-muted-dark">Verdict:</span>
          <span
            className={`font-semibold ${
              gateVerdict === 'ACCEPT'
                ? 'text-emerald-verdict'
                : gateVerdict === 'ABSTAIN'
                ? 'text-rose-500'
                : 'text-amber-warning'
            }`}
          >
            {gateVerdict}
          </span>
        </div>

        {/* Narrative Description */}
        <div className="space-y-2 text-xs sm:text-sm text-muted-fg dark:text-muted-dark leading-relaxed">
          <p>{description}</p>
        </div>

        {/* Next Preview Callout */}
        <div className="p-3 rounded-xl border border-hairline dark:border-hairline-dark bg-paper/60 dark:bg-paper-dark/60 flex items-center justify-between text-xs text-muted-fg dark:text-muted-dark font-mono">
          <span className="truncate">{nextPreview}</span>
          <span className="shrink-0 text-cobalt dark:text-cyan-accent flex items-center gap-1 font-semibold ml-2">
            Auto-transition
          </span>
        </div>

        {/* Countdown Indicator & Controls */}
        <div className="pt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-t border-hairline dark:border-hairline-dark">
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                playTick(soundEnabled);
                onTogglePause();
              }}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-xs font-medium text-ink dark:text-ink-dark hover:border-cobalt transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50"
              title={isPaused ? 'Resume countdown (Space)' : 'Pause countdown (Space)'}
            >
              {isPaused ? (
                <>
                  <Play className="w-3.5 h-3.5 text-cobalt fill-current" />
                  <span>Resume</span>
                </>
              ) : (
                <>
                  <Pause className="w-3.5 h-3.5 text-muted-fg" />
                  <span>Pause ({countdown}s)</span>
                </>
              )}
            </button>

            <button
              onClick={() => {
                playTick(soundEnabled);
                onStop();
              }}
              className="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-xs font-medium text-muted-fg dark:text-muted-dark hover:text-rose-500 hover:border-rose-500/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500/50"
              title="Stop Tour (Esc)"
            >
              <Square className="w-3 h-3 fill-current" />
              <span>Stop</span>
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                playTick(soundEnabled);
                onSkip();
              }}
              className="px-3 py-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-xs font-medium text-ink dark:text-ink-dark hover:border-cobalt transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50"
            >
              Skip Step
            </button>

            <button
              onClick={() => {
                playConfirmation(soundEnabled);
                onContinue();
              }}
              className="inline-flex items-center gap-1.5 px-4 py-1.5 rounded-lg bg-cobalt hover:bg-cobalt-hover text-white text-xs font-semibold shadow-fine transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50 active:scale-95"
            >
              <span>Continue Now</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

