import React from 'react';
import { Settings, Shield, Database, Cpu, Lock, CheckCircle2, AlertTriangle, Key, Terminal, HardDrive } from 'lucide-react';

export default function SettingsDiagnostics({ diagnostics = {} }) {
  const env = diagnostics.environment || {};
  const db = diagnostics.database || {};
  const safety = diagnostics.safety_controls || {};

  return (
    <div className="space-y-6">
      {/* Title Card */}
      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">
          <Settings className="w-4 h-4" />
          <span>System Environment & Safety Policy</span>
        </div>
        <h2 className="text-xl font-extrabold text-white tracking-tight">Settings & Diagnostics</h2>
        <p className="text-xs text-slate-400">
          Operational constraints, digital-twin telemetry adapters, and deterministic verification safeguards.
        </p>
      </div>

      {/* 3 Core Metric Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>LLM Engine Mode</span>
            <Lock className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-xl font-black text-white">
            {safety.llm_api_configured ? 'LLM Enhanced' : 'Deterministic Offline'}
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            {safety.llm_api_configured ? 'External provider connected' : 'Zero external API calls. Fully air-gapped.'}
          </p>
        </div>

        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>Credential Status</span>
            <Key className="w-3.5 h-3.5 text-amber-400" />
          </div>
          <div className="text-xl font-black text-amber-300">
            {safety.llm_api_configured ? 'Configured' : 'Not Configured (Demo)'}
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            No API keys required for synthetic decision assurance.
          </p>
        </div>

        <div className="glass-card p-5 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs font-mono text-slate-400 uppercase">
            <span>SQLite Audit Storage</span>
            <HardDrive className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-xl font-black text-emerald-400 font-mono">
            {db.exists ? 'Connected' : 'Active Memory'}
          </div>
          <p className="text-[11px] text-slate-400 font-mono">
            {db.path ? `Path: ${db.path.slice(-30)}` : 'fidelitygate.db'} ({db.sizeBytes || 0} bytes)
          </p>
        </div>
      </div>

      {/* Safety & Operational Invariants */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-emerald-400" />
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              Safety Controls & Boundaries
            </h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            The decision gate is engineered with zero-drift deterministic semantics. Under no circumstances will a candidate intervention be marked as ACCEPT if uncertainty bounds cross the SLO threshold.
          </p>

          <div className="space-y-2.5 font-mono text-xs">
            <div className="flex items-center space-x-2.5 p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span className="text-slate-200">Offline-capable; zero phone-home calls</span>
            </div>
            <div className="flex items-center space-x-2.5 p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span className="text-slate-200">Read-only infrastructure actions</span>
            </div>
            <div className="flex items-center space-x-2.5 p-2.5 rounded-xl bg-slate-900 border border-slate-800">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
              <span className="text-slate-200">Fail-closed gate semantics</span>
            </div>
          </div>
        </div>

        <div className="glass-panel p-6 rounded-2xl space-y-4">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              Engine Environment
            </h3>
          </div>
          <p className="text-xs text-slate-300 leading-relaxed">
            Full-stack orchestration connecting React, Three.js, Express, and Python digital twin queueing models.
          </p>

          <div className="space-y-2 text-xs font-mono">
            <div className="flex justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Node Runtime:</span>
              <span className="text-cyan-300 font-bold">{env.nodeVersion || 'v25.x'}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Platform OS:</span>
              <span className="text-slate-200">{env.platform || 'Windows'}</span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Memory RSS:</span>
              <span className="text-slate-200">
                {env.memoryUsage ? `${Math.round(env.memoryUsage.rss / 1024 / 1024)} MB` : '42 MB'}
              </span>
            </div>
            <div className="flex justify-between p-2 rounded-lg bg-slate-900 border border-slate-800">
              <span className="text-slate-400">Server Uptime:</span>
              <span className="text-slate-200">{env.uptimeSeconds || 0} seconds</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
