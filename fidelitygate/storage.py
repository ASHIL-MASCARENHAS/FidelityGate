import json
import sqlite3
from datetime import datetime, timezone
from typing import List, Optional
from .schemas import GateReport, Scenario
from .ingestion.models import (
    DatasetSourceManifest,
    IngestionReport,
    DataQualityIssue,
    IngestionSummary,
)
from .triage.models import (
    AnomalyFinding,
    EvidenceItem,
    CorrelationReport,
    InvestigationContext,
    TriageRunSummary,
    FindingSeverity,
    FindingStatus,
    LabelOrigin,
    EvidenceType,
)
from .investigation.models import (
    InvestigationSummary,
    InvestigationReport,
    DiagnosticPlan,
    InvestigationEvent,
    Hypothesis,
)
from .evaluation.models import (
    MitigationEvaluationSummary,
    MitigationEvaluationReport,
    CandidateEvaluation,
    EvaluationEvent,
)
from .adaptive.models import (
    AdaptiveInvestigationSummary,
    AdaptiveInvestigationReport,
    DiagnosticExecutionRecord,
    UncertaintyUpdate,
    AdaptiveEvent,
)
from .xai.models import DecisionExplanation
from .workflow.models import (
    WorkflowRunSummary,
    WorkflowEvent,
    HumanApprovalRecord,
    InterventionOutcomeReport,
)


