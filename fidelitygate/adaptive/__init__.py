"""fidelitygate/adaptive/__init__.py
Layer 5 Counterexample-Guided Adaptive Diagnostics, Measurement Models,
Uncertainty Interval Updates, and Decision Re-evaluation.
"""

from .models import (
    MeasurementErrorType,
    ObservationMode,
    MeasurementModel,
    DiagnosticObservation,
    UncertaintyInterval,
    UncertaintyUpdate,
    DiagnosticCandidateEvaluation,
    DiagnosticExecutionRecord,
    AdaptiveCycleResult,
    AdaptiveRunStatus,
    AdaptiveInvestigationRequest,
    AdaptiveInvestigationSummary,
    AdaptiveInvestigationReport,
    AdaptiveEvent,
)
from .measurement_registry import (
    ALLOWLISTED_MEASUREMENT_MODELS,
    DiagnosticMeasurementRegistry,
)
from .uncertainty_updater import (
    InconsistentMeasurementError,
    UncertaintyUpdater,
)
from .selector import (
    AdaptiveDiagnosticSelector,
)
from .engine import (
    AdaptiveInvestigationEngine,
)

__all__ = [
    "MeasurementErrorType",
    "ObservationMode",
    "MeasurementModel",
    "DiagnosticObservation",
    "UncertaintyInterval",
    "UncertaintyUpdate",
    "DiagnosticCandidateEvaluation",
    "DiagnosticExecutionRecord",
    "AdaptiveCycleResult",
    "AdaptiveRunStatus",
    "AdaptiveInvestigationRequest",
    "AdaptiveInvestigationSummary",
    "AdaptiveInvestigationReport",
    "AdaptiveEvent",
    "ALLOWLISTED_MEASUREMENT_MODELS",
    "DiagnosticMeasurementRegistry",
    "InconsistentMeasurementError",
    "UncertaintyUpdater",
    "AdaptiveDiagnosticSelector",
    "AdaptiveInvestigationEngine",
]

