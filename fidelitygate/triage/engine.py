import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from ..config import settings
from ..storage import StorageEngine
from ..ingestion.models import NormalizedObservation
from .models import (
    AnomalyFinding,
    CorrelationReport,
    EvidenceItem,
    FindingSeverity,
    InvestigationContext,
    TriageRunRequest,
    TriageRunSummary,
)
from .detectors.statistical import RobustStatisticalDetector
from .detectors.change import StepChangeDetector
from .detectors.event_case import SourceEventCaseDetector
from .correlation import EvidenceCorrelationEngine
from .context_builder import InvestigationContextBuilder


class AnomalyTriageEngine:
    """Orchestrates deterministic anomaly detection, evidence correlation, and context creation."""

    def __init__(self, storage: Optional[StorageEngine] = None):
        self.storage = storage or StorageEngine(settings.DATABASE_PATH)
        self.stat_detector = RobustStatisticalDetector()
        self.step_detector = StepChangeDetector()
        self.case_detector = SourceEventCaseDetector()
        self.correlation_engine = EvidenceCorrelationEngine(time_proximity_seconds=60.0)

    def load_observations(
        self,
        ingestion_id: Optional[str] = None,
        source_id: Optional[str] = None,
        direct_observations: Optional[List[NormalizedObservation]] = None,
    ) -> Tuple[List[NormalizedObservation], str, str]:
        """Loads normalized observations from disk or memory."""
        if direct_observations is not None:
            dataset_id = direct_observations[0].source_dataset if direct_observations else (source_id or "unknown")
            version = direct_observations[0].source_version if direct_observations else "master"
            return direct_observations, dataset_id, version

        if not ingestion_id:
            # Query recent ingestion report for source_id
            summaries = self.storage.list_ingestion_summaries(limit=10)
            if source_id:
                matched = [s for s in summaries if source_id in s.dataset_id]
                if matched:
                    ingestion_id = matched[0].ingestion_id
            elif summaries:
                ingestion_id = summaries[0].ingestion_id

        if not ingestion_id:
            raise ValueError("No ingestion_id provided and no recent ingestion runs found.")

        report = self.storage.get_ingestion_report(ingestion_id)
        if not report:
            raise FileNotFoundError(f"Ingestion run '{ingestion_id}' not found in storage.")

        processed_path_str = report.output_artifacts.get("processed_observations")
        if not processed_path_str:
            # Check default path
            candidate = settings.processed_data_path / f"{ingestion_id}_normalized.jsonl"
            if candidate.exists():
                processed_path_str = str(candidate)

        if not processed_path_str or not Path(processed_path_str).exists():
            raise FileNotFoundError(f"Normalized observation artifact not found for run '{ingestion_id}'.")

        observations: List[NormalizedObservation] = []
        with open(processed_path_str, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    observations.append(NormalizedObservation.model_validate_json(line.strip()))

        return observations, report.dataset_id, report.dataset_version

    def run_triage(
        self,
        request: TriageRunRequest,
        direct_observations: Optional[List[NormalizedObservation]] = None,
    ) -> Tuple[TriageRunSummary, InvestigationContext, CorrelationReport, List[AnomalyFinding], List[EvidenceItem]]:
        """Executes full Layer 2 triage, correlation, and context building pipeline."""
        started_at = datetime.now(timezone.utc).isoformat()
        triage_run_id = f"trg-{uuid4().hex[:8]}"

        # 1. Load observations
        obs_list, dataset_id, version = self.load_observations(
            ingestion_id=request.ingestion_id,
            source_id=request.source_id,
            direct_observations=direct_observations,
        )

        detector_config: Dict[str, Any] = {
            "z_threshold": request.z_threshold,
            "min_samples": request.min_samples,
            "metrics_filter": request.metrics_filter,
            "entities_filter": request.entities_filter,
            "case_file": request.case_file,
        }

        all_findings: List[AnomalyFinding] = []
        all_evidence: List[EvidenceItem] = []

        # 2. Run Robust Statistical Detector
        stat_findings, stat_evidence = self.stat_detector.detect(
            obs_list, detector_config, triage_run_id
        )
        all_findings.extend(stat_findings)
        all_evidence.extend(stat_evidence)

        # 3. Run Step Change Detector
        step_findings, step_evidence = self.step_detector.detect(
            obs_list, detector_config, triage_run_id
        )
        all_findings.extend(step_findings)
        all_evidence.extend(step_evidence)

        # 4. Run Source Case Event Detector (if case file specified)
        if request.case_file:
            case_findings, case_evidence = self.case_detector.detect(
                obs_list, detector_config, triage_run_id
            )
            all_findings.extend(case_findings)
            all_evidence.extend(case_evidence)

        # Deduplicate evidence
        unique_evidence_map: Dict[str, EvidenceItem] = {}
        for ev in all_evidence:
            if ev.evidence_id not in unique_evidence_map:
                unique_evidence_map[ev.evidence_id] = ev
        deduped_evidence = list(unique_evidence_map.values())

        # 5. Deterministic Correlation
        correlation_report, supporting_ids, contradictory_ids = self.correlation_engine.correlate(
            triage_run_id=triage_run_id,
            findings=all_findings,
            evidence_items=deduped_evidence,
            max_context_evidence=request.max_context_evidence,
        )

        # 6. Build Compact Investigation Context for Layer 3 Agent
        context = InvestigationContextBuilder.build_context(
            triage_run_id=triage_run_id,
            source_dataset=dataset_id,
            source_version=version,
            findings=all_findings,
            evidence_items=deduped_evidence,
            supporting_evidence_ids=supporting_ids,
            contradictory_evidence_ids=contradictory_ids,
            case_metadata={"case_file": request.case_file} if request.case_file else None,
            scenario_id=request.scenario_id,
            quality_warnings=correlation_report.data_quality_warnings,
            unresolved_questions=correlation_report.unresolved_questions,
            max_evidence_count=request.max_context_evidence,
        )

        # 7. Summary & Highest Severity
        highest_sev = FindingSeverity.LOW
        severity_rank = {
            FindingSeverity.CRITICAL: 4,
            FindingSeverity.HIGH: 3,
            FindingSeverity.MEDIUM: 2,
            FindingSeverity.LOW: 1,
            FindingSeverity.UNKNOWN: 0,
        }
        for f in all_findings:
            if severity_rank[f.severity] > severity_rank[highest_sev]:
                highest_sev = f.severity

        completed_at = datetime.now(timezone.utc).isoformat()
        summary = TriageRunSummary(
            triage_run_id=triage_run_id,
            ingestion_id=request.ingestion_id or "direct_memory",
            source_dataset=dataset_id,
            started_at=started_at,
            completed_at=completed_at,
            total_observations_scanned=len(obs_list),
            findings_count=len(all_findings),
            evidence_items_count=len(deduped_evidence),
            status="SUCCESS",
            highest_severity=highest_sev,
        )

        # 8. Persist to Storage Engine
        self.storage.save_triage_run(
            summary=summary,
            context=context,
            correlation=correlation_report,
            findings=all_findings,
            evidence=deduped_evidence,
        )

        return summary, context, correlation_report, all_findings, deduped_evidence

