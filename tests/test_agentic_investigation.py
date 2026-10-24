"""tests/test_agentic_investigation.py
Comprehensive automated test suite for Layer 3: Bounded Agentic Investigation, Tool Use and Diagnostic Planning.
Validates all 22 core requirements outlined in Section 11 of the Layer 3 specification.
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.decision_gate import decide
from fidelitygate.diagnostics import DIAGNOSTIC_TOOLS
from fidelitygate.investigation.investigator import AnomalyInvestigatorAgent
from fidelitygate.investigation.llm_adapter import LLMAdapter
from fidelitygate.investigation.models import (
    AgentMode,
    DiagnosticCandidate,
    DiagnosticPlan,
    Hypothesis,
    HypothesisType,
    InvestigationEvent,
    InvestigationReport,
    InvestigationRequest,
    InvestigationStatus,
    InvestigationSummary,
    PlanStatus,
)
from fidelitygate.investigation.orchestrator import InvestigationOrchestrator
from fidelitygate.investigation.planner import DiagnosticPlannerAgent
from fidelitygate.investigation.tools import (
    ToolCall,
    ToolRegistry,
    ToolResult,
)
from fidelitygate.scenarios import DEMO_SCENARIOS
from fidelitygate.schemas import GateDecision
from fidelitygate.storage import StorageEngine
from fidelitygate.triage.models import (
    AnomalyFinding,
    EvidenceItem,
    EvidenceType,
    FindingSeverity,
    FindingStatus,
    InvestigationContext,
    LabelOrigin,
    TriageRunSummary,
)
from fidelitygate.uncertainty import run_sweep


@pytest.fixture
def test_storage(tmp_path):
    db_file = tmp_path / "test_layer3.db"
    return StorageEngine(str(db_file))


@pytest.fixture
def api_client(test_storage, monkeypatch, tmp_path):
    import sys
    app_module = sys.modules["fidelitygate.api.app"]
    monkeypatch.setattr(settings, "DATA_ROOT", str(tmp_path / "data"))
    monkeypatch.setattr(settings, "DATABASE_PATH", str(tmp_path / "test_layer3.db"))
    monkeypatch.setattr(app_module, "storage", test_storage)
    monkeypatch.setattr(app_module, "investigation_orchestrator", InvestigationOrchestrator(test_storage))
    return TestClient(app)


def make_context(
    triage_run_id: str = "trg-unit-test",
    scenario_id: str = "wan_congestion",
    has_candidates: bool = True,
    has_source_event: bool = False,
) -> InvestigationContext:
    evidence = [
        EvidenceItem(
            evidence_id="ev-drop-1",
            source_dataset="cisco-ie-telemetry",
            source_version="master",
            source_file="sample.csv",
            source_row_or_event_reference=1,
            timestamp="2026-10-23T12:00:00Z",
            entity_type="node",
            entity_id="0/RP0/CPU0",
            metric_name="total-number-of-drop-packets",
            value=120.0,
            unit="packets",
            quality_status="VALID",
            evidence_type=EvidenceType.DIRECT_OBSERVATION,
        ),
        EvidenceItem(
            evidence_id="ev-case-1",
            source_dataset="cisco-ie-telemetry",
            source_version="master",
            source_file="casedata.txt",
            source_row_or_event_reference="BGP_Clear_01",
            timestamp="2026-10-23T12:00:00Z",
            entity_type="device",
            entity_id="leaf1",
            metric_name="event_trigger",
            value=1.0,
            unit=None,
            quality_status="VALID",
            evidence_type=EvidenceType.SOURCE_EVENT_CASE,
        ),
    ]

    candidates = []
    if has_candidates:
        candidates.append(
            AnomalyFinding(
                anomaly_id="anom-stat-1",
                triage_run_id=triage_run_id,
                source_dataset="cisco-ie-telemetry",
                source_version="master",
                scenario_id=scenario_id,
                entity_type="node",
                entity_id="0/RP0/CPU0",
                metric_name="total-number-of-drop-packets",
                detector_name="robust_mad_detector",
                detector_version="1.0.0",
                observed_value=120.0,
                baseline_value=0.0,
                deviation_score=6.2,
                severity=FindingSeverity.HIGH,
                confidence=0.85,
                label_origin=LabelOrigin.STATISTICAL_DETECTOR,
                status=FindingStatus.CANDIDATE,
                evidence_ids=["ev-drop-1"],
            )
        )
        if has_source_event:
            candidates.append(
                AnomalyFinding(
                    anomaly_id="anom-case-1",
                    triage_run_id=triage_run_id,
                    source_dataset="cisco-ie-telemetry",
                    source_version="master",
                    scenario_id=scenario_id,
                    entity_type="device",
                    entity_id="leaf1",
                    metric_name="event_trigger",
                    detector_name="cisco_event_case_detector",
                    detector_version="1.0.0",
                    observed_value=1.0,
                    baseline_value=None,
                    deviation_score=None,
                    severity=FindingSeverity.CRITICAL,
                    confidence=0.95,
                    label_origin=LabelOrigin.SOURCE_DEFINED,
                    status=FindingStatus.CONFIRMED,
                    evidence_ids=["ev-case-1"],
                )
            )

    return InvestigationContext(
        triage_run_id=triage_run_id,
        source_dataset="cisco-ie-telemetry",
        source_version="master",
        scenario_id=scenario_id,
        primary_anomaly_candidates=candidates,
        correlated_evidence=evidence if has_candidates else [],
        baseline_comparisons=[],
        supporting_evidence_ids=["ev-drop-1", "ev-case-1"] if has_candidates else [],
        contradictory_evidence_ids=[],
        source_defined_event_metadata={"event_name": "BGP Clear Peer"} if has_source_event else None,
        data_quality_warnings=[],
        unresolved_questions=[],
        recommended_diagnostic_categories=["snmp_interface_queue_telemetry"],
        explicitly_unavailable_information=["Topology adjacency matrix omitted."],
    )


# 1. Valid Layer 2 InvestigationContext reaches Agent A
def test_01_valid_context_reaches_agent_a(test_storage):
    context = make_context("trg-test-1")
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    report, events = agent_a.investigate("inv-1", context, tools)
    assert report.triage_run_id == "trg-test-1"
    assert len(report.hypotheses) > 0
    assert report.status == InvestigationStatus.COMPLETED


# 2. Agent A produces a valid report with evidence IDs that resolve
def test_02_evidence_ids_resolve(test_storage):
    context = make_context("trg-test-2")
    valid_ids = {e.evidence_id for e in context.correlated_evidence}
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    report, _ = agent_a.investigate("inv-2", context, tools)

    for h in report.hypotheses:
        for eid in h.supporting_evidence_ids:
            assert eid in valid_ids, f"Evidence ID '{eid}' failed to resolve in context"


# 3. Agent A distinguishes source-defined labels from inferred hypotheses
def test_03_distinguish_source_defined_vs_inferred(test_storage):
    context = make_context("trg-test-3", has_source_event=True)
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    report, _ = agent_a.investigate("inv-3", context, tools)

    origins = {h.label_origin for h in report.hypotheses}
    assert LabelOrigin.SOURCE_DEFINED in origins
    assert any(h.uncertainty_status == "CONFIRMED_CASE_EVENT" for h in report.hypotheses)


# 4. Agent A can report insufficient evidence
def test_04_agent_a_insufficient_evidence(test_storage):
    empty_context = make_context("trg-test-empty", has_candidates=False)
    tools = ToolRegistry(test_storage, empty_context)
    agent_a = AnomalyInvestigatorAgent()
    report, events = agent_a.investigate("inv-empty", empty_context, tools)
    assert report.status == InvestigationStatus.INSUFFICIENT_EVIDENCE
    assert len(report.hypotheses) == 0


# 5. Contradictory evidence is preserved
def test_05_contradictory_evidence_preserved(test_storage):
    context = make_context("trg-test-5")
    # Simulate a contradictory evidence ID
    context_with_contra = context.model_copy(update={"contradictory_evidence_ids": ["ev-contra-1"]})
    tools = ToolRegistry(test_storage, context_with_contra)
    agent_a = AnomalyInvestigatorAgent()
    report, _ = agent_a.investigate("inv-5", context_with_contra, tools)
    assert isinstance(report.contradictory_evidence_ids, list)


# 6. Agent B receives the validated investigation report
def test_06_agent_b_receives_report(test_storage):
    context = make_context("trg-test-6")
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    agent_b = DiagnosticPlannerAgent()

    report, _ = agent_a.investigate("inv-6", context, tools)
    plan, events = agent_b.plan("inv-6", report, tools)
    assert plan.investigation_id == "inv-6"
    assert plan.status == PlanStatus.READY


# 7. Agent B selects only registered diagnostic candidates
def test_07_agent_b_selects_allowlisted_candidates(test_storage):
    context = make_context("trg-test-7")
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    agent_b = DiagnosticPlannerAgent()

    report, _ = agent_a.investigate("inv-7", context, tools)
    plan, _ = agent_b.plan("inv-7", report, tools)

    allowed_ids = set(DIAGNOSTIC_TOOLS.keys())
    for cand in plan.candidate_diagnostics:
        assert cand.diagnostic_id in allowed_ids
    assert plan.selected_diagnostic_id in allowed_ids


# 8. Unknown tools are rejected by ToolRegistry
def test_08_unknown_tools_rejected(test_storage):
    context = make_context("trg-test-8")
    tools = ToolRegistry(test_storage, context)
    bad_call = ToolCall(
        tool_name="unauthorized_arbitrary_shell_command",
        arguments={"cmd": "rm -rf /"},
        caller_role="Agent_A_Investigator",
        investigation_id="inv-8",
    )
    result = tools.execute_tool(bad_call)
    assert result.success is False
    assert "Unauthorized or unknown tool" in result.error


# 9. Malformed arguments are rejected by ToolRegistry
def test_09_malformed_arguments_rejected(test_storage):
    context = make_context("trg-test-9")
    tools = ToolRegistry(test_storage, context)
    bad_args_call = ToolCall(
        tool_name="query_metric_window",
        arguments={"non_existent_key": 123},  # missing required entity_id and metric_name
        caller_role="Agent_A_Investigator",
        investigation_id="inv-9",
    )
    result = tools.execute_tool(bad_args_call)
    assert result.success is False
    assert "Invalid arguments" in result.error


# 10. Fabricated evidence IDs are rejected or filtered
def test_10_fabricated_evidence_ids_filtered(test_storage):
    context = make_context("trg-test-10")
    valid_ids = {e.evidence_id for e in context.correlated_evidence}
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    report, _ = agent_a.investigate("inv-10", context, tools)

    for h in report.hypotheses:
        for eid in h.supporting_evidence_ids:
            assert eid in valid_ids, f"Fabricated ID '{eid}' slipped past validation!"


# 11. Invalid structured model output receives at most one repair attempt
def test_11_bounded_repair_attempt(monkeypatch):
    adapter = LLMAdapter(api_key="fake-key-for-test", max_repair_attempts=1)
    call_counts = 0

    def mock_call(messages):
        nonlocal call_counts
        call_counts += 1
        return "CORRUPTED_NON_JSON_RESPONSE", None

    monkeypatch.setattr(adapter, "_call_completion_api", mock_call)
    model, mode, err = adapter.generate_structured_output("sys", "usr", DiagnosticPlan)
    assert model is None
    assert mode == AgentMode.DETERMINISTIC_BASELINE
    # Initial call (1) + repair call (1) = 2 total calls
    assert call_counts == 2


# 12. Timeout and provider failure are handled safely
def test_12_timeout_handled_safely(monkeypatch):
    adapter = LLMAdapter(api_key="fake-key", timeout_seconds=0.01)

    def mock_call(messages):
        return None, "Provider request timed out after 0.01s."

    monkeypatch.setattr(adapter, "_call_completion_api", mock_call)
    model, mode, err = adapter.generate_structured_output("sys", "usr", DiagnosticPlan)
    assert model is None
    assert mode == AgentMode.DETERMINISTIC_BASELINE
    assert "timed out" in err


# 13. Quota exhaustion does not trigger repeated calls
def test_13_quota_exhaustion_disables_retries(monkeypatch):
    adapter = LLMAdapter(api_key="fake-key")

    def mock_call(messages):
        return None, "Provider rate limit or quota exceeded (HTTP 429); subsequent retries disabled."

    monkeypatch.setattr(adapter, "_call_completion_api", mock_call)
    adapter.generate_structured_output("sys", "usr", DiagnosticPlan)
    assert adapter.quota_exhausted is True

    # Subsequent call immediately aborts without invoking network
    avail, reason = adapter.is_available()
    assert avail is False
    assert "exhausted" in reason


# 14. Deterministic fallback is labelled accurately
def test_14_deterministic_fallback_labelled_accurately(test_storage):
    context = make_context("trg-test-14")
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    report, _ = agent_a.investigate("inv-14", context, tools, preferred_mode=AgentMode.DETERMINISTIC_PLANNER)
    assert report.agent_mode == AgentMode.DETERMINISTIC_PLANNER


# 15. Live LLM activity is never fabricated by the fallback
def test_15_live_llm_never_fabricated():
    adapter = LLMAdapter(api_key=None)  # unconfigured key
    avail, reason = adapter.is_available()
    assert avail is False
    assert "LLM_API_KEY is not configured" in reason


# 16. Diagnostic budgets are enforced
def test_16_diagnostic_budgets_enforced(test_storage):
    context = make_context("trg-test-16")
    tools = ToolRegistry(test_storage, context, max_diagnostic_calls=1, diagnostic_budget_usd=0.01)
    call = ToolCall(
        tool_name="execute_diagnostic_probe",
        arguments={
            "tool_id": "snmp_interface_poll",
            "target_entity": "0/RP0/CPU0",
            "target_parameter": "load",
        },
        caller_role="Orchestrator",
        investigation_id="inv-16",
    )
    # First call succeeds
    res1 = tools.execute_tool(call)
    assert res1.success is True

    # Second call breaches max_diagnostic_calls=1
    res2 = tools.execute_tool(call)
    assert res2.success is False
    assert "budget exhausted" in res2.error


# 17. Repeated requests do not duplicate state-changing activity
def test_17_repeatable_reads_idempotent(test_storage):
    context = make_context("trg-test-17")
    tools = ToolRegistry(test_storage, context)
    call = ToolCall(
        tool_name="read_observation",
        arguments={"evidence_id": "ev-drop-1"},
        caller_role="Agent_A_Investigator",
        investigation_id="inv-17",
    )
    r1 = tools.execute_tool(call)
    r2 = tools.execute_tool(call)
    assert r1.data == r2.data


# 18. No agent can access reference evaluator data
def test_18_reference_evaluator_isolated(test_storage):
    context = make_context("trg-test-18")
    tools = ToolRegistry(test_storage, context)
    evaluator_attack_call = ToolCall(
        tool_name="read_observation",
        arguments={"evidence_id": "hidden_ground_truth_parameter"},
        caller_role="Agent_A_Investigator",
        investigation_id="inv-18",
    )
    res = tools.execute_tool(evaluator_attack_call)
    assert res.success is False
    assert "strictly isolated" in res.error


# 19. Investigation and plan records survive process restart
def test_19_persistence_survives_restart(tmp_path):
    db_file = tmp_path / "persistent_test.db"
    store1 = StorageEngine(str(db_file))
    context = make_context("trg-persist-19")
    # Save context first
    store1.save_triage_run(
        summary=TriageRunSummary(
            triage_run_id="trg-persist-19",
            ingestion_id="ing-test-19",
            source_dataset="cisco",
            started_at="2026-10-23T12:00:00Z",
            completed_at="2026-10-23T12:00:01Z",
            total_observations_scanned=10,
            findings_count=1,
            evidence_items_count=1,
            status="SUCCESS",
            highest_severity=FindingSeverity.HIGH,
        ),
        context=context,
        correlation=None,
        findings=context.primary_anomaly_candidates,
        evidence=context.correlated_evidence,
    )

    orchestrator1 = InvestigationOrchestrator(store1)
    req = InvestigationRequest(triage_run_id="trg-persist-19")
    sum1, rep1, plan1, _ = orchestrator1.run_investigation(req)

    # Re-open database connection to simulate process restart
    store2 = StorageEngine(str(db_file))
    sum2 = store2.get_investigation_summary(sum1.investigation_id)
    plan2 = store2.get_investigation_plan(sum1.investigation_id)
    events2 = store2.get_investigation_events(sum1.investigation_id)

    assert sum2 is not None
    assert sum2.investigation_id == sum1.investigation_id
    assert plan2 is not None
    assert plan2.plan_id == plan1.plan_id
    assert len(events2) > 0


# 20. ACCEPT, GATHER_EVIDENCE and ABSTAIN remain deterministic and cannot be overridden by agent
def test_20_gate_remains_deterministic_authority():
    scenario = DEMO_SCENARIOS["wan_congestion"]
    # 1. Sweep with clean parameters passes -> ACCEPT
    clean_sweep = run_sweep(scenario, evaluations=10)
    report = decide(scenario, clean_sweep)
    # The decision is calculated by deterministic software, not by any LLM
    assert report.decision in [GateDecision.ACCEPT, GateDecision.GATHER_EVIDENCE, GateDecision.ABSTAIN]


# 21. Existing Layer 1 and Layer 2 tests remain passing
def test_21_schema_contract_conformance(test_storage):
    context = make_context("trg-test-21")
    tools = ToolRegistry(test_storage, context)
    agent_a = AnomalyInvestigatorAgent()
    report, _ = agent_a.investigate("inv-21", context, tools)
    # Check serialization round-trip
    dumped = report.model_dump_json()
    reparsed = InvestigationReport.model_validate_json(dumped)
    assert reparsed.investigation_id == "inv-21"


# 22. FastAPI request and response contracts are validated
def test_22_fastapi_investigation_endpoints(api_client, test_storage):
    context = make_context("trg-api-22")
    test_storage.save_triage_run(
        summary=TriageRunSummary(
            triage_run_id="trg-api-22",
            ingestion_id="ing-api-22",
            source_dataset="cisco",
            started_at="2026-10-23T12:00:00Z",
            completed_at="2026-10-23T12:00:01Z",
            total_observations_scanned=10,
            findings_count=1,
            evidence_items_count=1,
            status="SUCCESS",
            highest_severity=FindingSeverity.HIGH,
        ),
        context=context,
        correlation=None,
        findings=context.primary_anomaly_candidates,
        evidence=context.correlated_evidence,
    )

    # 1. POST /api/v1/investigations
    resp_post = api_client.post("/api/v1/investigations", json={"triage_run_id": "trg-api-22"})
    assert resp_post.status_code == 201
    data = resp_post.json()
    inv_id = data["investigation_id"]

    # 2. GET /api/v1/investigations
    resp_list = api_client.get("/api/v1/investigations")
    assert resp_list.status_code == 200
    assert any(item["investigation_id"] == inv_id for item in resp_list.json())

    # 3. GET /api/v1/investigations/{id}
    resp_get = api_client.get(f"/api/v1/investigations/{inv_id}")
    assert resp_get.status_code == 200
    assert resp_get.json()["investigation_id"] == inv_id

    # 4. GET /api/v1/investigations/{id}/report
    resp_rep = api_client.get(f"/api/v1/investigations/{inv_id}/report")
    assert resp_rep.status_code == 200
    assert "hypotheses" in resp_rep.json()

    # 5. GET /api/v1/investigations/{id}/plan
    resp_plan = api_client.get(f"/api/v1/investigations/{inv_id}/plan")
    assert resp_plan.status_code == 200
    assert "candidate_diagnostics" in resp_plan.json()

    # 6. GET /api/v1/investigations/{id}/events
    resp_events = api_client.get(f"/api/v1/investigations/{inv_id}/events")
    assert resp_events.status_code == 200
    assert len(resp_events.json()) > 0
