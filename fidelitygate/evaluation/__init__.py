"""fidelitygate/evaluation/__init__.py
Layer 4: Candidate Mitigation Evaluation, Digital-Twin Simulation, and SLO Verification.
"""

from .models import (
    CandidateAction,
    CandidateComparison,
    CandidateEvaluation,
    CandidateEvaluationStatus,
    EvaluationEvent,
    LinkSimulationResult,
    MitigationActionType,
    MitigationEvaluationReport,
    MitigationEvaluationRequest,
    MitigationEvaluationSummary,
    NetworkTopology,
    PathValidationResult,
    ReferenceEvaluationResult,
    ReferenceEvaluationStatus,
    SimulationPrediction,
    TopologyEdge,
    TopologyNode,
    TrafficFlow,
    ValidationStatus,
)
from .validator import CandidatePathValidator
from .simulator import InsufficientModelDataError, NetworkSimulator
from .uncertainty_evaluator import CandidateUncertaintyEvaluator
from .reference_evaluator import IndependentReferenceEvaluator
from .topologies import (
    SCENARIO_TOPOLOGIES,
    create_fiber_drift_topology,
    create_traffic_burst_topology,
    create_wan_congestion_topology,
    get_topology_for_scenario,
)
from .engine import MitigationEvaluationEngine

__all__ = [
    "CandidateAction",
    "CandidateComparison",
    "CandidateEvaluation",
    "CandidateEvaluationStatus",
    "EvaluationEvent",
    "LinkSimulationResult",
    "MitigationActionType",
    "MitigationEvaluationReport",
    "MitigationEvaluationRequest",
    "MitigationEvaluationSummary",
    "NetworkTopology",
    "PathValidationResult",
    "ReferenceEvaluationResult",
    "ReferenceEvaluationStatus",
    "SimulationPrediction",
    "TopologyEdge",
    "TopologyNode",
    "TrafficFlow",
    "ValidationStatus",
    "CandidatePathValidator",
    "InsufficientModelDataError",
    "NetworkSimulator",
    "CandidateUncertaintyEvaluator",
    "IndependentReferenceEvaluator",
    "SCENARIO_TOPOLOGIES",
    "create_fiber_drift_topology",
    "create_traffic_burst_topology",
    "create_wan_congestion_topology",
    "get_topology_for_scenario",
    "MitigationEvaluationEngine",
]

