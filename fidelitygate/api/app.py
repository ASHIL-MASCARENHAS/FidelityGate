import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ..config import settings
from ..storage import StorageEngine
from ..ingestion.models import (
    DatasetSourceManifest,
    IngestionReport,
    IngestionRequest,
    IngestionSummary,
)
from ..ingestion.pipeline import IngestionPipeline, IngestionSecurityError
from ..triage.models import (
    AnomalyFinding,
    CorrelationReport,
    InvestigationContext,
    TriageRunRequest,
    TriageRunSummary,
)
from ..triage.engine import AnomalyTriageEngine
from ..investigation.models import (
    InvestigationRequest,
    InvestigationSummary,
    InvestigationReport,
    DiagnosticPlan,
    InvestigationEvent,
)
from ..investigation.orchestrator import InvestigationOrchestrator
from ..evaluation.models import (
    MitigationEvaluationRequest,
    MitigationEvaluationSummary,
    MitigationEvaluationReport,
    CandidateEvaluation,
    EvaluationEvent,
)
from ..evaluation.engine import MitigationEvaluationEngine
from ..adaptive.models import (
    AdaptiveInvestigationRequest,
    AdaptiveInvestigationSummary,
    AdaptiveInvestigationReport,
    DiagnosticExecutionRecord,
    AdaptiveEvent,
)
from ..adaptive.engine import AdaptiveInvestigationEngine
from ..xai.models import (
    DecisionExplanation,
    ExplanationRequest,
    ExplanationSummary,
    GateRuleExplanation,
    LocalSensitivityReport,
)
from ..xai.engine import ExplanationEngine, StorageResourceNotFoundError
from ..workflow.models import (
    WorkflowRunRequest,
    WorkflowRunSummary,
    WorkflowEvent,
    ApprovalRequest,
    HumanApprovalRecord,
    InterventionOutcomeReport,
)
from ..workflow.orchestrator import EndToEndWorkflowOrchestrator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("fidelitygate.api")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="FidelityGate Layer 1 Canonical REST API for Trustworthy Network Data Ingestion and Decision Assurance",
)

# Enable CORS for Next.js frontend, Vercel deployments, and local development
cors_origins = list(settings.CORS_ORIGINS) if isinstance(settings.CORS_ORIGINS, list) else ["*"]
for origin in [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://fidelitygate.vercel.app",
]:
    if origin not in cors_origins:
        cors_origins.append(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

storage = StorageEngine(settings.DATABASE_PATH)
pipeline = IngestionPipeline(storage)


@app.get("/api/v1/health", tags=["System"])
def get_health() -> Dict[str, Any]:
    """Health and readiness diagnostic check for backend services and persistence."""
    db_ok = False
    try:
        # Check SQLite connection and schema accessibility
        storage.list_manifests()
        db_ok = True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")

    data_root_accessible = settings.data_root_path.exists()

    overall_status = "healthy" if db_ok and data_root_accessible else "degraded"

    return {
        "status": overall_status,
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "path": settings.DATABASE_PATH,
            "connected": db_ok,
        },
        "storage": {
            "data_root": str(settings.data_root_path),
            "accessible": data_root_accessible,
        },
    }


@app.get("/api/v1/sources", response_model=List[DatasetSourceManifest], tags=["Data Ingestion"])
def list_sources() -> List[DatasetSourceManifest]:
    """Lists all approved, registered dataset source manifests."""
    manifests = storage.list_manifests()
    if not manifests:
        # Return default Cisco Telemetry registered source reference if none yet ingested
        default_cisco = DatasetSourceManifest(
            source_id="cisco-ie-telemetry",
            name="Cisco Innovation Edge Network Telemetry",
            source_url="https://github.com/cisco-ie/telemetry",
            publication_reference="ACM SIGCOMM BigDama'18 / IEEE INFOCOM'18",
            dataset_version="master",
            license="CDLA-Permissive-1.0",
            attribution="Cisco Systems, Inc. (Community Data License Agreement – Permissive – Version 1.0)",
            download_timestamp=None,
            source_format="CSV",
            raw_file_path="raw/cisco_telemetry",
            sha256_checksum="UNVERIFIED",
            description="Interface counters, drop stats, CPU, and route statistics from real-world Cisco IOS-XR lab runs.",
            limitations=[
                "Does not contain topology or link capacity definitions directly in telemetry CSV.",
                "Does not include post-intervention reroute outcomes or synthetic measurement-error envelopes.",
                "Units are preserved as documented; unverified units are kept explicitly null.",
            ],
        )
        return [default_cisco]
    return manifests


