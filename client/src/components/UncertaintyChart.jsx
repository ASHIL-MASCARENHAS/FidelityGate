import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, TrendingUp, Sliders, Shield } from 'lucide-react';

export default function UncertaintyChart({ points = [], slo = 45, nominal = 18, worst = 49.5, violations = 0, sensitivity = {} }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);

  if (!points || points.length === 0) {
    return (
      <div className="h-[360px] flex items-center justify-center border border-bg-border/60 rounded-2xl bg-bg-card/40 text-slate-500 font-mono text-xs">
        No sweep data available. Run investigation to generate uncertainty envelope.
      </div>
    );
  }

  // Chart dimensions
  const width = 600;
  const height = 260;
  const padding = { top: 25, right: 35, bottom: 45, left: 55 };

  const innerWidth = width - padding.left - padding.right;
  const innerHeight = height - padding.top - padding.bottom;

  // Extents
  const minLatency = Math.min(...points.map((p) => p.latency_ms), nominal) * 0.9;
  const maxLatency = Math.max(...points.map((p) => p.latency_ms), slo, worst) * 1.1;

  const minX = 1;
  const maxX = points.length;

  const scaleX = (val) => padding.left + ((val - minX) / (maxX - minX || 1)) * innerWidth;
  const scaleY = (val) => padding.top + innerHeight - ((val - minLatency) / (maxLatency - minLatency || 1)) * innerHeight;

  // Build SVG path
  const pathD = points.reduce((acc, p, idx) => {
    const x = scaleX(p.sample);
    const y = scaleY(p.latency_ms);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const areaD = `${pathD} L ${scaleX(maxX)} ${scaleY(minLatency)} L ${scaleX(minX)} ${scaleY(minLatency)} Z`;

  const sloY = scaleY(slo);

  return (
    <div className="flex flex-col h-[360px] rounded-2xl bg-[#0b1424] border border-cyan-900/40 p-4 relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-cyan-400" />
          <h3 className="text-xs font-mono font-bold tracking-wider text-slate-200 uppercase">
            Uncertainty Sweep Envelope
          </h3>
        </div>
        <div className="flex items-center space-x-3 text-[11px] font-mono">
          <span className="flex items-center space-x-1 text-slate-400">
            <span className="w-2.5 h-0.5 bg-cyan-400 inline-block" />
            <span>Sweep Curve</span>
          </span>
          <span className="flex items-center space-x-1 text-rose-400 font-semibold">
            <span className="w-3 border-t-2 border-dashed border-rose-500 inline-block" />
            <span>SLO {slo}ms</span>
          </span>
        </div>
      </div>

      {/* SVG Chart Area */}
      <div className="relative flex-1">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#54d6e8" stopOpacity="0.35" />
              <stop offset="100%" stopColor="#54d6e8" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#38bdf8" />
              <stop offset="70%" stopColor="#54d6e8" />
              <stop offset="100%" stopColor={violations > 0 ? '#ff667d' : '#39d3a4'} />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((pct, i) => {
            const y = padding.top + innerHeight * pct;
            const val = maxLatency - (maxLatency - minLatency) * pct;
            return (
              <g key={i}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={width - padding.right}
                  y2={y}
                  stroke="#1c2c42"
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3}
                  textAnchor="end"
                  fill="#64748b"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {val.toFixed(0)}ms
                </text>
              </g>
            );
          })}

          {/* Area Fill */}
          <path d={areaD} fill="url(#areaGradient)" />

          {/* SLO Reference Threshold Line */}
          <line
            x1={padding.left}
            y1={sloY}
            x2={width - padding.right}
            y2={sloY}
            stroke="#ff667d"
            strokeWidth="1.8"
            strokeDasharray="4 4"
          />
          <text
            x={width - padding.right + 4}
            y={sloY + 3}
            fill="#ff667d"
            fontSize="10"
            fontFamily="monospace"
            fontWeight="bold"
          >
            SLO
          </text>

          {/* Sweep Curve */}
          <path d={pathD} fill="none" stroke="url(#lineGradient)" strokeWidth="2.5" />

          {/* Sample Points */}
          {points.map((p) => {
            const cx = scaleX(p.sample);
            const cy = scaleY(p.latency_ms);
            const isViolated = p.violated;
            const isHovered = hoveredPoint && hoveredPoint.sample === p.sample;

            return (
              <g key={p.sample} className="cursor-pointer" onMouseEnter={() => setHoveredPoint(p)}>
                {isViolated && (
                  <circle cx={cx} cy={cy} r="7" fill="none" stroke="#ff667d" strokeWidth="1.2" opacity="0.6" className="animate-ping" />
                )}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : isViolated ? 4.5 : 3.5}
                  fill={isViolated ? '#ff667d' : '#54d6e8'}
                  stroke="#080d17"
                  strokeWidth="1.5"
                />
              </g>
            );
          })}

          {/* X Axis labels */}
          <text x={scaleX(1)} y={height - 12} fill="#64748b" fontSize="10" fontFamily="monospace">
            Sample #1
          </text>
          <text x={scaleX(maxX / 2)} y={height - 12} textAnchor="middle" fill="#64748b" fontSize="10" fontFamily="monospace">
            Variation Sweep Samples ({points.length} evaluations)
          </text>
          <text x={scaleX(maxX)} y={height - 12} textAnchor="end" fill="#64748b" fontSize="10" fontFamily="monospace">
            Sample #{maxX}
          </text>
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute z-20 pointer-events-none bg-[#0a1220]/95 backdrop-blur-md border border-cyan-500/60 p-2.5 rounded-xl shadow-2xl text-[11px] font-mono text-slate-200 -translate-x-1/2 -translate-y-full"
            style={{
              left: `${(scaleX(hoveredPoint.sample) / width) * 100}%`,
              top: `${(scaleY(hoveredPoint.latency_ms) / height) * 100 - 8}%`,
            }}
          >
            <div className="flex items-center justify-between gap-3 font-bold border-b border-slate-800 pb-1 mb-1">
              <span>Sample #{hoveredPoint.sample}</span>
              <span className={hoveredPoint.violated ? 'text-rose-400' : 'text-emerald-400'}>
                {hoveredPoint.violated ? 'SLO BREACH' : 'COMPLIANT'}
              </span>
            </div>
            <div className="space-y-0.5 text-slate-300">
              <div>Latency: <b className="text-cyan-300">{hoveredPoint.latency_ms} ms</b></div>
              <div>Load Factor: <b>{hoveredPoint.load_factor}x</b></div>
              <div>Calibration: <b>{hoveredPoint.latency_factor}x</b></div>
            </div>
          </div>
        )}
      </div>

      {/* Sensitivity Breakdown Footer */}
      <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
        <div className="flex items-center space-x-2 text-slate-400">
          <Sliders className="w-3.5 h-3.5 text-cyan-400" />
          <span>Sensitivity Range:</span>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500">Latency Drift:</span>
            <span className="text-cyan-300 font-semibold">
              +{sensitivity?.['Latency calibration'] ? sensitivity['Latency calibration'].toFixed(1) : '28.3'} ms
            </span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="text-slate-500">Load Spike:</span>
            <span className="text-cyan-300 font-semibold">
              +{sensitivity?.['Traffic load'] ? (sensitivity['Traffic load'] * 100).toFixed(1) : '15.2'}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
