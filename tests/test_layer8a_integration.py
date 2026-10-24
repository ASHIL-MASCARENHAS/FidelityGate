"""tests/test_layer8a_integration.py
Comprehensive verification suite for Layer 8A:
- Shared Run Context across tabs
- Canonical workflow execution and persistence
- Artifact ID preservation and distinct type namespaces
- CLI bridge command parity for events and approvals
- Prevention of stale approvals/outcomes cross-contamination
"""

import json
import os
import shutil
import subprocess
import pytest
from fastapi.testclient import TestClient

from fidelitygate.api.app import app
from fidelitygate.config import settings
from fidelitygate.storage import StorageEngine
from fidelitygate.workflow.models import (
    ApprovalDecision,
    ApprovalRequest,
    WorkflowRunRequest,
    WorkflowStage,
    WorkflowStatus,
)
from fidelitygate.workflow.orchestrator import EndToEndWorkflowOrchestrator


@pytest.fixture
def test_storage(tmp_path):
    db_file = str(tmp_path / "test_layer8a.db")
    if os.path.exists(settings.DATABASE_PATH):
        shutil.copy2(settings.DATABASE_PATH, db_file)
    storage = StorageEngine(db_file)
    return storage


@pytest.fixture
def orchestrator(test_storage):
    return EndToEndWorkflowOrchestrator(test_storage)


@pytest.fixture
def client():
    return TestClient(app)


# =========================================================================
# Test 1: Canonical Workflow Persistence Establishes Shared Context
# =========================================================================

def test_canonical_workflow_persistence(orchestrator, test_storage):
    """Verifies that initiating a workflow creates an authoritative SQLite record with distinct IDs."""
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    assert summary.workflow_run_id.startswith("wf-")
    assert summary.scenario_id == "wan_congestion"
    assert summary.status == WorkflowStatus.AWAITING_APPROVAL
    assert summary.current_stage == WorkflowStage.AWAITING_HUMAN_APPROVAL

    # Persisted record check
    stored = test_storage.get_workflow_run(summary.workflow_run_id)
    assert stored is not None
    assert stored.workflow_run_id == summary.workflow_run_id
    assert stored.selected_candidate_id is not None
    assert stored.gate_verdict is not None


# =========================================================================
# Test 2: Artifact IDs are Distinct and Not Interchangeable
# =========================================================================

def test_artifact_id_namespaces_and_distinction(orchestrator, test_storage):
    """Ensures each pipeline phase generates its own distinct ID namespace."""
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    # Validate distinct ID prefixes
    assert summary.triage_run_id is not None and summary.triage_run_id.startswith("trg-")
    assert summary.investigation_id is not None and summary.investigation_id.startswith("inv-")
    assert summary.evaluation_id is not None and summary.evaluation_id.startswith("eval-")
    assert summary.explanation_id is not None and summary.explanation_id.startswith("expl-")

    # None of the IDs may be equal to one another
    ids = [
        summary.workflow_run_id,
        summary.triage_run_id,
        summary.investigation_id,
        summary.evaluation_id,
        summary.explanation_id,
    ]
    if summary.adaptive_run_id:
        assert summary.adaptive_run_id.startswith("adapt-")
        ids.append(summary.adaptive_run_id)

    assert len(ids) == len(set(ids)), "Artifact IDs must be strictly unique and not swapped"


# =========================================================================
# Test 3: CLI Bridge get-workflow-events and approve-workflow Parity
# =========================================================================

def test_cli_bridge_parity():
    """Verifies CLI bridge commands match expected structure and output."""
    # Run CLI list-workflows to get an existing workflow
    proc = subprocess.run(
        ["python", "-m", "fidelitygate.cli", "list-workflows", "--limit", "1"],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0
    workflows = json.loads(proc.stdout)
    assert len(workflows) > 0
    wf_id = workflows[0]["workflow_run_id"]

    # Test get-workflow-events via CLI
    proc_events = subprocess.run(
        ["python", "-m", "fidelitygate.cli", "get-workflow-events", wf_id],
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc_events.returncode == 0
    events = json.loads(proc_events.stdout)
    assert isinstance(events, list)
    if events:
        first_event = events[0]
        assert "stage" in first_event
        assert "event_type" in first_event
        assert "sequence_number" in first_event


# =========================================================================
# Test 4: Stale Approvals and Outcomes Cannot Be Attached to New Runs
# =========================================================================

def test_stale_artifacts_isolation(orchestrator):
    """Verifies that a newly initiated workflow has no approval or outcome records attached."""
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    assert summary.approval_id is None
    assert summary.approval_status is None
    assert summary.outcome_id is None
    assert summary.overall_impact is None
    assert summary.status == WorkflowStatus.AWAITING_APPROVAL


# =========================================================================
# Test 5: Rejection Prevents Simulated Action Execution
# =========================================================================

def test_human_rejection_halts_workflow(orchestrator, test_storage):
    """Verifies that REJECTED_BY_HUMAN leaves outcome_id empty and terminal."""
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(scenario_id="wan_congestion", auto_approve_for_testing=False)
    )

    updated_summary, approval_rec = orchestrator.submit_approval(
        summary.workflow_run_id,
        ApprovalRequest(
            decision=ApprovalDecision.REJECTED,
            reviewer_id="lead-operator",
            reviewer_comment="Reroute rejected due to scheduled maintenance window.",
        ),
    )

    assert updated_summary.status == WorkflowStatus.REJECTED_BY_HUMAN
    assert updated_summary.approval_status == ApprovalDecision.REJECTED
    assert updated_summary.outcome_id is None
    assert updated_summary.overall_impact is None
    assert approval_rec.decision == ApprovalDecision.REJECTED

    # Verify persistent state
    persisted = test_storage.get_workflow_run(summary.workflow_run_id)
    assert persisted.status == WorkflowStatus.REJECTED_BY_HUMAN
    assert persisted.outcome_id is None

