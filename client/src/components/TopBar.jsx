import React, { useState } from 'react';
import { Calendar, ChevronDown, Bell, Moon, Sun, AlertTriangle, AlertCircle, ShieldAlert } from 'lucide-react';

export default function TopBar({ activeTitle = 'Overview Dashboard', theme, setTheme, onSelectScenario }) {
  const [timeRange, setTimeRange] = useState('Last 24 Hours');

  return (
    <div className="bg-white dark:bg-[#0c1424] border-b border-slate-200 dark:border-slate-800 sticky top-0 z-30 select-none">
      {/* Top Header Row */}
      <div className="px-6 py-3 flex items-center justify-between border-b border-slate-100 dark:border-slate-800/60">
        <div>
          <h1 className="text-lg font-bold text-slate-900 dark:text-white tracking-tight">
            {activeTitle}
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          {/* Time Range Selector */}
          <div className="relative">
            <button className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-xs font-medium text-slate-700 dark:text-slate-200 hover:bg-slate-100 transition-colors">
              <Calendar className="w-3.5 h-3.5 text-slate-500" />
              <span>{timeRange}</span>
              <ChevronDown className="w-3 h-3 text-slate-400" />
            </button>
          </div>

          {/* Theme Mode Toggle */}
          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-1.5 rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-300 hover:text-slate-900 transition-colors"
            title="Toggle Light/Dark Theme"
          >
            {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
          </button>
        </div>
      </div>

      {/* Horizontal Alert Marquee Banner (Matching Aryaka screenshot top alert bar) */}
      <div className="px-6 py-1.5 bg-slate-50/80 dark:bg-slate-900/60 border-b border-slate-100 dark:border-slate-800/80 flex items-center justify-between text-xs overflow-x-auto gap-4">
        <div className="flex items-center space-x-3 flex-shrink-0">
          {/* Alert 1 */}
          <div className="flex items-center space-x-1.5 text-slate-600 dark:text-slate-300">
            <span className="text-slate-400 text-[11px]">-Loss is higher than 30% →</span>
          </div>

          {/* Alert 2: Critical */}
          <div className="flex items-center space-x-1.5 bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-800/60 px-2 py-0.5 rounded-md text-[11px]">
            <span className="font-bold text-rose-600 dark:text-rose-400">● Critical</span>
            <span className="text-slate-700 dark:text-slate-200 font-medium">
              WAN-042 | Counterexample: +19.8% load burst breaches SLO (45.5 ms) →
            </span>
          </div>

          {/* Alert 3: Major */}
          <div className="flex items-center space-x-1.5 bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800/60 px-2 py-0.5 rounded-md text-[11px]">
            <span className="font-bold text-amber-600 dark:text-amber-400">● Major</span>
            <span className="text-slate-700 dark:text-slate-200 font-medium">
              FIBER-017 | Latency calibration drift +24ms exceeds 40ms SLO →
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2 flex-shrink-0 text-[11px]">
          <span className="text-rose-600 dark:text-rose-400 font-bold">• Critical</span>
          <button className="text-cyan-600 dark:text-cyan-400 font-semibold hover:underline">
            See All (8)
          </button>
        </div>
      </div>
    </div>
  );
}
