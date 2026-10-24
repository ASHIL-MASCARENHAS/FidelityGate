'use client';

import React, { createContext, useContext, useState, useEffect, useCallback, useRef } from 'react';
import {
  WorkflowRunSummary,
  WorkflowEvent,
  HumanApprovalRecord,
  InterventionOutcomeReport,
  WorkflowStage,
  WorkflowStatus,
  GateDecisionType,
  ApprovalDecision,
  OverallImpact,
  SelectedRunContextType,
} from '@/types';

const WorkflowRunContext = createContext<SelectedRunContextType | undefined>(undefined);

export function WorkflowRunProvider({
  children,
  initialRunId,
}: {
  children: React.ReactNode;
  initialRunId?: string;
}) {
  const [selectedWorkflowRunId, setSelectedWorkflowRunId] = useState<string | null>(initialRunId || null);
  const [selectedWorkflow, setSelectedWorkflow] = useState<WorkflowRunSummary | null>(null);
  const [workflowEvents, setWorkflowEvents] = useState<WorkflowEvent[]>([]);
  const [approvalRecord, setApprovalRecord] = useState<HumanApprovalRecord | null>(null);
  const [outcomeReport, setOutcomeReport] = useState<InterventionOutcomeReport | null>(null);
  const [lastRefreshedAt, setLastRefreshedAt] = useState<string | null>(null);
  const [isStale, setIsStale] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Active request tracking to avoid race conditions when switching runs rapidly
  const activeFetchIdRef = useRef<string | null>(null);

  const fetchRunArtifacts = useCallback(async (runId: string) => {
    activeFetchIdRef.current = runId;
    setIsLoading(true);
    setError(null);

    try {
      // 1. Fetch canonical workflow summary
      const resSum = await fetch(`/api/v1/workflows/${runId}`, { cache: 'no-store' });
      if (activeFetchIdRef.current !== runId) return;

      if (!resSum.ok) {
        const errJson = await resSum.json().catch(() => ({}));
        throw new Error(errJson.detail || errJson.error || `Workflow '${runId}' not found`);
      }
      const summary: WorkflowRunSummary = await resSum.json();
      if (activeFetchIdRef.current !== runId) return;
      setSelectedWorkflow(summary);

      // 2. Fetch monotonically sequenced workflow events
      try {
        const resEvents = await fetch(`/api/v1/workflows/${runId}/events`, { cache: 'no-store' });
        if (activeFetchIdRef.current === runId && resEvents.ok) {
          const eventsData = await resEvents.json();
          setWorkflowEvents(Array.isArray(eventsData) ? eventsData : []);
        } else if (activeFetchIdRef.current === runId) {
          setWorkflowEvents([]);
        }
      } catch {
        if (activeFetchIdRef.current === runId) setWorkflowEvents([]);
      }

      // 3. Fetch human approval record if stage >= AWAITING_HUMAN_APPROVAL or approval_id exists
      try {
        const resAppr = await fetch(`/api/v1/workflows/${runId}/approval`, { cache: 'no-store' });
        if (activeFetchIdRef.current === runId && resAppr.ok) {
          const apprData = await resAppr.json();
          setApprovalRecord(apprData);
        } else if (activeFetchIdRef.current === runId) {
          setApprovalRecord(null);
        }
      } catch {
        if (activeFetchIdRef.current === runId) setApprovalRecord(null);
      }

      // 4. Fetch intervention outcome report if outcome_id exists or workflow is completed
      try {
        const resOut = await fetch(`/api/v1/workflows/${runId}/outcome`, { cache: 'no-store' });
        if (activeFetchIdRef.current === runId && resOut.ok) {
          const outData = await resOut.json();
          setOutcomeReport(outData);
        } else if (activeFetchIdRef.current === runId) {
          setOutcomeReport(null);
        }
      } catch {
        if (activeFetchIdRef.current === runId) setOutcomeReport(null);
      }

      if (activeFetchIdRef.current === runId) {
        setLastRefreshedAt(new Date().toISOString());
        setIsStale(false);
      }
    } catch (err: any) {
      if (activeFetchIdRef.current === runId) {
        setError(err.message || 'Failed to load workflow run');
      }
    } finally {
      if (activeFetchIdRef.current === runId) {
        setIsLoading(false);
      }
    }
  }, []);

  const clearSelectedWorkflow = useCallback(() => {
    activeFetchIdRef.current = null;
    setSelectedWorkflowRunId(null);
    setSelectedWorkflow(null);
    setWorkflowEvents([]);
    setApprovalRecord(null);
    setOutcomeReport(null);
    setLastRefreshedAt(null);
    setIsStale(false);
    setIsLoading(false);
    setError(null);
  }, []);

  const selectWorkflowRun = useCallback(async (runId: string) => {
    if (!runId) {
      clearSelectedWorkflow();
      return;
    }
    setSelectedWorkflowRunId(runId);
    await fetchRunArtifacts(runId);
  }, [fetchRunArtifacts, clearSelectedWorkflow]);

  const setWorkflowSummary = useCallback((summary: WorkflowRunSummary) => {
    setSelectedWorkflowRunId(summary.workflow_run_id);
    setSelectedWorkflow(summary);
    setLastRefreshedAt(new Date().toISOString());
    setIsStale(false);
    // Fetch associated events, approval, outcome in background
    fetchRunArtifacts(summary.workflow_run_id);
  }, [fetchRunArtifacts]);

  const refreshSelectedWorkflow = useCallback(async () => {
    if (selectedWorkflowRunId) {
      await fetchRunArtifacts(selectedWorkflowRunId);
    }
  }, [selectedWorkflowRunId, fetchRunArtifacts]);

  // Initial load if initialRunId was provided
  useEffect(() => {
    if (initialRunId) {
      selectWorkflowRun(initialRunId);
    }
  }, [initialRunId, selectWorkflowRun]);

  const value: SelectedRunContextType = {
    selectedWorkflowRunId,
    selectedWorkflow,
    scenarioId: selectedWorkflow?.scenario_id || 'wan_congestion',
    workflowStatus: selectedWorkflow?.status || null,
    currentStage: selectedWorkflow?.current_stage || null,
    gateVerdict: selectedWorkflow?.gate_verdict || null,
    selectedCandidateId: selectedWorkflow?.selected_candidate_id || null,
    triageRunId: selectedWorkflow?.triage_run_id || null,
    investigationId: selectedWorkflow?.investigation_id || null,
    evaluationId: selectedWorkflow?.evaluation_id || null,
    adaptiveRunId: selectedWorkflow?.adaptive_run_id || null,
    explanationId: selectedWorkflow?.explanation_id || null,
    approvalId: selectedWorkflow?.approval_id || null,
    outcomeId: selectedWorkflow?.outcome_id || null,
    lastRefreshedAt,
    isStale,
    isLoading,
    error,
    workflowEvents,
    approvalRecord,
    outcomeReport,
    selectWorkflowRun,
    setWorkflowSummary,
    refreshSelectedWorkflow,
    clearSelectedWorkflow,
  };

  return (
    <WorkflowRunContext.Provider value={value}>
      {children}
    </WorkflowRunContext.Provider>
  );
}

export function useWorkflowRun(): SelectedRunContextType {
  const context = useContext(WorkflowRunContext);
  if (!context) {
    throw new Error('useWorkflowRun must be used within a WorkflowRunProvider');
  }
  return context;
}
