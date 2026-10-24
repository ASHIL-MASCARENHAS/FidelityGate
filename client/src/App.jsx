import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Sidebar from './components/Sidebar';
import TopBar from './components/TopBar';
import AryakaOverviewDashboard from './components/AryakaOverviewDashboard';
import DecisionWorkspace from './components/DecisionWorkspace';
import ExecutionTraceView from './components/ExecutionTraceView';
import EvaluationLab from './components/EvaluationLab';
import FidelityMonitoringRecharts from './components/FidelityMonitoringRecharts';
import RiveValidationMotion from './components/RiveValidationMotion';
import RunHistory from './components/RunHistory';
import SettingsDiagnostics from './components/SettingsDiagnostics';

const DEFAULT_SCENARIOS = {
  wan_congestion: {
    scenario_id: 'WAN-042',
    name: 'WAN congestion / reroute',
    description: 'Illustrative branch-to-core traffic burst with a proposed reroute.',
    nominal_latency_ms: 18.0,
    capacity_mbps: 1000.0,
    offered_load_mbps: 760.0,
    slo_latency_ms: 45.0,
    latency_multiplier_min: 0.85,
    latency_multiplier_max: 1.35,
    stability_threshold: 0.9,
  },
  fiber_drift: {
    scenario_id: 'FIBER-017',
    name: 'Fiber latency calibration drift',
    description: 'Illustrative route where the twin may understate propagation delay.',
    nominal_latency_ms: 24.0,
    capacity_mbps: 900.0,
    offered_load_mbps: 690.0,
    slo_latency_ms: 40.0,
    latency_multiplier_min: 0.85,
    latency_multiplier_max: 1.6,
    stability_threshold: 0.9,
  },
  traffic_burst: {
    scenario_id: 'BURST-006',
    name: 'Hidden traffic burst',
    description: 'Illustrative load spike used to exercise conservative gate behavior.',
    nominal_latency_ms: 15.0,
    capacity_mbps: 800.0,
    offered_load_mbps: 730.0,
    slo_latency_ms: 35.0,
    latency_multiplier_min: 0.9,
    latency_multiplier_max: 1.5,
    stability_threshold: 0.9,
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState('overview'); // Default to Aryaka Overview Dashboard
  const [theme, setTheme] = useState('light'); // Default to clean enterprise light theme matching Aryaka screenshot
  const [scenarios, setScenarios] = useState(DEFAULT_SCENARIOS);
  const [selectedKey, setSelectedKey] = useState('wan_congestion');
  const [evaluations, setEvaluations] = useState(25);
  const [investigationResult, setInvestigationResult] = useState(null);
  const [adaptiveResult, setAdaptiveResult] = useState(null);
  const [runs, setRuns] = useState([]);
  const [benchmarkResults, setBenchmarkResults] = useState([]);
  const [diagnostics, setDiagnostics] = useState({});
  const [loading, setLoading] = useState(false);
  const [adaptiveLoading, setAdaptiveLoading] = useState(false);
  const [apiHealthy, setApiHealthy] = useState(false);

  // Apply theme class to document root
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  // Check API health & load initial scenarios and runs
  useEffect(() => {
    async function initData() {
      try {
        const healthRes = await fetch('/api/health');
        if (healthRes.ok) {
          setApiHealthy(true);
        }

        // Fetch scenarios
        const scnRes = await fetch('/api/scenarios');
        if (scnRes.ok) {
          const scnJson = await scnRes.json();
          if (scnJson.data) setScenarios(scnJson.data);
        }

        // Fetch recent runs
        const runsRes = await fetch('/api/runs?limit=50');
        if (runsRes.ok) {
          const runsJson = await runsRes.json();
          if (runsJson.data) setRuns(runsJson.data);
        }

        // Fetch diagnostics
        const diagRes = await fetch('/api/diagnostics');
        if (diagRes.ok) {
          const diagJson = await diagRes.json();
          setDiagnostics(diagJson);
        }

        runInvestigation('wan_congestion', 25);
        runAdaptiveInvestigation('wan_congestion');
      } catch (err) {
        console.warn('Backend API connection pending:', err.message);
        generateLocalFallbackInvestigation('wan_congestion', 25);
      }
    }

    initData();
  }, []);

  // Local fallback calculator
  const generateLocalFallbackInvestigation = (key, count) => {
    const scn = DEFAULT_SCENARIOS[key] || DEFAULT_SCENARIOS.wan_congestion;
    const points = [];
    const minM = scn.latency_multiplier_min;
    const maxM = scn.latency_multiplier_max;

    let worst = 0;
    let breaches = 0;

    for (let i = 0; i < count; i++) {
      const a = minM + ((maxM - minM) * i) / Math.max(count - 1, 1);
      const b = 0.95 + ((1.15 - 0.95) * i) / Math.max(count - 1, 1);
      const util = Math.min((scn.offered_load_mbps * b) / scn.capacity_mbps, 0.999);
      const q = (0.15 * util) / Math.max(1.0 - util, 0.05);
      const lat = scn.nominal_latency_ms * a * (1 + q);
      if (lat > worst) worst = lat;
      const violated = lat > scn.slo_latency_ms;
      if (violated) breaches++;

      points.push({
        sample: i + 1,
        latency_factor: Math.round(a * 1000) / 1000,
        load_factor: Math.round(b * 1000) / 1000,
        latency_ms: Math.round(lat * 10) / 10,
        utilization: Math.round(util * 1000) / 1000,
        violated,
      });
    }

    const nominal = points[0]?.latency_ms || scn.nominal_latency_ms;
    const stability = 1 - breaches / count;

    let decision = 'ACCEPT';
    let reason = 'All evaluated variations satisfy the latency SLO and stability threshold.';
    if (nominal <= scn.slo_latency_ms && breaches > 0) {
      decision = 'GATHER_EVIDENCE';
      reason = 'Nominal prediction passes, but uncertainty variations breach the SLO; gather diagnostics.';
    } else if (nominal > scn.slo_latency_ms) {
      decision = 'ABSTAIN';
      reason = 'The candidate cannot be justified within the configured uncertainty envelope; fail closed.';
    }

    setInvestigationResult({
      run_id: 1,
      scenario: scn,
      gate: {
        decision,
        reason,
        report: {
          evaluations: count,
          nominal_latency_ms: nominal,
          worst_latency_ms: worst,
          peak_utilization: 0.874,
          stability_score: stability,
          violations: breaches,
          sensitivity: {
            'Latency calibration': worst - nominal,
            'Traffic load': 0.152,
          },
        },
      },
      sweep_points: points,
    });
  };

  const runInvestigation = async (key, count) => {
    setLoading(true);
    try {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_key: key, evaluations: count }),
      });

      if (res.ok) {
        const json = await res.json();
        setInvestigationResult(json);
        setApiHealthy(true);

        const runsRes = await fetch('/api/runs?limit=50');
        if (runsRes.ok) {
          const runsJson = await runsRes.json();
          if (runsJson.data) setRuns(runsJson.data);
        }
      } else {
        generateLocalFallbackInvestigation(key, count);
      }
    } catch (err) {
      console.warn('API investigate fallback:', err);
      generateLocalFallbackInvestigation(key, count);
    } finally {
      setLoading(false);
    }
  };

  const runAdaptiveInvestigation = async (key) => {
    const targetKey = key || selectedKey;
    setAdaptiveLoading(true);
    try {
      const res = await fetch('/api/adaptive-investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_key: targetKey }),
      });

      if (res.ok) {
        const json = await res.json();
        setAdaptiveResult(json);
      }
    } catch (err) {
      console.warn('Adaptive investigation error:', err);
    } finally {
      setAdaptiveLoading(false);
    }
  };

  const handleEvaluateAll = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/evaluate-all', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ evaluations: 25 }),
      });

      if (res.ok) {
        const json = await res.json();
        if (json.data) setBenchmarkResults(json.data);
      }
    } catch (err) {
      console.warn('API evaluate-all fallback:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshRuns = async () => {
    setLoading(true);
    try {
      const runsRes = await fetch('/api/runs?limit=50');
      if (runsRes.ok) {
        const runsJson = await runsRes.json();
        if (runsJson.data) setRuns(runsJson.data);
      }
    } catch (err) {
      console.warn('Refresh runs error:', err);
    } finally {
      setLoading(false);
    }
  };

  const currentReport = investigationResult?.gate?.report;
  const currentDecision = investigationResult?.gate?.decision || 'GATHER_EVIDENCE';

  const titles = {
    overview: 'Overview Dashboard',
    decision: 'Decision Workspace',
    trace: 'Execution Trace (AgentOps)',
    evaluation: 'Evaluation Lab (4-Way Baselines)',
    monitoring: 'Telemetry Monitoring (Recharts)',
    motion: 'Motion & Sync Signals (Rive)',
    history: 'Persistent Audit Trail (Runs)',
    docs: 'Documentation & Canonical Contracts',
    settings: 'Settings & Diagnostics',
  };

  return (
    <div className="min-h-screen flex bg-[#f4f6f9] dark:bg-[#090f1d] text-slate-800 dark:text-slate-100 transition-colors duration-200">
      {/* Left Collapsible Navigation Sidebar (Matching Aryaka screenshot) */}
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header & Alert Marquee Bar */}
        <TopBar
          activeTitle={titles[activeTab] || 'Overview Dashboard'}
          theme={theme}
          setTheme={setTheme}
          onSelectScenario={(k) => {
            setSelectedKey(k);
            setActiveTab('decision');
          }}
        />

        {/* View Content */}
        <main className="flex-1 p-5 overflow-y-auto">
          <AnimatePresence mode="wait">
            {activeTab === 'overview' && (
              <motion.div
                key="overview"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <AryakaOverviewDashboard
                  scenarios={scenarios}
                  selectedScenarioKey={selectedKey}
                  onSelectScenario={(k) => {
                    setSelectedKey(k);
                    runInvestigation(k, evaluations);
                  }}
                  onTriggerDiagnostic={(k) => {
                    setSelectedKey(k);
                    runAdaptiveInvestigation(k);
                    setActiveTab('trace');
                  }}
                  investigationResult={investigationResult}
                />
              </motion.div>
            )}

            {activeTab === 'decision' && (
              <motion.div
                key="decision"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <DecisionWorkspace
                  scenarios={scenarios}
                  selectedKey={selectedKey}
                  setSelectedKey={setSelectedKey}
                  evaluations={evaluations}
                  setEvaluations={setEvaluations}
                  onRunInvestigation={runInvestigation}
                  investigationResult={investigationResult}
                  loading={loading}
                />
              </motion.div>
            )}

            {activeTab === 'trace' && (
              <motion.div
                key="trace"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <ExecutionTraceView
                  executionTrace={adaptiveResult?.execution_trace || []}
                  counterexample={adaptiveResult?.counterexample}
                  diagnosticObservation={adaptiveResult?.diagnostic_observation}
                  gateVerdict={adaptiveResult?.gate}
                  scenario={scenarios[selectedKey]}
                  onRunAdaptive={() => runAdaptiveInvestigation(selectedKey)}
                  loading={adaptiveLoading}
                />
              </motion.div>
            )}

            {activeTab === 'evaluation' && (
              <motion.div
                key="evaluation"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <EvaluationLab
                  onEvaluateAll={handleEvaluateAll}
                  benchmarkResults={benchmarkResults}
                  loading={loading}
                />
              </motion.div>
            )}

            {activeTab === 'monitoring' && (
              <motion.div
                key="monitoring"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <FidelityMonitoringRecharts
                  runs={runs}
                  currentReport={currentReport}
                  scenario={scenarios[selectedKey]}
                />
              </motion.div>
            )}

            {activeTab === 'motion' && (
              <motion.div
                key="motion"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <RiveValidationMotion currentDecision={currentDecision} />
              </motion.div>
            )}

            {activeTab === 'history' && (
              <motion.div
                key="history"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <RunHistory runs={runs} onRefresh={handleRefreshRuns} loading={loading} />
              </motion.div>
            )}

            {activeTab === 'docs' && (
              <motion.div
                key="docs"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
                className="aryaka-card p-6 space-y-4"
              >
                <h3 className="text-base font-bold">Canonical Project Documentation & Contracts</h3>
                <p className="text-xs text-slate-500">
                  Shared project context surviving model switches, saved in <code className="font-mono bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">/docs</code>.
                </p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-mono pt-2">
                  {[
                    { file: 'PROJECT_BRIEF.md', desc: 'Problem, target user, technical contribution' },
                    { file: 'ARCHITECTURE.md', desc: 'Component responsibilities, data flow, state machine' },
                    { file: 'CONTRACTS.md', desc: 'Pydantic schemas, REST endpoints, TypeScript types' },
                    { file: 'METHODOLOGY.md', desc: 'Convex queueing math, counterexample search, error models' },
                    { file: 'EVALUATION_PROTOCOL.md', desc: 'Baselines, scenario IDs, ground-truth trials' },
                    { file: 'CURRENT_STATUS.md', desc: 'Implemented features, verified tests, known limits' },
                    { file: 'DECISIONS.md', desc: 'Architectural Decision Records (ADR 001 - 004)' },
                    { file: 'HANDOFF.md', desc: 'Current task, changed files, test results' },
                  ].map((doc) => (
                    <div key={doc.file} className="p-3 rounded-lg border border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-900/60">
                      <span className="font-bold text-cyan-700 dark:text-cyan-400 block">{doc.file}</span>
                      <span className="text-[11px] text-slate-500 font-sans">{doc.desc}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {activeTab === 'settings' && (
              <motion.div
                key="settings"
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -8 }}
                transition={{ duration: 0.15 }}
              >
                <SettingsDiagnostics diagnostics={diagnostics} />
              </motion.div>
            )}
          </AnimatePresence>
        </main>
      </div>
    </div>
  );
}
