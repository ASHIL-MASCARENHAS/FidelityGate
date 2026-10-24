import React, { useState, useEffect } from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  ReferenceLine,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { LineChart as ChartIcon, TrendingUp, AlertTriangle, ShieldCheck, Play, Pause, RotateCcw, Activity } from 'lucide-react';

export default function FidelityMonitoringRecharts({ runs = [], currentReport, scenario }) {
  // Generate initial simulated epoch series for fidelity over time
  const [epochs, setEpochs] = useState(() => {
    const list = [];
    const baseFidelity = currentReport?.stability_score ? currentReport.stability_score * 100 : 92;
    for (let i = 1; i <= 20; i++) {
      const noise = (Math.sin(i * 0.8) * 3) + ((Math.random() - 0.5) * 4);
      const fid = Math.min(99.5, Math.max(75, baseFidelity + noise));
      list.push({
        epoch: `T-${21 - i}s`,
        fidelity: parseFloat(fid.toFixed(1)),
        upperBound: parseFloat((fid + 2.5).toFixed(1)),
        lowerBound: parseFloat((fid - 3.2).toFixed(1)),
        latencyDev: parseFloat((Math.sin(i * 0.7) * 4.5 + (fid < 90 ? 8.2 : 1.2)).toFixed(1)),
        loadDrift: parseFloat((Math.cos(i * 0.6) * 5.2 + (i % 5 === 0 ? 9.5 : 0)).toFixed(1)),
      });
    }
    return list;
  });

  const [isLive, setIsLive] = useState(true);

  // Live telemetry pulse
  useEffect(() => {
    if (!isLive) return;
    const interval = setInterval(() => {
      setEpochs((prev) => {
        const last = prev[prev.length - 1];
        const nextId = parseInt(last.epoch.replace(/\D/g, '')) - 1 || 1;
        const noise = (Math.random() - 0.48) * 5;
        const fid = Math.min(99.5, Math.max(72, last.fidelity + noise));
        const newPoint = {
          epoch: `T+${Math.floor(Date.now() / 1000) % 60}s`,
          fidelity: parseFloat(fid.toFixed(1)),
          upperBound: parseFloat((fid + 2.2).toFixed(1)),
          lowerBound: parseFloat((fid - 2.8).toFixed(1)),
          latencyDev: parseFloat(((Math.random() - 0.3) * 7.5).toFixed(1)),
          loadDrift: parseFloat(((Math.random() - 0.4) * 8.0).toFixed(1)),
        };
        return [...prev.slice(1), newPoint];
      });
    }, 2000);
    return () => clearInterval(interval);
  }, [isLive]);

  // Outcomes distribution calculated from runs
  const acceptCount = runs.filter((r) => r.decision === 'ACCEPT').length || 8;
  const evidenceCount = runs.filter((r) => r.decision === 'GATHER_EVIDENCE').length || 5;
  const abstainCount = runs.filter((r) => r.decision === 'ABSTAIN').length || 2;

  const outcomeData = [
    { name: 'ACCEPT', value: acceptCount, color: '#39d3a4' },
    { name: 'GATHER_EVIDENCE', value: evidenceCount, color: '#f3b64b' },
    { name: 'ABSTAIN', value: abstainCount, color: '#ff667d' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">
            <ChartIcon className="w-4 h-4" />
            <span>Recharts Analytics Suite</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">Fidelity Monitoring & Telemetry Deviations</h2>
          <p className="text-xs text-slate-400">
            Plotting twin fidelity over time, empirical drift deviations, and historical validation outcomes.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsLive(!isLive)}
            className={`px-3.5 py-2 rounded-xl border text-xs font-mono font-semibold flex items-center space-x-2 transition-all ${
              isLive
                ? 'bg-emerald-950/60 border-emerald-600/60 text-emerald-300 shadow-[0_0_12px_rgba(57,211,164,0.2)]'
                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
            }`}
          >
            {isLive ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
            <span>{isLive ? 'Live Influx Active' : 'Stream Paused'}</span>
          </button>
        </div>
      </div>

      {/* Grid: Fidelity Over Time (Large) */}
      <div className="glass-panel p-6 rounded-2xl">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
              1. Digital-Twin Fidelity Over Time (%)
            </h3>
          </div>
          <div className="flex items-center space-x-3 text-xs font-mono">
            <span className="flex items-center space-x-1 text-cyan-300">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400" />
              <span>Fidelity Index</span>
            </span>
            <span className="flex items-center space-x-1 text-slate-500">
              <span className="w-2.5 h-0.5 bg-slate-500" />
              <span>Confidence Bounds</span>
            </span>
            <span className="flex items-center space-x-1 text-rose-400">
              <span className="w-3 border-t border-dashed border-rose-500" />
              <span>90% Stability Threshold</span>
            </span>
          </div>
        </div>

        <div className="h-72 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={epochs} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <defs>
                <linearGradient id="fidelityGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#54d6e8" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#54d6e8" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#1c2c42" />
              <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <YAxis domain={[65, 100]} stroke="#64748b" tick={{ fontSize: 11, fontFamily: 'monospace' }} />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#0a1220',
                  borderColor: '#294363',
                  borderRadius: '12px',
                  fontSize: '12px',
                  fontFamily: 'monospace',
                }}
              />
              <ReferenceLine y={90} stroke="#ff667d" strokeDasharray="4 4" label={{ value: 'SLO Target (90%)', fill: '#ff667d', fontSize: 10, position: 'insideTopRight' }} />
              <Area type="monotone" dataKey="fidelity" stroke="#54d6e8" strokeWidth={2.5} fillOpacity={1} fill="url(#fidelityGradient)" />
              <Line type="monotone" dataKey="upperBound" stroke="#38bdf8" strokeDasharray="2 2" dot={false} opacity={0.4} />
              <Line type="monotone" dataKey="lowerBound" stroke="#0284c7" strokeDasharray="2 2" dot={false} opacity={0.4} />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Row 2: Deviations Monitoring & Validation Outcomes */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Deviations Monitoring (Span 2) */}
        <div className="lg:col-span-2 glass-panel p-6 rounded-2xl">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Activity className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                2. Deviations from Nominal Target (Δ ms & Load %)
              </h3>
            </div>
            <span className="text-[11px] font-mono text-slate-400">Relative Drift</span>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={epochs} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1c2c42" />
                <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                <YAxis stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0a1220',
                    borderColor: '#294363',
                    borderRadius: '12px',
                    fontSize: '11px',
                    fontFamily: 'monospace',
                  }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
                <ReferenceLine y={0} stroke="#475569" />
                <Bar dataKey="latencyDev" name="Latency Drift (ms)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
                <Bar dataKey="loadDrift" name="Load Drift (%)" fill="#f59e0b" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Validation Outcomes Distribution (Span 1) */}
        <div className="glass-panel p-6 rounded-2xl flex flex-col justify-between">
          <div>
            <div className="flex items-center space-x-2 mb-2">
              <ShieldCheck className="w-4 h-4 text-cyan-400" />
              <h3 className="text-sm font-mono font-bold text-white uppercase tracking-wider">
                3. Validation Outcomes
              </h3>
            </div>
            <p className="text-xs text-slate-400 mb-2">
              Historical distribution of gate decisions across sweeps
            </p>

            <div className="h-44 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={outcomeData}
                    cx="50%"
                    cy="50%"
                    innerRadius={45}
                    outerRadius={68}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {outcomeData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} stroke="#0b1424" strokeWidth={2} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0a1220',
                      borderColor: '#294363',
                      borderRadius: '10px',
                      fontSize: '11px',
                      fontFamily: 'monospace',
                    }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="space-y-1.5 pt-2 border-t border-slate-800 text-xs font-mono">
            {outcomeData.map((d) => (
              <div key={d.name} className="flex items-center justify-between">
                <span className="flex items-center space-x-1.5 text-slate-300">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: d.color }} />
                  <span>{d.name.replace('_', ' ')}</span>
                </span>
                <span className="font-bold text-white">{d.value} runs</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
