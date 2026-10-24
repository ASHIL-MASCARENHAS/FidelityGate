'use client';

import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  HelpCircle,
  TrendingUp,
  Gauge,
  Layers,
  Database,
  RefreshCw,
  Lock,
  Scale,
  Sparkles,
  ChevronDown,
  ChevronRight,
  ExternalLink,
} from 'lucide-react';
import { DecisionExplanation, GateRuleExplanation, RuleStatus } from '@/types';

interface DecisionExplanationPanelProps {
  scenarioKey?: string;
  adaptiveRunId?: string;
  evaluationId?: string;
  explanationId?: string;
  workflowRunId?: string;
  explanation?: DecisionExplanation | null;
  onRefresh?: () => void;
  loading?: boolean;
}

function normalizeExplanation(data: any): DecisionExplanation {
  if (!data || typeof data !== 'object') {
    throw new Error('Invalid explanation payload');
  }
  return {
    ...data,
    constraint_results: Array.isArray(data.constraint_results) ? data.constraint_results : [],
    uncertainty_changes: Array.isArray(data.uncertainty_changes) ? data.uncertainty_changes : [],
    evidence_items: Array.isArray(data.evidence_items) ? data.evidence_items : [],
    limitations: Array.isArray(data.limitations) ? data.limitations : [],
    unresolved_questions: Array.isArray(data.unresolved_questions) ? data.unresolved_questions : [],
    supporting_findings: Array.isArray(data.supporting_findings) ? data.supporting_findings : [],
    sensitivity_results: data.sensitivity_results
      ? {
          ...data.sensitivity_results,
          evaluated_parameters: Array.isArray(data.sensitivity_results.evaluated_parameters)
            ? data.sensitivity_results.evaluated_parameters.map((p: any) => ({
                ...p,
                perturbations: Array.isArray(p.perturbations) ? p.perturbations : [],
              }))
            : [],
        }
      : null,
  };
}

