"""fidelitygate/xai/__init__.py
Layer 6: Evidence-Based Explainable AI, Decision Attribution and Local Sensitivity.
"""

from .counterexample_explainer import CounterexampleExplainer
from .engine import ExplanationEngine
from .measurement_explainer import MeasurementExplainer
from .models import (
    CounterexampleExplanation,
    DecisionExplanation,
    ExplanationMode,
    ExplanationRequest,
    ExplanationSummary,
    GateRuleExplanation,
    LocalSensitivityReport,
    ParameterSensitivity,
    ProvenanceItem,
    RuleStatus,
    UncertaintyExplanation,
)
from .rule_explainer import GateRuleExplainer
from .sensitivity_analyzer import SensitivityAnalyzer
from .summary_generator import DecisionSummaryGenerator

__all__ = [
    "RuleStatus",
    "ExplanationMode",
    "GateRuleExplanation",
    "CounterexampleExplanation",
    "ProvenanceItem",
    "UncertaintyExplanation",
    "ParameterSensitivity",
    "LocalSensitivityReport",
    "DecisionExplanation",
    "ExplanationRequest",
    "ExplanationSummary",
    "GateRuleExplainer",
    "CounterexampleExplainer",
    "MeasurementExplainer",
    "SensitivityAnalyzer",
    "DecisionSummaryGenerator",
    "ExplanationEngine",
]

