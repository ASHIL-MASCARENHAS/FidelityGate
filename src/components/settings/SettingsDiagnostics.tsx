'use client';

import React from 'react';
import {
  Settings,
  Shield,
  Lock,
  Key,
  Terminal,
  HardDrive,
  CheckCircle2,
  Volume2,
  VolumeX,
  Sun,
  Moon,
  Sparkles,
  Zap,
} from 'lucide-react';
import { DiagnosticInfo } from '@/types';
import { playTick, playConfirmation } from '@/lib/sound';

interface SettingsDiagnosticsProps {
  diagnostics?: DiagnosticInfo | null;
  theme?: 'light' | 'dark';
  setTheme?: (t: 'light' | 'dark') => void;
  soundEnabled?: boolean;
  setSoundEnabled?: (s: boolean) => void;
  motionReduced?: boolean;
  setMotionReduced?: (m: boolean) => void;
}

export function SettingsDiagnostics({
  diagnostics,
  theme = 'light',
  setTheme,
  soundEnabled = false,
  setSoundEnabled,
  motionReduced = false,
  setMotionReduced,
}: SettingsDiagnosticsProps) {
  const env = diagnostics?.environment || {};
  const db = diagnostics?.database || {};
  const safety = diagnostics?.safety_controls || {};

  return (
    <div className="space-y-6">
      {/* Title Card */}
      <div className="editorial-card p-6">
        <div className="flex items-center space-x-2 t-eyebrow text-cobalt mb-2">
          <Settings className="w-4 h-4" />
          <span>System Environment &amp; Preferences</span>
        </div>
        <h2 className="text-lg font-semibold text-ink dark:text-ink-dark tracking-tight">
          Settings &amp; Diagnostics
        </h2>
        <p className="text-xs text-muted-fg dark:text-muted-dark">
          Interface preferences, operational constraints, digital-twin telemetry adapters, and deterministic verification safeguards.
        </p>
      </div>

      {/* Engineering Interface Preferences */}
      <div className="editorial-card p-6 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-hairline dark:border-hairline-dark">
          <div className="flex items-center space-x-2 t-panel-title">
            <Sparkles className="w-4 h-4 text-cobalt" />
            <span>Interface Controls &amp; Feedback</span>
          </div>
          <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">User Config</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Theme Preference */}
          <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-muted-fg dark:text-muted-dark uppercase">Color Theme</span>
              {theme === 'dark' ? (
                <Moon className="w-3.5 h-3.5 text-muted-fg" />
              ) : (
                <Sun className="w-3.5 h-3.5 text-amber-warning" />
              )}
            </div>
            <div>
              <span className="text-sm font-bold text-ink dark:text-ink-dark block">
                {theme === 'dark' ? 'Dark Mode' : 'Light Mode'}
              </span>
              <span className="text-[11px] text-muted-fg dark:text-muted-dark">
                {theme === 'dark' ? 'Deep ink & charcoal' : 'Warm off-white & ivory'}
              </span>
            </div>
            {setTheme && (
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    setTheme('light');
                  }}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    theme === 'light'
                      ? 'bg-cobalt text-white border-cobalt'
                      : 'bg-surface dark:bg-surface-dark border-hairline dark:border-hairline-dark text-muted-fg'
                  }`}
                >
                  Light
                </button>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    setTheme('dark');
                  }}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    theme === 'dark'
                      ? 'bg-cobalt text-white border-cobalt'
                      : 'bg-surface dark:bg-surface-dark border-hairline dark:border-hairline-dark text-muted-fg'
                  }`}
                >
                  Dark
                </button>
              </div>
            )}
          </div>

          {/* Sound Preference */}
          <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-muted-fg dark:text-muted-dark uppercase">Interface Sounds</span>
              {soundEnabled ? (
                <Volume2 className="w-3.5 h-3.5 text-cobalt" />
              ) : (
                <VolumeX className="w-3.5 h-3.5 text-muted-fg" />
              )}
            </div>
            <div>
              <span className="text-sm font-bold text-ink dark:text-ink-dark block">
                {soundEnabled ? 'Enabled' : 'Disabled (Default)'}
              </span>
              <span className="text-[11px] text-muted-fg dark:text-muted-dark">
                Synthesized Web Audio API ticks
              </span>
            </div>
            <div className="flex gap-2 pt-1">
              {setSoundEnabled && (
                <button
                  onClick={() => {
                    const next = !soundEnabled;
                    setSoundEnabled(next);
                    if (next) playConfirmation(true);
                  }}
                  className="flex-1 py-1.5 rounded-lg text-xs font-medium border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark text-ink dark:text-ink-dark hover:border-cobalt transition-colors"
                >
                  {soundEnabled ? 'Mute Audio' : 'Enable Audio'}
                </button>
              )}
              {soundEnabled && (
                <button
                  onClick={() => playTick(true)}
                  className="px-2.5 py-1.5 rounded-lg text-xs font-medium bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt hover:bg-cobalt hover:text-white transition-colors"
                  title="Test shutter click"
                >
                  Test Tick
                </button>
              )}
            </div>
          </div>

          {/* Motion Preference */}
          <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-muted-fg dark:text-muted-dark uppercase">Motion Sensitivity</span>
              <Zap className="w-3.5 h-3.5 text-cobalt" />
            </div>
            <div>
              <span className="text-sm font-bold text-ink dark:text-ink-dark block">
                {motionReduced ? 'Reduced Motion' : 'Standard Motion'}
              </span>
              <span className="text-[11px] text-muted-fg dark:text-muted-dark">
                Complies with WCAG 2.2 AA
              </span>
            </div>
            {setMotionReduced && (
              <div className="flex gap-2 pt-1">
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    setMotionReduced(false);
                  }}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    !motionReduced
                      ? 'bg-cobalt text-white border-cobalt'
                      : 'bg-surface dark:bg-surface-dark border-hairline dark:border-hairline-dark text-muted-fg'
                  }`}
                >
                  Full Motion
                </button>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    setMotionReduced(true);
                  }}
                  className={`flex-1 py-1.5 rounded-lg text-xs font-medium border transition-colors ${
                    motionReduced
                      ? 'bg-cobalt text-white border-cobalt'
                      : 'bg-surface dark:bg-surface-dark border-hairline dark:border-hairline-dark text-muted-fg'
                  }`}
                >
                  Reduced
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 3 Core Backend Metric Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="editorial-card p-5 space-y-2">
          <div className="flex items-center justify-between t-eyebrow">
            <span>LLM Engine Mode</span>
            <Lock className="w-3.5 h-3.5 text-cobalt" />
          </div>
          <div className="text-xl font-semibold text-ink dark:text-ink-dark t-metric">
            {safety.llm_api_configured ? 'LLM Enhanced' : 'Deterministic Offline'}
          </div>
          <p className="text-[11px] text-muted-fg dark:text-muted-dark font-mono">
            {safety.llm_api_configured
              ? 'External LLM provider configured'
              : 'Zero external API calls. Fully air-gapped deterministic core.'}
          </p>
        </div>

        <div className="editorial-card p-5 space-y-2">
          <div className="flex items-center justify-between t-eyebrow">
            <span>Credential Status</span>
            <Key className="w-3.5 h-3.5 text-amber-warning" />
          </div>
          <div className="text-xl font-semibold text-amber-warning t-metric">
            {safety.llm_api_configured ? 'Configured' : 'Not Required (Deterministic)'}
          </div>
          <p className="text-[11px] text-muted-fg dark:text-muted-dark font-mono">
            Deterministic digital twin does not require external API keys.
          </p>
        </div>

        <div className="editorial-card p-5 space-y-2">
          <div className="flex items-center justify-between t-eyebrow">
            <span>SQLite Audit Storage</span>
            <HardDrive className="w-3.5 h-3.5 text-emerald-verdict" />
          </div>
          <div className="text-xl font-semibold text-emerald-verdict t-metric">
            {db.exists ? 'Connected' : diagnostics ? 'Database Not Found' : 'Checking...'}
          </div>
          <p className="text-[11px] text-muted-fg dark:text-muted-dark font-mono truncate">
            {db.path ? `Path: ...${db.path.slice(-25)}` : 'fidelitygate.db'} ({db.sizeBytes !== undefined ? `${db.sizeBytes} bytes` : 'checking...'})
          </p>
        </div>
      </div>

      {/* Safety & Operational Invariants */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="editorial-card p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-emerald-verdict" />
            <h3 className="t-panel-title">
              Safety Controls &amp; Boundaries
            </h3>
          </div>
          <p className="text-xs text-muted-fg dark:text-muted-dark leading-relaxed">
            The decision gate is engineered with zero-drift deterministic semantics. Under no circumstances will a candidate intervention be marked as ACCEPT if uncertainty bounds cross the SLO threshold.
          </p>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="flex items-center space-x-2.5 p-2.5 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <CheckCircle2 className="w-4 h-4 text-emerald-verdict flex-shrink-0" />
              <span className="text-ink dark:text-ink-dark">Offline-capable; zero external phone-home</span>
            </div>
            <div className="flex items-center space-x-2.5 p-2.5 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <CheckCircle2 className="w-4 h-4 text-emerald-verdict flex-shrink-0" />
              <span className="text-ink dark:text-ink-dark">Read-only infrastructure diagnostics</span>
            </div>
            <div className="flex items-center space-x-2.5 p-2.5 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <CheckCircle2 className="w-4 h-4 text-emerald-verdict flex-shrink-0" />
              <span className="text-ink dark:text-ink-dark">Fail-closed gate semantics</span>
            </div>
          </div>
        </div>

        <div className="editorial-card p-6 space-y-4">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-cobalt" />
            <h3 className="t-panel-title">
              Engine Environment
            </h3>
          </div>
          <p className="text-xs text-muted-fg dark:text-muted-dark leading-relaxed">
            Next.js App Router orchestration connecting Three.js, Recharts, Framer Motion, and Python digital twin queueing models.
          </p>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between p-2 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <span className="text-muted-fg dark:text-muted-dark">Node Runtime:</span>
              <span className="text-cobalt font-bold">{env.nodeVersion || 'Unavailable'}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <span className="text-muted-fg dark:text-muted-dark">Platform OS:</span>
              <span className="text-ink dark:text-ink-dark">{env.platform || 'Unavailable'}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <span className="text-muted-fg dark:text-muted-dark">Memory RSS:</span>
              <span className="text-ink dark:text-ink-dark">
                {env.memoryUsage?.rss ? `${Math.round(env.memoryUsage.rss / 1024 / 1024)} MB` : 'Unavailable'}
              </span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark">
              <span className="text-muted-fg dark:text-muted-dark">Server Uptime:</span>
              <span className="text-ink dark:text-ink-dark">
                {env.uptimeSeconds !== undefined ? `${env.uptimeSeconds} seconds` : 'Unavailable'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default SettingsDiagnostics;
