from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from .models import (
    AnomalyFinding,
    CorrelationReport,
    EvidenceItem,
    EvidenceType,
)


class EvidenceCorrelationEngine:
    """Deterministic, rule-based correlation engine associating multi-source network observations."""

    def __init__(self, time_proximity_seconds: float = 60.0):
        self.time_proximity_seconds = time_proximity_seconds

    def correlate(
        self,
        triage_run_id: str,
        findings: List[AnomalyFinding],
        evidence_items: List[EvidenceItem],
        max_context_evidence: int = 50,
    ) -> Tuple[CorrelationReport, List[str], List[str]]:
        """Correlates findings and evidence.
        Returns:
            (correlation_report, supporting_evidence_ids, contradictory_evidence_ids)
        """
        correlation_id = f"corr-{uuid4().hex[:8]}"
        supported_relationships: List[Dict[str, Any]] = []
        unresolved_questions: List[str] = []
        data_quality_warnings: List[str] = []
        limitations: List[str] = []

        # Deduplicate evidence items by ID while preserving ordering
        unique_evidence_map: Dict[str, EvidenceItem] = {}
        for ev in evidence_items:
            if ev.evidence_id not in unique_evidence_map:
                unique_evidence_map[ev.evidence_id] = ev

        deduped_evidence = list(unique_evidence_map.values())

        # Collect affected entities and time window
        affected_entities: Set[str] = set()
        timestamps: List[str] = []

        for f in findings:
            affected_entities.add(f.entity_id)
            if f.window_start:
                timestamps.append(f.window_start)
            if f.window_end:
                timestamps.append(f.window_end)

        for ev in deduped_evidence:
            affected_entities.add(ev.entity_id)
            if ev.timestamp:
                timestamps.append(ev.timestamp)

        time_window = {
            "start": min(timestamps) if timestamps else None,
            "end": max(timestamps) if timestamps else None,
        }

        # 1. Rule 1 & 2: Entity & Metric Clustering
        findings_by_entity: Dict[str, List[AnomalyFinding]] = defaultdict(list)
        for f in findings:
            findings_by_entity[f.entity_id].append(f)

        for ent, ent_findings in findings_by_entity.items():
            if len(ent_findings) > 1:
                supported_relationships.append({
                    "relationship_type": "co_occurring_metric_cluster",
                    "description": f"Multiple metric deviations co-occurring on device '{ent}'",
                    "entity_id": ent,
                    "finding_ids": [f.anomaly_id for f in ent_findings],
                    "metrics": [f.metric_name for f in ent_findings],
                })

        # 2. Rule 3: Temporal Proximity Association
        # Compare findings with parsed timestamps within proximity delta
        for i in range(len(findings)):
            for j in range(i + 1, len(findings)):
                f1 = findings[i]
                f2 = findings[j]
                if f1.window_start and f2.window_start:
                    try:
                        t1 = datetime.fromisoformat(f1.window_start)
                        t2 = datetime.fromisoformat(f2.window_start)
                        delta_sec = abs((t2 - t1).total_seconds())
                        if delta_sec <= self.time_proximity_seconds and f1.entity_id != f2.entity_id:
                            supported_relationships.append({
                                "relationship_type": "temporally_associated",
                                "description": f"Candidate findings on '{f1.entity_id}' and '{f2.entity_id}' occurred within {delta_sec:.1f}s",
                                "entity_ids": [f1.entity_id, f2.entity_id],
                                "finding_ids": [f1.anomaly_id, f2.anomaly_id],
                                "delta_seconds": round(delta_sec, 2),
                            })
                    except Exception:
                        pass

        # 3. Rule 4: Source-defined event cross-referencing
        source_event_findings = [f for f in findings if f.label_origin.value == "SOURCE_DEFINED"]
        statistical_findings = [f for f in findings if f.label_origin.value == "STATISTICAL_DETECTOR"]

        for sf in source_event_findings:
            matched_stats = [
                st for st in statistical_findings
                if sf.entity_id in st.entity_id or st.entity_id in sf.entity_id
            ]
            if matched_stats:
                supported_relationships.append({
                    "relationship_type": "source_event_telemetry_corroboration",
                    "description": f"Source-documented event '{sf.entity_id}' corroborated by statistical metric deviations",
                    "source_finding_id": sf.anomaly_id,
                    "corroborating_finding_ids": [st.anomaly_id for st in matched_stats],
                })

        # 4. Partition Supporting vs Contradictory Evidence
        supporting_evidence_ids: List[str] = []
        contradictory_evidence_ids: List[str] = []

        for ev in deduped_evidence:
            if ev.quality_status == "SUSPECT":
                data_quality_warnings.append(
                    f"Evidence {ev.evidence_id} on {ev.entity_id}:{ev.metric_name} flagged SUSPECT"
                )
            if ev.evidence_type in [EvidenceType.DIRECT_OBSERVATION, EvidenceType.SOURCE_EVENT_CASE, EvidenceType.DERIVED_RATE]:
                supporting_evidence_ids.append(ev.evidence_id)
            elif ev.evidence_type == EvidenceType.BASELINE_WINDOW:
                # Baseline window serves as reference evidence
                supporting_evidence_ids.append(ev.evidence_id)

        # 5. Check for Topology and Adjacency Limitations
        limitations.append(
            "Topology adjacency graph is unavailable in public Cisco telemetry CSV; correlations operate at device/node level."
        )
        limitations.append(
            "Non-causal correlation: temporal proximity establishes co-occurrence, not causal dependency."
        )

        if not source_event_findings and len(statistical_findings) > 0:
            unresolved_questions.append(
                "Telemetry deviations detected without matching source-defined case event; requires external diagnostic verification."
            )

        # Build Report
        report = CorrelationReport(
            correlation_id=correlation_id,
            triage_run_id=triage_run_id,
            time_window=time_window,
            affected_entities=sorted(list(affected_entities)),
            finding_ids=[f.anomaly_id for f in findings],
            evidence_ids=[ev.evidence_id for ev in deduped_evidence[:max_context_evidence]],
            supported_relationships=supported_relationships,
            unresolved_questions=unresolved_questions,
            data_quality_warnings=data_quality_warnings,
            correlation_method="DETERMINISTIC_TEMPORAL_AND_ENTITY_GRAPH",
            limitations=limitations,
        )

        return report, supporting_evidence_ids[:max_context_evidence], contradictory_evidence_ids

