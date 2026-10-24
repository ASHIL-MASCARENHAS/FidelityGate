import React, { useState } from 'react';
import { History, Search, Filter, ShieldCheck, AlertTriangle, XCircle, FileJson, Copy, Check, ExternalLink, Calendar, Database } from 'lucide-react';

export default function RunHistory({ runs = [], onRefresh, loading }) {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterDecision, setFilterDecision] = useState('ALL');
  const [selectedRun, setSelectedRun] = useState(null);
  const [copied, setCopied] = useState(false);

  // Filter runs
  const filteredRuns = runs.filter((run) => {
    const matchesSearch =
      run.scenario_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      run.scenario_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      run.reason.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterDecision === 'ALL' || run.decision === filterDecision;
    return matchesSearch && matchesFilter;
  });

  const handleCopyJson = (obj) => {
    navigator.clipboard.writeText(JSON.stringify(obj, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="space-y-6">
      {/* Header & Controls */}
      <div className="glass-panel p-6 rounded-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2 text-cyan-400 font-mono text-xs font-bold uppercase tracking-wider mb-1">
            <Database className="w-4 h-4" />
            <span>SQLite Persistent Audit Trail</span>
          </div>
          <h2 className="text-xl font-extrabold text-white tracking-tight">Investigation Run History</h2>
          <p className="text-xs text-slate-400">Auditable, immutable decision log saved directly to fidelitygate.db</p>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          {/* Search Bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search scenarios or reasons..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-[#09111d] border border-slate-700/80 rounded-xl pl-9 pr-3.5 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 w-56 md:w-64"
            />
          </div>

          {/* Decision Filter Tabs */}
          <div className="flex items-center space-x-1 bg-[#09111d] p-1 rounded-xl border border-slate-800">
            {['ALL', 'ACCEPT', 'GATHER_EVIDENCE', 'ABSTAIN'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterDecision(tab)}
                className={`px-3 py-1.5 rounded-lg text-[11px] font-mono font-semibold transition-all ${
                  filterDecision === tab
                    ? 'bg-slate-800 text-cyan-300 shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {tab.replace('_', ' ')}
              </button>
            ))}
          </div>

          <button
            onClick={onRefresh}
            disabled={loading}
            className="p-2.5 rounded-xl bg-slate-900 border border-slate-700 text-slate-300 hover:text-white hover:border-cyan-500 transition-colors"
            title="Refresh Runs"
          >
            <History className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Runs Table */}
      <div className="glass-panel rounded-2xl overflow-hidden border border-slate-800/80">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#09111d] border-b border-slate-800 font-mono text-slate-400 text-[11px] uppercase tracking-wider">
              <tr>
                <th className="py-3 px-4">Run ID</th>
                <th className="py-3 px-4">Timestamp (UTC)</th>
                <th className="py-3 px-4">Scenario</th>
                <th className="py-3 px-4">Gate Decision</th>
                <th className="py-3 px-4">Worst Latency</th>
                <th className="py-3 px-4">SLO Violations</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {filteredRuns.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-500 font-sans">
                    No runs match the filter criteria. Execute an investigation in the Decision Workspace.
                  </td>
                </tr>
              ) : (
                filteredRuns.map((r) => {
                  const isAccept = r.decision === 'ACCEPT';
                  const isEvidence = r.decision === 'GATHER_EVIDENCE';
                  const badgeClass = isAccept
                    ? 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
                    : isEvidence
                    ? 'bg-amber-950/80 text-amber-300 border-amber-800/80'
                    : 'bg-rose-950/80 text-rose-300 border-rose-800/80';

                  const rep = r.report || {};

                  return (
                    <tr
                      key={r.id}
                      className="hover:bg-slate-850/50 transition-colors group cursor-pointer"
                      onClick={() => setSelectedRun(r)}
                    >
                      <td className="py-3.5 px-4 font-bold text-cyan-400">
                        #{r.id}
                      </td>
                      <td className="py-3.5 px-4 text-slate-300 text-[11px]">
                        {r.created_at ? new Date(r.created_at).toISOString().replace('T', ' ').slice(0, 19) : '—'}
                      </td>
                      <td className="py-3.5 px-4 font-sans">
                        <div className="font-semibold text-white">{r.scenario_name}</div>
                        <div className="text-[10px] font-mono text-slate-400">{r.scenario_id}</div>
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`inline-flex items-center space-x-1.5 px-2.5 py-1 rounded-full text-[10px] font-bold border ${badgeClass}`}>
                          {isAccept ? (
                            <ShieldCheck className="w-3 h-3" />
                          ) : isEvidence ? (
                            <AlertTriangle className="w-3 h-3" />
                          ) : (
                            <XCircle className="w-3 h-3" />
                          )}
                          <span>{r.decision.replace('_', ' ')}</span>
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-slate-200">
                        {rep.worst_latency_ms ? `${rep.worst_latency_ms.toFixed(1)} ms` : '—'}
                      </td>
                      <td className="py-3.5 px-4">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${rep.violations > 0 ? 'bg-rose-950 text-rose-400 border border-rose-800' : 'bg-emerald-950 text-emerald-400'}`}>
                          {rep.violations ?? 0} Breaches
                        </span>
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedRun(r);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-700 text-cyan-300 hover:border-cyan-500 text-[11px] font-sans font-semibold"
                        >
                          View Details
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
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-[#0b1424] border border-cyan-800/80 rounded-2xl max-w-2xl w-full max-h-[85vh] flex flex-col shadow-2xl animate-in zoom-in-95 duration-150">
            {/* Modal Header */}
            <div className="p-5 border-b border-slate-800 flex items-center justify-between">
              <div>
                <span className="text-xs font-mono text-cyan-400 font-bold uppercase">
                  Run Audit Inspector · #{selectedRun.id}
                </span>
                <h3 className="text-lg font-bold text-white">{selectedRun.scenario_name}</h3>
              </div>
              <button
                onClick={() => setSelectedRun(null)}
                className="w-8 h-8 rounded-lg bg-slate-900 border border-slate-700 text-slate-400 hover:text-white flex items-center justify-center"
              >
                ✕
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-5 overflow-y-auto space-y-4">
              <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800">
                <span className="text-xs font-mono text-slate-400 block mb-1">Gate Decision Reason</span>
                <p className="text-xs text-slate-200 leading-relaxed font-sans">{selectedRun.reason}</p>
              </div>

              {/* JSON Payload Inspector */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-mono text-slate-300 flex items-center space-x-1.5">
                    <FileJson className="w-3.5 h-3.5 text-cyan-400" />
                    <span>Gate Report JSON Payload</span>
                  </span>
                  <button
                    onClick={() => handleCopyJson(selectedRun)}
                    className="flex items-center space-x-1 text-xs font-mono text-cyan-300 hover:text-cyan-200 bg-cyan-950/60 border border-cyan-800/80 px-2.5 py-1 rounded-lg"
                  >
                    {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                    <span>{copied ? 'Copied!' : 'Copy JSON'}</span>
                  </button>
                </div>
                <pre className="bg-[#060a12] border border-slate-800 p-4 rounded-xl text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-72">
                  {JSON.stringify(selectedRun, null, 2)}
                </pre>
              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedRun(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold font-sans"
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