@app.get("/api/v1/sources/{source_id}", response_model=DatasetSourceManifest, tags=["Data Ingestion"])
def get_source(source_id: str) -> DatasetSourceManifest:
    """Retrieves metadata and verified checksum manifest for a specific dataset source."""
    manifest = storage.get_manifest(source_id)
    if not manifest:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source manifest '{source_id}' not found.",
        )
    return manifest


@app.post(
    "/api/v1/ingestions",
    response_model=IngestionReport,
    status_code=status.HTTP_201_CREATED,
    tags=["Data Ingestion"]
)
def create_ingestion(request: IngestionRequest) -> IngestionReport:
    """Initiates bounded schema validation, normalization, and provenance tracking for a dataset file."""
    logger.info(f"Ingestion requested for source '{request.source_id}', path: '{request.relative_path}'")
    try:
        report = pipeline.run_ingestion(request)
        if report.status == "FAILED":
            # If failed due to security/missing file, raise 400 Bad Request
            critical_msg = (
                report.errors_or_limitations[0]
                if report.errors_or_limitations
                else "Ingestion failed schema or file validation."
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content=report.model_dump(),
            )
        return report
    except IngestionSecurityError as sec_err:
        logger.warning(f"Rejected unsafe ingestion request: {sec_err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(sec_err),
        )
    except Exception as exc:
        logger.error(f"Unexpected ingestion failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion pipeline failure: {str(exc)}",
        )


@app.get("/api/v1/ingestions", response_model=List[IngestionSummary], tags=["Data Ingestion"])
def list_ingestions(limit: int = Query(default=50, ge=1, le=500)) -> List[IngestionSummary]:
    """Lists recent ingestion execution runs and high-level summaries."""
    return storage.list_ingestion_summaries(limit=limit)


@app.get(
    "/api/v1/ingestions/{ingestion_id}",
    response_model=IngestionSummary,
    tags=["Data Ingestion"]
)
def get_ingestion(ingestion_id: str) -> IngestionSummary:
    """Queries execution status and summary metrics for an ingestion run."""
    report = storage.get_ingestion_report(ingestion_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion run '{ingestion_id}' not found.",
        )
    return IngestionSummary(
        ingestion_id=report.ingestion_id,
        dataset_id=report.dataset_id,
        status=report.status,
        source_file=report.source_file,
        source_checksum=report.source_checksum,
        source_row_count=report.source_row_count,
        accepted_count=report.accepted_count,
        quarantined_count=report.quarantined_count,
        started_at=report.started_at,
        completed_at=report.completed_at,
    )


@app.get(
    "/api/v1/ingestions/{ingestion_id}/report",
    response_model=IngestionReport,
    tags=["Data Ingestion"]
)
def get_ingestion_report(ingestion_id: str) -> IngestionReport:
    """Retrieves full detailed IngestionReport including all data-quality issues and provenance."""
    report = storage.get_ingestion_report(ingestion_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion report '{ingestion_id}' not found.",
        )
    return report


@app.get("/api/v1/ingestions/{ingestion_id}/quarantine", tags=["Data Ingestion"])
def get_ingestion_quarantine(ingestion_id: str) -> List[Dict[str, Any]]:
    """Retrieves quarantined malformed records for inspection by human operator."""
    return pipeline.quarantine_manager.load_quarantine(ingestion_id)


# ==========================================
# Layer 2: Anomaly Triage & Evidence Correlation Endpoints
# ==========================================

triage_engine = AnomalyTriageEngine(storage)


