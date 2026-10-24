"""fidelitygate/investigation package
Layer 3: Bounded Agentic Investigation, Tool Use and Diagnostic Planning.
"""

from .models import (
    AgentMode,
    DiagnosticCandidate,
    DiagnosticPlan,
    Hypothesis,
    HypothesisType,
    InvestigationEvent,
    InvestigationReport,
    InvestigationRequest,
    InvestigationStatus,
    InvestigationSummary,
    PlanStatus,
)
from .tools import (
    ToolCall,
    ToolCategory,
    ToolDefinition,
    ToolRegistry,
    ToolResult,
)
from .investigator import AnomalyInvestigatorAgent
from .planner import DiagnosticPlannerAgent
from .llm_adapter import LLMAdapter
from .orchestrator import InvestigationOrchestrator

__all__ = [
    "AgentMode",
    "DiagnosticCandidate",
    "DiagnosticPlan",
    "Hypothesis",
    "HypothesisType",
    "InvestigationEvent",
    "InvestigationReport",
    "InvestigationRequest",
    "InvestigationStatus",
    "InvestigationSummary",
    "PlanStatus",
    "ToolCall",
    "ToolCategory",
    "ToolDefinition",
    "ToolRegistry",
    "ToolResult",
    "AnomalyInvestigatorAgent",
    "DiagnosticPlannerAgent",
    "LLMAdapter",
    "InvestigationOrchestrator",
]

