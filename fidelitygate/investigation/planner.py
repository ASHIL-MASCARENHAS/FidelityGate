"""fidelitygate/investigation/planner.py
Agent B: Diagnostic and Mitigation Planner.
Consumes Agent A's validated InvestigationReport, ranks allowlisted diagnostic actions,
and formulates candidate mitigation interventions for digital-twin evaluation.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from ..diagnostics import DIAGNOSTIC_TOOLS
from .llm_adapter import LLMAdapter
from .models import (
    AgentMode,
    DiagnosticCandidate,
    DiagnosticPlan,
    InvestigationReport,
    InvestigationStatus,
    PlanStatus,
)
from .tools import ToolCall, ToolRegistry


class DiagnosticPlannerAgent:
    """Agent B: Specializes in diagnostic selection and mitigation proposal planning."""

    ROLE_NAME = "Agent_B_Planner"

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None):
        self.llm = llm_adapter or LLMAdapter()

    def plan(
        self,
        investigation_id: str,
        report: InvestigationReport,
        tools: ToolRegistry,
        preferred_mode: Optional[AgentMode] = None,
        max_diagnostics: int = 3,
    ) -> Tuple[DiagnosticPlan, List[Dict[str, Any]]]:
        """Formulates actionable DiagnosticPlan based on Agent A's report and tool catalog."""
        events: List[Dict[str, Any]] = []

        # 1. Validation of Agent A's report
        if report.status == InvestigationStatus.INSUFFICIENT_EVIDENCE or not report.hypotheses:
            plan = DiagnosticPlan(
                plan_id=f"plan-{uuid4().hex[:8]}",
                investigation_id=investigation_id,
                candidate_diagnostics=[],
                selected_diagnostic_id=None,
                proposed_interventions=[],
                stop_conditions=["Insufficient investigation evidence to justify diagnostic expenditure."],
                budget_remaining={
                    "diagnostic_calls_remaining": tools.max_diagnostic_calls - tools.diagnostic_call_count,
                    "usd_remaining": round(tools.diagnostic_budget_usd - tools.cumulative_cost_usd, 4),
                },
                limitations=["No diagnostic candidates formed due to insufficient evidence in Agent A report."],
                status=PlanStatus.INSUFFICIENT_EVIDENCE,
            )
            events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": self.ROLE_NAME,
                "event_type": "PLANNING_ABORTED",
                "details": {"reason": "Agent A report had status INSUFFICIENT_EVIDENCE"}
            })
            return plan, events

        # 2. Query Approved Diagnostic Catalog via Tool Call
        cat_call = ToolCall(
            tool_name="list_diagnostic_catalog",
            arguments={},
            caller_role=self.ROLE_NAME,
            investigation_id=investigation_id,
        )
        cat_result = tools.execute_tool(cat_call)
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.ROLE_NAME,
            "event_type": "TOOL_CALL",
            "details": {"tool": "list_diagnostic_catalog", "success": cat_result.success}
        })

        catalog = cat_result.data.get("catalog", []) if cat_result.success and cat_result.data else []
        allowed_tool_ids: Set[str] = {t["tool_id"] for t in catalog}

        # 3. Formulate Candidate Diagnostics
        candidates: List[DiagnosticCandidate] = []
        rank = 1

        for hyp in report.hypotheses:
            # Map hypothesis type to allowlisted diagnostic tool
            if hyp.hypothesis_type.value in ["FORWARDING_DROP_SURGE", "BGP_SESSION_FLAP"]:
                tool_id = "snmp_interface_poll"
            elif hyp.hypothesis_type.value in ["CONTROL_PLANE_CPU_SPIKE", "UNCONFIRMED_ANOMALY"]:
                tool_id = "active_rtt_probe"
            elif hyp.hypothesis_type.value == "BUFFER_CONGESTION":
                tool_id = "passive_telemetry_flow"
            else:
                tool_id = "active_rtt_probe"

            if tool_id in allowed_tool_ids and not any(c.diagnostic_id == tool_id for c in candidates):
                tool_info = DIAGNOSTIC_TOOLS[tool_id]
                candidates.append(
                    DiagnosticCandidate(
                        diagnostic_id=tool_id,
                        tool_name=tool_info["name"],
                        target_entity=hyp.statement.split("'")[1] if "'" in hyp.statement else "0/RP0/CPU0",
                        target_parameter=tool_info["target_parameter"],
                        purpose=f"Resolves uncertainty in hypothesis '{hyp.hypothesis_id}' regarding {tool_info['target_parameter']}.",
                        related_finding_ids=report.primary_finding_ids[:5],
                        related_evidence_ids=hyp.supporting_evidence_ids[:5],
                        expected_information_type=f"Bounded measurement of {tool_info['unit']} with ±{tool_info['declared_error_bound']} error.",
                        estimated_cost_usd=tool_info["cost_usd"],
                        availability_status="AVAILABLE",
                        rank=rank,
                    )
                )
                rank += 1
                if len(candidates) >= max_diagnostics:
                    break

        # Fallback if catalog matching was empty
        if not candidates and catalog:
            first_tool = catalog[0]
            candidates.append(
                DiagnosticCandidate(
                    diagnostic_id=first_tool["tool_id"],
                    tool_name=first_tool["name"],
                    target_entity="0/RP0/CPU0",
                    target_parameter=first_tool["target_parameter"],
                    purpose="Baseline diagnostic probe to evaluate physical transit delay.",
                    related_finding_ids=report.primary_finding_ids[:3],
                    related_evidence_ids=report.supporting_evidence_ids[:3],
                    expected_information_type=f"Measurement with declared error ±{first_tool['declared_error_bound']}.",
                    estimated_cost_usd=first_tool["cost_usd"],
                    availability_status="AVAILABLE",
                    rank=1,
                )
            )

        # 4. Propose Candidate Mitigation Action via Tool Call
        reroute_id = f"R-{report.scenario_id or 'reroute'}-alt1"
        reroute_call = ToolCall(
            tool_name="propose_candidate_reroute",
            arguments={
                "route_id": reroute_id,
                "path": ["leaf1", "spine2", "leaf6"],
                "rationale": "Bypasses congested primary forwarding plane through alternate spine transit."
            },
            caller_role=self.ROLE_NAME,
            investigation_id=investigation_id,
        )
        reroute_result = tools.execute_tool(reroute_call)
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.ROLE_NAME,
            "event_type": "TOOL_CALL",
            "details": {"tool": "propose_candidate_reroute", "route_id": reroute_id, "success": reroute_result.success}
        })

        # 5. Budget Calculation
        calls_remaining = max(tools.max_diagnostic_calls - tools.diagnostic_call_count, 0)
        usd_remaining = max(round(tools.diagnostic_budget_usd - tools.cumulative_cost_usd, 4), 0.0)

        # 6. Stop Conditions & Limitations
        stop_conditions = [
            "Stop diagnostics immediately if cumulative cost exceeds $0.05 USD.",
            "If diagnostic measurement confirms SLO breach, immediately transition to ABSTAIN (fail-closed).",
            "Candidate reroute cannot be enacted without independent digital-twin simulation and human operator approval."
        ]

        limitations = [
            "Planner evaluates candidate diagnostics from an allowlisted catalog; it does not execute live network changes.",
            "Selected diagnostic must be dispatched and validated by Orchestrator before gate re-evaluation.",
            "Digital-twin latency and capacity constraints will be deterministically verified in subsequent layers."
        ]

        selected_id = candidates[0].diagnostic_id if candidates else None

        plan = DiagnosticPlan(
            plan_id=f"plan-{uuid4().hex[:8]}",
            investigation_id=investigation_id,
            candidate_diagnostics=candidates,
            selected_diagnostic_id=selected_id,
            proposed_interventions=[reroute_id] if reroute_result.success else [],
            stop_conditions=stop_conditions,
            budget_remaining={
                "diagnostic_calls_remaining": calls_remaining,
                "usd_remaining": usd_remaining,
                "max_tool_calls_permitted": tools.max_tool_calls,
            },
            limitations=limitations,
            status=PlanStatus.READY if candidates else PlanStatus.NO_USEFUL_DIAGNOSTIC,
        )

        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.ROLE_NAME,
            "event_type": "PLAN_GENERATED",
            "details": {
                "plan_id": plan.plan_id,
                "candidates_count": len(plan.candidate_diagnostics),
                "selected_diagnostic": plan.selected_diagnostic_id,
                "status": plan.status.value,
            }
        })

        return plan, events

