import React, { useState } from 'react';
import { ShieldAlert, ChevronRight, Activity, Cloud, Layers, CheckCircle2, Sliders } from 'lucide-react';

export default function RightAssurancePanels({ onSelectScenario }) {
  const [activeTab, setActiveTab] = useState('routes'); // 'routes' or 'cloud'
  const [subFilter, setSubFilter] = useState('all');

  const flows = [
    { name: 'Salesforce Transit', flows: '780 Flows', latency: '14 ms', status: 'optimal' },
    { name: 'Zoom Real-Time', flows: '680 Flows', latency: '18 ms', status: 'optimal' },
    { name: 'Workday ERP Core', flows: '680 Flows', latency: '22 ms', status: 'optimal' },
    { name: 'ServiceNow Fabric', flows: '512 Flows', latency: '16 ms', status: 'optimal' },
    { name: 'Google Workspace', flows: '120 Flows', latency: '12 ms', status: 'optimal' },
    { name: 'Atlassian Jira WAN', flows: '320 Flows', latency: '24 ms', status: 'optimal' },
    { name: 'Box Cloud Storage', flows: '45 Flows', latency: '28 ms', status: 'optimal' },
  ];

  return (
    <div className="space-y-4">
      {/* Panel 1: Threats & Violations Prevented (Matching Aryaka screenshot) */}
      <div className="aryaka-card p-4 space-y-3">
        <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-100 font-bold text-xs">
          <ShieldAlert className="w-3.5 h-3.5 text-teal-600" />
          <span>Threats & SLO Breaches Prevented</span>
        </div>

        <div>
          <div className="flex items-baseline space-x-2 font-mono">
            <span className="text-2xl font-black text-slate-900 dark:text-white">4,638</span>
            <span className="text-xs text-slate-400">Total Prevented</span>
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">↗ 72%</span>
          </div>
        </div>

        {/* Breakdown List with Chevrons */}
        <div className="space-y-2 pt-1">
          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <div>
              <span className="text-slate-700 dark:text-slate-200 font-semibold block text-[11px]">
                Uncertainty Drift Violations
              </span>
              <span className="text-[10px] text-slate-400 font-mono">1,112 Prevented <b className="text-emerald-500">↗ 95%</b></span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>

          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <div>
              <span className="text-slate-700 dark:text-slate-200 font-semibold block text-[11px]">
                Counterexample Fragility Tripped
              </span>
              <span className="text-[10px] text-slate-400 font-mono">876 Prevented <b className="text-emerald-500">↗ 82%</b></span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>

          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <div>
              <span className="text-slate-700 dark:text-slate-200 font-semibold block text-[11px]">
                Queue Buffer Overflows
              </span>
              <span className="text-[10px] text-slate-400 font-mono">398 Prevented <b className="text-rose-500">↗ 41%</b></span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>

          <div className="p-2 rounded-lg bg-slate-50 dark:bg-slate-900/60 border border-slate-100 dark:border-slate-800 flex items-center justify-between text-xs cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors">
            <div>
              <span className="text-slate-700 dark:text-slate-200 font-semibold block text-[11px]">
                False Abstentions Restored
              </span>
              <span className="text-[10px] text-slate-400 font-mono">123 Restored <b className="text-amber-500">↗ 34%</b></span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>
        </div>
      </div>

      {/* Panel 2: Top 10 Apps / Flows (Matching Aryaka screenshot) */}
      <div className="aryaka-card p-4 space-y-3">
        <div className="flex items-center justify-between text-xs font-bold text-slate-800 dark:text-slate-100">
          <div className="flex items-center space-x-1.5">
            <Layers className="w-3.5 h-3.5 text-teal-600" />
            <span>Top 10 Flows & Candidate Routes</span>
          </div>
        </div>

        {/* Tab Controls */}
        <div className="flex items-center space-x-1 bg-slate-100 dark:bg-slate-900 p-0.5 rounded-lg border border-slate-200 dark:border-slate-800 text-[11px] font-medium">
          <button
            onClick={() => setActiveTab('routes')}
            className={`flex-1 py-1 rounded text-center transition-all ${
              activeTab === 'routes'
                ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-bold shadow-xs'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            Network Routes
          </button>
          <button
            onClick={() => setActiveTab('cloud')}
            className={`flex-1 py-1 rounded text-center transition-all ${
              activeTab === 'cloud'
                ? 'bg-white dark:bg-slate-800 text-slate-900 dark:text-white font-bold shadow-xs'
                : 'text-slate-500 hover:text-slate-900'
            }`}
          >
            SaaS Fabric
          </button>
        </div>

        {/* Sub-pills */}
        <div className="flex items-center space-x-1.5 text-[10px] font-mono">
          <button
            onClick={() => setSubFilter('all')}
            className={`px-2 py-0.5 rounded-full border ${
              subFilter === 'all'
                ? 'bg-cyan-50 dark:bg-cyan-950 border-cyan-300 text-cyan-700 dark:text-cyan-300 font-bold'
                : 'border-slate-200 text-slate-400'
            }`}
          >
            All Flows
          </button>
          <button
            onClick={() => setSubFilter('genai')}
            className={`px-2 py-0.5 rounded-full border ${
              subFilter === 'genai'
                ? 'bg-cyan-50 dark:bg-cyan-950 border-cyan-300 text-cyan-700 dark:text-cyan-300 font-bold'
                : 'border-slate-200 text-slate-400'
            }`}
          >
            ⚡ Gen AI Probes
          </button>
        </div>

        {/* List of Flows */}
        <div className="space-y-1.5 text-[11px] font-mono divide-y divide-slate-100 dark:divide-slate-800/80">
          {flows.map((item) => (
            <div key={item.name} className="pt-1.5 flex items-center justify-between">
              <span className="font-sans text-slate-800 dark:text-slate-200 font-medium truncate">
                {item.name}
              </span>
              <span className="text-slate-500 font-bold">{item.flows}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
