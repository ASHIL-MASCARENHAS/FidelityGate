'use client';

import React from 'react';
import { Server, Activity, ChevronLeft, ChevronRight, Users, Zap } from 'lucide-react';
import { GateReport, SweepReport, Scenario } from '@/types';

interface LeftTelemetryPanelsProps {
  report?: SweepReport | GateReport | null;
  scenario?: Scenario | null;
}

export function LeftTelemetryPanels({ report, scenario }: LeftTelemetryPanelsProps) {
  // Top 5 sites data (matching Aryaka dashboard)
  const topSites = [
    { name: 'Santa-Cla', util: 92 },
    { name: 'Bangalor', util: 78 },
    { name: 'New-York', util: 64 },
    { name: 'San Jose', util: 38 },
    { name: 'Denver', util: 18 },
  ];

  return (
    <div className="space-y-4">
      {/* Panel 1: Sites Network Status */}
      <div className="aryaka-card p-4 space-y-3">
        <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-100 font-bold text-xs">
          <Server className="w-3.5 h-3.5 text-teal-600" />
          <span>Sites Network Status</span>
        </div>

        <div>
          <div className="flex items-baseline space-x-1.5">
            <span className="text-2xl font-black text-slate-900 dark:text-white font-mono">48</span>
            <span className="text-xs text-slate-400 font-medium">Sites</span>
          </div>

          {/* Segmented Colored Progress Bar */}
          <div className="w-full h-2 rounded-full overflow-hidden flex mt-2 bg-slate-100 dark:bg-slate-800">
            <div className="h-full bg-teal-500 rounded-l-full" style={{ width: '80%' }} />
            <div className="h-full bg-amber-400" style={{ width: '12%' }} />
            <div className="h-full bg-rose-500 rounded-r-full" style={{ width: '8%' }} />
          </div>

          <div className="flex items-center justify-between text-[11px] font-mono mt-2 text-slate-500 dark:text-slate-400">
            <span className="text-teal-600 dark:text-teal-400 font-semibold">• 43 Healthy</span>
            <span className="text-amber-600 dark:text-amber-400 font-semibold">• 3 Warning</span>
            <span className="text-rose-600 dark:text-rose-400 font-semibold">• 2 Errors</span>
          </div>
        </div>
      </div>

      {/* Panel 2: Top 5 Sites Utilization */}
      <div className="aryaka-card p-4 space-y-3">
        <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-100 font-bold text-xs">
          <Activity className="w-3.5 h-3.5 text-teal-600" />
          <span>Top 5 Sites Utilization</span>
        </div>

        {/* Vertical Bar Chart */}
        <div className="h-28 flex items-end justify-between pt-2 px-1 gap-2">
          {topSites.map((site) => (
            <div key={site.name} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
              <div
                className="w-full bg-teal-500 dark:bg-teal-400 hover:bg-teal-600 rounded-t-sm transition-all"
                style={{ height: `${site.util}%` }}
                title={`${site.name}: ${site.util}%`}
              />
              <span className="text-[9px] font-mono text-slate-400 truncate w-full text-center">
                {site.name}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Panel 3: Bandwidth Saved / Counterexample Margin */}
      <div className="aryaka-card p-4 space-y-2 relative">
        <div className="flex items-center justify-between text-xs font-bold text-slate-800 dark:text-slate-100">
          <div className="flex items-center space-x-1.5">
            <Zap className="w-3.5 h-3.5 text-amber-500" />
            <span>Bandwidth Saved</span>
          </div>
          <div className="flex space-x-1">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-300 dark:bg-slate-600" />
          </div>
        </div>

        <div className="flex items-baseline justify-between pt-1">
          <div className="flex items-baseline space-x-1.5 font-mono">
            <span className="text-2xl font-black text-slate-900 dark:text-white">234.42 GB</span>
            <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400">↗ 10%</span>
          </div>
        </div>

        <p className="text-[11px] text-slate-500 dark:text-slate-400 leading-relaxed">
          <b>Bandwidth savings in action:</b> In June, FidelityGate queue optimization saved you approximately 240 GB of buffer traffic — equivalent to 12 hours of HD telemetry.
        </p>

        <div className="flex justify-end space-x-1 pt-1">
          <button className="p-1 rounded border border-slate-200 dark:border-slate-700 text-slate-400 hover:text-slate-600">
            <ChevronLeft className="w-3 h-3" />
          </button>
          <button className="p-1 rounded border border-slate-200 dark:border-slate-700 text-slate-400 hover:text-slate-600">
            <ChevronRight className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Panel 4: Remote Users / Telemetry Ingress */}
      <div className="aryaka-card p-4 space-y-2">
        <div className="flex items-center space-x-2 text-slate-800 dark:text-slate-100 font-bold text-xs mb-1">
          <Users className="w-3.5 h-3.5 text-teal-600" />
          <span>Remote Users</span>
        </div>

        <div className="space-y-2 text-xs">
          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 flex items-center justify-between border border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-[11px] text-slate-400 block">Unique Users (All Regions)</span>
              <span className="font-bold text-slate-900 dark:text-white font-mono text-sm">421 Users</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>

          <div className="p-2.5 rounded-lg bg-slate-50 dark:bg-slate-900/60 flex items-center justify-between border border-slate-100 dark:border-slate-800">
            <div>
              <span className="text-[11px] text-slate-400 block">Failed Sessions (All Regions)</span>
              <span className="font-bold text-rose-600 font-mono text-sm">21 Sessions</span>
            </div>
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
          </div>
        </div>
      </div>
    </div>
  );
}
export default LeftTelemetryPanels;
