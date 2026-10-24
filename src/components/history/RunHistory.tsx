'use client';

import React, { useState } from 'react';
import { History, Search, ShieldCheck, AlertTriangle, XCircle, FileJson, Copy, Check, Database, ExternalLink } from 'lucide-react';
import { RunRecord } from '@/types';

interface RunHistoryProps {
  runs?: RunRecord[];
  onRefresh?: () => void;
  onSelectRun?: (run: RunRecord) => void;
  loading?: boolean;
}

export function RunHistory({ runs = [], onRefresh, onSelectRun, loading }: RunHistoryProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [selectedRun, setSelectedRun] = useState<RunRecord | null>(null);
  const [copied, setCopied] = useState(false);

  const safeRuns = Array.isArray(runs) ? runs : [];

  // Filter runs
  const filteredRuns = safeRuns.filter((run) => {
    const name = run.scenario_name || '';
    const id = run.scenario_id || '';
    const reason = run.reason || '';
    const matchesSearch =
      name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      reason.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterDecision === 'ALL' || run.decision === filterDecision;
    return matchesSearch && matchesFilter;
  });

  const handleCopyJson = (obj: unknown) => {
    navigator.clipboard.writeText(JSON.stringify(obj, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLoadRun = (run: RunRecord) => {
    if (onSelectRun) {
      onSelectRun(run);
    }
    setSelectedRun(null);
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="editorial-card p-6 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 t-eyebrow text-cobalt mb-2">
            <Database className="w-4 h-4" />
            <span>SQLite Persistent Audit Trail</span>
          </div>
          <h2 className="text-lg font-semibold text-ink dark:text-ink-dark tracking-tight">
            Investigation &amp; Workflow Run History
          </h2>
          <p className="text-xs text-muted-fg dark:text-muted-dark">
            Auditable, immutable decision log saved directly to fidelitygate.db. Select any past run to restore its context across all tabs.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-muted-fg dark:text-muted-dark absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search scenarios or reasons..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark rounded-lg pl-9 pr-3.5 py-2 text-xs text-ink dark:text-ink-dark placeholder:text-muted-fg dark:placeholder:text-muted-dark focus:outline-none focus:border-cobalt w-56 md:w-64"
            />
          </div>

          {/* Decision Filter Tabs */}
          <div className="flex items-center space-x-1 bg-paper dark:bg-paper-dark p-1 rounded-lg border border-hairline dark:border-hairline-dark">
            {['ALL', 'ACCEPT', 'GATHER_EVIDENCE', 'ABSTAIN'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterDecision(tab)}
                className={`px-3 py-1.5 rounded-md text-[11px] font-mono font-semibold transition-all ${
                  filterDecision === tab
                    ? 'bg-cobalt text-white shadow-fine'
                    : 'text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                }`}
              >
                {tab.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2.5 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:border-cobalt transition-colors shadow-fine"
            title="Refresh Runs from Database"
            aria-label="Refresh runs"
          >
            <History className={`w-4 h-4 ${loading ? 'animate-spin text-cobalt' : ''}`} />
          </button>
        </div>
      </div>

      {/* Runs Table */}
      <div className="editorial-card rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-paper dark:bg-paper-dark/80 border-b border-hairline dark:border-hairline-dark t-eyebrow">
              <tr>
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Scenario</th>
                <th className="py-3 px-4">Gate Decision</th>
                <th className="py-3 px-4">Worst Latency</th>
                <th className="py-3 px-4">SLO Violations</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-hairline dark:divide-hairline-dark font-mono">
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-muted-fg dark:text-muted-dark font-sans">
                    {safeRuns.length === 0
                      ? 'No runs recorded in fidelitygate.db yet. Execute an investigation or workflow.'
                      : 'No runs match the filter criteria.'}
                  </td>
                </tr>
              ) : (
                filteredRuns.map((r) => {
                  const isAccept = r.decision === 'ACCEPT';
                  const isEvidence = r.decision === 'GATHER_EVIDENCE';
                  const badgeClass = isAccept
                    ? 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark text-emerald-verdict border-emerald-verdict/30'
                    : isEvidence
                    ? 'bg-amber-warning-subtle dark:bg-amber-warning-dark text-amber-warning border-amber-warning/30'
                    : 'bg-rose-abstain-subtle dark:bg-rose-abstain-dark text-rose-abstain border-rose-abstain/30';

                  const rep = r.report || {};

                  return (
                    <tr
                      key={r.id}
                      className="hover:bg-paper dark:hover:bg-paper-dark/60 transition-colors group cursor-pointer"
                      onClick={() => setSelectedRun(r)}
                    >
                      <td className="py-3.5 px-4 font-bold text-cobalt">#{r.id}</td>
                      <td className="py-3.5 px-4 text-muted-fg dark:text-muted-dark text-[11px]">
                        {r.created_at
                          ? new Date(r.created_at).toISOString().replace('T', ' ').slice(0, 19)
                          : '—'}
                      </td>
                      <td className="py-3.5 px-4 font-sans">
                        <div className="font-semibold text-ink dark:text-ink-dark">{r.scenario_name}</div>
                        <div className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">{r.scenario_id}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[11px] font-bold border ${badgeClass}`}
                        >
                          {isAccept ? (
                            <ShieldCheck className="w-3 h-3" />
                          ) : isEvidence ? (
                            <AlertTriangle className="w-3 h-3" />
                          ) : (
                            <XCircle className="w-3 h-3" />
                          )}
                          <span>{(r.decision || 'UNKNOWN').replace('_', ' ')}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-ink dark:text-ink-dark">
                        {rep.worst_latency_ms ? `${rep.worst_latency_ms.toFixed(1)} ms` : '—'}
                      </td>
                      <td className="py-3.5 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                            rep.violations && rep.violations > 0
                              ? 'bg-rose-abstain-subtle dark:bg-rose-abstain-dark text-rose-abstain border border-rose-abstain/30'
                              : 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark text-emerald-verdict'
                          }`}
                        >
                          {rep.violations ?? 0} Breaches
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right space-x-2">
                        {onSelectRun && (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleLoadRun(r);
                            }}
                            className="px-2.5 py-1 rounded-lg bg-cobalt hover:bg-cobalt-hover text-white text-[11px] font-sans font-semibold transition-colors shadow-fine"
                            title="Load Run Context Across Tabs"
                          >
                            Load in Workspace
                          </button>
                        )}
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRun(r);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark text-cobalt hover:border-cobalt text-[11px] font-sans font-semibold transition-colors shadow-fine"
                        >
                          Inspect JSON
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Modal / Detail Drawer for Selected Run */}
      {selectedRun && (
        <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark rounded-xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-elevation animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-hairline dark:border-hairline-dark flex items-center justify-between">
              <div>
                <span className="t-eyebrow text-cobalt">
                  Run Audit Inspector · #{selectedRun.id}
                </span>
                <h3 className="text-lg font-bold text-ink dark:text-ink-dark">{selectedRun.scenario_name}</h3>
              </div>
              <button
                onClick={() => setSelectedRun(null)}
                className="w-8 h-8 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 overflow-y-auto space-y-4">
              <div className="p-4 rounded-xl bg-paper dark:bg-paper-dark/60 border border-hairline dark:border-hairline-dark">
                <span className="text-xs text-muted-fg dark:text-muted-dark block mb-1">
                  Gate Decision Reason
                </span>
                <p className="text-xs text-ink dark:text-ink-dark leading-relaxed font-sans">{selectedRun.reason}</p>
              </div>

              {/* JSON Payload Inspector */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-ink dark:text-ink-dark flex items-center space-x-1.5">
                    <FileJson className="w-3.5 h-3.5 text-cobalt" />
                    <span>Gate Report JSON Payload</span>
                  </span>
                  <button
                    onClick={() => handleCopyJson(selectedRun)}
                    className="flex items-center space-x-1 text-xs font-mono text-cobalt bg-cobalt-subtle dark:bg-cobalt-subtle-dark border border-cobalt/30 px-2.5 py-1 rounded-lg"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-verdict" /> : <Copy className="w-3 h-3" />}
                    <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
                  </button>
                </div>
                <pre className="bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark p-4 rounded-xl text-[11px] font-mono text-ink dark:text-ink-dark overflow-x-auto max-h-72">
                  {JSON.stringify(selectedRun, null, 2)}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-hairline dark:border-hairline-dark flex items-center justify-between">
              {onSelectRun && (
                <button
                  onClick={() => handleLoadRun(selectedRun)}
                  className="px-4 py-2 rounded-lg bg-cobalt hover:bg-cobalt-hover text-white text-xs font-semibold font-sans transition-colors flex items-center space-x-1.5"
                >
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Load Run in Workspace</span>
                </button>
              )}
              <button
                onClick={() => setSelectedRun(null)}
                className="px-4 py-2 rounded-lg bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark hover:border-cobalt text-ink dark:text-ink-dark text-xs font-semibold font-sans transition-colors ml-auto"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RunHistory;
