'use client';

import React, { useState, useEffect } from 'react';
import { Play, BarChart2, TrendingUp, RefreshCw, Scale, AlertTriangle, ShieldCheck } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
} from 'recharts';
import { BaselineMetrics } from '@/types';
import { useChartTheme, tooltipStyle } from '@/lib/chart-theme';

interface EvaluationLabProps {
  onEvaluateAll?: () => void;
  benchmarkResults?: Array<{
    scenario_id: string;
    name: string;
    decision: string;
    reason: string;
    worst_latency_ms: number;
  }>;
  loading?: boolean;
}

export function EvaluationLab({
  onEvaluateAll,
  benchmarkResults = [],
  loading,
}: EvaluationLabProps) {
  const [activeTab, setActiveTab] = useState<'baselines' | 'fleet_scenarios'>('baselines');
  const chart = useChartTheme();
  const tip = tooltipStyle(chart);
  const [baselineData, setBaselineData] = useState<Record<string, BaselineMetrics> | null>(null);
  const [loadingBaselines, setLoadingBaselines] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Fetch baseline comparison on mount
  useEffect(() => {
    fetchBaselines();
  }, []);

  const fetchBaselines = async () => {
    setLoadingBaselines(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/baselines');
      if (!res.ok) {
        throw new Error(`Baselines API returned HTTP ${res.status}`);
      }
      const json = await res.json();
      const base = json.data?.baselines || json.baselines;
      if (base && typeof base === 'object' && Object.keys(base).length > 0) {
        setBaselineData(base);
      } else {
        throw new Error('No baseline data returned from benchmark harness');
      }
    } catch (e: any) {
      console.warn('Failed to fetch baselines:', e);
      setErrorMessage(e.message || 'Failed to fetch baselines');
      setBaselineData(null);
    } finally {
      setLoadingBaselines(false);
    }
  };

  // Format Recharts data strictly from real benchmark data (no fabricated fallback)
  const baselinesList: BaselineMetrics[] = baselineData
    ? Object.keys(baselineData).map((k) => baselineData[k])
    : [];

  const results = benchmarkResults.length > 0 ? benchmarkResults : [];

  return (
    <div className="space-y-6">
      {/* Header & View Mode Selector */}
      <div className="editorial-card p-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center space-x-2 t-eyebrow text-cobalt mb-2">
              <Scale className="w-4 h-4" />
              <span>Rigorous Evaluation Harness</span>
            </div>
            <h2 className="text-lg font-semibold text-ink dark:text-ink-dark tracking-tight">
              Evaluation Lab &amp; Baseline Comparisons
            </h2>
            <p className="text-xs text-muted-fg dark:text-muted-dark">
              Proving technical differentiation against standard baselines: unsafe acceptances, false abstentions, latency, and cost.
            </p>
          </div>

          <div className="flex items-center space-x-2">
            <div className="bg-paper dark:bg-paper-dark p-1 rounded-xl border border-hairline dark:border-hairline-dark flex items-center space-x-1">
              <button
                onClick={() => setActiveTab('baselines')}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
                  activeTab === 'baselines'
                    ? 'bg-cobalt text-white shadow-fine'
                    : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                Four-Way Baseline Comparison
              </button>
              <button
                onClick={() => setActiveTab('fleet_scenarios')}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono font-semibold transition-all ${
                  activeTab === 'fleet_scenarios'
                    ? 'bg-cobalt text-white shadow-fine'
                    : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                Fleet Benchmark Matrix
              </button>
            </div>

            {activeTab === 'baselines' ? (
              <button
                onClick={fetchBaselines}
                disabled={loadingBaselines}
                className="p-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark shadow-fine transition-colors"
                title="Refresh Baselines"
                aria-label="Refresh baselines"
              >
                <RefreshCw className={`w-4 h-4 ${loadingBaselines ? 'animate-spin text-cobalt' : ''}`} />
              </button>
            ) : (
              <button
                onClick={onEvaluateAll}
                disabled={loading}
                className="py-2 px-4 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white font-semibold text-xs uppercase font-mono flex items-center space-x-1.5 shadow-fine transition-all"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Run All</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {activeTab === 'baselines' ? (
        <div className="space-y-6">
          {loadingBaselines ? (
            <div className="editorial-card p-12 text-center space-y-3">
              <RefreshCw className="w-6 h-6 animate-spin text-cobalt mx-auto" />
              <p className="text-xs text-muted-fg font-mono">Executing 4-way baseline comparison harness...</p>
            </div>
          ) : baselinesList.length === 0 ? (
            <div className="editorial-card p-12 text-center space-y-3 border border-dashed border-hairline dark:border-hairline-dark rounded-xl">
              <BarChart2 className="w-8 h-8 text-muted-fg mx-auto opacity-50" />
              <h4 className="text-sm font-bold text-ink dark:text-ink-dark">No Benchmark Results Loaded</h4>
              <p className="text-xs text-muted-fg dark:text-muted-dark max-w-md mx-auto">
                {errorMessage || 'Click below to execute the 4-way evaluation harness and compare Nominal-Only, Fixed Safety Margin, Non-Adaptive Sweep, and Adaptive FidelityGate.'}
              </p>
              <button
                onClick={fetchBaselines}
                className="mt-2 px-4 py-2 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white text-xs font-mono font-semibold inline-flex items-center space-x-1.5 shadow-fine"
              >
                <Play className="w-3.5 h-3.5 fill-white" />
                <span>Run 4-Way Evaluation Harness</span>
              </button>
            </div>
          ) : (
            <>
              {/* 4-Way Comparison Cards Grid */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {baselinesList.map((b) => {
                  const isFidelityGate = b.name.includes('Adaptive');
                  return (
                    <div
                      key={b.name}
                      className={`p-5 rounded-xl editorial-card transition-all ${
                        isFidelityGate
                          ? 'border-cobalt ring-1 ring-cobalt/20 bg-cobalt-subtle/30 dark:bg-cobalt-subtle-dark/20'
                          : ''
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark border border-hairline dark:border-hairline-dark uppercase">
                          {isFidelityGate ? 'Our Method' : 'Baseline'}
                        </span>
                        <span
                          className={`text-xs font-mono font-bold ${
                            b.unsafe_acceptance_pct > 0 ? 'text-rose-abstain' : 'text-emerald-verdict'
                          }`}
                        >
                          {b.accuracy_pct}% Accuracy
                        </span>
                      </div>

                      <h4 className="text-sm font-bold text-ink dark:text-ink-dark tracking-tight">{b.name}</h4>
                      <p className="text-[11px] text-muted-fg dark:text-muted-dark mt-1 italic leading-relaxed line-clamp-2">
                        {b.question}
                      </p>

                      <div className="mt-4 pt-3 border-t border-hairline dark:border-hairline-dark space-y-2 text-xs font-mono">
                        <div className="flex justify-between">
                          <span className="text-muted-fg dark:text-muted-dark">Unsafe Accept:</span>
                          <span
                            className={
                              b.unsafe_acceptance_pct > 0
                                ? 'text-rose-abstain font-bold'
                                : 'text-emerald-verdict font-bold'
                            }
                          >
                            {b.unsafe_acceptance_pct}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-fg dark:text-muted-dark">False Abstain:</span>
                          <span
                            className={
                              b.false_abstention_pct > 20
                                ? 'text-amber-warning font-bold'
                                : 'text-ink dark:text-ink-dark font-medium'
                            }
                          >
                            {b.false_abstention_pct}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-muted-fg dark:text-muted-dark">Avg Latency:</span>
                          <span className="text-cobalt font-bold">{b.avg_latency_ms} ms</span>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {/* Recharts Bar Charts for 4-Way Evaluation */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Chart 1: Safety & False Abstention Comparison */}
                <div className="editorial-card p-6">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <BarChart2 className="w-4 h-4 text-cobalt" />
                      <h3 className="t-panel-title">
                        Unsafe Acceptances vs False Abstentions (%)
                      </h3>
                    </div>
                    <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">Lower is Better</span>
                  </div>

                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={baselinesList} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
                        <XAxis
                          dataKey="name"
                          stroke={chart.axis}
                          tick={{ fontSize: 10, fill: chart.axisTick }}
                        />
                        <YAxis
                          stroke={chart.axis}
                          tick={{ fontSize: 10, fill: chart.axisTick }}
                          domain={[0, 60]}
                        />
                        <Tooltip contentStyle={tip} cursor={{ fill: chart.grid, fillOpacity: 0.35 }} />
                        <Legend wrapperStyle={{ fontSize: 11, color: chart.axisTick }} />
                        <Bar
                          dataKey="unsafe_acceptance_pct"
                          name="Unsafe Acceptance (%)"
                          fill={chart.abstain}
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey="false_abstention_pct"
                          name="False Abstention (%)"
                          fill={chart.evidence}
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>

                {/* Chart 2: Latency & Cost Trade-off */}
                <div className="editorial-card p-6">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-4 h-4 text-cobalt" />
                      <h3 className="t-panel-title">
                        Decision Latency (ms) &amp; Simulation Sweeps
                      </h3>
                    </div>
                    <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">Compute Efficiency</span>
                  </div>

                  <div className="h-64 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={baselinesList} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke={chart.grid} />
                        <XAxis
                          dataKey="name"
                          stroke={chart.axis}
                          tick={{ fontSize: 10, fill: chart.axisTick }}
                        />
                        <YAxis stroke={chart.axis} tick={{ fontSize: 10, fill: chart.axisTick }} />
                        <Tooltip contentStyle={tip} cursor={{ fill: chart.grid, fillOpacity: 0.35 }} />
                        <Legend wrapperStyle={{ fontSize: 11, color: chart.axisTick }} />
                        <Bar
                          dataKey="avg_latency_ms"
                          name="Decision latency (ms)"
                          fill={chart.cobalt}
                          radius={[4, 4, 0, 0]}
                        />
                        <Bar
                          dataKey="avg_evaluations"
                          name="Evaluations count"
                          fill={chart.violet}
                          radius={[4, 4, 0, 0]}
                        />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      ) : (
        /* Fleet Scenario Matrix */
        <div className="space-y-5">
          {results.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
              {results.map((res) => {
                const isAccept = res.decision === 'ACCEPT';
                const isEvidence = res.decision === 'GATHER_EVIDENCE';
                const borderColor = isAccept
                  ? 'border-emerald-verdict/40'
                  : isEvidence
                  ? 'border-amber-warning/40'
                  : 'border-rose-abstain/40';

                return (
                  <div key={res.scenario_id} className={`p-5 rounded-xl border ${borderColor} editorial-card space-y-3`}>
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-cobalt">{res.scenario_id}</span>
                      <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-ink dark:text-ink-dark">
                        {res.decision}
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-ink dark:text-ink-dark">{res.name}</h4>
                    <p className="text-[11px] text-muted-fg dark:text-muted-dark line-clamp-2">{res.reason}</p>
                    <div className="pt-2 border-t border-hairline dark:border-hairline-dark text-xs font-mono flex justify-between">
                      <span className="text-muted-fg dark:text-muted-dark">Worst Latency:</span>
                      <span className="text-ink dark:text-ink-dark font-bold">{res.worst_latency_ms} ms</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="editorial-card p-12 text-center space-y-3">
              <Scale className="w-8 h-8 text-muted-fg dark:text-muted-dark mx-auto opacity-50" />
              <h4 className="text-sm font-bold text-ink dark:text-ink-dark">No fleet benchmark trials executed yet</h4>
              <p className="text-xs text-muted-fg dark:text-muted-dark max-w-md mx-auto">
                Click &ldquo;Run All&rdquo; above to dispatch synthetic evaluations across all defined scenarios in the test suite.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default EvaluationLab;
