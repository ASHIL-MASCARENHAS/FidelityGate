"""fidelitygate/investigation/orchestrator.py
Bounded multi-agent workflow orchestrator coordinating Agent A, Agent B,
typed tool permissions, budget enforcement, and SQLite persistence.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from .investigator import AnomalyInvestigatorAgent
from .llm_adapter import LLMAdapter
from .models import (
    AgentMode,
    DiagnosticPlan,
    InvestigationEvent,
    InvestigationReport,
    InvestigationRequest,
    InvestigationStatus,
    InvestigationSummary,
    PlanStatus,
)
from .planner import DiagnosticPlannerAgent
from .tools import ToolCall, ToolRegistry


class InvestigationOrchestrator:
    """Orchestrates bounded agentic investigation and diagnostic planning."""

    def __init__(self, storage: Optional[Any] = None):
        if storage is None:
            from ..storage import StorageEngine
            self.storage = StorageEngine()
        else:
            self.storage = storage
        self.llm_adapter = LLMAdapter()
        self.investigator = AnomalyInvestigatorAgent(self.llm_adapter)
        self.planner = DiagnosticPlannerAgent(self.llm_adapter)

    def run_investigation(
        self,
        request: InvestigationRequest,
        execute_selected_probe: bool = False,
    ) -> Tuple[InvestigationSummary, InvestigationReport, DiagnosticPlan, List[InvestigationEvent]]:
        """Executes full Layer 3 workflow:
        Triage Context -> Agent A (Investigator) -> InvestigationReport -> Agent B (Planner) -> DiagnosticPlan.
        """
        investigation_id = f"inv-{uuid4().hex[:8]}"
        events: List[InvestigationEvent] = []

        # 1. Load Layer 2 InvestigationContext
        context = self.storage.get_investigation_context(request.triage_run_id)
        if not context:
            raise ValueError(
                f"Triage run '{request.triage_run_id}' not found or has no persisted InvestigationContext."
            )

        events.append(
            InvestigationEvent(
                event_id=f"evt-{uuid4().hex[:8]}",
                investigation_id=investigation_id,
                actor="Orchestrator",
                event_type="INVESTIGATION_STARTED",
                details={
                    "triage_run_id": request.triage_run_id,
                    "source_dataset": context.source_dataset,
                    "findings_count": len(context.primary_anomaly_candidates),
                }
            )
        )

        # 2. Initialize Tool Registry
        tools = ToolRegistry(
            storage=self.storage,
            context=context,
        )

        # 3. Agent A: Anomaly Investigator
        report, a_events = self.investigator.investigate(
            investigation_id=investigation_id,
            context=context,
            tools=tools,
            preferred_mode=request.agent_mode,
            max_hypotheses=request.max_hypotheses,
        )
        for raw_e in a_events:
            events.append(
                InvestigationEvent(
                    event_id=f"evt-{uuid4().hex[:8]}",
                    investigation_id=investigation_id,
                    actor=raw_e["actor"],
                    event_type=raw_e["event_type"],
                    details=raw_e.get("details", {})
                )
            )

        # 4. Agent B: Diagnostic and Mitigation Planner
        plan, b_events = self.planner.plan(
            investigation_id=investigation_id,
            report=report,
            tools=tools,
            preferred_mode=request.agent_mode,
            max_diagnostics=request.max_diagnostics,
        )
        for raw_e in b_events:
            events.append(
                InvestigationEvent(
                    event_id=f"evt-{uuid4().hex[:8]}",
                    investigation_id=investigation_id,
                    actor=raw_e["actor"],
                    event_type=raw_e["event_type"],
                    details=raw_e.get("details", {})
                )
            )

        # 5. Optional Orchestrator-Controlled Diagnostic Probe Execution
        if execute_selected_probe and plan.selected_diagnostic_id and plan.status == PlanStatus.READY:
            probe_call = ToolCall(
                tool_name="execute_diagnostic_probe",
                arguments={
                    "tool_id": plan.selected_diagnostic_id,
                    "target_entity": plan.candidate_diagnostics[0].target_entity if plan.candidate_diagnostics else "0/RP0/CPU0",
                    "target_parameter": plan.candidate_diagnostics[0].target_parameter if plan.candidate_diagnostics else "latency",
                },
                caller_role="Orchestrator",
                investigation_id=investigation_id,
            )
            probe_result = tools.execute_tool(probe_call)
            events.append(
                InvestigationEvent(
                    event_id=f"evt-{uuid4().hex[:8]}",
                    investigation_id=investigation_id,
                    actor="Orchestrator",
                    event_type="DIAGNOSTIC_PROBE_EXECUTED",
                    details={
                        "tool_id": plan.selected_diagnostic_id,
                        "success": probe_result.success,
                        "result": probe_result.data if probe_result.success else probe_result.error,
                    }
                )
            )

        # 6. Build Summary
        completed_at = datetime.now(timezone.utc).isoformat()
        summary = InvestigationSummary(
            investigation_id=investigation_id,
            triage_run_id=request.triage_run_id,
            scenario_id=request.scenario_id or context.scenario_id,
            agent_mode=report.agent_mode,
            status=report.status,
            hypotheses_count=len(report.hypotheses),
            candidate_diagnostics_count=len(plan.candidate_diagnostics),
            selected_diagnostic_id=plan.selected_diagnostic_id,
            created_at=report.created_at,
            completed_at=completed_at,
            fallback_reason=self.llm_adapter.last_failure_reason,
        )

        events.append(
            InvestigationEvent(
                event_id=f"evt-{uuid4().hex[:8]}",
                investigation_id=investigation_id,
                actor="Orchestrator",
                event_type="INVESTIGATION_COMPLETED",
                details={
                    "status": summary.status.value,
                    "agent_mode": summary.agent_mode.value,
                    "hypotheses_count": summary.hypotheses_count,
                    "diagnostics_count": summary.candidate_diagnostics_count,
                }
            )
        )

        # 7. Persist to SQLite
        self.storage.save_investigation(
            summary=summary,
            report=report,
            plan=plan,
            events=events,
        )

        return summary, report, plan, events
