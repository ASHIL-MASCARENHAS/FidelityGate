import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
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


def parse_pdt_timestamp(pdt_str: str) -> Optional[datetime]:
    """Parses a PDT timestamp string like '8/4/17 10:20' into UTC datetime."""
    if not pdt_str or not pdt_str.strip():
        return None
    cleaned = pdt_str.strip()
    match = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})\s+(\d{1,2}):(\d{2})$", cleaned)
    if not match:
        return None
    month, day, year_part, hour, minute = match.groups()
    year = int(year_part)
    if year < 100:
        year += 2000
    # PDT is UTC-7
    pdt_tz = timezone(timedelta(hours=-7))
    dt_local = datetime(year, int(month), int(day), int(hour), int(minute), tzinfo=pdt_tz)
    return dt_local.astimezone(timezone.utc)


class SourceEventCaseDetector(BaseDetector):
    """Correlates observations against documented experiment case event metadata."""

    name: str = "cisco_event_case_detector"
    version: str = "1.0.0"

    def parse_case_file(self, case_file_path: Path) -> List[Dict[str, Any]]:
        """Parses markdown pipe-delimited casedata.txt files from Cisco IE telemetry."""
        if not case_file_path.exists():
            return []

        events: List[Dict[str, Any]] = []
        with open(case_file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [line.strip() for line in f if line.strip() and "|" in line]

        if len(lines) < 2:
            return []

        # Find header line
        header_line = lines[0]
        headers = [h.strip() for h in header_line.split("|") if h.strip()]

        for line in lines[1:]:
            if "---" in line or "___" in line:
                continue
            cols = [c.strip() for c in line.split("|")][1:-1]
            if len(cols) < 5:
                continue

            event_name = cols[0]
            start_pdt = cols[3] if len(cols) > 3 else ""
            end_pdt = cols[4] if len(cols) > 4 else ""
            device_str = cols[6] if len(cols) > 6 else ""

            if not event_name or not start_pdt:
                continue

            start_utc = parse_pdt_timestamp(start_pdt)
            end_utc = parse_pdt_timestamp(end_pdt) if end_pdt else None

            if start_utc:
                # Normalize target devices list
                devices = []
                cleaned_dev = device_str.lower().replace("&", ",").replace("-", ",")
                for part in cleaned_dev.split(","):
                    p = part.strip().replace(" ", "")
                    if p:
                        devices.append(p)

                events.append({
                    "event_name": event_name,
                    "start_utc": start_utc,
                    "end_utc": end_utc or (start_utc + timedelta(minutes=5)),
                    "devices": devices,
                    "raw_device_str": device_str,
                    "start_iso": start_utc.isoformat(),
                    "end_iso": (end_utc or (start_utc + timedelta(minutes=5))).isoformat(),
                })

        return events

    def detect(
        self,
        observations: List[NormalizedObservation],
        config: Dict[str, Any],
        triage_run_id: str,
    ) -> Tuple[List[AnomalyFinding], List[EvidenceItem]]:
        case_file_path_str = config.get("case_file")
        if not case_file_path_str:
            return [], []

        case_file_path = Path(case_file_path_str)
        if not case_file_path.is_absolute():
            # Resolve relative to cwd or data
            candidate = (Path.cwd() / case_file_path).resolve()
            if candidate.exists():
                case_file_path = candidate

        events = self.parse_case_file(case_file_path)
        if not events:
            return [], []

        findings: List[AnomalyFinding] = []
        evidence_items: List[EvidenceItem] = []

        # Correlate observations with active event windows
        for event in events:
            start_dt = event["start_utc"]
            end_dt = event["end_utc"]
            target_devices = event["devices"]

            matching_obs = []
            for obs in observations:
                if not obs.timestamp:
                    continue
                try:
                    obs_dt = datetime.fromisoformat(obs.timestamp)
                except Exception:
                    continue

                if start_dt <= obs_dt <= end_dt:
                    # Match device
                    obs_entity = obs.entity_id.lower().replace(" ", "")
                    obs_device = str(obs.provenance.get("device", "")).lower().replace(" ", "")
                    is_match = any(d in obs_entity or d in obs_device for d in target_devices)
                    if is_match:
                        matching_obs.append(obs)

            if matching_obs:
                case_ev_id = f"ev-case-{uuid4().hex[:8]}"
                evidence_items.append(
                    EvidenceItem(
                        evidence_id=case_ev_id,
                        source_dataset=matching_obs[0].source_dataset,
                        source_version=matching_obs[0].source_version,
                        source_file=case_file_path.name,
                        source_row_or_event_reference=event["event_name"],
                        timestamp=event["start_iso"],
                        entity_type="device",
                        entity_id=event["raw_device_str"],
                        metric_name="case_event_window",
                        value=1.0,
                        unit=None,
                        quality_status="VALID",
                        evidence_type=EvidenceType.SOURCE_EVENT_CASE,
                        transformation=None,
                        limitations=[f"Source documented event: {event['event_name']}"],
                    )
                )

                for obs in matching_obs[:10]:  # Cap individual evidence attachments
                    obs_ev_id = f"ev-case-obs-{uuid4().hex[:8]}"
                    evidence_items.append(
                        EvidenceItem(
                            evidence_id=obs_ev_id,
                            source_dataset=obs.source_dataset,
                            source_version=obs.source_version,
                            source_file=obs.provenance.get("source_file", "unknown"),
                            source_row_or_event_reference=obs.provenance.get("source_row_index", 0),
                            timestamp=obs.timestamp,
                            entity_type=obs.entity_type,
                            entity_id=obs.entity_id,
                            metric_name=obs.metric_name,
                            value=obs.value,
                            unit=obs.unit,
                            quality_status=obs.quality_status,
                            evidence_type=EvidenceType.DIRECT_OBSERVATION,
                        )
                    )

                primary_obs = matching_obs[0]
                finding = AnomalyFinding(
                    anomaly_id=f"anom-case-{uuid4().hex[:8]}",
                    triage_run_id=triage_run_id,
                    source_dataset=primary_obs.source_dataset,
                    source_version=primary_obs.source_version,
                    scenario_id=primary_obs.scenario_id,
                    entity_type="device",
                    entity_id=event["raw_device_str"],
                    metric_name="source_documented_event",
                    window_start=event["start_iso"],
                    window_end=event["end_iso"],
                    detector_name=self.name,
                    detector_version=self.version,
                    observed_value=1.0,
                    baseline_value=0.0,
                    deviation_score=None,
                    severity=PriorityScorer.calculate_severity(
                        metric_name="source_documented_event",
                        observed_value=1.0,
                        baseline_value=0.0,
                        deviation_score=None,
                        label_origin=LabelOrigin.SOURCE_DEFINED,
                        entity_id=event["raw_device_str"],
                    ),
                    confidence=0.95,
                    label_origin=LabelOrigin.SOURCE_DEFINED,
                    status=FindingStatus.CANDIDATE,
                    evidence_ids=[case_ev_id],
                    limitations=[f"Sourced directly from case file '{case_file_path.name}'"],
                )
                findings.append(finding)

        return findings, evidence_items

