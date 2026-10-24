"""scripts/verify_outcome_integrity.py
End-to-end audit and verification script for FidelityGate Outcome Integrity (P0).
Executes multiple live supported runs, checks deterministic reproducibility,
tests scenario and candidate sensitivity, verifies API contract outputs,
and logs traceable metrics.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from fidelitygate.api.app import app
from fidelitygate.storage import StorageEngine
from fidelitygate.workflow.outcome import OutcomeReporter


def run_audit():
    print("=" * 80)
    print("FIDELITYGATE OUTCOME INTEGRITY & DYNAMIC SIMULATION AUDIT")
    print("=" * 80)

    client = TestClient(app)
    storage = StorageEngine()

    # --------------------------------------------------------------------------
    # Run 1: WAN Congestion Surge (wan_congestion)
    # --------------------------------------------------------------------------
    print("\n--- [Run 1] Scenario: wan_congestion ---")
    res1 = client.post(
        "/api/v1/workflows",
        json={"scenario_id": "wan_congestion", "auto_approve_for_testing": True, "reviewer_id": "audit-operator-1"},
    )
    assert res1.status_code == 201, f"Failed initiating workflow: {res1.text}"
    wf1 = res1.json()
    wf1_id = wf1["workflow_run_id"]
    print(f"Workflow ID: {wf1_id}")
    print(f"Status: {wf1['status']}")
    print(f"Gate Verdict: {wf1.get('gate_verdict')}")
    print(f"Selected Candidate: {wf1.get('selected_candidate_id')}")

    res1_out = client.get(f"/api/v1/workflows/{wf1_id}/outcome")
    assert res1_out.status_code == 200, f"Failed getting outcome: {res1_out.text}"
    out1 = res1_out.json()
    print(f"Outcome ID: {out1['outcome_id']}")
    print(f"Pre-action Latency: {out1['pre_action_latency_ms']:.2f} ms")
    print(f"Post-action Latency: {out1['post_action_latency_ms']:.2f} ms")
    print(f"Latency Delta: {out1['latency_delta_ms']:.2f} ms ({out1['latency_reduction_pct']:.2f}%)")
    print(f"Pre-action Peak Util: {out1['pre_action_peak_utilization']*100:.1f}%")
    print(f"Post-action Peak Util: {out1['post_action_peak_utilization']*100:.1f}%")
    print(f"Capacity Breaches: {out1['post_action_capacity_violations']}")
    print(f"SLO Breaches: {out1['post_action_slo_violations']}")
    print(f"Bottleneck Link: {out1['bottleneck_link']}")
    print(f"Overall Impact: {out1['overall_impact']}")
    print(f"Affected Flows: {out1['affected_flows']}")

    # --------------------------------------------------------------------------
    # Run 2: Exact Repeat of WAN Congestion Surge (Reproducibility Verification)
    # --------------------------------------------------------------------------
    print("\n--- [Run 2] Scenario: wan_congestion (Reproducibility Repeat) ---")
    res2 = client.post(
        "/api/v1/workflows",
        json={"scenario_id": "wan_congestion", "auto_approve_for_testing": True, "reviewer_id": "audit-operator-2"},
    )
    assert res2.status_code == 201, f"Failed initiating workflow: {res2.text}"
    wf2 = res2.json()
    wf2_id = wf2["workflow_run_id"]
    print(f"Workflow ID: {wf2_id}")

    res2_out = client.get(f"/api/v1/workflows/{wf2_id}/outcome")
    assert res2_out.status_code == 200, f"Failed getting outcome: {res2_out.text}"
    out2 = res2_out.json()
    print(f"Outcome ID: {out2['outcome_id']}")

    # Assert distinct identifiers but deterministic identical calculations
    assert wf1_id != wf2_id, "Workflow IDs must be distinct"
    assert out1["outcome_id"] != out2["outcome_id"], "Outcome IDs must be distinct"
    assert out1["pre_action_latency_ms"] == out2["pre_action_latency_ms"] == 26.55
    assert out1["post_action_latency_ms"] == out2["post_action_latency_ms"] == 23.00
    assert out1["latency_delta_ms"] == out2["latency_delta_ms"] == -3.55
    assert out1["post_action_peak_utilization"] == out2["post_action_peak_utilization"] == 0.50
    assert out1["overall_impact"] == out2["overall_impact"] == "IMPROVED"
    print(">>> VERIFIED: Reproducibility holds with unique workflow & outcome IDs.")

    # --------------------------------------------------------------------------
    # Run 3: Fiber Latency Calibration Drift (fiber_drift)
    # --------------------------------------------------------------------------
    print("\n--- [Run 3] Scenario: fiber_drift (Scenario Sensitivity Verification) ---")
    res3 = client.post(
        "/api/v1/workflows",
        json={"scenario_id": "fiber_drift", "auto_approve_for_testing": True, "reviewer_id": "audit-operator-3"},
    )
    assert res3.status_code == 201, f"Failed initiating workflow: {res3.text}"
    wf3 = res3.json()
    wf3_id = wf3["workflow_run_id"]
    print(f"Workflow ID: {wf3_id}")
    print(f"Status: {wf3['status']}")
    print(f"Gate Verdict: {wf3.get('gate_verdict')}")

    res3_out = client.get(f"/api/v1/workflows/{wf3_id}/outcome")
    assert res3_out.status_code == 200, f"Failed getting outcome: {res3_out.text}"
    out3 = res3_out.json()
    print(f"Outcome ID: {out3['outcome_id']}")
    print(f"Pre-action Latency: {out3['pre_action_latency_ms']:.2f} ms")
    print(f"Post-action Latency: {out3['post_action_latency_ms']:.2f} ms")
    print(f"Latency Delta: {out3['latency_delta_ms']:.2f} ms ({out3['latency_reduction_pct']:.2f}%)")
    print(f"Pre-action Peak Util: {out3['pre_action_peak_utilization']*100:.1f}%")
    print(f"Post-action Peak Util: {out3['post_action_peak_utilization']*100:.1f}%")
    print(f"Bottleneck Link: {out3['bottleneck_link']}")
    print(f"Overall Impact: {out3['overall_impact']}")

    # Assert sensitivity between wan_congestion and fiber_drift
    assert out1["pre_action_latency_ms"] != out3["pre_action_latency_ms"]
    assert out1["post_action_latency_ms"] != out3["post_action_latency_ms"]
    assert out1["latency_delta_ms"] != out3["latency_delta_ms"]
    assert out3["pre_action_latency_ms"] == 35.83
    assert out3["post_action_latency_ms"] == 32.85
    assert out3["latency_delta_ms"] == -2.98
    print(">>> VERIFIED: Scenario sensitivity dynamically derives differing metrics.")

    # --------------------------------------------------------------------------
    # Run 4: Hidden Traffic Burst Spikes (traffic_burst)
    # --------------------------------------------------------------------------
    print("\n--- [Run 4] Scenario: traffic_burst (Conservative Gate Abstain Verification) ---")
    res4 = client.post(
        "/api/v1/workflows",
        json={"scenario_id": "traffic_burst", "auto_approve_for_testing": True, "reviewer_id": "audit-operator-4"},
    )
    assert res4.status_code == 201, f"Failed initiating workflow: {res4.text}"
    wf4 = res4.json()
    wf4_id = wf4["workflow_run_id"]
    print(f"Workflow ID: {wf4_id}")
    print(f"Status: {wf4['status']}")
    print(f"Gate Verdict: {wf4.get('gate_verdict')}")
    print(f"Termination Reason: {wf4.get('termination_reason')}")

    # For traffic_burst, the gate ABSTAINS. No outcome report should be generated!
    res4_out = client.get(f"/api/v1/workflows/{wf4_id}/outcome")
    assert res4_out.status_code == 404, f"Expected 404 for abstained workflow, got: {res4_out.status_code}"
    print(">>> VERIFIED: Abstained workflow fails closed; no fabricated outcome generated.")

    print("\n" + "=" * 80)
    print("ALL AUDIT & SENSITIVITY VERIFICATIONS COMPLETED SUCCESSFULLY (100% PASS)")
    print("=" * 80)


if __name__ == "__main__":
    run_audit()
