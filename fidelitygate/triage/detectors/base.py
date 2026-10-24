from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple
from ..models import AnomalyFinding, EvidenceItem
from ...ingestion.models import NormalizedObservation


class BaseDetector(ABC):
    """Abstract base detector for explainable, deterministic network telemetry triage."""

    name: str = "base_detector"
    version: str = "1.0.0"

    @abstractmethod
    def detect(
        self,
        observations: List[NormalizedObservation],
        config: Dict[str, Any],
        triage_run_id: str,
    ) -> Tuple[List[AnomalyFinding], List[EvidenceItem]]:
        """Processes normalized observation streams and returns findings with supporting evidence."""
        pass

