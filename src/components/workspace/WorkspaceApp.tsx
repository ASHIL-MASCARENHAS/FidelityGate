'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  ShieldCheck,
  Clock,
  Cpu,
  LineChart,
  History,
  Settings,
  FileText,
  RotateCw,
  Plus,
  Bell,
  Sun,
  Moon,
  Volume2,
  VolumeX,
  Server,
  Network,
  Radio,
  Home,
  UserCheck,
  BookOpen,
  Play,
  Square,
} from 'lucide-react';
import { useAutoDemo } from '@/hooks/useAutoDemo';
import { AutoDemoModal } from '@/components/demo/AutoDemoModal';
import { AutoDemoFloatingControl } from '@/components/demo/AutoDemoFloatingControl';
import { NoWorkflowModal } from '@/components/demo/NoWorkflowModal';
import { AutoDemoCompletionModal } from '@/components/demo/AutoDemoCompletionModal';
import { UserGuide } from '@/components/guide/UserGuide';
import { DecisionWorkspace } from '@/components/workspace/DecisionWorkspace';
import { WorkflowOrchestrationPanel } from '@/components/workspace/WorkflowOrchestrationPanel';
import { DecisionExplanationPanel } from '@/components/xai/DecisionExplanationPanel';
import { ExecutionTraceView } from '@/components/trace/ExecutionTraceView';
import { EvaluationLab } from '@/components/evaluation/EvaluationLab';
import { FidelityMonitoringRecharts } from '@/components/monitoring/FidelityMonitoringRecharts';
import { RiveValidationMotion } from '@/components/motion/RiveValidationMotion';
import { RunHistory } from '@/components/history/RunHistory';
import { SettingsDiagnostics } from '@/components/settings/SettingsDiagnostics';
import { HumanApprovalModal } from '@/components/workspace/HumanApprovalModal';
import { DEFAULT_SCENARIOS } from '@/config/site';
import { DiagnosticInfo, InvestigationResult, RunRecord, Scenario } from '@/types';
import { playTick, playConfirmation } from '@/lib/sound';
import { WorkflowRunProvider, useWorkflowRun } from '@/context/WorkflowRunContext';

interface WorkspaceAppProps {
  initialTab?: string;
  theme?: 'light' | 'dark';
  setTheme?: (t: 'light' | 'dark') => void;
  soundEnabled?: boolean;
  setSoundEnabled?: (s: boolean) => void;
  onBackToLanding?: () => void;
}

