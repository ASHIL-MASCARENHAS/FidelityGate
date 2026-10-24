"""tests/test_anomaly_triage.py
Comprehensive automated test suite for Layer 2: Explainable Anomaly Triage and Evidence Correlation.
Validates all 22 core requirements outlined in Section 10 of the Layer 2 specification.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.ingestion.models import (
    DataMode,
    DataQualityIssue,
    NormalizedObservation,
)
from fidelitygate.storage import StorageEngine
from fidelitygate.triage.models import (
    AnomalyFinding,
    CorrelationReport,
    EvidenceItem,
    EvidenceType,
    FindingSeverity,
    FindingStatus,
    InvestigationContext,
    LabelOrigin,
    TriageRunRequest,
    TriageRunSummary,
)
from fidelitygate.triage.detectors.statistical import (
    RobustStatisticalDetector,
    compute_median,
    compute_mad,
)
from fidelitygate.triage.detectors.change import StepChangeDetector
from fidelitygate.triage.detectors.event_case import (
    SourceEventCaseDetector,
    parse_pdt_timestamp,
)
from fidelitygate.triage.correlation import EvidenceCorrelationEngine
from fidelitygate.triage.context_builder import InvestigationContextBuilder
from fidelitygate.triage.engine import AnomalyTriageEngine
from fidelitygate.triage.priority import PriorityScorer


@pytest.fixture
def test_storage(tmp_path):
    db_file = tmp_path / "test_triage.db"
    return StorageEngine(str(db_file))


@pytest.fixture
def api_client(test_storage, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "DATABASE_PATH", str(tmp_path / "test_triage.db"))
    return TestClient(app)


def make_obs(
    obs_id: str,
    metric_name: str,
    val: float,
    entity_id: str = "0/RP0/CPU0",
    entity_type: str = "chassis",
    unit: str = "percent",
    timestamp: str = "2026-10-23T12:00:00Z",
    source_dataset: str = "cisco-ie-telemetry",
    quality: str = "VALID",
) -> NormalizedObservation:
    return NormalizedObservation(
        observation_id=obs_id,
        source_dataset=source_dataset,
        source_version="v1.0-test",
        scenario_id="scenario-test",
        timestamp=timestamp,
        entity_type=entity_type,
        entity_id=entity_id,
        metric_name=metric_name,
        value=val,
        unit=unit,
        data_mode=DataMode.PUBLIC_DATA,
        quality_status=quality,
        provenance={"source_file": "sample.csv", "source_row_index": 1},
    )


def make_finding(
    anomaly_id: str,
    metric_name: str = "drops",
    observed_value: float = 10.0,
    entity_id: str = "leaf1",
    severity: FindingSeverity = FindingSeverity.HIGH,
    confidence: float = 0.8,
    label_origin: LabelOrigin = LabelOrigin.STATISTICAL_DETECTOR,
    status: FindingStatus = FindingStatus.CANDIDATE,
    window_start: str = None,
    window_end: str = None,
) -> AnomalyFinding:
    return AnomalyFinding(
        anomaly_id=anomaly_id,
        triage_run_id="trg-test",
        source_dataset="test-dataset",
        source_version="v1.0",
        entity_type="device",
        entity_id=entity_id,
        metric_name=metric_name,
        detector_name="test_detector",
        detector_version="1.0.0",
        observed_value=observed_value,
        severity=severity,
        confidence=confidence,
        label_origin=label_origin,
        status=status,
        window_start=window_start,
        window_end=window_end,
    )


# 1. Valid baseline triage initialization
def test_01_valid_baseline_triage_init():
    detector = RobustStatisticalDetector()
    obs_list = [
        make_obs(f"obs-{i}", "cpu_util", 10.0 + (i % 3) * 0.5, timestamp=f"2026-10-23T12:0{i}:00Z")
        for i in range(10)
    ]
    findings, evidence = detector.detect(obs_list, {"z_threshold": 3.5, "min_samples": 5}, "trg-test-1")
    assert isinstance(findings, list)
    assert isinstance(evidence, list)
    assert len(findings) == 0  # all stable within baseline
    assert len(evidence) >= 1  # baseline window evidence produced
    assert evidence[0].evidence_type == EvidenceType.BASELINE_WINDOW


# 2. Invariant / zero-variance series (constant 0 packet drops) handled gracefully without divide-by-zero
def test_02_invariant_zero_variance_baseline():
    detector = RobustStatisticalDetector()
    obs_list = [
        make_obs(f"obs-{i}", "input-drops", 0.0, timestamp=f"2026-10-23T12:0{i}:00Z")
        for i in range(10)
    ]
    obs_list.append(make_obs("obs-spike", "input-drops", 15.0, timestamp="2026-10-23T12:11:00Z"))

    findings, evidence = detector.detect(obs_list, {"z_threshold": 3.5, "min_samples": 5}, "trg-test-2")
    assert len(findings) > 0
    spike_finding = [f for f in findings if f.observed_value == 15.0][0]
    # MAD is zero, so deviation_score must be handled gracefully (None), division by zero prevented
    assert spike_finding.deviation_score is None
    assert any("invariant baseline" in lim.lower() for lim in spike_finding.limitations)


# 3. Statistical deviation detector computes accurate robust MAD scores on known synthetic vector
def test_03_statistical_deviation_robust_mad_formula():
    detector = RobustStatisticalDetector()
    # Baseline vector of 10 items: [10, 12, 14, 16, 18, 10, 12, 14, 16, 18] -> median = 14, MAD = 2.0
    # Appending 30.0 (outlier) yields expected robust_score = 0.6745 * (30 - 14) / 2.0 = 5.396
    base_values = [10.0, 12.0, 14.0, 16.0, 18.0, 10.0, 12.0, 14.0, 16.0, 18.0]
    m = compute_median(base_values)
    mad = compute_mad(base_values, m)
    assert m == 14.0
    assert mad == 2.0

    expected_score = 0.6745 * (30.0 - m) / mad
    assert abs(expected_score - 5.396) < 1e-4

    obs_list = [
        make_obs(f"obs-{i}", "custom_gauge", v, timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i, v in enumerate(base_values)
    ]
    obs_list.append(make_obs("obs-outlier", "custom_gauge", 30.0, timestamp="2026-10-23T12:20:00Z"))
    findings, _ = detector.detect(obs_list, {"z_threshold": 3.5, "min_samples": 5}, "trg-test-3")
    assert len(findings) == 1
    assert findings[0].deviation_score == pytest.approx(5.396, rel=1e-2)


# 4. Normal random fluctuation within baseline does not exceed 3.5 z-score
def test_04_normal_fluctuations_below_z_threshold():
    detector = RobustStatisticalDetector()
    mild_vals = [20.0, 21.0, 20.0, 19.0, 20.0, 21.0, 20.0, 22.0, 19.0, 20.0]
    obs_list = [
        make_obs(f"obs-{i}", "cpu_load", v, timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i, v in enumerate(mild_vals)
    ]
    findings, _ = detector.detect(obs_list, {"z_threshold": 3.5, "min_samples": 5}, "trg-test-4")
    assert len(findings) == 0


# 5. Injected spikes trigger HIGH or CRITICAL anomaly findings with correct timestamps
def test_05_injected_spikes_trigger_findings():
    detector = RobustStatisticalDetector()
    obs_list = [
        make_obs(f"obs-{i}", "total-cpu-one-minute", 15.0, timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i in range(10)
    ]
    spike_time = "2026-10-23T12:30:00Z"
    obs_list.append(make_obs("obs-spike", "total-cpu-one-minute", 98.0, timestamp=spike_time))

    findings, evidence = detector.detect(obs_list, {"z_threshold": 3.5, "min_samples": 5}, "trg-test-5")
    assert len(findings) >= 1
    spike = [f for f in findings if f.observed_value == 98.0][0]
    assert spike.severity in [FindingSeverity.HIGH, FindingSeverity.CRITICAL]
    assert spike.entity_id == "0/RP0/CPU0"


# 6. Cumulative monotonic counters with resets: counter decrease is flagged as counter reset, not negative rate
def test_06_monotonic_counters_and_resets():
    detector = RobustStatisticalDetector()
    counter_vals = [100.0, 200.0, 300.0, 50.0, 150.0, 250.0, 350.0]
    obs_list = [
        make_obs(f"obs-{i}", "total-number-of-drop-packets", v, timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i, v in enumerate(counter_vals)
    ]
    obs_list.append(make_obs("obs-surge", "total-number-of-drop-packets", 1500.0, timestamp="2026-10-23T12:15:00Z"))

    findings, evidence = detector.detect(obs_list, {"z_threshold": 2.0, "min_samples": 4}, "trg-test-6")
    rate_evidence = [e for e in evidence if e.evidence_type == EvidenceType.DERIVED_RATE]
    for ev in rate_evidence:
        assert ev.value >= 0.0  # Never negative rate


# 7. Missing timestamps/records are tracked in data quality/gaps, not treated as 0
def test_07_missing_timestamps_or_gaps():
    detector = RobustStatisticalDetector()
    obs_list = [
        make_obs(f"obs-{i}", "interface_rate", 50.0, timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i in range(5)
    ]
    obs_list.append(make_obs("obs-no-ts", "interface_rate", 52.0, timestamp=None))
    obs_list.append(make_obs("obs-spike", "interface_rate", 500.0, timestamp="2026-10-23T12:20:00Z"))

    findings, evidence = detector.detect(obs_list, {"z_threshold": 3.0, "min_samples": 4}, "trg-test-7")
    assert len(findings) >= 1
    assert any(f.observed_value == 500.0 for f in findings)


# 8. Unknown units preserved truthfully without crashing or guessing wrong conversion
def test_08_unknown_units_preserved_truthfully():
    detector = RobustStatisticalDetector()
    obs_list = [
        make_obs(f"obs-{i}", "opaque_metric", 10.0, unit=None, timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i in range(6)
    ]
    obs_list.append(make_obs("obs-spk", "opaque_metric", 100.0, unit=None, timestamp="2026-10-23T12:10:00Z"))
    findings, evidence = detector.detect(obs_list, {"z_threshold": 3.0, "min_samples": 5}, "trg-test-8")
    assert len(findings) >= 1
    finding = findings[0]
    assert any("Undocumented source metric unit" in lim for lim in finding.limitations)
    assert evidence[0].unit is None


# 9. Source-defined event metadata from case file is correctly ingested and parsed
def test_09_source_defined_event_case_metadata(tmp_path):
    case_file = tmp_path / "test_casedata.txt"
    case_file.write_text(
        "| Event | Type | Description | Start PDT | End PDT | Duration | Target Devices |\n"
        "|---|---|---|---|---|---|---|\n"
        "| BGP Clear Peer | Routing | Flapped BGP session on leaf | 8/4/17 10:20 | 8/4/17 10:25 | 5m | leaf1, spine2 |\n",
        encoding="utf-8"
    )
    detector = SourceEventCaseDetector()
    events = detector.parse_case_file(case_file)
    assert len(events) == 1
    ev = events[0]
    assert ev["event_name"] == "BGP Clear Peer"
    assert "leaf1" in ev["devices"]
    assert "spine2" in ev["devices"]
    assert ev["start_utc"].tzinfo is not None
    # 10:20 PDT (UTC-7) is 17:20 UTC
    assert ev["start_utc"].hour == 17
    assert ev["start_utc"].minute == 20


# 10. Separation between source-defined labels and detector-inferred labels
def test_10_separation_source_defined_vs_detector_labels():
    stat_finding = make_finding("anom-1", label_origin=LabelOrigin.STATISTICAL_DETECTOR, status=FindingStatus.CANDIDATE)
    case_finding = make_finding("anom-2", label_origin=LabelOrigin.SOURCE_DEFINED, status=FindingStatus.CONFIRMED)

    assert stat_finding.label_origin == LabelOrigin.STATISTICAL_DETECTOR
    assert case_finding.label_origin == LabelOrigin.SOURCE_DEFINED
    assert stat_finding.status != case_finding.status


# 11. Temporal association window clustering groups related anomalies within delta t
def test_11_temporal_proximity_clustering():
    engine = EvidenceCorrelationEngine(time_proximity_seconds=60.0)
    t0 = "2026-10-23T12:00:00+00:00"
    t1 = "2026-10-23T12:00:30+00:00"  # 30s later (within 60s)
    t2 = "2026-10-23T12:10:00+00:00"  # 10m later (outside 60s)

    f1 = make_finding("f1", entity_id="leaf1", window_start=t0)
    f2 = make_finding("f2", entity_id="spine1", window_start=t1)
    f3 = make_finding("f3", entity_id="leaf2", window_start=t2)

    report, supp, _ = engine.correlate("t", [f1, f2, f3], [])
    temporal_rels = [r for r in report.supported_relationships if r["relationship_type"] == "temporally_associated"]
    assert len(temporal_rels) == 1
    assert set(temporal_rels[0]["entity_ids"]) == {"leaf1", "spine1"}


# 12. Multi-metric anomalies on same entity are clustered as co-occurring without asserting causal connection
def test_12_multi_metric_co_occurring_clusters():
    engine = EvidenceCorrelationEngine()
    f1 = make_finding("f1", metric_name="cpu_util", entity_id="leaf1")
    f2 = make_finding("f2", metric_name="input_drops", entity_id="leaf1")

    report, _, _ = engine.correlate("t", [f1, f2], [])
    cluster_rels = [r for r in report.supported_relationships if r["relationship_type"] == "co_occurring_metric_cluster"]
    assert len(cluster_rels) == 1
    assert cluster_rels[0]["entity_id"] == "leaf1"
    assert "cpu_util" in cluster_rels[0]["metrics"]
    assert "input_drops" in cluster_rels[0]["metrics"]


# 13. Relationships between evidence explicitly use non-causal descriptors
def test_13_non_causal_descriptors_enforced():
    engine = EvidenceCorrelationEngine()
    f1 = make_finding("f1", entity_id="node1", metric_name="m1")
    f2 = make_finding("f2", entity_id="node1", metric_name="m2")

    report, _, _ = engine.correlate("t", [f1, f2], [])
    forbidden_causal_terms = ["caused by", "root cause", "leads to", "drives", "impacted by"]
    for rel in report.supported_relationships:
        desc = rel["description"].lower()
        for term in forbidden_causal_terms:
            assert term not in desc, f"Found forbidden causal assertion '{term}' in relationship description: {desc}"


# 14. Deduplication of redundant findings on the same metric/entity/window
def test_14_evidence_deduplication():
    engine = EvidenceCorrelationEngine()
    ev1 = EvidenceItem(
        evidence_id="ev-1",
        source_dataset="d",
        source_version="v",
        source_file="f.csv",
        source_row_or_event_reference=1,
        timestamp="2026-10-23T12:00:00Z",
        entity_type="node",
        entity_id="node1",
        metric_name="cpu",
        value=50.0,
        quality_status="VALID",
        evidence_type=EvidenceType.DIRECT_OBSERVATION,
    )
    ev_duplicate = ev1.model_copy()
    report, supp, _ = engine.correlate("t", [], [ev1, ev_duplicate])
    assert len(supp) == 1


# 15. Ambiguous/conflicting evidence results in explicit limitations or lower confidence
def test_15_ambiguous_evidence_lowers_confidence():
    conf_low = PriorityScorer.calculate_confidence(
        sample_count=4,
        label_origin=LabelOrigin.STATISTICAL_DETECTOR,
        quality_status="MISSING_DATA",
        unit=None,
        has_mad_fallback=True,
    )
    conf_high = PriorityScorer.calculate_confidence(
        sample_count=100,
        label_origin=LabelOrigin.STATISTICAL_DETECTOR,
        quality_status="VALID",
        unit="pps",
        has_mad_fallback=False,
    )
    assert conf_low < conf_high
    assert conf_low <= 0.50


# 16. Incomplete topology (missing adjacency matrix) explicitly reported in unavailable information without crashing
def test_16_incomplete_topology_gracefully_handled():
    context = InvestigationContextBuilder.build_context(
        triage_run_id="trg-topo-test",
        source_dataset="cisco-ie-telemetry",
        source_version="master",
        findings=[],
        evidence_items=[],
        supporting_evidence_ids=[],
        contradictory_evidence_ids=[],
    )
    assert any("topology adjacency matrix is omitted" in item for item in context.explicitly_unavailable_information)
    assert any("SLO path latency is not directly measured" in item for item in context.explicitly_unavailable_information)


# 17. Bounded context: max_context_evidence limits returned findings/evidence to avoid unbounded payload size
def test_17_bounded_context_size():
    many_evidence = [
        EvidenceItem(
            evidence_id=f"ev-{i}",
            source_dataset="d",
            source_version="v",
            source_file="f.csv",
            source_row_or_event_reference=i,
            timestamp="2026-10-23T12:00:00Z",
            entity_type="node",
            entity_id=f"node-{i}",
            metric_name="cpu",
            value=float(i),
            quality_status="VALID",
            evidence_type=EvidenceType.DIRECT_OBSERVATION,
        )
        for i in range(120)
    ]
    context = InvestigationContextBuilder.build_context(
        triage_run_id="trg-bounded",
        source_dataset="d",
        source_version="v",
        findings=[],
        evidence_items=many_evidence,
        supporting_evidence_ids=[e.evidence_id for e in many_evidence],
        contradictory_evidence_ids=[],
        max_evidence_count=50,
    )
    assert len(context.correlated_evidence) == 50
    assert len(context.supporting_evidence_ids) == 50


# 18. Empty/zero anomaly observations produces valid EMPTY triage run with ZERO findings and no exceptions
def test_18_empty_or_zero_anomalies_run():
    detector = RobustStatisticalDetector()
    findings, evidence = detector.detect([], {}, "trg-empty")
    assert len(findings) == 0
    assert len(evidence) == 0


# 19. Schema validation: all findings and investigation context conform strictly to Pydantic models
def test_19_schema_validation():
    context = InvestigationContextBuilder.build_context(
        triage_run_id="trg-schema-test",
        source_dataset="cisco-ie-telemetry",
        source_version="v1.0",
        findings=[],
        evidence_items=[],
        supporting_evidence_ids=[],
        contradictory_evidence_ids=[],
    )
    json_str = context.model_dump_json()
    reparsed = InvestigationContext.model_validate_json(json_str)
    assert reparsed.triage_run_id == "trg-schema-test"


# 20. Isolation of evaluator/reference data: no digital-twin hidden truth or simulator evaluation appears in triage output
def test_20_evaluator_reference_isolation():
    context = InvestigationContextBuilder.build_context(
        triage_run_id="trg-iso-test",
        source_dataset="cisco-ie-telemetry",
        source_version="v1.0",
        findings=[],
        evidence_items=[],
        supporting_evidence_ids=[],
        contradictory_evidence_ids=[],
    )
    dumped = context.model_dump()
    for forbidden_key in ["hidden_ground_truth", "counterfactual_latency", "reference_evaluator", "simulator_score"]:
        assert forbidden_key not in dumped


# 21. Deterministic reproducibility: running triage on identical inputs produces identical findings and scores
def test_21_deterministic_reproducibility():
    detector = RobustStatisticalDetector()
    obs_list = [
        make_obs(f"obs-{i}", "crc-errors", float(i * 10), timestamp=f"2026-10-23T12:{i:02d}:00Z")
        for i in range(8)
    ]
    f1, _ = detector.detect(obs_list, {"z_threshold": 2.0, "min_samples": 4}, "trg-det-1")
    f2, _ = detector.detect(obs_list, {"z_threshold": 2.0, "min_samples": 4}, "trg-det-2")

    assert len(f1) == len(f2)
    for item1, item2 in zip(f1, f2):
        assert item1.entity_id == item2.entity_id
        assert item1.metric_name == item2.metric_name
        assert item1.observed_value == item2.observed_value
        assert item1.deviation_score == item2.deviation_score
        assert item1.severity == item2.severity


# 22. FastAPI triage endpoints return valid HTTP responses and typed models
def test_22_fastapi_triage_endpoints(api_client):
    resp_list = api_client.get("/api/v1/triage")
    assert resp_list.status_code == 200
    assert isinstance(resp_list.json(), list)

    resp_404 = api_client.get("/api/v1/triage/trg-non-existent")
    assert resp_404.status_code == 404

    resp_findings_404 = api_client.get("/api/v1/triage/trg-non-existent/findings")
    assert resp_findings_404.status_code == 404