export function DecisionExplanationPanel({
  scenarioKey = 'wan_congestion',
  adaptiveRunId,
  evaluationId,
  explanationId,
  workflowRunId,
  explanation: initialExplanation,
  onRefresh,
  loading: externalLoading,
}: DecisionExplanationPanelProps) {
  const [explanation, setExplanation] = useState<DecisionExplanation | null>(
    initialExplanation ? normalizeExplanation(initialExplanation) : null
  );
  const [internalLoading, setInternalLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'rules' | 'counterexample' | 'diagnostics' | 'sensitivity' | 'provenance'>('rules');
  const [expandedRule, setExpandedRule] = useState<string | null>(null);

  const loading = externalLoading || internalLoading;

  const fetchCanonicalExplanation = async (explId: string) => {
    setInternalLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch(`/api/v1/explanations/${encodeURIComponent(explId)}`);
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(data.detail || data.error || `Failed to fetch explanation ${explId}`);
      }
      const rawExplanation = data.explanation || data;
      setExplanation(normalizeExplanation(rawExplanation));
    } catch (err: any) {
      console.warn('Failed to load canonical explanation:', err.message);
      setErrorMessage(err.message || 'Error fetching explanation');
      setExplanation(null);
    } finally {
      setInternalLoading(false);
    }
  };

  const fetchExplanation = async () => {
    if (explanationId) {
      await fetchCanonicalExplanation(explanationId);
      return;
    }
    setInternalLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch('/api/v1/explanations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          adaptive_run_id: adaptiveRunId || undefined,
          evaluation_id: evaluationId || undefined,
          scenario_id: scenarioKey,
          compute_sensitivity: true,
        }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        const errorDetail =
          data.detail || data.error || `Failed to generate explanation (status ${res.status})`;
        throw new Error(errorDetail);
      }

      const rawExplanation = data.explanation || data;
      setExplanation(normalizeExplanation(rawExplanation));
    } catch (err: any) {
      console.warn('Failed to load live explanation:', err.message);
      setErrorMessage(err.message || 'Error generating explanation');
      setExplanation(null);
    } finally {
      setInternalLoading(false);
    }
  };

  useEffect(() => {
    if (initialExplanation) {
      setExplanation(normalizeExplanation(initialExplanation));
    } else if (explanationId) {
      fetchCanonicalExplanation(explanationId);
    } else if (evaluationId || adaptiveRunId) {
      fetchExplanation();
    } else {
      // Avoid synthesizing unprompted on mount when no context is selected
      setExplanation(null);
      setErrorMessage(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [scenarioKey, adaptiveRunId, evaluationId, explanationId, initialExplanation]);

  const getStatusBadge = (status: RuleStatus) => {
    switch (status) {
      case 'PASSED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-500 border border-emerald-500/20">
            <CheckCircle2 className="w-3.5 h-3.5" />
            PASSED
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-500 border border-rose-500/20">
            <XCircle className="w-3.5 h-3.5" />
            FAILED
          </span>
        );
      case 'UNKNOWN':
      default:
        return (
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-500 border border-amber-500/20">
            <HelpCircle className="w-3.5 h-3.5" />
            UNKNOWN
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header Card */}
      <div className="p-6 rounded-2xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-hairline dark:border-hairline-dark">
          <div>
            <div className="flex items-center gap-2.5">
              <span className="p-2 rounded-xl bg-cobalt/10 text-cobalt dark:bg-cobalt/20">
                <ShieldCheck className="w-5 h-5" />
              </span>
              <div>
                <h2 className="text-xl font-extrabold text-ink dark:text-ink-dark tracking-tight">
                  Evidence-Based Decision Attribution & XAI
                </h2>
                <p className="text-xs text-muted-fg dark:text-muted-dark">
                  Deterministic audit trail aligning NISTIR 8312 explainability principles with physical telemetry.
                </p>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchExplanation}
              disabled={loading}
              className="px-3.5 py-2 text-xs font-medium rounded-xl border border-hairline dark:border-hairline-dark hover:bg-paper-dark/10 dark:hover:bg-paper/5 text-ink dark:text-ink-dark flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
              Re-Synthesize
            </button>
            {explanation && (
              <span
                className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${
                  explanation.decision === 'ACCEPT'
                    ? 'bg-emerald-500/10 text-emerald-500 border border-emerald-500/30'
                    : explanation.decision === 'GATHER_EVIDENCE'
                    ? 'bg-amber-500/10 text-amber-500 border border-amber-500/30'
                    : 'bg-rose-500/10 text-rose-500 border border-rose-500/30'
                }`}
              >
                GATE VERDICT: {explanation.decision}
              </span>
            )}
          </div>
        </div>

        {/* Executive Summary */}
        {explanation ? (
          <div className="mt-5 space-y-4">
            <div className="p-4 rounded-xl bg-cobalt/5 dark:bg-cobalt/10 border border-cobalt/20">
              <div className="flex items-start gap-3">
                <Sparkles className="w-4 h-4 text-cobalt mt-0.5 shrink-0" />
                <div className="space-y-1">
                  <div className="text-xs font-bold uppercase tracking-wider text-cobalt">
                    Authoritative Plain-Language Summary
                  </div>
                  <p className="text-sm leading-relaxed text-ink/90 dark:text-ink-dark/90 font-sans">
                    {explanation.summary}
                  </p>
                </div>
              </div>
            </div>

            {/* Metadata Pills */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-[11px] font-mono">
              <div className="p-2.5 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                <span className="text-muted-fg dark:text-muted-dark block">Explanation ID</span>
                <span className="text-ink dark:text-ink-dark font-semibold truncate block">{explanation.explanation_id}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                <span className="text-muted-fg dark:text-muted-dark block">Data Substrate</span>
                <span className="text-cobalt font-semibold truncate block">{explanation.data_mode}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                <span className="text-muted-fg dark:text-muted-dark block">Candidate ID</span>
                <span className="text-emerald-500 font-semibold truncate block">{explanation.candidate_id || 'None'}</span>
              </div>
              <div className="p-2.5 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                <span className="text-muted-fg dark:text-muted-dark block">Policy Version</span>
                <span className="text-ink dark:text-ink-dark font-semibold truncate block">{explanation.policy_version}</span>
              </div>
            </div>
          </div>
        ) : loading ? (
          <div className="mt-6 text-center py-8">
            <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cobalt mb-2" />
            <p className="text-xs text-muted-fg dark:text-muted-dark">
              Synthesizing evidence-based explanation from Layer 1–5 artifacts...
            </p>
          </div>
        ) : errorMessage ? (
          <div className="mt-5 p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-500 space-y-2">
            <div className="flex items-center gap-2 font-bold text-xs">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Explanation Unavailable</span>
            </div>
            <p className="text-xs text-muted-fg dark:text-muted-dark">{errorMessage}</p>
            <button
              onClick={fetchExplanation}
              className="mt-2 px-3 py-1.5 text-xs font-semibold rounded-lg bg-rose-500 text-white hover:bg-rose-600 transition-colors inline-flex items-center gap-1.5"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              Retry Synthesis
            </button>
          </div>
        ) : (
          <div className="mt-6 text-center py-8 border border-dashed border-hairline dark:border-hairline-dark rounded-xl">
            <ShieldCheck className="w-6 h-6 mx-auto text-muted-fg mb-2 opacity-60" />
            <p className="text-xs text-muted-fg dark:text-muted-dark max-w-md mx-auto mb-3">
              {workflowRunId
                ? `No decision explanation has been synthesized for workflow run ${workflowRunId} yet.`
                : 'No decision explanation selected. Choose a workflow run from Audit Runs or click below to synthesize for current scenario.'}
            </p>
            <button
              onClick={fetchExplanation}
              disabled={loading}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-cobalt hover:bg-cobalt-hover text-white inline-flex items-center gap-2 transition-all disabled:opacity-50"
            >
              <Sparkles className="w-3.5 h-3.5" />
              Synthesize Explanation
            </button>
          </div>
        )}
      </div>

      {/* Tabs Navigation */}
      {explanation && !loading && (
        <div className="space-y-4">
          <div className="flex border-b border-hairline dark:border-hairline-dark gap-2 text-xs font-semibold">
            <button
              onClick={() => setActiveTab('rules')}
              className={`pb-2.5 px-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'rules'
                  ? 'border-cobalt text-cobalt'
                  : 'border-transparent text-muted-fg hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              <Scale className="w-4 h-4" />
              Gate Rules ({(explanation.constraint_results || []).length})
            </button>
            <button
              onClick={() => setActiveTab('counterexample')}
              className={`pb-2.5 px-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'counterexample'
                  ? 'border-cobalt text-cobalt'
                  : 'border-transparent text-muted-fg hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
              Counterexample Replay
            </button>
            <button
              onClick={() => setActiveTab('diagnostics')}
              className={`pb-2.5 px-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'diagnostics'
                  ? 'border-cobalt text-cobalt'
                  : 'border-transparent text-muted-fg hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              <Gauge className="w-4 h-4" />
              Measurements ({(explanation.uncertainty_changes || []).length})
            </button>
            <button
              onClick={() => setActiveTab('sensitivity')}
              className={`pb-2.5 px-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'sensitivity'
                  ? 'border-cobalt text-cobalt'
                  : 'border-transparent text-muted-fg hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              Sensitivity Gradients
            </button>
            <button
              onClick={() => setActiveTab('provenance')}
              className={`pb-2.5 px-3 border-b-2 flex items-center gap-2 transition-colors ${
                activeTab === 'provenance'
                  ? 'border-cobalt text-cobalt'
                  : 'border-transparent text-muted-fg hover:text-ink dark:hover:text-ink-dark'
              }`}
            >
              <Database className="w-4 h-4" />
              Evidence Provenance ({(explanation.evidence_items || []).length})
            </button>
          </div>

          {/* TAB 1: Deterministic Gate Rules */}
          {activeTab === 'rules' && (
            <div className="space-y-3">
              {(explanation.constraint_results || []).map((rule, idx) => {
                const isExpanded = expandedRule === rule.rule_id;
                return (
                  <div
                    key={rule.rule_id}
                    className="p-4 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark transition-all hover:border-cobalt/40"
                  >
                    <div
                      className="flex items-center justify-between cursor-pointer"
                      onClick={() => setExpandedRule(isExpanded ? null : rule.rule_id)}
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xs font-mono text-muted-fg dark:text-muted-dark">
                          #{idx + 1}
                        </span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-bold text-ink dark:text-ink-dark">
                              {rule.rule_name}
                            </span>
                            <span className="text-[10px] font-mono text-muted-fg px-1.5 py-0.5 rounded bg-hairline/20 dark:bg-hairline-dark">
                              {rule.rule_id}
                            </span>
                          </div>
                          <div className="text-[11px] text-muted-fg dark:text-muted-dark mt-0.5 font-mono">
                            Target: <span className="text-ink dark:text-ink-dark">{rule.target_metric}</span> | Observed:{' '}
                            <span className="font-semibold text-ink dark:text-ink-dark">
                              {rule.observed_value != null ? rule.observed_value.toFixed(2) : 'N/A'} {rule.unit}
                            </span>{' '}
                            (Condition: {rule.threshold_condition})
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-3">
                        {getStatusBadge(rule.status)}
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-muted-fg" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-muted-fg" />
                        )}
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="mt-3 pt-3 border-t border-hairline dark:border-hairline-dark text-xs text-ink dark:text-ink-dark space-y-2">
                        <p className="leading-relaxed bg-hairline/10 dark:bg-hairline-dark/20 p-3 rounded-lg">
                          {rule.explanation}
                        </p>
                        <div className="flex items-center justify-between text-[11px] font-mono text-muted-fg dark:text-muted-dark">
                          <span>Evidence Reference: {rule.supporting_evidence_ref}</span>
                          <span>Mandatory Predicate: {rule.is_mandatory ? 'YES' : 'NO'}</span>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* TAB 2: Counterexample Replay */}
          {activeTab === 'counterexample' && (
            <div className="p-5 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark space-y-4">
              {explanation.counterexample_summary ? (
                <>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                      <h4 className="text-xs font-bold text-ink dark:text-ink-dark uppercase tracking-wider">
                        Counterexample Parameter Vector & Margin Breach
                      </h4>
                    </div>
                    <span className="text-[11px] font-mono text-muted-fg">
                      {explanation.counterexample_summary.counterexample_id}
                    </span>
                  </div>

                  <p className="text-xs text-ink dark:text-ink-dark leading-relaxed">
                    {explanation.counterexample_summary.explanation}
                  </p>

                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                    <div className="p-3 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                      <span className="text-muted-fg block text-[10px]">Nominal Delay</span>
                      <span className="text-emerald-500 font-bold">
                        {explanation.counterexample_summary.nominal_latency_ms.toFixed(1)} ms
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                      <span className="text-muted-fg block text-[10px]">Perturbed Delay</span>
                      <span className="text-rose-500 font-bold">
                        {explanation.counterexample_summary.perturbed_latency_ms.toFixed(1)} ms
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                      <span className="text-muted-fg block text-[10px]">Latency SLO</span>
                      <span className="text-ink dark:text-ink-dark font-bold">
                        {explanation.counterexample_summary.slo_latency_ms.toFixed(1)} ms
                      </span>
                    </div>
                    <div className="p-3 rounded-lg bg-hairline/20 dark:bg-hairline-dark/40 border border-hairline dark:border-hairline-dark">
                      <span className="text-muted-fg block text-[10px]">Breach Margin</span>
                      <span className="text-rose-500 font-bold">
                        +{explanation.counterexample_summary.violation_margin_ms.toFixed(1)} ms
                      </span>
                    </div>
                  </div>

                  <div className="p-3 rounded-lg bg-hairline/10 dark:bg-hairline-dark/20 font-mono text-xs">
                    <span className="text-muted-fg text-[11px] block mb-1">Perturbation Vector:</span>
                    <pre className="text-cobalt">
                      {JSON.stringify(explanation.counterexample_summary.exact_parameter_vector, null, 2)}
                    </pre>
                  </div>
                </>
              ) : (
                <div className="text-center py-6 text-xs text-muted-fg">
                  No active counterexamples detected. Candidate route verified robust across all declared variations.
                </div>
              )}
            </div>
          )}

          {/* TAB 3: Diagnostic Measurements & Uncertainty Updates */}
          {activeTab === 'diagnostics' && (
            <div className="space-y-4">
              {(explanation.uncertainty_changes || []).length > 0 ? (
                (explanation.uncertainty_changes || []).map((u) => (
                  <div
                    key={u.cycle_number}
                    className="p-5 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Gauge className="w-4 h-4 text-cobalt" />
                        <h4 className="text-xs font-bold text-ink dark:text-ink-dark">
                          Cycle #{u.cycle_number}: {u.tool_name} ({u.tool_id})
                        </h4>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-500 border border-emerald-500/20 font-semibold">
                        -{u.width_reduction_pct.toFixed(1)}% Uncertainty Width
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                      <div className="p-3 rounded-lg bg-hairline/10 dark:bg-hairline-dark/30">
                        <span className="text-muted-fg block text-[10px]">Physical Raw Observation</span>
                        <span className="text-ink dark:text-ink-dark font-semibold">
                          {u.raw_measured_value != null ? `${u.raw_measured_value.toFixed(3)} ${u.raw_unit}` : 'N/A'}{' '}
                          {u.raw_error_bound ? `(±${u.raw_error_bound} ${u.raw_unit})` : ''}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-hairline/10 dark:bg-hairline-dark/30">
                        <span className="text-muted-fg block text-[10px]">Inverted Parameter Estimate</span>
                        <span className="text-cobalt font-semibold">
                          {u.parameter_measured_value.toFixed(4)} {u.parameter_unit} (±{u.parameter_error_bound.toFixed(4)})
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs font-mono">
                      <div className="p-3 rounded-lg bg-amber-500/5 border border-amber-500/20">
                        <span className="text-amber-500 block text-[10px]">Prior Uncertainty Interval</span>
                        <span className="font-semibold text-ink dark:text-ink-dark">
                          [{u.prior_interval[0].toFixed(4)}, {u.prior_interval[1].toFixed(4)}] {u.parameter_unit}
                        </span>
                      </div>
                      <div className="p-3 rounded-lg bg-emerald-500/5 border border-emerald-500/20">
                        <span className="text-emerald-500 block text-[10px]">Updated Posterior Interval</span>
                        <span className="font-semibold text-ink dark:text-ink-dark">
                          {u.posterior_interval
                            ? `[${u.posterior_interval[0].toFixed(4)}, ${u.posterior_interval[1].toFixed(4)}] ${u.parameter_unit}`
                            : 'REJECTED (INCONSISTENT)'}
                        </span>
                      </div>
                    </div>

                    <div className="text-[11px] text-muted-fg dark:text-muted-dark space-y-1">
                      <p>
                        <strong>Preserved Unrelated Dimensions:</strong>{' '}
                        {(u.unrelated_dimensions_preserved || []).join(', ') || 'All orthogonal parameters'}
                      </p>
                      <p>
                        <strong>Gate Impact:</strong> {u.subsequent_gate_impact}
                      </p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-5 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark text-center py-6 text-xs text-muted-fg">
                  No adaptive diagnostic cycles recorded for this evaluation.
                </div>
              )}
            </div>
          )}

          {/* TAB 4: Sensitivity Gradients */}
          {activeTab === 'sensitivity' && (
            explanation.sensitivity_results ? (
              <div className="p-5 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-cobalt" />
                    <h4 className="text-xs font-bold text-ink dark:text-ink-dark uppercase tracking-wider">
                      One-At-A-Time (OAT) Sensitivity Gradients
                    </h4>
                  </div>
                  <span className="text-xs font-mono text-muted-fg">
                    Primary Driver: {explanation.sensitivity_results.most_sensitive_parameter}
                  </span>
                </div>

                <div className="space-y-4">
                  {(explanation.sensitivity_results.evaluated_parameters || []).map((p) => (
                    <div key={p.parameter_name} className="p-3.5 rounded-lg bg-hairline/10 dark:bg-hairline-dark/20 space-y-2">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-ink dark:text-ink-dark font-mono">{p.parameter_name}</span>
                          {p.is_critical_bottleneck && (
                            <span className="px-1.5 py-0.5 rounded text-[10px] bg-rose-500/10 text-rose-500 font-semibold">
                              CRITICAL
                            </span>
                          )}
                        </div>
                        <span className="text-xs font-mono text-muted-fg">
                          Latency Elasticity: <strong className="text-ink dark:text-ink-dark">{p.latency_elasticity.toFixed(2)}</strong>
                        </span>
                      </div>

                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] font-mono">
                        {(p.perturbations || []).map((pert) => (
                          <div
                            key={pert.perturbation_pct}
                            className="p-2 rounded bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark"
                          >
                            <span className="text-muted-fg block">
                              {pert.perturbation_pct > 0 ? `+${pert.perturbation_pct}` : pert.perturbation_pct}%
                            </span>
                            <span className="text-ink dark:text-ink-dark font-semibold">
                              {pert.resulting_latency_ms.toFixed(1)} ms
                            </span>
                            <span className="text-[10px] text-muted-fg block">
                              {(pert.resulting_utilization * 100).toFixed(0)}% Util
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="p-3 rounded-lg bg-hairline/10 dark:bg-hairline-dark/30 text-[11px] text-muted-fg dark:text-muted-dark leading-relaxed">
                  <strong>Methodology Disclosure:</strong> {explanation.sensitivity_results.methodology_disclosure}
                </div>
              </div>
            ) : (
              <div className="p-5 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark text-center py-6 text-xs text-muted-fg">
                No sensitivity report available for this candidate.
              </div>
            )
          )}

          {/* TAB 5: Evidence Provenance */}
          {activeTab === 'provenance' && (
            <div className="space-y-3">
              {(explanation.evidence_items || []).map((item) => (
                <div
                  key={item.observation_id}
                  className="p-4 rounded-xl bg-paper dark:bg-card-dark border border-hairline dark:border-hairline-dark space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Database className="w-3.5 h-3.5 text-cobalt" />
                      <span className="text-xs font-bold font-mono text-ink dark:text-ink-dark">
                        {item.observation_id}
                      </span>
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cobalt/10 text-cobalt font-semibold">
                        {item.label_origin}
                      </span>
                    </div>
                    <span className="text-[11px] font-mono text-muted-fg">{item.timestamp}</span>
                  </div>

                  <p className="text-xs font-mono text-muted-fg break-all">
                    Metric: <span className="text-ink dark:text-ink-dark">{item.metric_name}</span> ={' '}
                    <strong className="text-cobalt">{item.value}</strong> {item.unit}
                  </p>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-[11px] font-mono text-muted-fg">
                    <div>Source: {item.source_dataset}</div>
                    <div>File: {item.source_file}</div>
                    <div>Quality: {item.data_quality_status}</div>
                  </div>

                  <div className="text-[11px] text-muted-fg bg-hairline/10 dark:bg-hairline-dark/20 p-2 rounded">
                    <strong>Descriptor:</strong> {item.relationship_descriptor} (Causal claim:{' '}
                    {item.is_causal_claim ? 'TRUE' : 'FALSE'})
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Knowledge Limitations Notice */}
          <div className="p-4 rounded-xl bg-amber-500/5 border border-amber-500/20 text-xs space-y-1.5">
            <div className="flex items-center gap-2 text-amber-500 font-bold uppercase tracking-wider text-[11px]">
              <Lock className="w-3.5 h-3.5" />
              Explicit Knowledge Limitations & Human Authorization Scope
            </div>
            {(explanation.limitations || []).map((lim, idx) => (
              <p key={idx} className="text-muted-fg dark:text-muted-dark leading-relaxed">
                • {lim}
              </p>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
