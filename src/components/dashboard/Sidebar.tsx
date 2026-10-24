'use client';

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
  ChevronDown,
  ChevronRight,
  HelpCircle,
  ArrowLeft,
  Sparkles,
} from 'lucide-react';
import { playTick } from '@/lib/sound';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  onBackToLanding?: () => void;
  soundEnabled?: boolean;
}

export function Sidebar({
  activeTab,
  setActiveTab,
  onBackToLanding,
  soundEnabled = false,
}: SidebarProps) {
  const [insightsOpen, setInsightsOpen] = useState(true);
  const [assuranceOpen, setAssuranceOpen] = useState(true);

  const menuItems = [
    { id: 'overview', label: 'Overview Dashboard', icon: LayoutDashboard },
  ];

  const insightsItems = [
    { id: 'decision', label: 'Decision Workspace', icon: Layers, badge: 'Topology' },
    { id: 'trace', label: 'Execution Trace', icon: Clock, badge: 'AgentOps' },
    { id: 'evaluation', label: 'Evaluation Lab', icon: Cpu, badge: '4-Way' },
    { id: 'monitoring', label: 'Monitoring', icon: LineChart, badge: 'Telemetry' },
    { id: 'motion', label: 'Motion & Sync', icon: Waves, badge: 'Rive' },
  ];

  const assuranceItems = [
    { id: 'history', label: 'Audit Trail (Runs)', icon: History },
    { id: 'docs', label: 'Docs & Contracts', icon: FileText },
    { id: 'settings', label: 'Settings & Diag', icon: Settings },
  ];

  const handleTabClick = (tabId: string) => {
    playTick(soundEnabled);
    setActiveTab(tabId);
  };

  return (
    <aside className="w-64 flex-shrink-0 bg-surface dark:bg-surface-dark border-r border-hairline dark:border-hairline-dark flex flex-col justify-between h-screen sticky top-0 z-40 select-none transition-colors">
      <div className="p-4 border-b border-hairline dark:border-hairline-dark space-y-3">
        {/* Brandmark + Back to Landing Button */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2.5">
            <div className="w-7 h-7 rounded-lg bg-cobalt flex items-center justify-center text-white font-mono text-xs font-bold shadow-fine">
              ◈
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-extrabold text-sm tracking-tight text-ink dark:text-ink-dark">
                  FidelityGate
                </span>
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-verdict" />
              </div>
              <p className="text-[11px] text-muted-fg dark:text-muted-dark font-mono tracking-wider uppercase">
                Decision Assurance
              </p>
            </div>
          </div>
        </div>

        {/* Back to Public Landing button */}
        {onBackToLanding && (
          <button
            onClick={() => {
              playTick(soundEnabled);
              onBackToLanding();
            }}
            className="w-full flex items-center justify-between px-3 py-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark hover:border-cobalt/40 text-xs font-medium text-muted-fg dark:text-muted-dark hover:text-cobalt transition-colors group"
          >
            <span className="flex items-center space-x-1.5">
              <ArrowLeft className="w-3.5 h-3.5 group-hover:-translate-x-0.5 transition-transform" />
              <span>Public Landing</span>
            </span>
            <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">ESC</span>
          </button>
        )}

        {/* Quick Search */}
        <div className="relative pt-1">
          <Search className="w-3.5 h-3.5 text-muted-fg dark:text-muted-dark absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search workspaces"
            className="w-full bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark rounded-lg pl-8 pr-8 py-1.5 text-xs text-ink dark:text-ink-dark placeholder:text-muted-fg dark:placeholder:text-muted-dark focus:outline-none focus:border-cobalt transition-colors"
          />
          <kbd className="absolute right-2.5 top-1/2 -translate-y-1/2 text-[11px] font-mono text-muted-fg dark:text-muted-dark bg-surface dark:bg-surface-dark px-1 py-0.2 rounded border border-hairline dark:border-hairline-dark">
            ⌘K
          </kbd>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-5 text-xs">
        <div>
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => handleTabClick(item.id)}
                className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition-all ${
                  isActive
                    ? 'bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt font-semibold shadow-fine'
                    : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-paper dark:hover:bg-paper-dark'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-cobalt' : 'text-muted-fg dark:text-muted-dark'}`} />
                <span>{item.label}</span>
              </button>
            );
          })}
        </div>

        <div>
          <button
            onClick={() => setInsightsOpen(!insightsOpen)}
            className="w-full flex items-center justify-between px-3 mb-1 text-[11px] font-bold tracking-wider text-muted-fg dark:text-muted-dark uppercase font-mono"
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
                    onClick={() => handleTabClick(item.id)}
                    className={`w-full flex items-center justify-between px-3 py-2 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt font-semibold shadow-fine'
                        : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-paper dark:hover:bg-paper-dark'
                    }`}
                  >
                    <div className="flex items-center space-x-2.5">
                      <Icon className={`w-4 h-4 ${isActive ? 'text-cobalt' : 'text-muted-fg dark:text-muted-dark'}`} />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${
                        isActive
                          ? 'bg-cobalt text-white'
                          : 'bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark border border-hairline dark:border-hairline-dark'
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

        <div>
          <button
            onClick={() => setAssuranceOpen(!assuranceOpen)}
            className="w-full flex items-center justify-between px-3 mb-1 text-[11px] font-bold tracking-wider text-muted-fg dark:text-muted-dark uppercase font-mono"
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
                    onClick={() => handleTabClick(item.id)}
                    className={`w-full flex items-center space-x-2.5 px-3 py-2 rounded-lg font-medium transition-all ${
                      isActive
                        ? 'bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt font-semibold shadow-fine'
                        : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-paper dark:hover:bg-paper-dark'
                    }`}
                  >
                    <Icon className={`w-4 h-4 ${isActive ? 'text-cobalt' : 'text-muted-fg dark:text-muted-dark'}`} />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="p-3 border-t border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark/60 space-y-2">
        <div className="flex items-center justify-between text-[11px] text-muted-fg dark:text-muted-dark px-1 font-mono">
          <span className="flex items-center space-x-1">
            <HelpCircle className="w-3.5 h-3.5" />
            <span>Deterministic Engine</span>
          </span>
          <span className="flex items-center space-x-1 text-emerald-verdict font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-verdict animate-pulse" />
            <span>Active</span>
          </span>
        </div>

        <div className="p-2 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark flex items-center space-x-2.5">
          <div className="w-7 h-7 rounded-md bg-cobalt-subtle dark:bg-cobalt-subtle-dark text-cobalt font-bold text-xs flex items-center justify-center font-mono">
            FG
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-xs font-semibold text-ink dark:text-ink-dark truncate">
              Lead Network Architect
            </p>
            <p className="text-[11px] text-muted-fg dark:text-muted-dark truncate">
              FidelityGate Engine v2.4
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
