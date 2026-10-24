"""scripts/verify_layer7_live.py
Live Full-Stack Verification for FidelityGate Layer 7:
Tests FastAPI backend (:8000) and Next.js frontend proxy (:3000)
for complete workflow orchestration, human approval boundary, and outcome reporting.
"""

import json
import urllib.request
import urllib.error
import sys

def test_endpoint(name, url, method="GET", data=None):
    print(f"\n--- Testing {name} [{method} {url}] ---")
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.getcode()
            content = resp.read().decode("utf-8")
            parsed = json.loads(content)
            print(f"[OK] Status: {status}")
            return parsed
    except urllib.error.HTTPError as e:
        err_content = e.read().decode("utf-8")
        print(f"[ERROR] HTTP {e.code}: {err_content}")
        raise
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        raise

def main():
    print("=" * 70)
    print("FIDELITYGATE LAYER 7 LIVE FULL-STACK VERIFICATION")
    print("=" * 70)

    # 1. FastAPI direct: health
    test_endpoint("FastAPI Health Check", "http://127.0.0.1:8000/api/v1/health")

    # 2. Next.js proxy: health
    test_endpoint("Next.js Proxy Health Check", "http://localhost:3000/api/v1/health")

    # 3. Next.js proxy: Initiate Layer 7 Workflow (pause at gate)
    wf_init = test_endpoint(
        "Next.js Initiate Workflow (Pause at Gate)",
        "http://localhost:3000/api/v1/workflows",
        method="POST",
        data={
            "scenario_id": "wan_congestion",
            "reviewer_id": "live-verifier-alice",
            "auto_approve_for_testing": False,
        }
    )
    wf_id = wf_init["workflow_run_id"]
    status = wf_init["status"]
    stage = wf_init["current_stage"]
    gate = wf_init["gate_verdict"]
    print(f"-> Workflow Run Created: {wf_id}")
    print(f"-> Current Stage: {stage} (Status: {status})")
    print(f"-> Gate Verdict: {gate}")
    assert status == "AWAITING_APPROVAL", f"Expected AWAITING_APPROVAL, got {status}"
    assert stage == "AWAITING_HUMAN_APPROVAL", f"Expected AWAITING_HUMAN_APPROVAL, got {stage}"

    # 4. Next.js proxy: Audit events stream
    events = test_endpoint(
        "Next.js Get Workflow Events",
        f"http://localhost:3000/api/v1/workflows/{wf_id}/events"
    )
    print(f"-> Recorded Events: {len(events)}")
    assert len(events) >= 8, f"Expected at least 8 events, got {len(events)}"
    seqs = [e["sequence_number"] for e in events]
    assert seqs == list(range(1, len(events) + 1)), "Event sequence numbers must be monotonic 1..N"

    # 5. Next.js proxy: Submit Human Approval
    appr_res = test_endpoint(
        "Next.js Submit Human Authorization",
        f"http://localhost:3000/api/v1/workflows/{wf_id}/approval",
        method="POST",
        data={
            "decision": "APPROVED",
            "reviewer_id": "live-verifier-alice",
            "reviewer_comment": "Verified and authorized for production rollout window.",
        }
    )
    assert appr_res["status"] == "COMPLETED", f"Expected COMPLETED, got {appr_res['status']}"
    assert appr_res["approval_status"] == "APPROVED", f"Expected APPROVED, got {appr_res['approval_status']}"
    print(f"-> Workflow Completed! Duration: {appr_res.get('duration_ms')} ms")

    # 6. Next.js proxy: Fetch Comparative Outcome Report
    outcome = test_endpoint(
        "Next.js Fetch Outcome Report",
        f"http://localhost:3000/api/v1/workflows/{wf_id}/outcome"
    )
    print("\n--- Comparative Twin Simulation Outcome Summary ---")
    print(f"Pre-Action Latency:        {outcome['pre_action_latency_ms']:.2f} ms")
    print(f"Post-Action Latency:       {outcome['post_action_latency_ms']:.2f} ms")
    print(f"Latency Shift:             {outcome['latency_delta_ms']:.2f} ms ({outcome['latency_reduction_pct']:.1f}% reduction)")
    print(f"Pre-Action Utilization:    {outcome['pre_action_peak_utilization']*100:.1f}%")
    print(f"Post-Action Utilization:   {outcome['post_action_peak_utilization']*100:.1f}%")
    print(f"Overall Impact:            {outcome['overall_impact']}")
    print(f"Outcome ID:                {outcome['outcome_id']}")
    print(f"Candidate ID:              {outcome['candidate_id']}")
    print(f"Assumptions & Limits:      {len(outcome['assumptions_and_limitations'])} recorded")

    assert outcome["overall_impact"] in ("IMPROVED", "NEUTRAL"), f"Unexpected impact {outcome['overall_impact']}"
    assert outcome["post_action_latency_ms"] < outcome["pre_action_latency_ms"], "Post latency should improve"

    # 7. Next.js proxy: List Workflows
    wf_list = test_endpoint(
        "Next.js List Workflows",
        "http://localhost:3000/api/v1/workflows?limit=5"
    )
    assert len(wf_list) >= 1, "Should return at least 1 workflow"
    print(f"-> Listed {len(wf_list)} recent workflows successfully.")

    print("\n" + "=" * 70)
    print("ALL LAYER 7 LIVE FULL-STACK CHECKS PASSED WITH 100% SUCCESS!")
    print("=" * 70)

if __name__ == "__main__":
    main()
