'use client';

import React, { useState } from 'react';
import { Search, ZoomIn, ZoomOut, RotateCcw, Check } from 'lucide-react';
import { SiteTopologyNode } from '@/types';

interface RadialNetworkTopologyProps {
  onSelectScenario?: (id: string) => void;
  onTriggerDiagnostic?: (scenarioKey: string) => void;
  selectedScenarioKey?: string;
}

export function RadialNetworkTopology({
  onSelectScenario,
  onTriggerDiagnostic,
  selectedScenarioKey,
}: RadialNetworkTopologyProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [zoomLevel, setZoomLevel] = useState(1);
  const [selectedNode, setSelectedNode] = useState<SiteTopologyNode | null>(null);
  const [activeFilters, setActiveFilters] = useState<Record<string, boolean>>({
    onPrem: true,
    virtualOffice: true,
    remoteAccess: true,
    hostedCloud: true,
  });

  // Center hub position
  const cx = 350;
  const cy = 250;

  // Nodes data arranged in radial orbits (matching Aryaka layout)
  const nodes: SiteTopologyNode[] = [
    // On-Premises (Teal / Green)
    { id: 'site-1', name: 'Santa Clara DC', type: 'onPrem', color: '#0d9488', r: 160, angle: -40, status: 'healthy', latency: 14, capacity: '1000 Mbps' },
    { id: 'site-2', name: 'Bangalore Core', type: 'onPrem', color: '#0d9488', r: 180, angle: 25, status: 'warning', latency: 26, capacity: '800 Mbps', scenarioKey: 'wan_congestion', counterexample: '+19.8% traffic burst causes SLO breach (45.5 ms)' },
    { id: 'site-3', name: 'Frankfurt Hub', type: 'onPrem', color: '#0d9488', r: 140, angle: 80, status: 'healthy', latency: 18, capacity: '1000 Mbps' },
    { id: 'site-4', name: 'Singapore Edge', type: 'onPrem', color: '#0d9488', r: 190, angle: 120, status: 'healthy', latency: 22, capacity: '500 Mbps' },
    { id: 'site-5', name: 'London POP', type: 'onPrem', color: '#0d9488', r: 170, angle: -110, status: 'healthy', latency: 16, capacity: '1000 Mbps' },
    { id: 'site-6', name: 'Sydney Branch', type: 'onPrem', color: '#0d9488', r: 210, angle: 160, status: 'healthy', latency: 28, capacity: '400 Mbps' },
    
    // Virtual Office (Purple)
    { id: 'vo-1', name: 'New York VO', type: 'virtualOffice', color: '#8b5cf6', r: 130, angle: -15, status: 'healthy', latency: 12, capacity: '600 Mbps' },
    { id: 'vo-2', name: 'Chicago VO', type: 'virtualOffice', color: '#8b5cf6', r: 150, angle: 55, status: 'healthy', latency: 15, capacity: '600 Mbps' },
    { id: 'vo-3', name: 'Austin VO', type: 'virtualOffice', color: '#8b5cf6', r: 175, angle: 95, status: 'error', latency: 39, capacity: '450 Mbps', scenarioKey: 'fiber_drift', counterexample: 'Fiber latency drift +24ms exceeds 40ms SLO' },
    { id: 'vo-4', name: 'Seattle VO', type: 'virtualOffice', color: '#8b5cf6', r: 200, angle: -75, status: 'healthy', latency: 16, capacity: '600 Mbps' },
    { id: 'vo-5', name: 'Tokyo VO', type: 'virtualOffice', color: '#8b5cf6', r: 220, angle: 140, status: 'healthy', latency: 24, capacity: '500 Mbps' },
    
    // Hosted Cloud (Blue / Cyan)
    { id: 'cloud-1', name: 'AWS US-East', type: 'hostedCloud', color: '#06b6d4', r: 210, angle: -45, status: 'healthy', latency: 11, capacity: '2000 Mbps' },
    { id: 'cloud-2', name: 'Azure West-Europe', type: 'hostedCloud', color: '#06b6d4', r: 220, angle: 65, status: 'warning', latency: 29, capacity: '1500 Mbps', scenarioKey: 'traffic_burst', counterexample: 'Burst load spikes queue buffer' },
    { id: 'cloud-3', name: 'GCP Asia-South', type: 'hostedCloud', color: '#06b6d4', r: 195, angle: -130, status: 'healthy', latency: 17, capacity: '2000 Mbps' },
    
    // Remote User Access Points (Pink)
    { id: 'ap-1', name: 'Remote Gateway EU', type: 'remoteAccess', color: '#ec4899', r: 155, angle: -160, status: 'healthy', latency: 19, capacity: '300 Mbps' },
    { id: 'ap-2', name: 'Remote Gateway APAC', type: 'remoteAccess', color: '#ec4899', r: 185, angle: -95, status: 'healthy', latency: 21, capacity: '300 Mbps' },
  ];

  const filteredNodes = nodes.filter(
    (n) => activeFilters[n.type] && (!searchTerm || n.name.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const toggleFilter = (key: string) => {
    setActiveFilters((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  return (
    <div className="aryaka-card p-5 relative overflow-hidden flex flex-col justify-between h-[620px]">
      {/* Top Search Bar & Tooltip */}
      <div className="flex items-center justify-between mb-2 z-10">
        <div className="relative w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search Sites"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-800 dark:text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
          />
        </div>

        {/* Search Helper Pill */}
        <div className="hidden lg:flex items-center space-x-1.5 px-3 py-1 rounded-lg bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-[11px] text-slate-500 font-mono">
          <span>Demonstration Topology Layout (Illustrative Site Geometry & Display Coordinates)</span>
        </div>
      </div>

      {/* SVG Radial Map Area */}
      <div className="relative flex-1 flex items-center justify-center overflow-hidden">
        <svg
          viewBox="0 0 700 500"
          className="w-full h-full transition-transform duration-300"
          style={{ transform: `scale(${zoomLevel})` }}
        >
          <defs>
            <radialGradient id="centerCoreGradient" cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="#8b5cf6" />
              <stop offset="60%" stopColor="#06b6d4" />
              <stop offset="100%" stopColor="#0d9488" />
            </radialGradient>
            <filter id="glow">
              <feGaussianBlur stdDeviation="3" result="coloredBlur" />
              <feMerge>
                <feMergeNode in="coloredBlur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Concentric Orbital Range Rings */}
          {[130, 160, 190, 220].map((radius, idx) => (
            <circle
              key={idx}
              cx={cx}
              cy={cy}
              r={radius}
              fill="none"
              stroke="#e2e8f0"
              strokeWidth="1"
              strokeDasharray="4 4"
              className="dark:stroke-slate-800"
            />
          ))}

          {/* Radiating Connection Lines & Nodes */}
          {filteredNodes.map((node) => {
            const rad = (node.angle * Math.PI) / 180;
            const x = cx + node.r * Math.cos(rad);
            const y = cy + node.r * Math.sin(rad);

            const isWarning = node.status === 'warning';
            const isError = node.status === 'error';
            const lineColor = isError ? '#ef4444' : isWarning ? '#f59e0b' : '#cbd5e1';

            return (
              <g
                key={node.id}
                className="cursor-pointer group"
                onClick={() => {
                  setSelectedNode(node);
                  if (node.scenarioKey && onSelectScenario) {
                    onSelectScenario(node.scenarioKey);
                  }
                }}
              >
                {/* Connection Line */}
                <line
                  x1={cx}
                  y1={cy}
                  x2={x}
                  y2={y}
                  stroke={lineColor}
                  strokeWidth={isError || isWarning ? 2 : 1.2}
                  className={isError || isWarning ? 'dark:stroke-rose-500' : 'dark:stroke-slate-700'}
                  opacity={0.8}
                />

                {/* Outer halo on hover / fault */}
                {(isError || isWarning) && (
                  <circle
                    cx={x}
                    cy={y}
                    r="16"
                    fill="none"
                    stroke={isError ? '#ef4444' : '#f59e0b'}
                    strokeWidth="1.5"
                    opacity="0.5"
                    className="animate-ping"
                  />
                )}

                {/* Node Circle */}
                <circle
                  cx={x}
                  cy={y}
                  r="11"
                  fill={node.color}
                  stroke="#ffffff"
                  strokeWidth="2.5"
                  className="transition-transform group-hover:scale-125"
                  filter="url(#glow)"
                />

                {/* Status Dot on Node */}
                <circle
                  cx={x + 7}
                  cy={y - 7}
                  r="3.5"
                  fill={isError ? '#ef4444' : isWarning ? '#f59e0b' : '#10b981'}
                  stroke="#ffffff"
                  strokeWidth="1"
                />
              </g>
            );
          })}

          {/* Centerpiece Radial Hub (FidelityGate Core) */}
          <g className="cursor-pointer" onClick={() => setSelectedNode(null)}>
            {/* Outer Pulsing Glow */}
            <circle cx={cx} cy={cy} r="46" fill="#8b5cf6" opacity="0.12" className="animate-pulse" />
            <circle cx={cx} cy={cy} r="38" fill="#06b6d4" opacity="0.18" />
            
            {/* Center Gradient Core */}
            <circle cx={cx} cy={cy} r="30" fill="url(#centerCoreGradient)" filter="url(#glow)" />
            
            {/* White Core Icon */}
            <rect x={cx - 10} y={cy - 10} width="20" height="20" rx="4" fill="#ffffff" />
            <path
              d={`M ${cx - 5} ${cy - 5} L ${cx + 5} ${cy - 5} L ${cx + 5} ${cy + 5} L ${cx - 5} ${cy + 5} Z`}
              fill="#8b5cf6"
            />
          </g>
        </svg>

        {/* Zoom & Pan Controls */}
        <div className="absolute right-3 bottom-14 flex flex-col space-y-1 bg-white dark:bg-slate-800 p-1 rounded-lg border border-slate-200 dark:border-slate-700 shadow-sm z-10">
          <button
            onClick={() => setZoomLevel((z) => Math.min(1.6, z + 0.15))}
            className="p-1.5 text-slate-600 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-slate-50 dark:hover:bg-slate-700 rounded"
            title="Zoom In"
            aria-label="Zoom in"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel((z) => Math.max(0.7, z - 0.15))}
            className="p-1.5 text-slate-600 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-slate-50 dark:hover:bg-slate-700 rounded"
            title="Zoom Out"
            aria-label="Zoom out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoomLevel(1)}
            className="p-1.5 text-slate-600 dark:text-slate-300 hover:text-cyan-600 dark:hover:text-cyan-400 hover:bg-slate-50 dark:hover:bg-slate-700 rounded"
            title="Reset View"
            aria-label="Reset zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>

        {/* Node Detail Popover */}
        {selectedNode && (
          <div className="absolute top-4 right-4 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 p-4 rounded-xl shadow-xl max-w-xs z-20 animate-in fade-in duration-150">
            <div className="flex items-center justify-between pb-2 mb-2 border-b border-slate-100 dark:border-slate-700">
              <div className="flex items-center space-x-2">
                <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: selectedNode.color }} />
                <h4 className="text-xs font-bold text-slate-900 dark:text-white">{selectedNode.name}</h4>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 text-xs"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1.5 text-[11px] font-mono text-slate-600 dark:text-slate-300">
              <div className="flex justify-between">
                <span>Nominal Latency:</span>
                <span className="font-bold text-slate-900 dark:text-white">{selectedNode.latency} ms</span>
              </div>
              <div className="flex justify-between">
                <span>Bandwidth Capacity:</span>
                <span className="font-bold">{selectedNode.capacity}</span>
              </div>
              <div className="flex justify-between">
                <span>Twin Status:</span>
                <span className={`font-bold uppercase ${selectedNode.status === 'healthy' ? 'text-emerald-600' : 'text-amber-600'}`}>
                  {selectedNode.status}
                </span>
              </div>

              {selectedNode.counterexample && (
                <div className="mt-2 p-2 rounded-lg bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 text-[11px] text-amber-800 dark:text-amber-300">
                  <span className="font-bold block mb-0.5">⚠️ Counterexample Fragility:</span>
                  {selectedNode.counterexample}
                </div>
              )}
            </div>

            {selectedNode.scenarioKey && (
              <button
                onClick={() => {
                  if (onTriggerDiagnostic && selectedNode.scenarioKey) {
                    onTriggerDiagnostic(selectedNode.scenarioKey);
                  }
                }}
                className="w-full mt-3 py-1.5 px-3 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-[11px] uppercase tracking-wider font-mono shadow-xs transition-colors"
              >
                Trigger Targeted Diagnostic
              </button>
            )}
          </div>
        )}
      </div>

      {/* Bottom Filter & Status Legend Pills */}
      <div className="pt-3 border-t border-slate-100 dark:border-slate-800/80 flex flex-wrap items-center justify-between gap-2 text-[11px] select-none">
        {/* Category Filter Pills */}
        <div className="flex flex-wrap items-center gap-1.5 font-medium">
          <button
            onClick={() => toggleFilter('onPrem')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border transition-all ${
              activeFilters.onPrem
                ? 'bg-teal-50 dark:bg-teal-950/50 border-teal-300 dark:border-teal-800 text-teal-700 dark:text-teal-300 font-semibold'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-200 text-slate-400'
            }`}
          >
            <Check className="w-3 h-3 text-teal-600" />
            <span>On Premises (21)</span>
          </button>

          <button
            onClick={() => toggleFilter('virtualOffice')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border transition-all ${
              activeFilters.virtualOffice
                ? 'bg-purple-50 dark:bg-purple-950/50 border-purple-300 dark:border-purple-800 text-purple-700 dark:text-purple-300 font-semibold'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-200 text-slate-400'
            }`}
          >
            <Check className="w-3 h-3 text-purple-600" />
            <span>Virtual Office (17)</span>
          </button>

          <button
            onClick={() => toggleFilter('remoteAccess')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border transition-all ${
              activeFilters.remoteAccess
                ? 'bg-pink-50 dark:bg-pink-950/50 border-pink-300 dark:border-pink-800 text-pink-700 dark:text-pink-300 font-semibold'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-200 text-slate-400'
            }`}
          >
            <Check className="w-3 h-3 text-pink-600" />
            <span>Remote User Access Point (2)</span>
          </button>

          <button
            onClick={() => toggleFilter('hostedCloud')}
            className={`flex items-center space-x-1.5 px-2.5 py-1 rounded-md border transition-all ${
              activeFilters.hostedCloud
                ? 'bg-blue-50 dark:bg-blue-950/50 border-blue-300 dark:border-blue-800 text-blue-700 dark:text-blue-300 font-semibold'
                : 'bg-slate-50 dark:bg-slate-800 border-slate-200 text-slate-400'
            }`}
          >
            <Check className="w-3 h-3 text-blue-600" />
            <span>Hosted Cloud (7)</span>
          </button>
        </div>

        {/* Status Badges */}
        <div className="flex items-center space-x-2 font-mono text-[11px]">
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-rose-50 dark:bg-rose-950 text-rose-600 dark:text-rose-400 font-bold border border-rose-200 dark:border-rose-800">
            <span>● Error (2)</span>
          </span>
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950 text-amber-600 dark:text-amber-400 font-bold border border-amber-200 dark:border-amber-800">
            <span>● Warning (3)</span>
          </span>
          <span className="flex items-center space-x-1 px-2 py-0.5 rounded bg-emerald-50 dark:bg-emerald-950 text-emerald-600 dark:text-emerald-400 font-bold border border-emerald-200 dark:border-emerald-800">
            <span>● Healthy (43)</span>
          </span>
        </div>
      </div>
    </div>
  );
}
export default RadialNetworkTopology;