function WorkspaceAppInner({
  initialTab = 'decision',
  theme: controlledTheme,
  setTheme: controlledSetTheme,
  soundEnabled: controlledSoundEnabled,
  setSoundEnabled: controlledSetSoundEnabled,
  onBackToLanding,
}: WorkspaceAppProps) {
  const {
    selectedWorkflow,
    selectedWorkflowRunId,
    selectWorkflowRun,
    refreshSelectedWorkflow,
    workflowEvents,
  } = useWorkflowRun();
  const [activeTab, setActiveTab] = useState<string>(initialTab);
  const [internalTheme, setInternalTheme] = useState<'light' | 'dark'>('dark');
  const [internalSound, setInternalSound] = useState<boolean>(false);
  const [motionReduced, setMotionReduced] = useState<boolean>(false);
  const [isApprovalModalOpen, setIsApprovalModalOpen] = useState<boolean>(false);

  const theme = controlledTheme ?? internalTheme;
  const setTheme = controlledSetTheme ?? setInternalTheme;
  const soundEnabled = controlledSoundEnabled ?? internalSound;
  const setSoundEnabled = controlledSetSoundEnabled ?? setInternalSound;

  // Auto Demo guided tour controller
  const autoDemo = useAutoDemo({
    activeTab,
    setActiveTab,
    soundEnabled,
  });

  // Keep the document theme class in sync so the workspace renders correctly
  // in both modes, including when it is mounted standalone at /workspace.
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle('dark', theme === 'dark');
  }, [theme]);

  // Workspace Data State
  const [scenarios, setScenarios] = useState<Record<string, Scenario>>(DEFAULT_SCENARIOS);
  const [selectedKey, setSelectedKey] = useState<string>('wan_congestion');
  const [evaluations, setEvaluations] = useState<number>(25);
  const [investigationResult, setInvestigationResult] = useState<InvestigationResult | null>(null);
  const [adaptiveResult, setAdaptiveResult] = useState<InvestigationResult | null>(null);
  const [runs, setRuns] = useState<RunRecord[]>([]);
  const [benchmarkResults, setBenchmarkResults] = useState<any[]>([]);
  const [diagnostics, setDiagnostics] = useState<DiagnosticInfo | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [adaptiveLoading, setAdaptiveLoading] = useState<boolean>(false);
  const [isSyncing, setIsSyncing] = useState<boolean>(false);

  // Apply theme class to document root
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  // Check prefers-reduced-motion media query on initial mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
      if (mediaQuery.matches) {
        setMotionReduced(true);
      }
    }
  }, []);

  // Load runs and diagnostics on mount
  useEffect(() => {
    handleRefreshRuns();
    fetch('/api/diagnostics')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setDiagnostics(data);
      })
      .catch(() => {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const runInvestigation = async (key: string, count: number) => {
    setLoading(true);
    try {
      const res = await fetch(`/api/investigate?scenario=${key}&evaluations=${count}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || 'Investigation endpoint offline');
      }
      const data = await res.json();
      setInvestigationResult(data);
    } catch (err: any) {
      console.warn('Live investigation request failed:', err.message);
      setInvestigationResult(null);
    } finally {
      setLoading(false);
    }
  };

  const runAdaptiveInvestigation = async (key: string) => {
    setAdaptiveLoading(true);
    try {
      const res = await fetch(`/api/adaptive-investigation?scenario=${key}`);
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || err.error || 'Adaptive investigation failed');
      }
      const data = await res.json();
      setAdaptiveResult(data);
    } catch (err: any) {
      console.warn('Adaptive investigation request failed:', err.message);
      setAdaptiveResult(null);
    } finally {
      setAdaptiveLoading(false);
    }
  };

  const handleSync = () => {
    playTick(soundEnabled);
    setIsSyncing(true);
    runInvestigation(selectedKey, evaluations);
    runAdaptiveInvestigation(selectedKey);
    setTimeout(() => setIsSyncing(false), 800);
  };

  const handleEvaluateAll = async () => {
    setLoading(true);
    playConfirmation(soundEnabled);
    try {
      const res = await fetch('/api/baselines');
      if (!res.ok) throw new Error('Baselines API offline');
      const data = await res.json();
      setBenchmarkResults(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.warn('Baselines evaluation failed:', err.message);
      setBenchmarkResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRefreshRuns = async () => {
    setLoading(true);
    playTick(soundEnabled);
    try {
      const res = await fetch('/api/runs');
      if (!res.ok) throw new Error('Runs API offline');
      const data = await res.json();
      setRuns(Array.isArray(data) ? data : []);
    } catch (err: any) {
      console.warn('Failed to load runs:', err.message);
      setRuns([]);
    } finally {
      setLoading(false);
    }
  };

  const currentScenario = scenarios[selectedKey] || scenarios.wan_congestion;
  const currentDecision = investigationResult?.gate?.decision || 'GATHER_EVIDENCE';
  const currentReport = investigationResult?.gate?.report || null;

  // Animation props respecting prefers-reduced-motion
  const animProps = motionReduced
    ? {
        initial: { opacity: 1 },
        animate: { opacity: 1 },
        exit: { opacity: 1 },
        transition: { duration: 0 },
      }
    : {
        initial: { opacity: 0, y: 6 },
        animate: { opacity: 1, y: 0 },
        exit: { opacity: 0, y: -6 },
        transition: { duration: 0.2 },
      };

  // Navigation Items matching the user reference
  const navTabs = [
    { id: 'decision', label: 'Topology', icon: Network },
    { id: 'workflow', label: 'Workflow & Approval', icon: UserCheck },
    { id: 'xai', label: 'Explainable AI', icon: ShieldCheck },
    { id: 'metrics', label: 'Metrics', icon: LineChart },
    { id: 'trace', label: 'Trace (AgentOps)', icon: Clock },
    { id: 'evaluation', label: 'Evaluation Lab', icon: Cpu },
    { id: 'history', label: 'Audit Runs', icon: History },
    { id: 'guide', label: 'User Guide', icon: BookOpen },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  // Per-tab page heading keeps the shell free of irrelevant context
  const tabMeta: Record<string, { title: string; description: string }> = {
    decision: {
      title: 'Global Network Topology',
      description:
        'Real-time orchestration and telemetry of decentralized edge instances across all active zones.',
    },
    workflow: {
      title: 'End-to-End Workflow & Human Authorization',
      description:
        'Deterministic 13-stage orchestration, human approval boundary, and isolated twin outcome reporting.',
    },
    xai: {
      title: 'Evidence-Based Explainable AI (XAI)',
      description:
        'Deterministic decision attribution, gate rule verification, counterexamples, and local sensitivity.',
    },
    metrics: {
      title: 'Fidelity Metrics',
      description: 'Nominal versus worst-case behaviour across recorded investigation runs.',
    },
    trace: {
      title: 'Execution Trace',
      description: 'Step-by-step agent reasoning, counterexamples, and diagnostic evidence.',
    },
    evaluation: {
      title: 'Evaluation Lab',
      description: 'Benchmark the gate against every scenario and compare verdict stability.',
    },
    history: {
      title: 'Audit Runs',
      description: 'Immutable record of past investigations and the verdict each one produced.',
    },
    guide: {
      title: 'Platform User Guide & Judging Evaluation',
      description: 'System concepts, 13-stage pipeline architecture, and hackathon evaluation criteria alignment.',
    },
    docs: {
      title: 'Platform User Guide & Judging Evaluation',
      description: 'System concepts, 13-stage pipeline architecture, and hackathon evaluation criteria alignment.',
    },
    settings: {
      title: 'Settings & Diagnostics',
      description: 'Interface preferences and backend connectivity checks.',
    },
  };

  const heading = tabMeta[activeTab] ?? tabMeta.decision;

  const summaryMetrics = [
    {
      label: 'Active nodes',
      value: '1,402',
      unit: '',
      delta: '+12% this week',
      positive: true,
      icon: Server,
    },
    {
      label: 'Avg latency',
      value: currentReport ? currentReport.nominal_latency_ms.toFixed(1) : '18.4',
      unit: 'ms',
      delta: '-2% this week',
      positive: true,
      icon: Clock,
    },
    {
      label: 'Throughput',
      value: String(currentScenario.capacity_mbps / 1000),
      unit: 'Gbps',
      delta: 'Stable',
      positive: false,
      icon: Activity,
    },
  ];

  const regions = [
    {
      id: 'us-east-1',
      city: 'N. Virginia',
      status: 'Healthy' as const,
      uptime: '99.999%',
      load: 64,
    },
    {
      id: 'eu-central-1',
      city: 'Frankfurt',
      status: 'Healthy' as const,
      uptime: '99.995%',
      load: 42,
    },
    {
      id: 'ap-northeast-1',
      city: 'Reroute proposed',
      status: 'Attention' as const,
      uptime: '99.950%',
      load: 89,
    },
  ];

  const iconButton =
    'inline-flex items-center justify-center w-9 h-9 rounded-lg text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark hover:bg-paper dark:hover:bg-paper-dark focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50 transition-colors';

  return (
    <div className="min-h-screen bg-paper dark:bg-paper-dark dark:workspace-mesh-bg text-ink dark:text-ink-dark font-sans px-4 py-6 sm:px-6 lg:px-8 lg:py-10 flex flex-col transition-colors">
      {/* Human Approval Modal */}
      <HumanApprovalModal
        isOpen={isApprovalModalOpen}
        onClose={() => setIsApprovalModalOpen(false)}
        scenarioName={currentScenario.name}
        nominalLatency={currentReport ? currentReport.nominal_latency_ms : currentScenario.nominal_latency_ms}
        worstLatency={currentReport ? currentReport.worst_latency_ms : (currentScenario.nominal_latency_ms * currentScenario.latency_multiplier_max)}
        sloThreshold={currentScenario.slo_latency_ms}
        gateVerdict={selectedWorkflow?.gate_verdict || currentDecision}
        workflowRunId={selectedWorkflow?.workflow_run_id}
        candidateId={selectedWorkflow?.selected_candidate_id || undefined}
        onApprove={() => {
          refreshSelectedWorkflow();
          handleRefreshRuns();
        }}
        soundEnabled={soundEnabled}
      />

      {/* Auto Demo Modals & Active Controls */}
      <AutoDemoModal
        isOpen={autoDemo.demoState === 'STATUS_POPUP'}
        step={autoDemo.currentStep}
        stepIndex={autoDemo.currentStepIndex}
        totalSteps={autoDemo.totalSteps}
        context={autoDemo.context}
        countdown={autoDemo.popupCountdown}
        isPaused={autoDemo.isPaused}
        onContinue={autoDemo.continueFromPopup}
        onSkip={autoDemo.skipCurrentStep}
        onStop={autoDemo.stopAutoDemo}
        onTogglePause={autoDemo.togglePause}
        soundEnabled={soundEnabled}
      />

      <NoWorkflowModal
        isOpen={autoDemo.demoState === 'NO_WORKFLOW'}
        onGoToWorkflow={() => {
          setActiveTab('workflow');
          autoDemo.setDemoState('IDLE');
        }}
        onGoToHistory={() => {
          setActiveTab('history');
          autoDemo.setDemoState('IDLE');
        }}
        onClose={() => autoDemo.setDemoState('IDLE')}
        soundEnabled={soundEnabled}
      />

      <AutoDemoCompletionModal
        isOpen={autoDemo.demoState === 'COMPLETED'}
        context={autoDemo.context}
        elapsedSeconds={autoDemo.elapsedSeconds}
        onRestart={autoDemo.restartDemo}
        onClose={() => autoDemo.setDemoState('IDLE')}
        soundEnabled={soundEnabled}
      />

      {/* Floating Demo Control during viewing */}
      {autoDemo.isAutoDemoRunning && autoDemo.demoState !== 'STATUS_POPUP' && (
        <AutoDemoFloatingControl
          step={autoDemo.currentStep}
          stepIndex={autoDemo.currentStepIndex}
          totalSteps={autoDemo.totalSteps}
          context={autoDemo.context}
          viewingCountdown={autoDemo.viewingCountdown}
          elapsedSeconds={autoDemo.elapsedSeconds}
          isPaused={autoDemo.isPaused}
          isAwaitingApprovalPause={autoDemo.isAwaitingApprovalPause}
          onNext={autoDemo.advanceToNextStep}
          onTogglePause={autoDemo.togglePause}
          onStop={autoDemo.stopAutoDemo}
          soundEnabled={soundEnabled}
        />
      )}

      <div className="w-full max-w-7xl mx-auto rounded-2xl bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark shadow-elevation overflow-hidden flex flex-col">
        {/* 1. CHROME BAR: identity on the left, controls on the right */}
        <header className="px-4 sm:px-6 h-[72px] flex items-center justify-between gap-4 border-b border-hairline dark:border-hairline-dark bg-surface/85 dark:bg-surface-dark/85 backdrop-blur-md sticky top-0 z-30">
          <div className="flex items-center gap-3 min-w-0">
            {onBackToLanding && (
              <button
                onClick={() => {
                  playTick(soundEnabled);
                  onBackToLanding();
                }}
                className="shrink-0 inline-flex items-center justify-center w-10 h-10 rounded-lg bg-cobalt text-white shadow-sm hover:bg-cobalt-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50 focus-visible:ring-offset-2 focus-visible:ring-offset-surface dark:focus-visible:ring-offset-surface-dark active:scale-95 transition-all"
                aria-label="Back to home"
                title="Back to home"
              >
                <Home className="w-[18px] h-[18px]" />
              </button>
            )}

            <span
              aria-hidden="true"
              className="hidden sm:block w-px h-7 bg-hairline dark:bg-hairline-dark shrink-0"
            />

            <div className="flex items-center gap-2.5 min-w-0">
              <Radio className="w-5 h-5 shrink-0 text-cobalt" />
              <div className="min-w-0 leading-snug">
                <span className="block text-[17px] font-semibold tracking-[-0.02em] truncate">
                  FidelityGate Core
                </span>
                <span className="block text-[13px] text-muted-fg dark:text-muted-dark truncate">
                  Production network
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => {
                playTick(soundEnabled);
                setTheme(theme === 'dark' ? 'light' : 'dark');
              }}
              className={iconButton}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            <button
              onClick={() => {
                const next = !soundEnabled;
                setSoundEnabled(next);
                playTick(next);
              }}
              className={iconButton}
              aria-label={soundEnabled ? 'Mute interface sound' : 'Enable interface sound'}
              title={soundEnabled ? 'Mute interface sound' : 'Enable interface sound'}
            >
              {soundEnabled ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            </button>

            <button
              onClick={handleSync}
              className={iconButton}
              aria-label="Sync digital twin with telemetry"
              title="Sync digital twin with telemetry"
            >
              <RotateCw className={`w-4 h-4 ${isSyncing ? 'animate-spin text-cobalt' : ''}`} />
            </button>

            <button
              onClick={() => {
                playTick(soundEnabled);
                setActiveTab('trace');
              }}
              className={`${iconButton} relative`}
              aria-label="View investigation trace"
              title="View investigation trace"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full bg-cobalt" />
            </button>

            <span
              aria-hidden="true"
              className="hidden sm:block w-px h-5 mx-2 bg-hairline dark:bg-hairline-dark"
            />

            <button
              onClick={() => {
                playConfirmation(soundEnabled);
                setIsApprovalModalOpen(true);
              }}
              className="inline-flex items-center gap-1.5 h-9 px-2.5 sm:px-3.5 rounded-lg bg-cobalt text-white text-xs font-semibold hover:bg-cobalt-hover focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50 focus-visible:ring-offset-2 focus-visible:ring-offset-surface dark:focus-visible:ring-offset-surface-dark active:scale-95 transition-all"
              title="Deploy reroute"
            >
              <Plus className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Deploy reroute</span>
            </button>

            <div
              className="ml-1.5 w-8 h-8 shrink-0 rounded-full bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark flex items-center justify-center text-[11px] font-semibold text-muted-fg dark:text-muted-dark relative"
              title="Operator"
            >
              OP
              <span className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full bg-emerald-verdict border-2 border-surface dark:border-surface-dark" />
            </div>
          </div>
        </header>

        {/* 2. SECTION TABS: one quiet row, underline for the active view */}
        <nav
          className="px-4 sm:px-6 border-b border-hairline dark:border-hairline-dark flex items-center justify-between gap-4 overflow-x-auto"
          aria-label="Workspace sections"
        >
          <div className="flex items-center gap-5 sm:gap-7 shrink-0">
            {navTabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => {
                    playTick(soundEnabled);
                    setActiveTab(tab.id);
                  }}
                  aria-current={isActive ? 'page' : undefined}
                  className={`relative shrink-0 inline-flex items-center gap-2 py-4 text-[13px] font-medium whitespace-nowrap border-b-2 -mb-px transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50 rounded-sm ${
                    isActive
                      ? 'border-cobalt text-ink dark:text-ink-dark'
                      : 'border-transparent text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>

          {/* Auto Demo Action in Central Navigation */}
          <div className="shrink-0 flex items-center gap-2 py-2">
            {!autoDemo.isAutoDemoRunning ? (
              <button
                onClick={() => {
                  playTick(soundEnabled);
                  autoDemo.startAutoDemo();
                }}
                className="inline-flex items-center gap-1.5 h-8 px-3 rounded-lg text-xs font-semibold text-cobalt dark:text-cyan-accent bg-cobalt-subtle dark:bg-cobalt-subtle-dark border border-cobalt/25 dark:border-cyan-accent/25 hover:bg-cobalt/15 dark:hover:bg-cyan-accent/15 transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-cobalt/50 shadow-sm active:scale-95"
                aria-label="Start Auto Demo tour"
                title="Start Auto Demo: automatically guides through each workspace section"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>Auto Demo</span>
              </button>
            ) : (
              <div className="inline-flex items-center gap-2 h-8 px-3 rounded-lg text-xs font-semibold bg-paper dark:bg-paper-dark border border-cobalt/35 dark:border-cyan-accent/35 shadow-sm">
                <span className="w-2 h-2 rounded-full bg-cyan-accent animate-ping" />
                <span className="text-ink dark:text-ink-dark">Demo Running</span>
                <span className="text-[11px] font-mono text-muted-fg dark:text-muted-dark">
                  {autoDemo.currentStepIndex + 1}/{autoDemo.totalSteps}
                </span>
                <button
                  onClick={() => {
                    playTick(soundEnabled);
                    autoDemo.stopAutoDemo();
                  }}
                  className="ml-1 text-muted-fg dark:text-muted-dark hover:text-rose-500 transition-colors p-0.5"
                  aria-label="Stop Auto Demo"
                  title="Stop Auto Demo"
                >
                  <Square className="w-3 h-3 fill-current" />
                </button>
              </div>
            )}
          </div>
        </nav>

        {/* 3. PAGE HEADING + CONTEXTUAL SUMMARY */}
        <div className="px-4 sm:px-6 lg:px-8 pt-6 sm:pt-8 pb-6 border-b border-hairline dark:border-hairline-dark space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4">
            <div className="max-w-2xl">
              <h2 className="text-xl sm:text-2xl font-semibold tracking-[-0.02em]">{heading.title}</h2>
              <p className="text-sm text-muted-fg dark:text-muted-dark mt-1.5 leading-relaxed">
                {heading.description}
              </p>
            </div>

            <label className="flex items-center gap-2 text-xs shrink-0">
              <span className="text-muted-fg dark:text-muted-dark">Scenario</span>
              <select
                value={selectedKey}
                onChange={(e) => {
                  playTick(soundEnabled);
                  setSelectedKey(e.target.value);
                }}
                className="bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark rounded-lg px-3 py-2 text-xs font-medium text-ink dark:text-ink-dark focus:outline-none focus:border-cobalt transition-colors cursor-pointer"
              >
                {Object.entries(scenarios).map(([k, s]) => (
                  <option key={k} value={k}>
                    {s.scenario_id} · {s.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {/* Topology summary belongs to the topology view only */}
          {activeTab === 'workflow' && (
              <motion.div key="workflow" {...animProps}>
                <WorkflowOrchestrationPanel
                  scenarioKey={selectedKey}
                  soundEnabled={soundEnabled}
                />
              </motion.div>
            )}

            {activeTab === 'decision' && (
            <>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {summaryMetrics.map((metric) => {
                  const Icon = metric.icon;
                  return (
                    <div
                      key={metric.label}
                      className="p-4 rounded-xl bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark"
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-medium uppercase tracking-wider text-muted-fg dark:text-muted-dark">
                          {metric.label}
                        </span>
                        <Icon className="w-4 h-4 text-muted-fg dark:text-muted-dark" />
                      </div>
                      <div className="mt-3 flex items-baseline gap-1.5">
                        <span className="text-2xl font-semibold tracking-tight tabular-nums">
                          {metric.value}
                        </span>
                        {metric.unit && (
                          <span className="text-sm text-muted-fg dark:text-muted-dark">
                            {metric.unit}
                          </span>
                        )}
                      </div>
                      <span
                        className={`mt-2 block text-[11px] font-medium ${
                          metric.positive
                            ? 'text-emerald-verdict'
                            : 'text-muted-fg dark:text-muted-dark'
                        }`}
                      >
                        {metric.delta}
                      </span>
                    </div>
                  );
                })}
              </div>

              <div className="rounded-xl border border-hairline dark:border-hairline-dark overflow-hidden">
                <div className="grid grid-cols-12 px-4 sm:px-5 py-2.5 bg-paper dark:bg-paper-dark border-b border-hairline dark:border-hairline-dark text-[11px] font-medium uppercase tracking-wider text-muted-fg dark:text-muted-dark">
                  <span className="col-span-5 sm:col-span-4">Region</span>
                  <span className="col-span-4 sm:col-span-3">Status</span>
                  <span className="hidden sm:block sm:col-span-2">Uptime</span>
                  <span className="col-span-3 text-right">Load</span>
                </div>

                <div className="divide-y divide-hairline dark:divide-hairline-dark">
                  {regions.map((region) => {
                    const attention = region.status === 'Attention';
                    return (
                      <div
                        key={region.id}
                        className="grid grid-cols-12 px-4 sm:px-5 py-3 items-center hover:bg-paper dark:hover:bg-paper-dark transition-colors"
                      >
                        <div className="col-span-5 sm:col-span-4 flex items-center gap-2.5 min-w-0">
                          <div className="w-7 h-7 shrink-0 rounded-md bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark flex items-center justify-center text-muted-fg dark:text-muted-dark">
                            <Server className="w-3.5 h-3.5" />
                          </div>
                          <div className="min-w-0 leading-tight">
                            <span className="block text-xs font-semibold truncate">
                              {region.id}
                            </span>
                            <span className="block text-[11px] text-muted-fg dark:text-muted-dark truncate">
                              {region.city}
                            </span>
                          </div>
                        </div>

                        <div className="col-span-4 sm:col-span-3">
                          <span
                            className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[11px] font-medium ${
                              attention
                                ? 'bg-amber-warning-subtle dark:bg-amber-warning-dark text-amber-warning'
                                : 'bg-emerald-verdict-subtle dark:bg-emerald-verdict-dark text-emerald-verdict'
                            }`}
                          >
                            <span
                              className={`w-1.5 h-1.5 rounded-full ${
                                attention ? 'bg-amber-warning' : 'bg-emerald-verdict'
                              }`}
                            />
                            {region.status}
                          </span>
                        </div>

                        <div className="hidden sm:block sm:col-span-2 text-xs tabular-nums text-muted-fg dark:text-muted-dark">
                          {region.uptime}
                        </div>

                        <div className="col-span-3 flex items-center justify-end gap-3">
                          <div className="hidden md:block w-24 h-1.5 rounded-full bg-hairline dark:bg-hairline-dark overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                attention ? 'bg-amber-warning' : 'bg-cobalt'
                              }`}
                              style={{ width: `${region.load}%` }}
                            />
                          </div>
                          <span
                            className={`text-xs tabular-nums w-9 text-right ${
                              attention
                                ? 'text-amber-warning font-semibold'
                                : 'text-muted-fg dark:text-muted-dark'
                            }`}
                          >
                            {region.load}%
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            </>
          )}
        </div>

        {/* 4. ACTIVE VIEW */}
        <main className="px-4 sm:px-6 lg:px-8 py-6 sm:py-8 flex-1">
          <AnimatePresence mode="wait">
            {activeTab === 'decision' && (
              <motion.div key="decision" {...animProps}>
                <DecisionWorkspace
                  scenarios={scenarios}
                  selectedKey={selectedKey}
                  setSelectedKey={setSelectedKey}
                  evaluations={evaluations}
                  setEvaluations={setEvaluations}
                  onRunInvestigation={runInvestigation}
                  investigationResult={investigationResult}
                  loading={loading}
                  soundEnabled={soundEnabled}
                />
              </motion.div>
            )}

            {activeTab === 'xai' && (
              <motion.div key="xai" {...animProps}>
                <DecisionExplanationPanel
                  scenarioKey={selectedKey}
                  workflowRunId={selectedWorkflow?.workflow_run_id}
                  explanationId={selectedWorkflow?.explanation_id || undefined}
                  evaluationId={selectedWorkflow?.evaluation_id || undefined}
                  adaptiveRunId={
                    selectedWorkflow?.adaptive_run_id ||
                    (typeof (adaptiveResult as any)?.adaptive_run_id === 'string' &&
                    (adaptiveResult as any).adaptive_run_id.startsWith('adapt-')
                      ? (adaptiveResult as any).adaptive_run_id
                      : undefined)
                  }
                />
              </motion.div>
            )}

            {activeTab === 'metrics' && (
              <motion.div key="metrics" {...animProps}>
                <FidelityMonitoringRecharts
                  runs={runs}
                  currentReport={currentReport}
                  scenario={currentScenario}
                />
              </motion.div>
            )}

            {activeTab === 'trace' && (
              <motion.div key="trace" {...animProps}>
                <ExecutionTraceView
                  workflowEvents={workflowEvents}
                  executionTrace={adaptiveResult?.execution_trace || []}
                  counterexample={adaptiveResult?.counterexample}
                  diagnosticObservation={adaptiveResult?.diagnostic_observation}
                  gateVerdict={
                    selectedWorkflow?.gate_verdict
                      ? {
                          decision: selectedWorkflow.gate_verdict as any,
                          reason: selectedWorkflow.termination_reason || '',
                        }
                      : adaptiveResult?.gate
                  }
                  scenario={currentScenario}
                  onRunAdaptive={() => runAdaptiveInvestigation(selectedKey)}
                  loading={adaptiveLoading}
                />
              </motion.div>
            )}

            {activeTab === 'evaluation' && (
              <motion.div key="evaluation" {...animProps}>
                <EvaluationLab
                  onEvaluateAll={handleEvaluateAll}
                  benchmarkResults={benchmarkResults}
                  loading={loading}
                />
              </motion.div>
            )}

            {activeTab === 'history' && (
              <motion.div key="history" {...animProps}>
                <RunHistory
                  runs={runs}
                  onRefresh={handleRefreshRuns}
                  onSelectRun={(run) => {
                    const runId = (run as any).workflow_run_id || (run.id ? (String(run.id).startsWith('wf-') ? String(run.id) : `wf-${run.id}`) : null);
                    if (runId) {
                      selectWorkflowRun(runId);
                      setActiveTab('workflow');
                    }
                  }}
                  loading={loading}
                />
              </motion.div>
            )}

            {(activeTab === 'guide' || activeTab === 'docs') && (
              <motion.div key="guide" {...animProps}>
                <UserGuide
                  soundEnabled={soundEnabled}
                  onNavigateTab={(tab) => {
                    playTick(soundEnabled);
                    setActiveTab(tab);
                  }}
                />
              </motion.div>
            )}

                        {activeTab === 'settings' && (
              <motion.div key="settings" {...animProps}>
                <SettingsDiagnostics
                  diagnostics={diagnostics}
                  theme={theme}
                  setTheme={setTheme}
                  soundEnabled={soundEnabled}
                  setSoundEnabled={setSoundEnabled}
                  motionReduced={motionReduced}
                  setMotionReduced={setMotionReduced}
                />
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* 5. STATUS FOOTER */}
        <footer className="px-4 sm:px-6 py-3 border-t border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark flex flex-wrap items-center justify-between gap-2 text-[11px] text-muted-fg dark:text-muted-dark">
          <span className="inline-flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-verdict" />
            All systems operational · Zero-drift gate active
          </span>
          <span className="tabular-nums">v2.4.1</span>
        </footer>
      </div>

      {/* 6. WORKSPACE FOOTER */}
      <footer className="w-full max-w-7xl mx-auto mt-8 pt-4 pb-8 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-muted-fg dark:text-muted-dark px-4 border-t border-hairline/60 dark:border-hairline-dark/60">
        <div className="flex items-center space-x-2.5">
          <span className="font-bold text-ink dark:text-ink-dark flex items-center space-x-1.5">
            <span className="font-mono text-cobalt font-bold">◈</span>
            <span>FidelityGate</span>
          </span>
          <span aria-hidden="true" className="text-hairline dark:text-hairline-dark">·</span>
          <span>Pre-Production Digital-Twin Validation</span>
        </div>
        <div className="flex items-center space-x-4 text-[11px]">
          <button
            onClick={() => setActiveTab('guide')}
            className="hover:text-cobalt transition-colors font-medium underline-offset-4 hover:underline"
          >
            User Guide &amp; Criteria
          </button>
          <span aria-hidden="true" className="w-px h-3 bg-hairline dark:bg-hairline-dark" />
          <button
            onClick={() => setActiveTab('workflow')}
            className="hover:text-cobalt transition-colors font-medium underline-offset-4 hover:underline"
          >
            Workflow &amp; Approval
          </button>
          <span aria-hidden="true" className="w-px h-3 bg-hairline dark:bg-hairline-dark" />
          <span className="font-mono text-muted-fg dark:text-muted-dark">v1.0.0</span>
        </div>
      </footer>
    </div>
  );
}

export function WorkspaceApp(props: WorkspaceAppProps) {
  return (
    <WorkflowRunProvider>
      <WorkspaceAppInner {...props} />
    </WorkflowRunProvider>
  );
}
