import React, { useState } from 'react';
import {
  LayoutDashboard,
  Layers,
  Clock,
  Cpu,
  LineChart,
  Waves,
  History,
  FileText,
  Settings,
  Search,
  Shield,
  Radio,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  HelpCircle,
  User,
  Zap,
  Globe
} from 'lucide-react';

export default function Sidebar({ activeTab, setActiveTab }) {
  const [insightsOpen, setInsightsOpen] = useState(true);
  const [assuranceOpen, setAssuranceOpen] = useState(true);

  const menuItems = [
    { id: 'overview', label: 'Overview Dashboard', icon: LayoutDashboard },
  ];

  const insightsItems = [
    { id: 'decision', label: 'Decision Workspace', icon: Layers, badge: 'Spline 3D' },
    { id: 'trace', label: 'Execution Trace', icon: Clock, badge: 'AgentOps' },
    { id: 'evaluation', label: 'Evaluation Lab', icon: Cpu, badge: '4-Way' },
    { id: 'monitoring', label: 'Monitoring', icon: LineChart, badge: 'Recharts' },
    { id: 'motion', label: 'Motion & Sync', icon: Waves, badge: 'Rive' },
  ];

  const assuranceItems = [
    { id: 'history', label: 'Audit Trail (Runs)', icon: History },
    { id: 'docs', label: 'Docs & Contracts', icon: FileText },
    { id: 'settings', label: 'Settings & Diag', icon: Settings },
  ];

  return (
    <aside className="w-64 flex-shrink-0 bg-white dark:bg-[#0c1424] border-r border-slate-200 dark:border-slate-800 flex flex-col justify-between h-screen sticky top-0 z-40 select-none">
      {/* Top Branding & Search */}
      <div className="p-4 border-b border-slate-100 dark:border-slate-800/80">
        <div className="flex items-center space-x-2.5 mb-4">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-600 to-indigo-600 flex items-center justify-center text-white font-black text-base shadow-sm">
            ◈
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-extrabold text-base tracking-tight text-slate-900 dark:text-white">
                FidelityGate
              </span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
            </div>
            <p className="text-[10px] text-slate-400 font-mono tracking-wider uppercase">
              Aryaka Network Assurance
            </p>
          </div>
        </div>

        {/* Quick Search Bar */}
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search"
            className="w-full bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-700/60 rounded-lg pl-8 pr-8 py-1.5 text-xs text-slate-700 dark:text-slate-200 placeholder-slate-400 focus:outline-none focus:border-cyan-500 transition-colors"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[10px] font-mono text-slate-400 bg-white dark:bg-slate-800 px-1 py-0.2 rounded border border-slate-200 dark:border-slate-700">
            ⌘K
          </kbd>
        </div>
      </div>

      {/* Navigation Links (Scrollable) */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5 text-xs">
        {/* Main Item */}
        <div>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition-all ${
                  isActive
                    ? 'bg-slate-100 dark:bg-slate-800/80 text-cyan-600 dark:text-cyan-400 font-semibold shadow-xs'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-400'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        {/* Section: INSIGHTS */}
        <div>
          <button
            onClick={() => setInsightsOpen(!insightsOpen)}
            className="w-full flex items-center justify-between px-3 mb-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase font-mono"
          >
            <span>INSIGHTS</span>
            {insightsOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>

          {insightsOpen && (
            <div className="space-y-0.5">
              {insightsItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-slate-100 dark:bg-slate-800/80 text-cyan-600 dark:text-cyan-400 font-semibold shadow-xs'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-400'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
                        isActive
                          ? 'bg-cyan-100 dark:bg-cyan-950 text-cyan-700 dark:text-cyan-300'
                          : 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400'
                      }`}>
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Section: ASSURANCE & GOVERNANCE */}
        <div>
          <button
            onClick={() => setAssuranceOpen(!assuranceOpen)}
            className="w-full flex items-center justify-between px-3 mb-1 text-[11px] font-bold tracking-wider text-slate-400 uppercase font-mono"
          >
            <span>ASSURANCE & GOVERNANCE</span>
            {assuranceOpen ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
          </button>

          {assuranceOpen && (
            <div className="space-y-0.5">
              {assuranceItems.map((item) => {
                const Icon = item.icon;
                const isActive = activeTab === item.id;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-slate-100 dark:bg-slate-800/80 text-cyan-600 dark:text-cyan-400 font-semibold shadow-xs'
                        : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white hover:bg-slate-50 dark:hover:bg-slate-800/40'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-cyan-600 dark:text-cyan-400' : 'text-slate-400'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Bottom User Card / Support */}
      <div className="p-3 border-t border-slate-100 dark:border-slate-800/80 bg-slate-50/50 dark:bg-[#0a101d] space-y-2">
        <div className="flex items-center justify-between text-[11px] text-slate-500 px-1 font-mono">
          <span className="flex items-center space-x-1">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Support</span>
          </span>
          <span className="flex items-center space-x-1 text-emerald-600 dark:text-emerald-400 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
            <span>Online</span>
          </span>
        </div>

        <div className="p-2 rounded-lg bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700/60 flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-md bg-slate-200 dark:bg-slate-700 text-slate-700 dark:text-slate-200 font-bold text-xs flex items-center justify-center font-mono">
            SK
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate">
              Shahil Kalehbhai
            </p>
            <p className="text-[10px] text-slate-400 truncate">
              Aryaka Networks Inc.
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
