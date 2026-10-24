from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .models import (
    AnomalyFinding,
    EvidenceItem,
    InvestigationContext,
)


class InvestigationContextBuilder:
    """Builds a compact, typed investigation context for downstream Anomaly Investigator agents."""

    @staticmethod
    def build_context(
        triage_run_id: str,
        source_dataset: str,
        source_version: str,
        findings: List[AnomalyFinding],
        evidence_items: List[EvidenceItem],
        supporting_evidence_ids: List[str],
        contradictory_evidence_ids: List[str],
        case_metadata: Optional[Dict[str, Any]] = None,
        scenario_id: Optional[str] = None,
        quality_warnings: Optional[List[str]] = None,
        unresolved_questions: Optional[List[str]] = None,
        max_evidence_count: int = 50,
    ) -> InvestigationContext:
        # 1. Prioritize findings by severity and confidence
        severity_order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
        sorted_findings = sorted(
            findings,
            key=lambda f: (severity_order.get(f.severity.value, 5), -f.confidence)
        )

        # 2. Extract baseline comparisons
        baseline_comparisons: List[Dict[str, Any]] = []
        for f in sorted_findings[:15]:
            if f.baseline_value is not None:
                baseline_comparisons.append({
                    "entity_id": f.entity_id,
                    "metric_name": f.metric_name,
                    "observed": f.observed_value,
                    "baseline": f.baseline_value,
                    "deviation_score": f.deviation_score,
                    "severity": f.severity.value,
                    "confidence": f.confidence,
                })

        # 3. Formulate recommended diagnostic probes based on observed failure modes
        diagnostic_categories: List[str] = []
        has_drops = any("drop" in f.metric_name.lower() for f in findings)
        has_cpu = any("cpu" in f.metric_name.lower() for f in findings)
        has_bgp = any("route" in f.metric_name.lower() or "bgp" in f.metric_name.lower() for f in findings)
        has_rate = any("rate" in f.metric_name.lower() for f in findings)

        if has_drops or has_rate:
            diagnostic_categories.append("snmp_interface_queue_telemetry")
        if has_drops or has_cpu:
            diagnostic_categories.append("icmp_rtt_latency_probe")
        if has_bgp:
            diagnostic_categories.append("bgp_rib_prefix_audit")

        if not diagnostic_categories:
            diagnostic_categories.append("icmp_rtt_latency_probe")

        # 4. Explicitly declare information unavailable in this public dataset
        unavailable_info = [
            "End-to-end user SLO path latency is not directly measured in Cisco interface counters.",
            "Complete physical network topology adjacency matrix is omitted from source CSV.",
            "Link operational capacity thresholds are not declared per-interface.",
            "Candidate reroute mitigations and counterfactual post-action outcomes must be modeled in simulation.",
        ]

        # 5. Cap evidence items to bounded limit
        bounded_evidence = evidence_items[:max_evidence_count]

        return InvestigationContext(
            triage_run_id=triage_run_id,
            source_dataset=source_dataset,
            source_version=source_version,
            scenario_id=scenario_id,
            generated_at=datetime.now(timezone.utc).isoformat(),
            primary_anomaly_candidates=sorted_findings[:20],
            correlated_evidence=bounded_evidence,
            baseline_comparisons=baseline_comparisons,
            supporting_evidence_ids=supporting_evidence_ids[:max_evidence_count],
            contradictory_evidence_ids=contradictory_evidence_ids,
            source_defined_event_metadata=case_metadata,
            data_quality_warnings=quality_warnings or [],
            unresolved_questions=unresolved_questions or [],
            recommended_diagnostic_categories=diagnostic_categories,
            explicitly_unavailable_information=unavailable_info,
        )

