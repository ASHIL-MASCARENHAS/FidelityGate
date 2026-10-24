"""fidelitygate/investigation/tools.py
Typed, allowlisted tool registry with strict permission boundaries, budgets, and security controls.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Type
from pydantic import BaseModel, Field

from ..diagnostics import DIAGNOSTIC_TOOLS, execute_diagnostic
from ..triage.models import InvestigationContext


class ToolCategory(str, Enum):
    READ = "READ"
    PROPOSE_ACTION = "PROPOSE_ACTION"
    MEASURE = "MEASURE"
    STATE_CHANGE = "STATE_CHANGE"


class ToolCall(BaseModel):
    """Structured request by an agent to execute an allowlisted tool."""
    tool_name: str
    arguments: Dict[str, Any]
    caller_role: str = Field(..., description="Role of the invoking agent (e.g. Agent_A_Investigator)")
    investigation_id: str


class ToolResult(BaseModel):
    """Structured response from tool execution."""
    tool_name: str
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0


@dataclass
class ToolDefinition:
    name: str
    description: str
    category: ToolCategory
    allowed_callers: Set[str]
    input_schema: Type[BaseModel]
    handler: Callable[..., Dict[str, Any]]
    cost_usd: float = 0.0
    timeout_seconds: float = 5.0
    requires_orchestrator_approval: bool = False


# ==========================================
# Tool Input Schemas
# ==========================================

class ReadObservationInput(BaseModel):
    evidence_id: Optional[str] = None
    entity_id: Optional[str] = None
    metric_name: Optional[str] = None


class GetCaseMetadataInput(BaseModel):
    triage_run_id: str


class QueryMetricWindowInput(BaseModel):
    entity_id: str
    metric_name: str
    limit: int = 10


class InspectTopologyInput(BaseModel):
    scenario_id: Optional[str] = None


class ListDiagnosticCatalogInput(BaseModel):
    target_parameter: Optional[str] = None


class ProposeCandidateRerouteInput(BaseModel):
    route_id: str
    path: List[str]
    rationale: str


class ExecuteDiagnosticProbeInput(BaseModel):
    tool_id: str
    target_entity: str
    target_parameter: str


# ==========================================
# Tool Registry Implementation
# ==========================================

class ToolRegistry:
    """Enforces strict allowlisting, parameter validation, caller permissions, and budget constraints."""

    def __init__(
        self,
        storage: Any = None,
        context: Optional[InvestigationContext] = None,
        max_tool_calls: int = 10,
        max_diagnostic_calls: int = 3,
        diagnostic_budget_usd: float = 0.05,
    ):
        self.storage = storage
        self.context = context
        self.max_tool_calls = max_tool_calls
        self.max_diagnostic_calls = max_diagnostic_calls
        self.diagnostic_budget_usd = diagnostic_budget_usd

        self.tool_call_count = 0
        self.diagnostic_call_count = 0
        self.cumulative_cost_usd = 0.0

        self.tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        self.register(
            ToolDefinition(
                name="read_observation",
                description="Query specific telemetry evidence or observation details by evidence ID or entity.",
                category=ToolCategory.READ,
                allowed_callers={"Agent_A_Investigator", "Agent_B_Planner", "Orchestrator"},
                input_schema=ReadObservationInput,
                handler=self._handle_read_observation,
            )
        )
        self.register(
            ToolDefinition(
                name="get_case_metadata",
                description="Retrieve documented experiment case event metadata (e.g. Cisco BGP clear event tables).",
                category=ToolCategory.READ,
                allowed_callers={"Agent_A_Investigator", "Orchestrator"},
                input_schema=GetCaseMetadataInput,
                handler=self._handle_get_case_metadata,
            )
        )
        self.register(
            ToolDefinition(
                name="query_metric_window",
                description="Retrieve baseline and observed metric window comparisons for an entity.",
                category=ToolCategory.READ,
                allowed_callers={"Agent_A_Investigator", "Agent_B_Planner", "Orchestrator"},
                input_schema=QueryMetricWindowInput,
                handler=self._handle_query_metric_window,
            )
        )
        self.register(
            ToolDefinition(
                name="inspect_topology",
                description="Query network nodes, roles, and declared interfaces from scenario context.",
                category=ToolCategory.READ,
                allowed_callers={"Agent_A_Investigator", "Agent_B_Planner", "Orchestrator"},
                input_schema=InspectTopologyInput,
                handler=self._handle_inspect_topology,
            )
        )
        self.register(
            ToolDefinition(
                name="list_diagnostic_catalog",
                description="Query approved diagnostic catalog with parameters, declared error bounds, and execution costs.",
                category=ToolCategory.READ,
                allowed_callers={"Agent_B_Planner", "Orchestrator"},
                input_schema=ListDiagnosticCatalogInput,
                handler=self._handle_list_diagnostic_catalog,
            )
        )
        self.register(
            ToolDefinition(
                name="propose_candidate_reroute",
                description="Formulate and register a candidate network mitigation reroute for subsequent digital-twin evaluation.",
                category=ToolCategory.PROPOSE_ACTION,
                allowed_callers={"Agent_B_Planner", "Orchestrator"},
                input_schema=ProposeCandidateRerouteInput,
                handler=self._handle_propose_candidate_reroute,
            )
        )
        self.register(
            ToolDefinition(
                name="execute_diagnostic_probe",
                description="Execute an allowlisted diagnostic measurement with declared error bounds. Requires Orchestrator authorization.",
                category=ToolCategory.MEASURE,
                allowed_callers={"Orchestrator"},  # Forbidden to agents directly!
                input_schema=ExecuteDiagnosticProbeInput,
                handler=self._handle_execute_diagnostic_probe,
                requires_orchestrator_approval=True,
            )
        )

    def register(self, tool_def: ToolDefinition) -> None:
        self.tools[tool_def.name] = tool_def

    def execute_tool(self, call: ToolCall) -> ToolResult:
        # 1. Budget Checks
        if self.tool_call_count >= self.max_tool_calls:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Tool call budget exhausted (max {self.max_tool_calls} calls permitted)."
            )

        # 2. Allowlist Check
        if call.tool_name not in self.tools:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Unauthorized or unknown tool '{call.tool_name}'. Permitted tools: {list(self.tools.keys())}"
            )

        tool_def = self.tools[call.tool_name]

        # 3. Caller Permission Check
        if call.caller_role not in tool_def.allowed_callers:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Access denied: Role '{call.caller_role}' is not authorized to call '{call.tool_name}'."
            )

        # 4. Reference Evaluator Isolation Boundary Check
        args_str = str(call.arguments).lower()
        forbidden_references = ["hidden_ground_truth", "reference_evaluator", "evaluator_ground_truth", "counterfactual_latency"]
        for forbidden in forbidden_references:
            if forbidden in args_str:
                return ToolResult(
                    tool_name=call.tool_name,
                    success=False,
                    error=f"Security violation: Reference evaluator data '{forbidden}' is strictly isolated and inaccessible."
                )

        # 5. Schema Validation
        try:
            validated_args = tool_def.input_schema(**call.arguments)
        except Exception as exc:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Invalid arguments for tool '{call.tool_name}': {str(exc)}"
            )

        # 6. Execute Handler
        try:
            self.tool_call_count += 1
            result_data = tool_def.handler(validated_args)
            return ToolResult(
                tool_name=call.tool_name,
                success=True,
                data=result_data,
            )
        except Exception as exc:
            return ToolResult(
                tool_name=call.tool_name,
                success=False,
                error=f"Tool execution failure: {str(exc)}"
            )

    # ==========================================
    # Handler Implementations
    # ==========================================

    def _handle_read_observation(self, args: ReadObservationInput) -> Dict[str, Any]:
        if not self.context:
            return {"observations": [], "message": "No active investigation context loaded."}

        matching = []
        for ev in self.context.correlated_evidence:
            if args.evidence_id and ev.evidence_id == args.evidence_id:
                matching.append(ev.model_dump())
            elif args.entity_id and ev.entity_id == args.entity_id:
                if not args.metric_name or ev.metric_name == args.metric_name:
                    matching.append(ev.model_dump())

        return {
            "evidence_count": len(matching),
            "evidence_items": matching[:10],
        }

    def _handle_get_case_metadata(self, args: GetCaseMetadataInput) -> Dict[str, Any]:
        if not self.context or not self.context.source_defined_event_metadata:
            return {"case_metadata": None, "message": "No source-defined case metadata present in context."}
        return {"case_metadata": self.context.source_defined_event_metadata}

    def _handle_query_metric_window(self, args: QueryMetricWindowInput) -> Dict[str, Any]:
        if not self.context:
            return {"comparisons": [], "message": "No active context."}

        comps = [
            c for c in self.context.baseline_comparisons
            if c.get("entity_id") == args.entity_id and c.get("metric_name") == args.metric_name
        ]
        return {
            "entity_id": args.entity_id,
            "metric_name": args.metric_name,
            "comparisons": comps[:args.limit],
        }

    def _handle_inspect_topology(self, args: InspectTopologyInput) -> Dict[str, Any]:
        from ..scenarios import DEMO_SCENARIOS
        scenario_key = args.scenario_id or (self.context.scenario_id if self.context else "wan_congestion")
        scenario = DEMO_SCENARIOS.get(scenario_key or "wan_congestion")
        if not scenario:
            return {
                "nodes": ["0/RP0/CPU0", "0/0/CPU0", "0/1/CPU0", "leaf1", "spine2"],
                "notice": "Representative nodes from ingested Cisco telemetry stream. Full physical adjacency omitted."
            }
        return {
            "scenario_id": scenario.scenario_id,
            "name": scenario.name,
            "primary_path": getattr(scenario, "primary_path", ["leaf1", "spine1", "leaf6"]),
            "nominal_latency_ms": scenario.nominal_latency_ms,
            "slo_latency_ms": scenario.slo_latency_ms,
            "offered_load_mbps": scenario.offered_load_mbps,
            "capacity_mbps": scenario.capacity_mbps,
            "limitations": ["Omitted physical link adjacency matrix in source telemetry CSV."]
        }

    def _handle_list_diagnostic_catalog(self, args: ListDiagnosticCatalogInput) -> Dict[str, Any]:
        catalog = []
        for tool_id, tool_info in DIAGNOSTIC_TOOLS.items():
            if args.target_parameter and args.target_parameter not in tool_info.get("target_parameter", ""):
                continue
            catalog.append({
                "tool_id": tool_id,
                "name": tool_info["name"],
                "target_parameter": tool_info["target_parameter"],
                "unit": tool_info["unit"],
                "declared_error_bound": tool_info["declared_error_bound"],
                "cost_usd": tool_info["cost_usd"],
                "execution_time_ms": tool_info["execution_time_ms"],
                "description": tool_info["description"],
            })
        return {"catalog": catalog}

    def _handle_propose_candidate_reroute(self, args: ProposeCandidateRerouteInput) -> Dict[str, Any]:
        return {
            "status": "REGISTERED",
            "candidate_route_id": args.route_id,
            "proposed_path": args.path,
            "rationale": args.rationale,
            "next_step": "Awaiting digital-twin simulation in Layer 5."
        }

    def _handle_execute_diagnostic_probe(self, args: ExecuteDiagnosticProbeInput) -> Dict[str, Any]:
        from ..scenarios import DEMO_SCENARIOS
        if self.diagnostic_call_count >= self.max_diagnostic_calls:
            raise RuntimeError(f"Diagnostic probe budget exhausted ({self.max_diagnostic_calls} probes executed).")

        tool_spec = DIAGNOSTIC_TOOLS.get(args.tool_id)
        if not tool_spec:
            raise ValueError(f"Unknown diagnostic tool '{args.tool_id}'.")

        cost = tool_spec.get("cost_usd", 0.0)
        if self.cumulative_cost_usd + cost > self.diagnostic_budget_usd:
            raise RuntimeError(f"Diagnostic probe exceeds cost budget of ${self.diagnostic_budget_usd:.3f}.")

        # Use demo scenario or default
        scenario = DEMO_SCENARIOS.get("wan_congestion")
        obs = execute_diagnostic(args.tool_id, scenario, simulated_ground_truth_factor=1.05)

        self.diagnostic_call_count += 1
        self.cumulative_cost_usd += cost

        return {
            "tool_id": obs.tool_id,
            "tool_name": obs.tool_name,
            "target_entity": args.target_entity,
            "target_parameter": obs.target_parameter,
            "measured_value": obs.measured_value,
            "unit": obs.unit,
            "declared_error_bound": obs.declared_error_bound,
            "confidence_interval": obs.confidence_interval,
            "cost_usd": obs.cost_usd,
            "observation_summary": obs.observation_summary,
        }