@app.post(
    "/api/v1/triage",
    response_model=TriageRunSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Anomaly Triage"]
)
def create_triage_run(request: TriageRunRequest) -> TriageRunSummary:
    """Executes deterministic anomaly detection, evidence correlation, and context creation."""
    logger.info(f"Triage run requested for ingestion_id='{request.ingestion_id}', source_id='{request.source_id}'")
    try:
        summary, _, _, _, _ = triage_engine.run_triage(request)
        return summary
    except (ValueError, FileNotFoundError) as err:
        logger.warning(f"Triage request error: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as exc:
        logger.error(f"Triage pipeline failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Triage pipeline failed: {str(exc)}",
        )


@app.get(
    "/api/v1/triage",
    response_model=List[TriageRunSummary],
    tags=["Anomaly Triage"]
)
def list_triage_runs(limit: int = Query(default=50, ge=1, le=500)) -> List[TriageRunSummary]:
    """Lists recent anomaly triage execution summaries."""
    return storage.list_triage_summaries(limit=limit)


@app.get(
    "/api/v1/triage/{triage_run_id}",
    response_model=TriageRunSummary,
    tags=["Anomaly Triage"]
)
def get_triage_run(triage_run_id: str) -> TriageRunSummary:
    """Retrieves summary metrics for a specific triage run."""
    summary = storage.get_triage_summary(triage_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Triage run '{triage_run_id}' not found.",
        )
    return summary


@app.get(
    "/api/v1/triage/{triage_run_id}/findings",
    response_model=List[AnomalyFinding],
    tags=["Anomaly Triage"]
)
def get_triage_findings(triage_run_id: str) -> List[AnomalyFinding]:
    """Queries candidate anomaly findings identified during the triage run."""
    summary = storage.get_triage_summary(triage_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Triage run '{triage_run_id}' not found.",
        )
    return storage.get_triage_findings(triage_run_id)


@app.get(
    "/api/v1/triage/{triage_run_id}/correlation",
    response_model=CorrelationReport,
    tags=["Anomaly Triage"]
)
def get_triage_correlation(triage_run_id: str) -> CorrelationReport:
    """Retrieves deterministic correlation report linking findings, entities, and evidence."""
    report = storage.get_triage_correlation(triage_run_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correlation report for triage run '{triage_run_id}' not found.",
        )
    return report


@app.get(
    "/api/v1/triage/{triage_run_id}/context",
    response_model=InvestigationContext,
    tags=["Anomaly Triage"]
)
def get_investigation_context(triage_run_id: str) -> InvestigationContext:
    """Retrieves compact, typed investigation context for downstream Layer 3 Anomaly Investigator agents."""
    context = storage.get_investigation_context(triage_run_id)
    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation context for triage run '{triage_run_id}' not found.",
        )
    return context


# ==========================================
# Layer 3: Agentic Investigation & Diagnostic Planning Endpoints
# ==========================================

investigation_orchestrator = InvestigationOrchestrator(storage)


