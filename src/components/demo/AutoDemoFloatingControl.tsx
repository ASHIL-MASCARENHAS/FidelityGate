'use client';

import React from 'react';
import {
  Play,
  Pause,
  ChevronRight,
  Square,
  Sparkles,
  AlertCircle,
  Eye,
  CheckCircle2,
  Clock,
} from 'lucide-react';
import { AutoDemoStep, AutoDemoContext } from '@/types/demo';
import { playTick, playConfirmation } from '@/lib/sound';

interface AutoDemoFloatingControlProps {
  step: AutoDemoStep;
  stepIndex: number;
  totalSteps: number;
  context: AutoDemoContext;
  viewingCountdown: number;
  isPaused: boolean;
  isAwaitingApprovalPause: boolean;
  onNext: () => void;
  onTogglePause: () => void;
  onStop: () => void;
  soundEnabled?: boolean;
  elapsedSeconds?: number;
}

export function AutoDemoFloatingControl({
  step,
  stepIndex,
  totalSteps,
  context,
  viewingCountdown,
  isPaused,
  isAwaitingApprovalPause,
  onNext,
  onTogglePause,
  onStop,
  soundEnabled = false,
  elapsedSeconds,
}: AutoDemoFloatingControlProps) {
  return (
    <aside
      className="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 w-[94%] max-w-2xl px-4 py-3 rounded-2xl bg-surface/95 dark:bg-surface-dark/95 backdrop-blur-md border border-hairline dark:border-hairline-dark shadow-elevation flex flex-wrap items-center justify-between gap-3 text-ink dark:text-ink-dark transition-all select-none"
      role="region"
      aria-label="Auto Demo active presentation controls"
    >
      {/* Left: Step progress and real workflow tag */}
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-8 h-8 rounded-xl bg-cobalt-subtle dark:bg-cobalt-subtle-dark flex items-center justify-center text-cobalt shrink-0">
          <Eye className="w-4 h-4 text-cobalt dark:text-cyan-accent" />
        </div>

        <div className="min-w-0 leading-tight">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-mono font-bold uppercase tracking-wider text-cobalt dark:text-cyan-accent">
              Auto Demo {stepIndex + 1}/{totalSteps}
            </span>
            <span className="text-muted-fg text-xs">·</span>
            <span className="text-xs font-semibold truncate text-ink dark:text-ink-dark">
              {step.tabLabel}
            </span>
          </div>

          <div className="flex items-center gap-2 text-[11px] font-mono text-muted-fg dark:text-muted-dark mt-0.5 truncate">
            <span>Run: {context.selectedWorkflowRunId || 'active'}</span>
            <span>·</span>
            <span className="text-cobalt dark:text-cyan-accent font-semibold">
              {context.currentStage || 'PROCESSING'}
            </span>
          </div>
        </div>
      </div>

      {/* Center: Monotonic tour timer & viewing countdown */}
      <div className="flex items-center gap-2">
        {typeof elapsedSeconds === 'number' && (
          <div className="hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-xs font-mono text-muted-fg dark:text-muted-dark">
            <Clock className="w-3.5 h-3.5 text-cobalt dark:text-cyan-accent" />
            <span>Tour:</span>
            <span className="font-bold text-ink dark:text-ink-dark tabular-nums">
              {Math.floor(elapsedSeconds / 60)}:{(elapsedSeconds % 60).toString().padStart(2, '0')}
            </span>
            <span className="text-[10px] text-muted-fg">/ 2:45</span>
          </div>
        )}

        {isAwaitingApprovalPause ? (
          <div className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-warning-subtle dark:bg-amber-warning-dark border border-amber-warning/30 text-amber-warning text-xs font-semibold animate-pulse">
            <AlertCircle className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Paused at Stage 11: Authorize below or click Next</span>
            <span className="sm:hidden">Paused: Action required</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-cyan-accent animate-ping" />
            <span className="text-muted-fg dark:text-muted-dark">
              {isPaused ? 'Viewing Paused' : 'Section:'}
            </span>
            <span className="font-bold text-ink dark:text-ink-dark tabular-nums">
              {viewingCountdown}s
            </span>
          </div>
        )}
      </div>

      {/* Right: Interactive controls (Pause, Next, Stop) */}
      <div className="flex items-center gap-1.5 shrink-0">
        {!isAwaitingApprovalPause && (
          <button
            onClick={() => {
              playTick(soundEnabled);
              onTogglePause();
            }}
            className="inline-flex items-center gap-1 h-8 px-2.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-xs font-medium text-ink dark:text-ink-dark hover:border-cobalt transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50"
            title={isPaused ? 'Resume countdown' : 'Pause countdown'}
          >
            {isPaused ? (
              <>
                <Play className="w-3 h-3 text-cobalt fill-current" />
                <span className="hidden sm:inline">Resume</span>
              </>
            ) : (
              <>
                <Pause className="w-3 h-3 text-muted-fg" />
                <span className="hidden sm:inline">Pause</span>
              </>
            )}
          </button>
        )}

        <button
          onClick={() => {
            playConfirmation(soundEnabled);
            onNext();
          }}
          className="inline-flex items-center gap-1 h-8 px-3 rounded-lg bg-cobalt hover:bg-cobalt-hover text-white text-xs font-semibold shadow-fine transition-all active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50"
          title="Proceed to next section"
        >
          <span>Next</span>
          <ChevronRight className="w-3.5 h-3.5" />
        </button>

        <button
          onClick={() => {
            playTick(soundEnabled);
            onStop();
          }}
          className="inline-flex items-center justify-center w-8 h-8 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark hover:text-rose-500 hover:border-rose-500/40 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-rose-500/50"
          title="Stop Auto Demo"
          aria-label="Stop Auto Demo"
        >
          <Square className="w-3 h-3 fill-current" />
        </button>
      </div>
    </aside>
  );
}
