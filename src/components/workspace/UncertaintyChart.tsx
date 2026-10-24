'use client';

import React, { useState } from 'react';
import { TrendingUp, Sliders } from 'lucide-react';
import { SweepPoint } from '@/types';
import { useChartTheme } from '@/lib/chart-theme';

interface UncertaintyChartProps {
  points?: SweepPoint[];
  slo?: number;
  nominal?: number;
  worst?: number;
  violations?: number;
  sensitivity?: Record<string, number>;
}

export function UncertaintyChart({
  points = [],
  slo = 45,
  nominal = 18,
  worst = 49.5,
  violations = 0,
  sensitivity = {},
}: UncertaintyChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<SweepPoint | null>(null);
  const chart = useChartTheme();

  if (!points || points.length === 0) {
    return (
      <div className="h-[360px] flex items-center justify-center rounded-xl border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark text-xs px-6 text-center">
        No sweep data available. Run an investigation to generate the uncertainty envelope.
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

  const scaleX = (val: number) => padding.left + ((val - minX) / (maxX - minX || 1)) * innerWidth;
  const scaleY = (val: number) =>
    padding.top + innerHeight - ((val - minLatency) / (maxLatency - minLatency || 1)) * innerHeight;

  // Build SVG path
  const pathD = points.reduce((acc, p, idx) => {
    const x = scaleX(p.sample);
    const y = scaleY(p.latency_ms);
    return idx === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
  }, '');

  const areaD = `${pathD} L ${scaleX(maxX)} ${scaleY(minLatency)} L ${scaleX(minX)} ${scaleY(minLatency)} Z`;

  const sloY = scaleY(slo);

  return (
    <div className="flex flex-col h-[360px] rounded-xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark p-4 relative overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <TrendingUp className="w-4 h-4 text-cobalt" />
          <h3 className="text-xs font-semibold tracking-tight text-ink dark:text-ink-dark">
            Uncertainty sweep envelope
          </h3>
        </div>
        <div className="flex items-center gap-x-3 text-[11px] text-muted-fg dark:text-muted-dark">
          <span className="flex items-center space-x-1.5">
            <span className="w-3 h-0.5 inline-block" style={{ backgroundColor: chart.cyan }} />
            <span>Sweep curve</span>
          </span>
          <span className="flex items-center space-x-1.5" style={{ color: chart.abstain }}>
            <span
              className="w-3 border-t-2 border-dashed inline-block"
              style={{ borderColor: chart.abstain }}
            />
            <span>SLO {slo}ms</span>
          </span>
        </div>
      </div>

      {/* SVG Chart Area */}
      <div className="relative flex-1">
        <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
          <defs>
            <linearGradient id="areaGradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor={chart.cyan} stopOpacity={chart.isDark ? 0.35 : 0.22} />
              <stop offset="100%" stopColor={chart.cyan} stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="lineGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor={chart.cobalt} />
              <stop offset="70%" stopColor={chart.cyan} />
              <stop offset="100%" stopColor={violations > 0 ? chart.abstain : chart.accept} />
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
                  stroke={chart.grid}
                  strokeDasharray="3 3"
                />
                <text
                  x={padding.left - 8}
                  y={y + 3}
                  textAnchor="end"
                  fill={chart.axisTick}
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
            stroke={chart.abstain}
            strokeWidth="1.8"
            strokeDasharray="4 4"
          />
          <text
            x={width - padding.right + 4}
            y={sloY + 3}
            fill={chart.abstain}
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
                  <circle
                    cx={cx}
                    cy={cy}
                    r="7"
                    fill="none"
                    stroke={chart.abstain}
                    strokeWidth="1.2"
                    opacity="0.6"
                    className="animate-ping"
                  />
                )}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isHovered ? 6 : isViolated ? 4.5 : 3.5}
                  fill={isViolated ? chart.abstain : chart.cyan}
                  stroke={chart.surface}
                  strokeWidth="1.5"
                />
              </g>
            );
          })}

          {/* X Axis labels */}
          <text
            x={scaleX(1)}
            y={height - 12}
            fill={chart.axisTick}
            fontSize="10"
            fontFamily="monospace"
          >
            Sample #1
          </text>
          <text
            x={scaleX(maxX / 2)}
            y={height - 12}
            textAnchor="middle"
            fill={chart.axisTick}
            fontSize="10"
            fontFamily="monospace"
          >
            Variation sweep samples ({points.length} evaluations)
          </text>
          <text
            x={scaleX(maxX)}
            y={height - 12}
            textAnchor="end"
            fill={chart.axisTick}
            fontSize="10"
            fontFamily="monospace"
          >
            Sample #{maxX}
          </text>
        </svg>

        {/* Hover Tooltip */}
        {hoveredPoint && (
          <div
            className="absolute z-20 pointer-events-none bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark p-2.5 rounded-lg shadow-elevation text-[11px] font-mono text-ink dark:text-ink-dark -translate-x-1/2 -translate-y-full"
            style={{
              left: `${(scaleX(hoveredPoint.sample) / width) * 100}%`,
              top: `${(scaleY(hoveredPoint.latency_ms) / height) * 100 - 8}%`,
            }}
          >
            <div className="flex items-center justify-between gap-3 font-semibold border-b border-hairline dark:border-hairline-dark pb-1 mb-1">
              <span>Sample #{hoveredPoint.sample}</span>
              <span className={hoveredPoint.violated ? 'text-rose-abstain' : 'text-emerald-verdict'}>
                {hoveredPoint.violated ? 'SLO BREACH' : 'COMPLIANT'}
              </span>
            </div>
            <div className="space-y-0.5 text-muted-fg dark:text-muted-dark">
              <div>
                Latency:{' '}
                <b className="text-ink dark:text-ink-dark">{hoveredPoint.latency_ms} ms</b>
              </div>
              <div>
                Load Factor: <b>{hoveredPoint.load_factor}x</b>
              </div>
              <div>
                Calibration: <b>{hoveredPoint.latency_factor}x</b>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Sensitivity Breakdown Footer */}
      <div className="pt-2.5 mt-1 border-t border-hairline dark:border-hairline-dark flex flex-wrap items-center justify-between gap-2 text-[11px]">
        <div className="flex items-center space-x-2 text-muted-fg dark:text-muted-dark">
          <Sliders className="w-3.5 h-3.5 text-cobalt" />
          <span>Sensitivity range</span>
        </div>
        <div className="flex items-center gap-x-4">
          <div className="flex items-center space-x-1.5">
            <span className="text-muted-fg dark:text-muted-dark">Latency drift</span>
            <span className="font-semibold tabular-nums text-ink dark:text-ink-dark">
              +{sensitivity['Latency calibration'] ? sensitivity['Latency calibration'].toFixed(1) : '28.3'} ms
            </span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="text-muted-fg dark:text-muted-dark">Load spike</span>
            <span className="font-semibold tabular-nums text-ink dark:text-ink-dark">
              +{sensitivity['Traffic load'] ? (sensitivity['Traffic load'] * 100).toFixed(1) : '15.2'}%
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
export default UncertaintyChart;