@app.post(
    "/api/v1/investigations",
    response_model=InvestigationSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Agentic Investigation"]
)
def create_investigation(request: InvestigationRequest) -> InvestigationSummary:
    """Executes Layer 3 bounded agentic investigation and diagnostic planning."""
    logger.info(f"Investigation requested for triage_run_id='{request.triage_run_id}'")
    try:
        summary, _, _, _ = investigation_orchestrator.run_investigation(request)
        return summary
    except ValueError as err:
        logger.warning(f"Investigation request validation error: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as exc:
        logger.error(f"Investigation orchestrator failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Investigation failed: {str(exc)}",
        )


@app.get(
    "/api/v1/investigations",
    response_model=List[InvestigationSummary],
    tags=["Agentic Investigation"]
)
def list_investigations(limit: int = Query(default=50, ge=1, le=500)) -> List[InvestigationSummary]:
    """Lists recent agentic investigation execution summaries."""
    return storage.list_investigation_summaries(limit=limit)


@app.get(
    "/api/v1/investigations/{investigation_id}",
    response_model=InvestigationSummary,
    tags=["Agentic Investigation"]
)
def get_investigation(investigation_id: str) -> InvestigationSummary:
    """Retrieves high-level summary metrics for a specific investigation."""
    summary = storage.get_investigation_summary(investigation_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return summary


@app.get(
    "/api/v1/investigations/{investigation_id}/report",
    response_model=InvestigationReport,
    tags=["Agentic Investigation"]
)
def get_investigation_report(investigation_id: str) -> InvestigationReport:
    """Retrieves full structured InvestigationReport produced by Agent A."""
    report = storage.get_investigation_report(investigation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation report for '{investigation_id}' not found.",
        )
    return report


@app.get(
    "/api/v1/investigations/{investigation_id}/plan",
    response_model=DiagnosticPlan,
    tags=["Agentic Investigation"]
)
def get_investigation_plan(investigation_id: str) -> DiagnosticPlan:
    """Retrieves actionable DiagnosticPlan produced by Agent B."""
    plan = storage.get_investigation_plan(investigation_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Diagnostic plan for '{investigation_id}' not found.",
        )
    return plan


@app.get(
    "/api/v1/investigations/{investigation_id}/events",
    response_model=List[InvestigationEvent],
    tags=["Agentic Investigation"]
)
def get_investigation_events(investigation_id: str) -> List[InvestigationEvent]:
    """Retrieves audit trace of state transitions and tool calls for the investigation."""
    summary = storage.get_investigation_summary(investigation_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return storage.get_investigation_events(investigation_id)


# ==========================================
# Layer 4: Candidate Mitigation Evaluation & Digital-Twin Simulation Endpoints
# ==========================================

mitigation_engine = MitigationEvaluationEngine(storage)


@app.post(
    "/api/v1/mitigation-evaluations",
    response_model=MitigationEvaluationSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Mitigation Evaluation"]
)
def create_mitigation_evaluation(request: MitigationEvaluationRequest) -> MitigationEvaluationSummary:
    """Executes Layer 4 candidate mitigation evaluation, path validation, and digital-twin simulation."""
    logger.info(f"Mitigation evaluation requested for investigation_id='{request.investigation_id}'")
    try:
        summary, _, _, _ = mitigation_engine.run_evaluation(request)
        return summary
    except ValueError as err:
        logger.warning(f"Mitigation evaluation validation error: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as exc:
        logger.error(f"Mitigation evaluation engine failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Evaluation failed: {str(exc)}",
        )


@app.get(
    "/api/v1/mitigation-evaluations",
    response_model=List[MitigationEvaluationSummary],
    tags=["Mitigation Evaluation"]
)
def list_mitigation_evaluations(limit: int = Query(default=50, ge=1, le=500)) -> List[MitigationEvaluationSummary]:
    """Lists recent mitigation evaluation run summaries."""
    return storage.list_mitigation_summaries(limit=limit)


@app.get(
    "/api/v1/mitigation-evaluations/{evaluation_id}",
    response_model=MitigationEvaluationSummary,
    tags=["Mitigation Evaluation"]
)
def get_mitigation_evaluation(evaluation_id: str) -> MitigationEvaluationSummary:
    """Retrieves summary metrics for a specific mitigation evaluation run."""
    summary = storage.get_mitigation_summary(evaluation_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mitigation evaluation '{evaluation_id}' not found.",
        )
    return summary


@app.get(
    "/api/v1/mitigation-evaluations/{evaluation_id}/candidates",
    response_model=List[CandidateEvaluation],
    tags=["Mitigation Evaluation"]
)
def get_mitigation_candidates(evaluation_id: str) -> List[CandidateEvaluation]:
    """Retrieves all candidate evaluations and validation records for a run."""
    summary = storage.get_mitigation_summary(evaluation_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mitigation evaluation '{evaluation_id}' not found.",
        )
    return storage.get_candidate_evaluations(evaluation_id)


@app.get(
    "/api/v1/mitigation-evaluations/{evaluation_id}/report",
    response_model=MitigationEvaluationReport,
    tags=["Mitigation Evaluation"]
)
def get_mitigation_report(evaluation_id: str) -> MitigationEvaluationReport:
    """Retrieves full detailed MitigationEvaluationReport with gate verdict and counterexamples."""
    report = storage.get_mitigation_report(evaluation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mitigation evaluation report for '{evaluation_id}' not found.",
        )
    return report


@app.get(
    "/api/v1/mitigation-evaluations/{evaluation_id}/events",
    response_model=List[EvaluationEvent],
    tags=["Mitigation Evaluation"]
)
def get_evaluation_events(evaluation_id: str) -> List[EvaluationEvent]:
    """Retrieves monotonically sequenced audit events recorded during mitigation evaluation."""
    summary = storage.get_mitigation_summary(evaluation_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Mitigation evaluation '{evaluation_id}' not found.",
        )
    return storage.get_evaluation_events(evaluation_id)


# ==========================================
# Layer 5: Counterexample-Guided Adaptive Diagnostics & Re-evaluation Endpoints
# ==========================================

adaptive_engine = AdaptiveInvestigationEngine(storage)


@app.post(
    "/api/v1/adaptive-investigations",
    response_model=AdaptiveInvestigationSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Adaptive Investigation"]
)
def create_adaptive_investigation(request: AdaptiveInvestigationRequest) -> AdaptiveInvestigationSummary:
    """Executes counterexample-guided adaptive diagnostics, uncertainty updates, and candidate re-evaluation."""
    logger.info(f"Adaptive investigation requested for evaluation_id='{request.evaluation_id}'")
    try:
        summary, _, _ = adaptive_engine.run_adaptive_investigation(request)
        return summary
    except ValueError as err:
        logger.warning(f"Adaptive investigation validation error: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )
    except Exception as exc:
        logger.error(f"Adaptive investigation engine failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Adaptive investigation execution failed: {str(exc)}",
        )


@app.get(
    "/api/v1/adaptive-investigations",
    response_model=List[AdaptiveInvestigationSummary],
    tags=["Adaptive Investigation"]
)
def list_adaptive_investigations(
    limit: int = Query(default=20, ge=1, le=100, description="Max runs to return")
) -> List[AdaptiveInvestigationSummary]:
    """Lists recent adaptive investigation summaries."""
    return storage.list_adaptive_summaries(limit=limit)


@app.get(
    "/api/v1/adaptive-investigations/{adaptive_run_id}",
    response_model=AdaptiveInvestigationSummary,
    tags=["Adaptive Investigation"]
)
def get_adaptive_summary(adaptive_run_id: str) -> AdaptiveInvestigationSummary:
    """Retrieves summary metrics and gate decisions for an adaptive investigation run."""
    summary = storage.get_adaptive_summary(adaptive_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive investigation '{adaptive_run_id}' not found.",
        )
    return summary


@app.get(
    "/api/v1/adaptive-investigations/{adaptive_run_id}/diagnostics",
    response_model=List[DiagnosticExecutionRecord],
    tags=["Adaptive Investigation"]
)
def get_adaptive_diagnostics(adaptive_run_id: str) -> List[DiagnosticExecutionRecord]:
    """Retrieves all diagnostic tool executions, observations, and error models for an adaptive run."""
    summary = storage.get_adaptive_summary(adaptive_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive investigation '{adaptive_run_id}' not found.",
        )
    return storage.get_adaptive_diagnostics(adaptive_run_id)


@app.get(
    "/api/v1/adaptive-investigations/{adaptive_run_id}/events",
    response_model=List[AdaptiveEvent],
    tags=["Adaptive Investigation"]
)
def get_adaptive_events(adaptive_run_id: str) -> List[AdaptiveEvent]:
    """Retrieves monotonically sequenced audit events recorded during adaptive investigation."""
    summary = storage.get_adaptive_summary(adaptive_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive investigation '{adaptive_run_id}' not found.",
        )
    return storage.get_adaptive_events(adaptive_run_id)


@app.get(
    "/api/v1/adaptive-investigations/{adaptive_run_id}/report",
    response_model=AdaptiveInvestigationReport,
    tags=["Adaptive Investigation"]
)
def get_adaptive_report(adaptive_run_id: str) -> AdaptiveInvestigationReport:
    """Retrieves full detailed AdaptiveInvestigationReport with before/after comparisons and gate justification."""
    report = storage.get_adaptive_report(adaptive_run_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adaptive investigation report for '{adaptive_run_id}' not found.",
        )
    return report


# ==========================================
# Layer 6: Evidence-Based Explainable AI (XAI) Endpoints
# ==========================================

explanation_engine = ExplanationEngine(storage)


def _sanitize_param(val: Optional[str]) -> Optional[str]:
    """Sanitizes string parameters, treating 'None', 'undefined', etc. as None."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "None", "null", "undefined", "NONE"):
        return None
    return s


@app.post(
    "/api/v1/explanations",
    response_model=DecisionExplanation,
    status_code=status.HTTP_201_CREATED,
    tags=["Explainable AI (XAI)"]
)
def create_explanation(request: ExplanationRequest) -> DecisionExplanation:
    """Generates an evidence-grounded DecisionExplanation linking rules, counterexamples, diagnostics, and sensitivity."""
    eval_id = _sanitize_param(request.evaluation_id)
    adapt_id = _sanitize_param(request.adaptive_run_id)
    run_id = _sanitize_param(request.run_id)
    scen_id = _sanitize_param(request.scenario_id)

    if run_id:
        if run_id.startswith("adapt-"):
            adapt_id = run_id
        elif run_id.startswith("eval-"):
            eval_id = run_id
        else:
            adapt_id = run_id

    if not eval_id and not adapt_id and not scen_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide at least one of 'evaluation_id', 'adaptive_run_id', 'run_id', or 'scenario_id'.",
        )

    logger.info(f"Explanation requested: evaluation_id='{eval_id}', adaptive_run_id='{adapt_id}', scenario_id='{scen_id}'")
    try:
        explanation = explanation_engine.generate_explanation(
            evaluation_id=eval_id,
            adaptive_run_id=adapt_id,
            scenario_id=scen_id,
            compute_sensitivity=request.compute_sensitivity,
            force_regenerate=request.force_regenerate,
        )
        return explanation
    except StorageResourceNotFoundError as err:
        logger.warning(f"Explanation resource not found: {err}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(err),
        )
    except ValueError as err:
        err_msg = str(err)
        if "not found in storage" in err_msg or "No completed evaluations found" in err_msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=err_msg,
            )
        logger.warning(f"Explanation validation error: {err}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=err_msg,
        )
    except Exception as exc:
        logger.error(f"Explanation engine failure: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Explanation generation failed: {str(exc)}",
        )


@app.get(
    "/api/v1/explanations",
    response_model=List[ExplanationSummary],
    tags=["Explainable AI (XAI)"]
)
def list_explanations(
    limit: int = Query(default=20, ge=1, le=100, description="Max explanations to return")
) -> List[ExplanationSummary]:
    """Lists recent decision explanation summaries."""
    return explanation_engine.list_explanations(limit=limit)


@app.get(
    "/api/v1/explanations/{explanation_id}",
    response_model=DecisionExplanation,
    tags=["Explainable AI (XAI)"]
)
def get_explanation(explanation_id: str) -> DecisionExplanation:
    """Retrieves full evidence-grounded DecisionExplanation by ID."""
    clean_id = _sanitize_param(explanation_id)
    if not clean_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing or invalid explanation_id.",
        )
    explanation = explanation_engine.get_explanation(clean_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision explanation '{clean_id}' not found.",
        )
    return explanation


@app.get(
    "/api/v1/explanations/{explanation_id}/rules",
    response_model=List[GateRuleExplanation],
    tags=["Explainable AI (XAI)"]
)
def get_explanation_rules(explanation_id: str) -> List[GateRuleExplanation]:
    """Retrieves rule-by-rule deterministic gate predicates and numerical evaluations."""
    explanation = explanation_engine.get_explanation(explanation_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision explanation '{explanation_id}' not found.",
        )
    return explanation.constraint_results


@app.get(
    "/api/v1/explanations/{explanation_id}/sensitivity",
    response_model=LocalSensitivityReport,
    tags=["Explainable AI (XAI)"]
)
def get_explanation_sensitivity(explanation_id: str) -> LocalSensitivityReport:
    """Retrieves deterministic local parameter sensitivity gradients and counterfactual edge perturbations."""
    explanation = explanation_engine.get_explanation(explanation_id)
    if not explanation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Decision explanation '{explanation_id}' not found.",
        )
    if not explanation.sensitivity_results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensitivity report not available for explanation '{explanation_id}'.",
        )
    return explanation.sensitivity_results


# ==========================================
# Layer 7: End-to-End Workflow Orchestration & Human Approval Endpoints
# ==========================================

workflow_orchestrator = EndToEndWorkflowOrchestrator(storage)


@app.post(
    "/api/v1/workflows",
    response_model=WorkflowRunSummary,
    status_code=status.HTTP_201_CREATED,
    tags=["Workflow Orchestration"]
)
def create_workflow_run(request: WorkflowRunRequest) -> WorkflowRunSummary:
    """Initiates an end-to-end decision workflow across Layers 1-6 up to the human approval boundary."""
    logger.info(f"Initiating workflow for scenario='{request.scenario_id}'")
    try:
        return workflow_orchestrator.initiate_workflow(request)
    except Exception as exc:
        logger.error(f"Workflow initiation failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow execution failed: {str(exc)}",
        )


@app.get(
    "/api/v1/workflows",
    response_model=List[WorkflowRunSummary],
    tags=["Workflow Orchestration"]
)
def list_workflow_runs(
    limit: int = Query(default=20, ge=1, le=100, description="Max runs to return")
) -> List[WorkflowRunSummary]:
    """Lists recent end-to-end workflow runs."""
    return storage.list_workflow_runs(limit=limit)


@app.get(
    "/api/v1/workflows/{workflow_run_id}",
    response_model=WorkflowRunSummary,
    tags=["Workflow Orchestration"]
)
def get_workflow_summary(workflow_run_id: str) -> WorkflowRunSummary:
    """Retrieves current execution status, stage, and gate verdicts for a workflow run."""
    summary = storage.get_workflow_run(workflow_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_run_id}' not found.",
        )
    return summary


@app.get(
    "/api/v1/workflows/{workflow_run_id}/events",
    response_model=List[WorkflowEvent],
    tags=["Workflow Orchestration"]
)
def get_workflow_events(workflow_run_id: str) -> List[WorkflowEvent]:
    """Retrieves monotonically sequenced audit events across all pipeline stages."""
    summary = storage.get_workflow_run(workflow_run_id)
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow run '{workflow_run_id}' not found.",
        )
    return storage.get_workflow_events(workflow_run_id)


@app.post(
    "/api/v1/workflows/{workflow_run_id}/approval",
    response_model=WorkflowRunSummary,
    tags=["Human Approval Boundary"]
)
def submit_workflow_approval(workflow_run_id: str, request: ApprovalRequest) -> WorkflowRunSummary:
    """Submits human authorization, rejection, or changes-requested decision."""
    logger.info(f"Submitting approval for workflow='{workflow_run_id}': decision='{request.decision}'")
    try:
        summary, _ = workflow_orchestrator.submit_approval(workflow_run_id, request)
        return summary
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Approval submission failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Approval submission failed: {str(exc)}",
        )


@app.get(
    "/api/v1/workflows/{workflow_run_id}/approval",
    response_model=HumanApprovalRecord,
    tags=["Human Approval Boundary"]
)
def get_workflow_approval(workflow_run_id: str) -> HumanApprovalRecord:
    """Retrieves human authorization record for an intervention."""
    approval = storage.get_approval_by_workflow(workflow_run_id)
    if not approval:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No human approval record found for workflow '{workflow_run_id}'.",
        )
    return approval


@app.post(
    "/api/v1/workflows/{workflow_run_id}/execute",
    response_model=InterventionOutcomeReport,
    tags=["Simulated Action Execution"]
)
def execute_workflow_intervention(workflow_run_id: str) -> InterventionOutcomeReport:
    """Executes the human-approved routing change in the isolated digital-twin simulator."""
    try:
        _, outcome = workflow_orchestrator.execute_simulated_intervention(workflow_run_id)
        return outcome
    except ValueError as val_err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
    except Exception as exc:
        logger.error(f"Simulation execution failed: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intervention execution failed: {str(exc)}",
        )


@app.get(
    "/api/v1/workflows/{workflow_run_id}/outcome",
    response_model=InterventionOutcomeReport,
    tags=["Outcome Reporting"]
)
def get_workflow_outcome(workflow_run_id: str) -> InterventionOutcomeReport:
    """Retrieves pre vs post intervention outcome report."""
    outcome = storage.get_outcome_by_workflow(workflow_run_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No outcome report found for workflow '{workflow_run_id}'. Intervention may not have executed yet.",
        )
    return outcome


# ==========================================
# Scenarios, Baselines, Runs & Investigation Endpoints (REST-Native)
# ==========================================

from ..scenarios import DEMO_SCENARIOS
from ..baseline_evaluator import run_four_way_comparison
from ..orchestrator import investigate
from ..cli import run_adaptive_investigation, get_detailed_sweep


@app.get("/api/v1/scenarios", tags=["Scenarios"])
@app.get("/api/scenarios", tags=["Scenarios"])
def get_scenarios_list() -> Dict[str, Any]:
    """Lists registered canonical network simulation scenarios."""
    scenarios_data = {k: s.model_dump() for k, s in DEMO_SCENARIOS.items()}
    return {"status": "success", "data": scenarios_data}


@app.get("/api/v1/baselines", tags=["Evaluation Lab"])
@app.get("/api/baselines", tags=["Evaluation Lab"])
def get_baselines_comparison() -> Dict[str, Any]:
    """Executes deterministic 4-way baseline benchmark evaluation."""
    comparison = run_four_way_comparison()
    return {"status": "success", "data": comparison}


@app.get("/api/v1/runs", tags=["Audit Runs"])
@app.get("/api/runs", tags=["Audit Runs"])
def get_recent_runs_list(limit: int = Query(default=50, ge=1, le=500)) -> List[Dict[str, Any]]:
    """Retrieves recent simulation and workflow runs from persistent storage."""
    rows = storage.recent(limit)
    runs = []
    for r in rows:
        runs.append({
            "id": r[0],
            "created_at": r[1],
            "scenario_id": r[2],
            "scenario_name": r[3],
            "decision": r[4],
            "reason": r[5],
            "report": json.loads(r[6]) if isinstance(r[6], str) else r[6],
        })
    return runs


@app.get("/api/v1/investigate", tags=["Investigation"])
@app.post("/api/v1/investigate", tags=["Investigation"])
@app.get("/api/investigate", tags=["Investigation"])
@app.post("/api/investigate", tags=["Investigation"])
def run_investigation_api(
    scenario: Optional[str] = Query(default=None),
    scenario_key: Optional[str] = Query(default=None),
    evaluations: int = Query(default=25),
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Executes deterministic investigation and digital-twin parameter sweep."""
    key = scenario_key or scenario
    if payload:
        key = payload.get("scenario_key") or payload.get("scenario") or key
        evaluations = payload.get("evaluations", evaluations)
    if not key:
        key = "wan_congestion"

    if key not in DEMO_SCENARIOS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scenario: {key}",
        )

    scenario_obj = DEMO_SCENARIOS[key]
    scenario_obj, gate, run_id = investigate(key, settings.DATABASE_PATH, evaluations)
    detailed_points = get_detailed_sweep(scenario_obj, evaluations)

    return {
        "status": "success",
        "run_id": run_id,
        "scenario": scenario_obj.model_dump(),
        "gate": {
            "decision": gate.decision.value,
            "reason": gate.reason,
            "report": gate.report.model_dump(),
        },
        "sweep_points": detailed_points,
    }


@app.get("/api/v1/adaptive-investigation", tags=["Adaptive Investigation"])
@app.post("/api/v1/adaptive-investigation", tags=["Adaptive Investigation"])
@app.get("/api/v1/adaptive-investigate", tags=["Adaptive Investigation"])
@app.post("/api/v1/adaptive-investigate", tags=["Adaptive Investigation"])
@app.get("/api/adaptive-investigation", tags=["Adaptive Investigation"])
@app.post("/api/adaptive-investigation", tags=["Adaptive Investigation"])
@app.get("/api/adaptive-investigate", tags=["Adaptive Investigation"])
@app.post("/api/adaptive-investigate", tags=["Adaptive Investigation"])
def run_adaptive_investigation_api(
    scenario: Optional[str] = Query(default=None),
    scenario_key: Optional[str] = Query(default=None),
    payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Executes counterexample search, targeted diagnostic probing, and Bayesian-bounded re-evaluation."""
    key = scenario_key or scenario
    if payload:
        key = payload.get("scenario_key") or payload.get("scenario") or key
    if not key:
        key = "wan_congestion"

    if key not in DEMO_SCENARIOS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scenario: {key}",
        )

    return run_adaptive_investigation(key, settings.DATABASE_PATH)



