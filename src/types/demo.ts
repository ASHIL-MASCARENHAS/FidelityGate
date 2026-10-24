import {
  WorkflowRunSummary,
  WorkflowEvent,
  HumanApprovalRecord,
  InterventionOutcomeReport,
  WorkflowStage,
  WorkflowStatus,
  GateDecisionType,
} from '@/types';

export type AutoDemoState =
  | 'IDLE'
  | 'NO_WORKFLOW'
  | 'STATUS_POPUP'
  | 'VIEWING'
  | 'PAUSED'
  | 'AWAITING_APPROVAL_PAUSE'
  | 'COMPLETED'
  | 'STOPPED';

export interface AutoDemoContext {
  selectedWorkflowRunId: string | null;
  selectedWorkflow: WorkflowRunSummary | null;
  workflowStatus: WorkflowStatus | null;
  currentStage: WorkflowStage | null;
  gateVerdict: GateDecisionType | null;
  selectedCandidateId: string | null;
  triageRunId: string | null;
  investigationId: string | null;
  evaluationId: string | null;
  adaptiveRunId: string | null;
  explanationId: string | null;
  approvalId: string | null;
  outcomeId: string | null;
  workflowEventsCount: number;
  hasApproval: boolean;
  hasOutcome: boolean;
  scenarioId: string | null;
  outcomeReport: InterventionOutcomeReport | null;
  approvalRecord: HumanApprovalRecord | null;
}

export interface AutoDemoStep {
  id: string;
  tabId: string;
  tabLabel: string;
  title: string;
  getHeading: (ctx: AutoDemoContext) => string;
  getDescription: (ctx: AutoDemoContext) => string;
  getNextPreview: (ctx: AutoDemoContext) => string;
  dwellSeconds?: number;
  isOptional?: boolean;
}

