import math
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

# Metrics that represent cumulative counters rather than instantaneous gauges
CUMULATIVE_COUNTER_METRICS = {
    "bytes-received",
    "bytes-sent",
    "packets-received",
    "packets-sent",
    "total-number-of-drop-packets",
    "no-route-packets",
    "discard-packets",
    "checksum-error-packets",
    "input-drops",
    "output-drops",
    "input-errors",
    "output-errors",
    "crc-errors",
}


def compute_median(values: List[float]) -> float:
    sorted_v = sorted(values)
    n = len(sorted_v)
    if n == 0:
        return 0.0
    mid = n // 2
    if n % 2 == 1:
        return sorted_v[mid]
    return (sorted_v[mid - 1] + sorted_v[mid]) / 2.0


def compute_mad(values: List[float], median_val: float) -> float:
    deviations = [abs(v - median_val) for v in values]
    return compute_median(deviations)


def compute_std(values: List[float], mean_val: float) -> float:
    if len(values) < 2:
        return 0.0
    var = sum((v - mean_val) ** 2 for v in values) / (len(values) - 1)
    return math.sqrt(max(var, 0.0))


class RobustStatisticalDetector(BaseDetector):
    """Detects metric outliers using robust Median Absolute Deviation (MAD) scaling.
    Formula: robust_score = 0.6745 * (value - median) / MAD.
    """

    name: str = "robust_mad_detector"
    version: str = "1.0.0"

    def detect(
        self,
        observations: List[NormalizedObservation],
        config: Dict[str, Any],
        triage_run_id: str,
    ) -> Tuple[List[AnomalyFinding], List[EvidenceItem]]:
        z_threshold = config.get("z_threshold", 3.5)
        min_samples = config.get("min_samples", 5)
        metrics_filter = config.get("metrics_filter")
        entities_filter = config.get("entities_filter")

        findings: List[AnomalyFinding] = []
        evidence_items: List[EvidenceItem] = []

        # 1. Group observations by (entity_type, entity_id, metric_name)
        series_map: Dict[Tuple[str, str, str], List[NormalizedObservation]] = defaultdict(list)
        for obs in observations:
            if metrics_filter and obs.metric_name not in metrics_filter:
                continue
            if entities_filter and obs.entity_id not in entities_filter:
                continue
            key = (obs.entity_type, obs.entity_id, obs.metric_name)
            series_map[key].append(obs)

        # 2. Analyze each series
        for (entity_type, entity_id, metric_name), obs_list in series_map.items():
            if len(obs_list) < min_samples:
                continue

            # Sort chronologically by timestamp (None timestamps placed at end)
            sorted_obs = sorted(obs_list, key=lambda o: (o.timestamp or "", o.observation_id))

            # Handle cumulative counters vs gauges
            is_cumulative = metric_name in CUMULATIVE_COUNTER_METRICS
            raw_values: List[float] = []
            obs_indices: List[int] = []
            has_counter_reset = False

            if is_cumulative:
                for idx in range(1, len(sorted_obs)):
                    prev_v = sorted_obs[idx - 1].value
                    curr_v = sorted_obs[idx].value
                    if curr_v < prev_v:
                        # Counter reset detected - do NOT compute negative delta
                        has_counter_reset = True
                        continue
                    delta = curr_v - prev_v
                    raw_values.append(delta)
                    obs_indices.append(idx)
            else:
                for idx, o in enumerate(sorted_obs):
                    raw_values.append(o.value)
                    obs_indices.append(idx)

            if len(raw_values) < min_samples:
                continue

            # Compute robust baseline metrics
            median_val = compute_median(raw_values)
            mad_val = compute_mad(raw_values, median_val)
            std_val = compute_std(raw_values, median_val)

            has_mad_fallback = False
            fallback_reason: Optional[str] = None
            if mad_val < 1e-9:
                has_mad_fallback = True
                fallback_reason = "MAD was zero (invariant baseline); robust score unavailable, evaluated via step difference"

            # Baseline evidence item
            baseline_ev_id = f"ev-base-{uuid4().hex[:8]}"
            evidence_items.append(
                EvidenceItem(
                    evidence_id=baseline_ev_id,
                    source_dataset=sorted_obs[0].source_dataset,
                    source_version=sorted_obs[0].source_version,
                    source_file=sorted_obs[0].provenance.get("source_file", "unknown"),
                    source_row_or_event_reference=f"Window N={len(raw_values)}",
                    timestamp=sorted_obs[0].timestamp,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    metric_name=metric_name,
                    value=median_val,
                    unit=sorted_obs[0].unit,
                    quality_status="VALID",
                    evidence_type=EvidenceType.BASELINE_WINDOW,
                    transformation="median",
                    limitations=[fallback_reason] if fallback_reason else [],
                )
            )

            # Evaluate each point against baseline
            for i, val in enumerate(raw_values):
                target_obs = sorted_obs[obs_indices[i]]
                score: Optional[float] = None
                is_anomalous = False

                if not has_mad_fallback:
                    # Canonical formula: 0.6745 * (val - median) / MAD
                    score = 0.6745 * (val - median_val) / mad_val
                    if abs(score) >= z_threshold:
                        is_anomalous = True
                else:
                    # Invariant baseline (MAD is zero): mark score unavailable and evaluate step diff
                    step_diff = abs(val - median_val)
                    if step_diff > 1e-6:
                        score = None  # Explicitly unavailable, division by zero prevented
                        is_anomalous = True

                if is_anomalous:
                    obs_ev_id = f"ev-obs-{uuid4().hex[:8]}"
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=obs_ev_id,
                            source_dataset=target_obs.source_dataset,
                            source_version=target_obs.source_version,
                            source_file=target_obs.provenance.get("source_file", "unknown"),
                            source_row_or_event_reference=target_obs.provenance.get("source_row_index", 0),
                            timestamp=target_obs.timestamp,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            metric_name=metric_name,
                            value=val,
                            unit=target_obs.unit,
                            quality_status=target_obs.quality_status,
                            evidence_type=EvidenceType.DIRECT_OBSERVATION if not is_cumulative else EvidenceType.DERIVED_RATE,
                            transformation="delta_rate" if is_cumulative else None,
                            limitations=[fallback_reason] if fallback_reason else [],
                        )
                    )

                    severity = PriorityScorer.calculate_severity(
                        metric_name=metric_name,
                        observed_value=val,
                        baseline_value=median_val,
                        deviation_score=score,
                        label_origin=LabelOrigin.STATISTICAL_DETECTOR,
                        entity_id=entity_id,
                    )
                    confidence = PriorityScorer.calculate_confidence(
                        sample_count=len(raw_values),
                        label_origin=LabelOrigin.STATISTICAL_DETECTOR,
                        quality_status=target_obs.quality_status,
                        unit=target_obs.unit,
                        has_mad_fallback=has_mad_fallback,
                    )

                    finding_limitations = []
                    if fallback_reason:
                        finding_limitations.append(fallback_reason)
                    if has_counter_reset:
                        finding_limitations.append("Series contained counter reset event")
                    if target_obs.unit is None:
                        finding_limitations.append("Undocumented source metric unit")

                    finding = AnomalyFinding(
                        anomaly_id=f"anom-stat-{uuid4().hex[:8]}",
                        triage_run_id=triage_run_id,
                        source_dataset=target_obs.source_dataset,
                        source_version=target_obs.source_version,
                        scenario_id=target_obs.scenario_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        metric_name=metric_name,
                        window_start=sorted_obs[0].timestamp,
                        window_end=sorted_obs[-1].timestamp,
                        detector_name=self.name,
                        detector_version=self.version,
                        observed_value=val,
                        baseline_value=median_val,
                        deviation_score=round(score, 3) if score is not None else None,
                        severity=severity,
                        confidence=confidence,
                        label_origin=LabelOrigin.STATISTICAL_DETECTOR,
                        status=FindingStatus.CANDIDATE,
                        evidence_ids=[baseline_ev_id, obs_ev_id],
                        limitations=finding_limitations,
                    )
                    findings.append(finding)

        return findings, evidence_items
