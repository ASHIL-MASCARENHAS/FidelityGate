'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useWorkflowRun } from '@/context/WorkflowRunContext';
import { AUTO_DEMO_STEPS } from '@/config/autoDemoSteps';
import { AutoDemoState, AutoDemoContext } from '@/types/demo';
import { playTick, playConfirmation } from '@/lib/sound';

interface UseAutoDemoProps {
  activeTab: string;
  setActiveTab: (tabId: string) => void;
  soundEnabled?: boolean;
}

export function useAutoDemo({
  activeTab,
  setActiveTab,
  soundEnabled = false,
}: UseAutoDemoProps) {
  const {
    selectedWorkflowRunId,
    selectedWorkflow,
    workflowStatus,
    currentStage,
    gateVerdict,
    selectedCandidateId,
    triageRunId,
    investigationId,
    evaluationId,
    adaptiveRunId,
    explanationId,
    approvalId,
    outcomeId,
    workflowEvents,
    approvalRecord,
    outcomeReport,
    scenarioId,
  } = useWorkflowRun();

  const [demoState, setDemoState] = useState<AutoDemoState>('IDLE');
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [popupCountdown, setPopupCountdown] = useState<number>(5);
  const [viewingCountdown, setViewingCountdown] = useState<number>(5);
  const [isPaused, setIsPaused] = useState<boolean>(false);

  // Timer references for robust cleanup
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevRunIdRef = useRef<string | null>(selectedWorkflowRunId);
  const prevStageRef = useRef<string | null>(currentStage);

  const clearTimer = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  }, []);

  // Assemble current typed context from shared run store
  const context: AutoDemoContext = useMemo(
    () => ({
      selectedWorkflowRunId,
      selectedWorkflow,
      workflowStatus,
      currentStage,
      gateVerdict,
      selectedCandidateId,
      triageRunId,
      investigationId,
      evaluationId,
      adaptiveRunId,
      explanationId,
      approvalId,
      outcomeId,
      workflowEventsCount: workflowEvents?.length || 0,
      hasApproval: !!approvalRecord,
      hasOutcome: !!outcomeReport,
      scenarioId: scenarioId || null,
      outcomeReport,
      approvalRecord,
    }),
    [
      selectedWorkflowRunId,
      selectedWorkflow,
      workflowStatus,
      currentStage,
      gateVerdict,
      selectedCandidateId,
      triageRunId,
      investigationId,
      evaluationId,
      adaptiveRunId,
      explanationId,
      approvalId,
      outcomeId,
      workflowEvents,
      approvalRecord,
      outcomeReport,
      scenarioId,
    ]
  );

  const currentStep = AUTO_DEMO_STEPS[currentStepIndex] || AUTO_DEMO_STEPS[0];
  const totalSteps = AUTO_DEMO_STEPS.length;

  // Stop tour if user changes the selected workflow while tour is active
  useEffect(() => {
    if (prevRunIdRef.current !== selectedWorkflowRunId) {
      prevRunIdRef.current = selectedWorkflowRunId;
      if (demoState !== 'IDLE' && demoState !== 'NO_WORKFLOW') {
        clearTimer();
        setDemoState('IDLE');
        setIsPaused(false);
      }
    }
  }, [selectedWorkflowRunId, demoState, clearTimer]);

  // Detect when human approval is granted while paused at Stage 11
  useEffect(() => {
    if (demoState === 'AWAITING_APPROVAL_PAUSE') {
      const isNowApprovedOrCompleted =
        currentStage === 'SIMULATED_ACTION' ||
        currentStage === 'OUTCOME_REPORTED' ||
        workflowStatus === 'APPROVED' ||
        workflowStatus === 'COMPLETED';

      if (isNowApprovedOrCompleted && prevStageRef.current === 'AWAITING_HUMAN_APPROVAL') {
        playConfirmation(soundEnabled);
        // Switch to viewing the post-action outcome for 5s before advancing
        setViewingCountdown(5);
        setDemoState('VIEWING');
      }
    }
    prevStageRef.current = currentStage;
  }, [currentStage, workflowStatus, demoState, soundEnabled]);

  // Main navigation action to execute the current step transition
  const executeStepNavigation = useCallback(
    (stepIdx: number) => {
      clearTimer();
      const targetStep = AUTO_DEMO_STEPS[stepIdx];
      if (!targetStep) {
        setDemoState('COMPLETED');
        return;
      }

      // Navigate to destination tab
      setActiveTab(targetStep.tabId);

      // Check if paused at human approval boundary
      const isWorkflowTab = targetStep.tabId === 'workflow';
      const isAwaitingApproval =
        currentStage === 'AWAITING_HUMAN_APPROVAL' ||
        workflowStatus === 'AWAITING_APPROVAL';

      if (isWorkflowTab && isAwaitingApproval) {
        setDemoState('AWAITING_APPROVAL_PAUSE');
      } else {
        setViewingCountdown(targetStep.dwellSeconds || 5);
        setDemoState('VIEWING');
      }
    },
    [clearTimer, setActiveTab, currentStage, workflowStatus]
  );

  // Advance to next step (from viewing or skip)
  const advanceToNextStep = useCallback(() => {
    clearTimer();
    if (currentStepIndex < totalSteps - 1) {
      const nextIdx = currentStepIndex + 1;
      setCurrentStepIndex(nextIdx);
      setPopupCountdown(5);
      setDemoState('STATUS_POPUP');
    } else {
      setDemoState('COMPLETED');
    }
  }, [clearTimer, currentStepIndex, totalSteps]);

  // Countdown timer in STATUS_POPUP
  useEffect(() => {
    if (demoState === 'STATUS_POPUP' && !isPaused) {
      clearTimer();
      intervalRef.current = setInterval(() => {
        setPopupCountdown((prev) => {
          if (prev <= 1) {
            clearTimer();
            executeStepNavigation(currentStepIndex);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearTimer();
    }
  }, [demoState, isPaused, currentStepIndex, executeStepNavigation, clearTimer]);

  // Countdown timer in VIEWING
  useEffect(() => {
    if (demoState === 'VIEWING' && !isPaused) {
      clearTimer();
      intervalRef.current = setInterval(() => {
        setViewingCountdown((prev) => {
          if (prev <= 1) {
            clearTimer();
            advanceToNextStep();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);

      return () => clearTimer();
    }
  }, [demoState, isPaused, advanceToNextStep, clearTimer]);

  // Start Auto Demo
  const startAutoDemo = useCallback(() => {
    clearTimer();
    if (!selectedWorkflowRunId) {
      setDemoState('NO_WORKFLOW');
      return;
    }
    setCurrentStepIndex(0);
    setPopupCountdown(5);
    setIsPaused(false);
    setDemoState('STATUS_POPUP');
  }, [clearTimer, selectedWorkflowRunId]);

  // Stop Auto Demo
  const stopAutoDemo = useCallback(() => {
    clearTimer();
    setDemoState('IDLE');
    setIsPaused(false);
  }, [clearTimer]);

  // Toggle Pause/Resume
  const togglePause = useCallback(() => {
    setIsPaused((prev) => !prev);
  }, []);

  // Continue immediately from popup
  const continueFromPopup = useCallback(() => {
    clearTimer();
    executeStepNavigation(currentStepIndex);
  }, [clearTimer, executeStepNavigation, currentStepIndex]);

  // Skip step
  const skipCurrentStep = useCallback(() => {
    advanceToNextStep();
  }, [advanceToNextStep]);

  // Restart demo
  const restartDemo = useCallback(() => {
    clearTimer();
    setCurrentStepIndex(0);
    setPopupCountdown(5);
    setIsPaused(false);
    setDemoState('STATUS_POPUP');
  }, [clearTimer]);

  // Cleanup timers on unmount
  useEffect(() => {
    return () => clearTimer();
  }, [clearTimer]);

  return {
    demoState,
    currentStep,
    currentStepIndex,
    totalSteps,
    context,
    popupCountdown,
    viewingCountdown,
    isPaused,
    isAwaitingApprovalPause: demoState === 'AWAITING_APPROVAL_PAUSE',
    isAutoDemoRunning:
      demoState === 'STATUS_POPUP' ||
      demoState === 'VIEWING' ||
      demoState === 'AWAITING_APPROVAL_PAUSE',
    startAutoDemo,
    stopAutoDemo,
    togglePause,
    continueFromPopup,
    skipCurrentStep,
    advanceToNextStep,
    restartDemo,
    setDemoState,
  };
}

