"""fidelitygate.workflow package
Layer 7 End-to-End Decision Assurance Workflow Orchestrator.
"""

from .models import (
    ApprovalDecision,
    ApprovalRequest,
    HumanApprovalRecord,
    InterventionOutcomeReport,
    OverallImpact,
    SimulatedInterventionRecord,
    WorkflowEvent,
    WorkflowRunRequest,
    WorkflowRunSummary,
    WorkflowStage,
    WorkflowStatus,
)
from .outcome import OutcomeReporter
from .simulation_adapter import SimulationActionAdapter

def __getattr__(name: str):
    if name == "EndToEndWorkflowOrchestrator":
        from .orchestrator import EndToEndWorkflowOrchestrator
        return EndToEndWorkflowOrchestrator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    "ApprovalDecision",
    "ApprovalRequest",
    "EndToEndWorkflowOrchestrator",
    "HumanApprovalRecord",
    "InterventionOutcomeReport",
    "OutcomeReporter",
    "OverallImpact",
    "SimulatedInterventionRecord",
    "SimulationActionAdapter",
    "WorkflowEvent",
    "WorkflowRunRequest",
    "WorkflowRunSummary",
    "WorkflowStage",
    "WorkflowStatus",
]
