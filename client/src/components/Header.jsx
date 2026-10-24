import React, { useState, useEffect } from 'react';
import { Activity, ShieldCheck, Database, Clock, AlertTriangle, Layers, History, Cpu, Settings, LineChart, Waves, Zap, FileText } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, apiHealthy }) {
  const [time, setTime] = useState(new Date().toUTCString().slice(17, 25) + ' UTC');

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(new Date().toUTCString().slice(17, 25) + ' UTC');
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { id: 'decision', label: 'Decision Workspace', icon: Layers, badge: 'Spline 3D' },
    { id: 'trace', label: 'Execution Trace', icon: Clock, badge: 'AgentOps' },
    { id: 'evaluation', label: 'Evaluation Lab', icon: Cpu, badge: '4-Way Baselines' },
    { id: 'monitoring', label: 'Monitoring', icon: LineChart, badge: 'Recharts' },
    { id: 'motion', label: 'Motion & Sync', icon: Waves, badge: 'Rive' },
    { id: 'history', label: 'Run History', icon: History },
    { id: 'settings', label: 'Docs & Context', icon: FileText },
  ];

  return (
    <header className="border-b border-bg-border/80 bg-bg-card/90 backdrop-blur-md sticky top-0 z-50">
      {/* Top Disclosure Alert Banner */}
      <div className="bg-gradient-to-r from-amber-950/40 via-amber-900/30 to-amber-950/40 border-b border-amber-800/40 px-4 py-1.5 flex items-center justify-between text-xs text-amber-300/90 font-mono">
        <div className="flex items-center space-x-2">
          <AlertTriangle className="w-3.5 h-3.5 text-amber-400 animate-pulse" />
          <span className="font-semibold tracking-wider">DEMO DATA — NOT LIVE INFRASTRUCTURE</span>
          <span className="hidden md:inline text-amber-400/60">• Counterexample-Guided Decision Assurance for Agentic Network Operations.</span>
        </div>
        <div className="flex items-center space-x-3 text-[11px]">
          <span className="flex items-center space-x-1">
            <span className={`w-2 h-2 rounded-full ${apiHealthy ? 'bg-emerald-400 shadow-[0_0_8px_#34d399]' : 'bg-rose-500 shadow-[0_0_8px_#f43f5e]'}`} />
            <span className="text-slate-300 font-sans">{apiHealthy ? 'API Online' : 'Connecting API...'}</span>
          </span>
          <span className="text-slate-500">|</span>
          <span className="text-slate-400 flex items-center space-x-1">
            <Clock className="w-3 h-3 text-cyan-400" />
            <span>{time}</span>
          </span>
        </div>
      </div>

      {/* Main Navigation Bar */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        {/* Brand & Eyebrow */}
        <div className="flex items-center space-x-4">
          <div className="relative group cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500/20 via-blue-600/20 to-purple-600/20 border border-cyan-500/40 flex items-center justify-center text-cyan-300 font-black text-xl shadow-[0_0_15px_rgba(84,214,232,0.2)] group-hover:shadow-[0_0_20px_rgba(84,214,232,0.4)] transition-all">
              ◈
            </div>
            <span className="absolute -bottom-1 -right-1 w-3 h-3 bg-emerald-400 border-2 border-[#080d17] rounded-full" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-xs font-mono font-bold tracking-widest text-cyan-400 uppercase">OPERATIONS / DECISION ASSURANCE</span>
              <span className="text-[10px] bg-cyan-950 text-cyan-300 border border-cyan-800/80 rounded-full px-2 py-0.5 font-mono font-semibold">v2.5 PRO</span>
            </div>
            <h1 className="text-xl font-extrabold text-white tracking-tight flex items-center space-x-2">
              <span>FidelityGate</span>
              <span className="text-slate-500 font-normal text-sm">|</span>
              <span className="text-slate-300 text-sm font-medium">Counterexample-Guided Decision Assurance</span>
            </h1>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1 bg-[#09101b] p-1 rounded-xl border border-bg-border/60 overflow-x-auto">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`relative px-3 py-2 rounded-lg text-xs font-semibold flex items-center space-x-1.5 transition-all whitespace-nowrap ${
                  isActive
                    ? 'bg-gradient-to-r from-cyan-500/20 to-blue-500/10 text-cyan-300 border border-cyan-500/40 shadow-[0_0_12px_rgba(84,214,232,0.15)]'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
                }`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? 'text-cyan-400' : 'text-slate-500'}`} />
                <span>{item.label}</span>
                {item.badge && (
                  <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded ${isActive ? 'bg-cyan-950 text-cyan-300 border border-cyan-700' : 'bg-slate-800 text-slate-400'}`}>
                    {item.badge}
                  </span>
                )}
                {isActive && (
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-0.5 bg-cyan-400 rounded-full" />
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