class StorageEngine:
    """ACID-compliant SQLite persistence for decision runs, Layer 1 ingestion, and Layer 2 anomaly triage."""

    def __init__(self, path: str = "fidelitygate.db"):
        self.path = path
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.path) as conn:
            # Preserved legacy table
            conn.execute('''CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                scenario_name TEXT NOT NULL,
                decision TEXT NOT NULL,
                reason TEXT NOT NULL,
                report_json TEXT NOT NULL
            )''')

            # Layer 1 Manifest Store
            conn.execute('''CREATE TABLE IF NOT EXISTS dataset_manifests (
                source_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                source_url TEXT NOT NULL,
                publication_reference TEXT NOT NULL,
                dataset_version TEXT NOT NULL,
                license TEXT NOT NULL,
                attribution TEXT NOT NULL,
                download_timestamp TEXT,
                source_format TEXT NOT NULL,
                raw_file_path TEXT NOT NULL,
                sha256_checksum TEXT NOT NULL,
                description TEXT NOT NULL,
                limitations_json TEXT NOT NULL
            )''')

            # Layer 1 Ingestion Audit Trail
            conn.execute('''CREATE TABLE IF NOT EXISTS ingestion_runs (
                ingestion_id TEXT PRIMARY KEY,
                dataset_id TEXT NOT NULL,
                dataset_version TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                source_file TEXT NOT NULL,
                source_checksum TEXT NOT NULL,
                source_row_count INTEGER NOT NULL,
                accepted_count INTEGER NOT NULL,
                rejected_count INTEGER NOT NULL,
                quarantined_count INTEGER NOT NULL,
                duplicate_count INTEGER NOT NULL,
                missing_or_invalid_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                report_json TEXT NOT NULL
            )''')

            # Layer 1 Quality Issues Store
            conn.execute('''CREATE TABLE IF NOT EXISTS data_quality_issues (
                issue_id TEXT PRIMARY KEY,
                ingestion_id TEXT NOT NULL,
                severity TEXT NOT NULL,
                dataset_ref TEXT NOT NULL,
                file_ref TEXT NOT NULL,
                row_ref INTEGER,
                category TEXT NOT NULL,
                description TEXT NOT NULL,
                disposition TEXT NOT NULL,
                FOREIGN KEY (ingestion_id) REFERENCES ingestion_runs(ingestion_id)
            )''')

            # Layer 2 Triage Runs
            conn.execute('''CREATE TABLE IF NOT EXISTS triage_runs (
                triage_run_id TEXT PRIMARY KEY,
                ingestion_id TEXT NOT NULL,
                source_dataset TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT NOT NULL,
                total_observations_scanned INTEGER NOT NULL,
                findings_count INTEGER NOT NULL,
                evidence_items_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                highest_severity TEXT NOT NULL,
                summary_json TEXT NOT NULL
            )''')

            # Layer 2 Anomaly Findings
            conn.execute('''CREATE TABLE IF NOT EXISTS anomaly_findings (
                anomaly_id TEXT PRIMARY KEY,
                triage_run_id TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                window_start TEXT,
                window_end TEXT,
                detector_name TEXT NOT NULL,
                observed_value REAL NOT NULL,
                baseline_value REAL,
                deviation_score REAL,
                severity TEXT NOT NULL,
                confidence REAL NOT NULL,
                label_origin TEXT NOT NULL,
                status TEXT NOT NULL,
                finding_json TEXT NOT NULL,
                FOREIGN KEY (triage_run_id) REFERENCES triage_runs(triage_run_id)
            )''')

            # Layer 2 Evidence Items
            conn.execute('''CREATE TABLE IF NOT EXISTS evidence_items (
                evidence_id TEXT PRIMARY KEY,
                triage_run_id TEXT NOT NULL,
                source_file TEXT NOT NULL,
                timestamp TEXT,
                entity_id TEXT NOT NULL,
                metric_name TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                evidence_type TEXT NOT NULL,
                item_json TEXT NOT NULL,
                FOREIGN KEY (triage_run_id) REFERENCES triage_runs(triage_run_id)
            )''')

            # Layer 2 Correlation Reports
            conn.execute('''CREATE TABLE IF NOT EXISTS correlation_reports (
                correlation_id TEXT PRIMARY KEY,
                triage_run_id TEXT NOT NULL,
                report_json TEXT NOT NULL,
                FOREIGN KEY (triage_run_id) REFERENCES triage_runs(triage_run_id)
            )''')

            # Layer 2 Investigation Contexts
            conn.execute('''CREATE TABLE IF NOT EXISTS investigation_contexts (
                triage_run_id TEXT PRIMARY KEY,
                context_json TEXT NOT NULL,
                FOREIGN KEY (triage_run_id) REFERENCES triage_runs(triage_run_id)
            )''')

            # Layer 3 Investigation Runs
            conn.execute('''CREATE TABLE IF NOT EXISTS investigation_runs (
                investigation_id TEXT PRIMARY KEY,
                triage_run_id TEXT NOT NULL,
                scenario_id TEXT,
                agent_mode TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                completed_at TEXT,
                summary_json TEXT NOT NULL,
                report_json TEXT NOT NULL,
                FOREIGN KEY (triage_run_id) REFERENCES triage_runs(triage_run_id)
            )''')

            # Layer 3 Hypotheses
            conn.execute('''CREATE TABLE IF NOT EXISTS hypotheses (
                hypothesis_id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                hypothesis_type TEXT NOT NULL,
                statement TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                label_origin TEXT NOT NULL,
                hypothesis_json TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigation_runs(investigation_id)
            )''')

            # Layer 3 Diagnostic Plans
            conn.execute('''CREATE TABLE IF NOT EXISTS diagnostic_plans (
                plan_id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                selected_diagnostic_id TEXT,
                status TEXT NOT NULL,
                plan_json TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigation_runs(investigation_id)
            )''')

            # Layer 3 Investigation Events
            conn.execute('''CREATE TABLE IF NOT EXISTS investigation_events (
                event_id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details_json TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigation_runs(investigation_id)
            )''')

            # Layer 4 Mitigation Evaluations
            conn.execute('''CREATE TABLE IF NOT EXISTS mitigation_evaluations (
                evaluation_id TEXT PRIMARY KEY,
                investigation_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                status TEXT NOT NULL,
                gate_verdict TEXT NOT NULL,
                created_at TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                FOREIGN KEY (investigation_id) REFERENCES investigation_runs(investigation_id)
            )''')

            # Layer 4 Candidate Evaluations
            conn.execute('''CREATE TABLE IF NOT EXISTS candidate_evaluations (
                candidate_id TEXT NOT NULL,
                evaluation_id TEXT NOT NULL,
                status TEXT NOT NULL,
                is_valid INTEGER NOT NULL,
                nominal_latency REAL,
                gate_decision TEXT NOT NULL,
                evaluation_json TEXT NOT NULL,
                PRIMARY KEY (candidate_id, evaluation_id),
                FOREIGN KEY (evaluation_id) REFERENCES mitigation_evaluations(evaluation_id)
            )''')

            # Layer 4 Mitigation Reports
            conn.execute('''CREATE TABLE IF NOT EXISTS mitigation_reports (
                evaluation_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                FOREIGN KEY (evaluation_id) REFERENCES mitigation_evaluations(evaluation_id)
            )''')

            # Layer 4 Evaluation Events
            conn.execute('''CREATE TABLE IF NOT EXISTS evaluation_events (
                event_id TEXT PRIMARY KEY,
                evaluation_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                stage TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                details_json TEXT NOT NULL,
                FOREIGN KEY (evaluation_id) REFERENCES mitigation_evaluations(evaluation_id)
            )''')

            # Layer 5 Adaptive Investigations
            conn.execute('''CREATE TABLE IF NOT EXISTS adaptive_investigations (
                adaptive_run_id TEXT PRIMARY KEY,
                evaluation_id TEXT NOT NULL,
                investigation_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                status TEXT NOT NULL,
                initial_gate_decision TEXT NOT NULL,
                final_gate_decision TEXT NOT NULL,
                decision_changed INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                summary_json TEXT NOT NULL,
                FOREIGN KEY (evaluation_id) REFERENCES mitigation_evaluations(evaluation_id)
            )''')

            # Layer 5 Adaptive Reports
            conn.execute('''CREATE TABLE IF NOT EXISTS adaptive_reports (
                adaptive_run_id TEXT PRIMARY KEY,
                report_json TEXT NOT NULL,
                FOREIGN KEY (adaptive_run_id) REFERENCES adaptive_investigations(adaptive_run_id)
            )''')

            # Layer 5 Diagnostic Executions
            conn.execute('''CREATE TABLE IF NOT EXISTS diagnostic_executions (
                execution_id TEXT PRIMARY KEY,
                adaptive_run_id TEXT NOT NULL,
                cycle_number INTEGER NOT NULL,
                diagnostic_id TEXT NOT NULL,
                target_parameter TEXT NOT NULL,
                execution_json TEXT NOT NULL,
                FOREIGN KEY (adaptive_run_id) REFERENCES adaptive_investigations(adaptive_run_id)
            )''')

            # Layer 5 Uncertainty Updates
            conn.execute('''CREATE TABLE IF NOT EXISTS uncertainty_updates (
                update_id TEXT PRIMARY KEY,
                adaptive_run_id TEXT NOT NULL,
                cycle_number INTEGER NOT NULL,
                parameter_name TEXT NOT NULL,
                is_consistent INTEGER NOT NULL,
                update_json TEXT NOT NULL,
                FOREIGN KEY (adaptive_run_id) REFERENCES adaptive_investigations(adaptive_run_id)
            )''')

            # Layer 5 Adaptive Events
            conn.execute('''CREATE TABLE IF NOT EXISTS adaptive_events (
                event_id TEXT PRIMARY KEY,
                adaptive_run_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                cycle_number INTEGER NOT NULL,
                stage TEXT NOT NULL,
                actor TEXT NOT NULL,
                event_type TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                details_json TEXT NOT NULL,
                FOREIGN KEY (adaptive_run_id) REFERENCES adaptive_investigations(adaptive_run_id)
            )''')

            # Layer 6 Decision Explanations
            conn.execute('''CREATE TABLE IF NOT EXISTS explanations (
                explanation_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                candidate_id TEXT,
                decision TEXT NOT NULL,
                created_at TEXT NOT NULL,
                explanation_json TEXT NOT NULL
            )''')

            # Layer 7 Workflow Runs
            conn.execute('''CREATE TABLE IF NOT EXISTS workflow_runs (
                workflow_run_id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                current_stage TEXT NOT NULL,
                status TEXT NOT NULL,
                selected_candidate_id TEXT,
                gate_verdict TEXT,
                approval_id TEXT,
                approval_status TEXT,
                outcome_id TEXT,
                overall_impact TEXT,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                duration_ms REAL,
                summary_json TEXT NOT NULL
            )''')

            # Layer 7 Workflow Events
            conn.execute('''CREATE TABLE IF NOT EXISTS workflow_events (
                event_id TEXT PRIMARY KEY,
                workflow_run_id TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                stage TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                event_json TEXT NOT NULL,
                FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(workflow_run_id)
            )''')

            # Layer 7 Human Approvals
            conn.execute('''CREATE TABLE IF NOT EXISTS workflow_approvals (
                approval_id TEXT PRIMARY KEY,
                workflow_run_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                gate_verdict TEXT NOT NULL,
                explanation_id TEXT NOT NULL,
                evidence_version TEXT NOT NULL,
                decision TEXT NOT NULL,
                reviewer_id TEXT NOT NULL,
                reviewer_comment TEXT,
                is_stale INTEGER NOT NULL,
                idempotency_key TEXT,
                created_at TEXT NOT NULL,
                approval_json TEXT NOT NULL,
                FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(workflow_run_id)
            )''')

            # Layer 7 Intervention Outcomes
            conn.execute('''CREATE TABLE IF NOT EXISTS workflow_outcomes (
                outcome_id TEXT PRIMARY KEY,
                workflow_run_id TEXT NOT NULL,
                scenario_id TEXT NOT NULL,
                candidate_id TEXT NOT NULL,
                approval_id TEXT NOT NULL,
                execution_id TEXT NOT NULL,
                overall_impact TEXT NOT NULL,
                pre_action_latency_ms REAL NOT NULL,
                post_action_latency_ms REAL NOT NULL,
                latency_delta_ms REAL NOT NULL,
                created_at TEXT NOT NULL,
                outcome_json TEXT NOT NULL,
                FOREIGN KEY (workflow_run_id) REFERENCES workflow_runs(workflow_run_id)
            )''')

    # Legacy compatibility methods
    def save(self, scenario: Scenario, gate: GateReport) -> int:
        with sqlite3.connect(self.path) as conn:
            cur = conn.execute(
                "INSERT INTO runs(created_at,scenario_id,scenario_name,decision,reason,report_json) VALUES(?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), scenario.scenario_id,
                 scenario.name, gate.decision.value, gate.reason, gate.report.model_dump_json()))
            return int(cur.lastrowid)

    def recent(self, limit: int = 50):
        with sqlite3.connect(self.path) as conn:
            return conn.execute(
                "SELECT id,created_at,scenario_id,scenario_name,decision,reason,report_json FROM runs ORDER BY id DESC LIMIT ?",
                (limit,)
            ).fetchall()

    # Layer 1 Ingestion and Manifest Persistence
    def save_manifest(self, manifest: DatasetSourceManifest) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT INTO dataset_manifests (
                    source_id, name, source_url, publication_reference, dataset_version,
                    license, attribution, download_timestamp, source_format, raw_file_path,
                    sha256_checksum, description, limitations_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source_id) DO UPDATE SET
                    name=excluded.name,
                    source_url=excluded.source_url,
                    publication_reference=excluded.publication_reference,
                    dataset_version=excluded.dataset_version,
                    license=excluded.license,
                    attribution=excluded.attribution,
                    download_timestamp=excluded.download_timestamp,
                    source_format=excluded.source_format,
                    raw_file_path=excluded.raw_file_path,
                    sha256_checksum=excluded.sha256_checksum,
                    description=excluded.description,
                    limitations_json=excluded.limitations_json
                ''',
                (
                    manifest.source_id, manifest.name, manifest.source_url,
                    manifest.publication_reference, manifest.dataset_version,
                    manifest.license, manifest.attribution, manifest.download_timestamp,
                    manifest.source_format, manifest.raw_file_path,
                    manifest.sha256_checksum, manifest.description,
                    json.dumps(manifest.limitations)
                )
            )

    def get_manifest(self, source_id: str) -> Optional[DatasetSourceManifest]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM dataset_manifests WHERE source_id = ?",
                (source_id,)
            ).fetchone()
            if not row:
                return None
            return DatasetSourceManifest(
                source_id=row["source_id"],
                name=row["name"],
                source_url=row["source_url"],
                publication_reference=row["publication_reference"],
                dataset_version=row["dataset_version"],
                license=row["license"],
                attribution=row["attribution"],
                download_timestamp=row["download_timestamp"],
                source_format=row["source_format"],
                raw_file_path=row["raw_file_path"],
                sha256_checksum=row["sha256_checksum"],
                description=row["description"],
                limitations=json.loads(row["limitations_json"]),
            )

    def list_manifests(self) -> List[DatasetSourceManifest]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM dataset_manifests ORDER BY source_id ASC").fetchall()
            return [
                DatasetSourceManifest(
                    source_id=row["source_id"],
                    name=row["name"],
                    source_url=row["source_url"],
                    publication_reference=row["publication_reference"],
                    dataset_version=row["dataset_version"],
                    license=row["license"],
                    attribution=row["attribution"],
                    download_timestamp=row["download_timestamp"],
                    source_format=row["source_format"],
                    raw_file_path=row["raw_file_path"],
                    sha256_checksum=row["sha256_checksum"],
                    description=row["description"],
                    limitations=json.loads(row["limitations_json"]),
                )
                for row in rows
            ]

    def save_ingestion_report(self, report: IngestionReport) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT INTO ingestion_runs (
                    ingestion_id, dataset_id, dataset_version, started_at, completed_at,
                    source_file, source_checksum, source_row_count, accepted_count,
                    rejected_count, quarantined_count, duplicate_count, missing_or_invalid_count,
                    status, report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ingestion_id) DO UPDATE SET
                    status=excluded.status,
                    completed_at=excluded.completed_at,
                    report_json=excluded.report_json
                ''',
                (
                    report.ingestion_id, report.dataset_id, report.dataset_version,
                    report.started_at, report.completed_at, report.source_file,
                    report.source_checksum, report.source_row_count, report.accepted_count,
                    report.rejected_count, report.quarantined_count, report.duplicate_count,
                    report.missing_or_invalid_count, report.status, report.model_dump_json()
                )
            )

            for issue in report.quality_issues:
                conn.execute(
                    '''INSERT OR REPLACE INTO data_quality_issues (
                        issue_id, ingestion_id, severity, dataset_ref, file_ref,
                        row_ref, category, description, disposition
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        issue.issue_id, report.ingestion_id, issue.severity,
                        issue.dataset_ref, issue.file_ref, issue.row_ref,
                        issue.category, issue.description, issue.disposition
                    )
                )

    def get_ingestion_report(self, ingestion_id: str) -> Optional[IngestionReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM ingestion_runs WHERE ingestion_id = ?",
                (ingestion_id,)
            ).fetchone()
            if not row:
                return None
            return IngestionReport.model_validate_json(row["report_json"])

    def find_ingestion_by_checksum_and_version(
        self, checksum: str, version: str
    ) -> Optional[IngestionReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                '''SELECT report_json FROM ingestion_runs 
                   WHERE source_checksum = ? AND dataset_version = ? AND status = 'SUCCESS'
                   ORDER BY completed_at DESC LIMIT 1''',
                (checksum, version)
            ).fetchone()
            if not row:
                return None
            return IngestionReport.model_validate_json(row["report_json"])

    def list_ingestion_summaries(self, limit: int = 50) -> List[IngestionSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT ingestion_id, dataset_id, status, source_file, source_checksum,
                          source_row_count, accepted_count, quarantined_count,
                          started_at, completed_at
                   FROM ingestion_runs ORDER BY started_at DESC LIMIT ?''',
                (limit,)
            ).fetchall()
            return [
                IngestionSummary(
                    ingestion_id=r["ingestion_id"],
                    dataset_id=r["dataset_id"],
                    status=r["status"],
                    source_file=r["source_file"],
                    source_checksum=r["source_checksum"],
                    source_row_count=r["source_row_count"],
                    accepted_count=r["accepted_count"],
                    quarantined_count=r["quarantined_count"],
                    started_at=r["started_at"],
                    completed_at=r["completed_at"],
                )
                for r in rows
            ]

    def get_data_quality_issues(self, ingestion_id: str) -> List[DataQualityIssue]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                '''SELECT issue_id, severity, dataset_ref, file_ref, row_ref,
                          category, description, disposition
                   FROM data_quality_issues WHERE ingestion_id = ? ORDER BY row_ref ASC''',
                (ingestion_id,)
            ).fetchall()
            return [
                DataQualityIssue(
                    issue_id=r["issue_id"],
                    severity=r["severity"],
                    dataset_ref=r["dataset_ref"],
                    file_ref=r["file_ref"],
                    row_ref=r["row_ref"],
                    category=r["category"],
                    description=r["description"],
                    disposition=r["disposition"],
                )
                for r in rows
            ]

    # Layer 2 Triage Persistence
    def save_triage_run(
        self,
        summary: TriageRunSummary,
        context: InvestigationContext,
        correlation: CorrelationReport,
        findings: List[AnomalyFinding],
        evidence: List[EvidenceItem],
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT INTO triage_runs (
                    triage_run_id, ingestion_id, source_dataset, started_at, completed_at,
                    total_observations_scanned, findings_count, evidence_items_count,
                    status, highest_severity, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(triage_run_id) DO UPDATE SET
                    completed_at=excluded.completed_at,
                    findings_count=excluded.findings_count,
                    evidence_items_count=excluded.evidence_items_count,
                    status=excluded.status,
                    highest_severity=excluded.highest_severity,
                    summary_json=excluded.summary_json
                ''',
                (
                    summary.triage_run_id, summary.ingestion_id, summary.source_dataset,
                    summary.started_at, summary.completed_at, summary.total_observations_scanned,
                    summary.findings_count, summary.evidence_items_count, summary.status,
                    summary.highest_severity.value, summary.model_dump_json()
                )
            )

            # Insert Findings
            for f in findings:
                conn.execute(
                    '''INSERT OR REPLACE INTO anomaly_findings (
                        anomaly_id, triage_run_id, entity_type, entity_id, metric_name,
                        window_start, window_end, detector_name, observed_value,
                        baseline_value, deviation_score, severity, confidence,
                        label_origin, status, finding_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        f.anomaly_id, summary.triage_run_id, f.entity_type, f.entity_id,
                        f.metric_name, f.window_start, f.window_end, f.detector_name,
                        f.observed_value, f.baseline_value, f.deviation_score,
                        f.severity.value, f.confidence, f.label_origin.value, f.status.value,
                        f.model_dump_json()
                    )
                )

            # Insert Evidence Items
            for ev in evidence:
                conn.execute(
                    '''INSERT OR REPLACE INTO evidence_items (
                        evidence_id, triage_run_id, source_file, timestamp,
                        entity_id, metric_name, value, unit, evidence_type, item_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        ev.evidence_id, summary.triage_run_id, ev.source_file,
                        ev.timestamp, ev.entity_id, ev.metric_name, ev.value,
                        ev.unit, ev.evidence_type.value, ev.model_dump_json()
                    )
                )

            # Insert Correlation Report
            if correlation is not None:
                conn.execute(
                    '''INSERT OR REPLACE INTO correlation_reports (
                        correlation_id, triage_run_id, report_json
                    ) VALUES (?, ?, ?)''',
                    (correlation.correlation_id, summary.triage_run_id, correlation.model_dump_json())
                )

            # Insert Investigation Context
            if context is not None:
                conn.execute(
                    '''INSERT OR REPLACE INTO investigation_contexts (
                        triage_run_id, context_json
                    ) VALUES (?, ?)''',
                    (summary.triage_run_id, context.model_dump_json())
                )

    def get_triage_summary(self, triage_run_id: str) -> Optional[TriageRunSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT summary_json FROM triage_runs WHERE triage_run_id = ?",
                (triage_run_id,)
            ).fetchone()
            if not row:
                return None
            return TriageRunSummary.model_validate_json(row["summary_json"])

    def list_triage_summaries(self, limit: int = 50) -> List[TriageRunSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT summary_json FROM triage_runs ORDER BY started_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [TriageRunSummary.model_validate_json(r["summary_json"]) for r in rows]

    def get_triage_findings(self, triage_run_id: str) -> List[AnomalyFinding]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT finding_json FROM anomaly_findings WHERE triage_run_id = ? ORDER BY confidence DESC",
                (triage_run_id,)
            ).fetchall()
            return [AnomalyFinding.model_validate_json(r["finding_json"]) for r in rows]

    def get_triage_correlation(self, triage_run_id: str) -> Optional[CorrelationReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM correlation_reports WHERE triage_run_id = ?",
                (triage_run_id,)
            ).fetchone()
            if not row:
                return None
            return CorrelationReport.model_validate_json(row["report_json"])

    def get_investigation_context(self, triage_run_id: str) -> Optional[InvestigationContext]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT context_json FROM investigation_contexts WHERE triage_run_id = ?",
                (triage_run_id,)
            ).fetchone()
            if not row:
                return None
            return InvestigationContext.model_validate_json(row["context_json"])

    # ==========================================
    # Layer 3: Investigation & Diagnostic Planning Storage
    # ==========================================

    def save_investigation(
        self,
        summary: InvestigationSummary,
        report: InvestigationReport,
        plan: DiagnosticPlan,
        events: List[InvestigationEvent],
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            # 1. Insert Investigation Run
            conn.execute(
                '''INSERT OR REPLACE INTO investigation_runs (
                    investigation_id, triage_run_id, scenario_id, agent_mode,
                    status, created_at, completed_at, summary_json, report_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    summary.investigation_id, summary.triage_run_id, summary.scenario_id,
                    summary.agent_mode.value, summary.status.value, summary.created_at,
                    summary.completed_at, summary.model_dump_json(), report.model_dump_json()
                )
            )

            # 2. Insert Hypotheses
            for h in report.hypotheses:
                conn.execute(
                    '''INSERT OR REPLACE INTO hypotheses (
                        hypothesis_id, investigation_id, hypothesis_type, statement,
                        confidence_score, label_origin, hypothesis_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        h.hypothesis_id, summary.investigation_id, h.hypothesis_type.value,
                        h.statement, h.confidence_score, h.label_origin.value, h.model_dump_json()
                    )
                )

            # 3. Insert Diagnostic Plan
            conn.execute(
                '''INSERT OR REPLACE INTO diagnostic_plans (
                    plan_id, investigation_id, selected_diagnostic_id, status, plan_json
                ) VALUES (?, ?, ?, ?, ?)''',
                (
                    plan.plan_id, summary.investigation_id, plan.selected_diagnostic_id,
                    plan.status.value, plan.model_dump_json()
                )
            )

            # 4. Insert Investigation Events
            for ev in events:
                conn.execute(
                    '''INSERT OR REPLACE INTO investigation_events (
                        event_id, investigation_id, timestamp, actor, event_type, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?)''',
                    (
                        ev.event_id, summary.investigation_id, ev.timestamp,
                        ev.actor, ev.event_type, json.dumps(ev.details)
                    )
                )

    def get_investigation_summary(self, investigation_id: str) -> Optional[InvestigationSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT summary_json FROM investigation_runs WHERE investigation_id = ?",
                (investigation_id,)
            ).fetchone()
            if not row:
                return None
            return InvestigationSummary.model_validate_json(row["summary_json"])

    def list_investigation_summaries(self, limit: int = 50) -> List[InvestigationSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT summary_json FROM investigation_runs ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [InvestigationSummary.model_validate_json(r["summary_json"]) for r in rows]

    def get_investigation_report(self, investigation_id: str) -> Optional[InvestigationReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM investigation_runs WHERE investigation_id = ?",
                (investigation_id,)
            ).fetchone()
            if not row:
                return None
            return InvestigationReport.model_validate_json(row["report_json"])

    def get_investigation_plan(self, investigation_id: str) -> Optional[DiagnosticPlan]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT plan_json FROM diagnostic_plans WHERE investigation_id = ?",
                (investigation_id,)
            ).fetchone()
            if not row:
                return None
            return DiagnosticPlan.model_validate_json(row["plan_json"])

    def get_investigation_events(self, investigation_id: str) -> List[InvestigationEvent]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT event_id, investigation_id, timestamp, actor, event_type, details_json FROM investigation_events WHERE investigation_id = ? ORDER BY timestamp ASC",
                (investigation_id,)
            ).fetchall()
            return [
                InvestigationEvent(
                    event_id=r["event_id"],
                    investigation_id=r["investigation_id"],
                    timestamp=r["timestamp"],
                    actor=r["actor"],
                    event_type=r["event_type"],
                    details=json.loads(r["details_json"]),
                )
                for r in rows
            ]

    # ==========================================
    # Layer 4: Mitigation Evaluation Storage
    # ==========================================

    def save_mitigation_evaluation(
        self,
        summary: MitigationEvaluationSummary,
        report: MitigationEvaluationReport,
        candidate_evaluations: List[CandidateEvaluation],
        events: List[EvaluationEvent],
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            # 1. Insert Mitigation Evaluation Run
            conn.execute(
                '''INSERT OR REPLACE INTO mitigation_evaluations (
                    evaluation_id, investigation_id, scenario_id, status,
                    gate_verdict, created_at, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    summary.evaluation_id, summary.investigation_id, summary.scenario_id,
                    summary.status, summary.gate_verdict.value, summary.created_at,
                    summary.model_dump_json()
                )
            )

            # 2. Insert Candidate Evaluations
            for ce in candidate_evaluations:
                conn.execute(
                    '''INSERT OR REPLACE INTO candidate_evaluations (
                        candidate_id, evaluation_id, status, is_valid,
                        nominal_latency, gate_decision, evaluation_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (
                        ce.candidate_id, ce.evaluation_id, ce.status.value,
                        1 if ce.validation.is_valid else 0,
                        ce.nominal_prediction.latency_ms if ce.nominal_prediction else None,
                        ce.gate_report.decision.value if ce.gate_report else "ABSTAIN",
                        ce.model_dump_json()
                    )
                )

            # 3. Insert Mitigation Report
            conn.execute(
                '''INSERT OR REPLACE INTO mitigation_reports (
                    evaluation_id, report_json
                ) VALUES (?, ?)''',
                (report.evaluation_id, report.model_dump_json())
            )

            # 4. Insert Evaluation Events
            for ev in events:
                conn.execute(
                    '''INSERT OR REPLACE INTO evaluation_events (
                        event_id, evaluation_id, timestamp, stage, actor,
                        event_type, sequence_number, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        ev.event_id, ev.evaluation_id, ev.timestamp, ev.stage,
                        ev.actor, ev.event_type, ev.sequence_number, json.dumps(ev.details)
                    )
                )

    def get_mitigation_summary(self, evaluation_id: str) -> Optional[MitigationEvaluationSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT summary_json FROM mitigation_evaluations WHERE evaluation_id = ?",
                (evaluation_id,)
            ).fetchone()
            if not row:
                return None
            return MitigationEvaluationSummary.model_validate_json(row["summary_json"])

    def list_mitigation_summaries(self, limit: int = 50) -> List[MitigationEvaluationSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT summary_json FROM mitigation_evaluations ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [MitigationEvaluationSummary.model_validate_json(r["summary_json"]) for r in rows]

    def get_candidate_evaluations(self, evaluation_id: str) -> List[CandidateEvaluation]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT evaluation_json FROM candidate_evaluations WHERE evaluation_id = ?",
                (evaluation_id,)
            ).fetchall()
            return [CandidateEvaluation.model_validate_json(r["evaluation_json"]) for r in rows]

    def get_mitigation_report(self, evaluation_id: str) -> Optional[MitigationEvaluationReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM mitigation_reports WHERE evaluation_id = ?",
                (evaluation_id,)
            ).fetchone()
            if not row:
                return None
            return MitigationEvaluationReport.model_validate_json(row["report_json"])

    def get_evaluation_events(self, evaluation_id: str) -> List[EvaluationEvent]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT event_id, evaluation_id, timestamp, stage, actor, event_type, sequence_number, details_json FROM evaluation_events WHERE evaluation_id = ? ORDER BY sequence_number ASC",
                (evaluation_id,)
            ).fetchall()
            return [
                EvaluationEvent(
                    event_id=r["event_id"],
                    evaluation_id=r["evaluation_id"],
                    timestamp=r["timestamp"],
                    stage=r["stage"],
                    actor=r["actor"],
                    event_type=r["event_type"],
                    sequence_number=r["sequence_number"],
                    details=json.loads(r["details_json"]),
                )
                for r in rows
            ]

    # Layer 5: Adaptive Investigations & Diagnostic Persistence
    def save_adaptive_investigation(
        self,
        summary: AdaptiveInvestigationSummary,
        report: AdaptiveInvestigationReport,
        events: List[AdaptiveEvent],
        diagnostic_records: List[DiagnosticExecutionRecord],
        uncertainty_updates: List[UncertaintyUpdate],
    ) -> None:
        with sqlite3.connect(self.path) as conn:
            # 1. Summary
            conn.execute(
                '''INSERT OR REPLACE INTO adaptive_investigations (
                    adaptive_run_id, evaluation_id, investigation_id, scenario_id,
                    status, initial_gate_decision, final_gate_decision, decision_changed,
                    created_at, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    summary.adaptive_run_id, summary.evaluation_id, summary.investigation_id,
                    summary.scenario_id, summary.status.value, summary.initial_gate_decision.value,
                    summary.final_gate_decision.value, 1 if summary.decision_changed else 0,
                    summary.created_at, summary.model_dump_json()
                )
            )

            # 2. Report
            conn.execute(
                '''INSERT OR REPLACE INTO adaptive_reports (adaptive_run_id, report_json)
                   VALUES (?, ?)''',
                (report.adaptive_run_id, report.model_dump_json())
            )

            # 3. Diagnostic Executions
            for diag in diagnostic_records:
                conn.execute(
                    '''INSERT OR REPLACE INTO diagnostic_executions (
                        execution_id, adaptive_run_id, cycle_number, diagnostic_id,
                        target_parameter, execution_json
                    ) VALUES (?, ?, ?, ?, ?, ?)''',
                    (
                        diag.execution_id, summary.adaptive_run_id, diag.cycle_number,
                        diag.diagnostic_id, diag.target_parameter, diag.model_dump_json()
                    )
                )

            # 4. Uncertainty Updates
            for upd in uncertainty_updates:
                conn.execute(
                    '''INSERT OR REPLACE INTO uncertainty_updates (
                        update_id, adaptive_run_id, cycle_number, parameter_name,
                        is_consistent, update_json
                    ) VALUES (?, ?, ?, ?, ?, ?)''',
                    (
                        upd.update_id, summary.adaptive_run_id, 1,
                        upd.parameter_name, 1 if upd.is_consistent else 0, upd.model_dump_json()
                    )
                )

            # 5. Adaptive Events
            for ev in events:
                conn.execute(
                    '''INSERT OR REPLACE INTO adaptive_events (
                        event_id, adaptive_run_id, timestamp, cycle_number,
                        stage, actor, event_type, sequence_number, details_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (
                        ev.event_id, ev.adaptive_run_id, ev.timestamp, ev.cycle_number,
                        ev.stage, ev.actor, ev.event_type, ev.sequence_number, json.dumps(ev.details)
                    )
                )

    def get_adaptive_summary(self, adaptive_run_id: str) -> Optional[AdaptiveInvestigationSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT summary_json FROM adaptive_investigations WHERE adaptive_run_id = ?",
                (adaptive_run_id,)
            ).fetchone()
            if not row:
                return None
            return AdaptiveInvestigationSummary.model_validate_json(row["summary_json"])

    def list_adaptive_summaries(self, limit: int = 50) -> List[AdaptiveInvestigationSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT summary_json FROM adaptive_investigations ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [AdaptiveInvestigationSummary.model_validate_json(r["summary_json"]) for r in rows]

    def get_adaptive_report(self, adaptive_run_id: str) -> Optional[AdaptiveInvestigationReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM adaptive_reports WHERE adaptive_run_id = ?",
                (adaptive_run_id,)
            ).fetchone()
            if not row:
                return None
            return AdaptiveInvestigationReport.model_validate_json(row["report_json"])

    def get_adaptive_diagnostics(self, adaptive_run_id: str) -> List[DiagnosticExecutionRecord]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT execution_json FROM diagnostic_executions WHERE adaptive_run_id = ? ORDER BY cycle_number ASC",
                (adaptive_run_id,)
            ).fetchall()
            return [DiagnosticExecutionRecord.model_validate_json(r["execution_json"]) for r in rows]

    def get_adaptive_events(self, adaptive_run_id: str) -> List[AdaptiveEvent]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT event_id, adaptive_run_id, timestamp, cycle_number, stage, actor, event_type, sequence_number, details_json FROM adaptive_events WHERE adaptive_run_id = ? ORDER BY sequence_number ASC",
                (adaptive_run_id,)
            ).fetchall()
            return [
                AdaptiveEvent(
                    event_id=r["event_id"],
                    adaptive_run_id=r["adaptive_run_id"],
                    timestamp=r["timestamp"],
                    cycle_number=r["cycle_number"],
                    stage=r["stage"],
                    actor=r["actor"],
                    event_type=r["event_type"],
                    sequence_number=r["sequence_number"],
                    details=json.loads(r["details_json"]),
                )
                for r in rows
            ]

    # Layer 6 Decision Explanation Methods
    def save_explanation(self, explanation: DecisionExplanation) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO explanations (
                    explanation_id, run_id, scenario_id, candidate_id, decision,
                    created_at, explanation_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    explanation.explanation_id,
                    explanation.run_id,
                    explanation.scenario_id,
                    explanation.candidate_id,
                    explanation.decision.value,
                    explanation.created_at,
                    explanation.model_dump_json(),
                ),
            )

    def get_explanation(self, explanation_id: str) -> Optional[DecisionExplanation]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT explanation_json FROM explanations WHERE explanation_id = ?",
                (explanation_id,),
            ).fetchone()
            if not row:
                return None
            return DecisionExplanation.model_validate_json(row["explanation_json"])

    def get_explanation_by_run(self, run_id: str) -> Optional[DecisionExplanation]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT explanation_json FROM explanations WHERE run_id = ? ORDER BY created_at DESC LIMIT 1",
                (run_id,),
            ).fetchone()
            if not row:
                return None
            return DecisionExplanation.model_validate_json(row["explanation_json"])

    def list_explanations(self, limit: int = 50) -> List[DecisionExplanation]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT explanation_json FROM explanations ORDER BY created_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [DecisionExplanation.model_validate_json(r["explanation_json"]) for r in rows]

    # Layer 7 Workflow Persistence Methods
    def save_workflow_run(self, summary: WorkflowRunSummary) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO workflow_runs (
                    workflow_run_id, scenario_id, current_stage, status, selected_candidate_id,
                    gate_verdict, approval_id, approval_status, outcome_id, overall_impact,
                    started_at, completed_at, duration_ms, summary_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    summary.workflow_run_id,
                    summary.scenario_id,
                    summary.current_stage.value,
                    summary.status.value,
                    summary.selected_candidate_id,
                    summary.gate_verdict.value if summary.gate_verdict else None,
                    summary.approval_id,
                    summary.approval_status.value if summary.approval_status else None,
                    summary.outcome_id,
                    summary.overall_impact.value if summary.overall_impact else None,
                    summary.started_at,
                    summary.completed_at,
                    summary.duration_ms,
                    summary.model_dump_json(),
                ),
            )

    def get_workflow_run(self, workflow_run_id: str) -> Optional[WorkflowRunSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT summary_json FROM workflow_runs WHERE workflow_run_id = ?",
                (workflow_run_id,),
            ).fetchone()
            if not row:
                return None
            return WorkflowRunSummary.model_validate_json(row["summary_json"])

    def list_workflow_runs(self, limit: int = 50) -> List[WorkflowRunSummary]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT summary_json FROM workflow_runs ORDER BY started_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [WorkflowRunSummary.model_validate_json(r["summary_json"]) for r in rows]

    def save_workflow_event(self, event: WorkflowEvent) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO workflow_events (
                    event_id, workflow_run_id, sequence_number, stage, event_type,
                    timestamp, event_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (
                    event.event_id,
                    event.workflow_run_id,
                    event.sequence_number,
                    event.stage.value,
                    event.event_type,
                    event.timestamp,
                    event.model_dump_json(),
                ),
            )

    def get_workflow_events(self, workflow_run_id: str) -> List[WorkflowEvent]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT event_json FROM workflow_events WHERE workflow_run_id = ? ORDER BY sequence_number ASC",
                (workflow_run_id,),
            ).fetchall()
            return [WorkflowEvent.model_validate_json(r["event_json"]) for r in rows]

    def save_approval(self, approval: HumanApprovalRecord) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO workflow_approvals (
                    approval_id, workflow_run_id, candidate_id, gate_verdict, explanation_id,
                    evidence_version, decision, reviewer_id, reviewer_comment, is_stale,
                    idempotency_key, created_at, approval_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    approval.approval_id,
                    approval.workflow_run_id,
                    approval.candidate_id,
                    approval.gate_verdict.value,
                    approval.explanation_id,
                    approval.evidence_version,
                    approval.decision.value,
                    approval.reviewer_id,
                    approval.reviewer_comment,
                    1 if approval.is_stale else 0,
                    approval.idempotency_key,
                    approval.created_at,
                    approval.model_dump_json(),
                ),
            )

    def get_approval(self, approval_id: str) -> Optional[HumanApprovalRecord]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT approval_json FROM workflow_approvals WHERE approval_id = ?",
                (approval_id,),
            ).fetchone()
            if not row:
                return None
            return HumanApprovalRecord.model_validate_json(row["approval_json"])

    def get_approval_by_workflow(self, workflow_run_id: str) -> Optional[HumanApprovalRecord]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT approval_json FROM workflow_approvals WHERE workflow_run_id = ? ORDER BY created_at DESC LIMIT 1",
                (workflow_run_id,),
            ).fetchone()
            if not row:
                return None
            return HumanApprovalRecord.model_validate_json(row["approval_json"])

    def save_outcome(self, outcome: InterventionOutcomeReport) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute(
                '''INSERT OR REPLACE INTO workflow_outcomes (
                    outcome_id, workflow_run_id, scenario_id, candidate_id, approval_id,
                    execution_id, overall_impact, pre_action_latency_ms, post_action_latency_ms,
                    latency_delta_ms, created_at, outcome_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (
                    outcome.outcome_id,
                    outcome.workflow_run_id,
                    outcome.scenario_id,
                    outcome.candidate_id,
                    outcome.approval_id,
                    outcome.execution_id,
                    outcome.overall_impact.value,
                    outcome.pre_action_latency_ms,
                    outcome.post_action_latency_ms,
                    outcome.latency_delta_ms,
                    outcome.created_at,
                    outcome.model_dump_json(),
                ),
            )

    def get_outcome(self, outcome_id: str) -> Optional[InterventionOutcomeReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT outcome_json FROM workflow_outcomes WHERE outcome_id = ?",
                (outcome_id,),
            ).fetchone()
            if not row:
                return None
            return InterventionOutcomeReport.model_validate_json(row["outcome_json"])

    def get_outcome_by_workflow(self, workflow_run_id: str) -> Optional[InterventionOutcomeReport]:
        with sqlite3.connect(self.path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT outcome_json FROM workflow_outcomes WHERE workflow_run_id = ? ORDER BY created_at DESC LIMIT 1",
                (workflow_run_id,),
            ).fetchone()
            if not row:
                return None
            return InterventionOutcomeReport.model_validate_json(row["outcome_json"])


# Maintain RunStore alias for backward compatibility
RunStore = StorageEngine
