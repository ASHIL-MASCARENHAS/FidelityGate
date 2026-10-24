from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..models import (
    AnomalyFinding,
    EvidenceItem,
    EvidenceType,
    FindingSeverity,
    FindingStatus,
    LabelOrigin,
)
from ..priority import PriorityScorer
from .base import BaseDetector
from ...ingestion.models import NormalizedObservation


class StepChangeDetector(BaseDetector):
    """Detects sudden consecutive jumps and relative step changes across observations."""

    name: str = "step_change_detector"
    version: str = "1.0.0"

    def detect(
        self,
        observations: List[NormalizedObservation],
        config: Dict[str, Any],
        triage_run_id: str,
    ) -> Tuple[List[AnomalyFinding], List[EvidenceItem]]:
        relative_threshold = config.get("relative_threshold", 1.5)  # 150% jump
        absolute_thresholds = config.get("absolute_thresholds", {
            "total-number-of-drop-packets": 50.0,
            "total-cpu-one-minute": 30.0,
            "input-drops": 10.0,
        })
        min_samples = config.get("min_samples", 3)

        findings: List[AnomalyFinding] = []
        evidence_items: List[EvidenceItem] = []

        series_map: Dict[Tuple[str, str, str], List[NormalizedObservation]] = defaultdict(list)
        for obs in observations:
            key = (obs.entity_type, obs.entity_id, obs.metric_name)
            series_map[key].append(obs)

        for (entity_type, entity_id, metric_name), obs_list in series_map.items():
            if len(obs_list) < min_samples:
                continue

            sorted_obs = sorted(obs_list, key=lambda o: (o.timestamp or "", o.observation_id))

            for i in range(1, len(sorted_obs)):
                prev_obs = sorted_obs[i - 1]
                curr_obs = sorted_obs[i]

                delta = curr_obs.value - prev_obs.value
                rel_change: Optional[float] = None
                has_nonzero_denom = abs(prev_obs.value) > 1e-6

                if has_nonzero_denom:
                    rel_change = delta / abs(prev_obs.value)

                is_anomaly = False
                abs_thresh = absolute_thresholds.get(metric_name)

                if abs_thresh is not None and abs(delta) >= abs_thresh:
                    is_anomaly = True
                elif rel_change is not None and abs(rel_change) >= relative_threshold:
                    is_anomaly = True

                if is_anomaly:
                    ev_prev_id = f"ev-step-prev-{uuid4().hex[:8]}"
                    ev_curr_id = f"ev-step-curr-{uuid4().hex[:8]}"

                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=ev_prev_id,
                            source_dataset=prev_obs.source_dataset,
                            source_version=prev_obs.source_version,
                            source_file=prev_obs.provenance.get("source_file", "unknown"),
                            source_row_or_event_reference=prev_obs.provenance.get("source_row_index", 0),
                            timestamp=prev_obs.timestamp,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            metric_name=metric_name,
                            value=prev_obs.value,
                            unit=prev_obs.unit,
                            quality_status=prev_obs.quality_status,
                            evidence_type=EvidenceType.DIRECT_OBSERVATION,
                        )
                    )
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=ev_curr_id,
                            source_dataset=curr_obs.source_dataset,
                            source_version=curr_obs.source_version,
                            source_file=curr_obs.provenance.get("source_file", "unknown"),
                            source_row_or_event_reference=curr_obs.provenance.get("source_row_index", 0),
                            timestamp=curr_obs.timestamp,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            metric_name=metric_name,
                            value=curr_obs.value,
                            unit=curr_obs.unit,
                            quality_status=curr_obs.quality_status,
                            evidence_type=EvidenceType.DIRECT_OBSERVATION,
                        )
                    )

                    limitations = []
                    if not has_nonzero_denom:
                        limitations.append("Previous value was zero; relative change undefined")

                    severity = PriorityScorer.calculate_severity(
                        metric_name=metric_name,
                        observed_value=curr_obs.value,
                        baseline_value=prev_obs.value,
                        deviation_score=rel_change,
                        label_origin=LabelOrigin.RULE_BASED,
                        entity_id=entity_id,
                    )
                    confidence = PriorityScorer.calculate_confidence(
                        sample_count=len(sorted_obs),
                        label_origin=LabelOrigin.RULE_BASED,
                        quality_status=curr_obs.quality_status,
                        unit=curr_obs.unit,
                    )

                    finding = AnomalyFinding(
                        anomaly_id=f"anom-step-{uuid4().hex[:8]}",
                        triage_run_id=triage_run_id,
                        source_dataset=curr_obs.source_dataset,
                        source_version=curr_obs.source_version,
                        scenario_id=curr_obs.scenario_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        metric_name=metric_name,
                        window_start=prev_obs.timestamp,
                        window_end=curr_obs.timestamp,
                        detector_name=self.name,
                        detector_version=self.version,
                        observed_value=curr_obs.value,
                        baseline_value=prev_obs.value,
                        deviation_score=round(rel_change, 3) if rel_change is not None else None,
                        severity=severity,
                        confidence=confidence,
                        label_origin=LabelOrigin.RULE_BASED,
                        status=FindingStatus.CANDIDATE,
                        evidence_ids=[ev_prev_id, ev_curr_id],
                        limitations=limitations,
                    )
                    findings.append(finding)

        return findings, evidence_items

