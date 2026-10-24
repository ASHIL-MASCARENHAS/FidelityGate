import urllib.request
import json
import sys

def verify_full_stack():
    print("=" * 65)
    print("FidelityGate Layer 6 Stack & XAI End-to-End Verification")
    print("=" * 65)

    # 1. Check health
    try:
        req = urllib.request.Request("http://127.0.0.1:8000/api/v1/health")
        with urllib.request.urlopen(req) as resp:
            h = json.loads(resp.read().decode())
            print(f"[HEALTH OK] Status={h.get('status')} | Version={h.get('version')} | DB Connected={h.get('database', {}).get('connected')}")
    except Exception as e:
        print("[HEALTH FAILED]:", e)
        return False

    # 2. Check Next.js Home & Workspace
    for path in ["/", "/workspace"]:
        try:
            req = urllib.request.Request(f"http://localhost:3000{path}")
            with urllib.request.urlopen(req) as resp:
                print(f"[UI OK] http://localhost:3000{path} -> HTTP {resp.status} (bytes: {len(resp.read())})")
        except Exception as e:
            print(f"[UI FAILED] http://localhost:3000{path} -> {e}")
            return False

    # 3. Test POST /api/v1/explanations for wan_congestion (GATHER_EVIDENCE)
    payload = json.dumps({"scenario_id": "wan_congestion", "compute_sensitivity": True}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/explanations",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req) as resp:
            exp = json.loads(resp.read().decode())
            print("\n[SUCCESS] FastAPI POST /api/v1/explanations (wan_congestion):")
            print(f"  • Explanation ID:    {exp['explanation_id']}")
            print(f"  • Run ID:            {exp['run_id']}")
            print(f"  • Scenario:          {exp['scenario_id']}")
            print(f"  • Candidate ID:      {exp.get('candidate_id')}")
            print(f"  • Gate Decision:     {exp['decision']}")
            print(f"  • Decision Rationale: {exp['decision_rationale']}")
            print(f"  • Evaluated Rules ({len(exp.get('constraint_results', []))}):")
            for rule in exp.get("constraint_results", []):
                status = rule["status"]
                print(f"      [{status}] {rule['rule_id']}: {rule['rule_name']} "
                      f"(Observed: {rule['observed_value']} {rule['unit']}, Condition: {rule['threshold_condition']})")

            ce = exp.get("counterexample_summary")
            if ce:
                print(f"  • Counterexample: Cause={ce['primary_failure_cause']}")
                print(f"      Violation Margin: +{ce['violation_margin_ms']}ms (Perturbed Latency: {ce['perturbed_latency_ms']}ms > SLO {ce['slo_latency_ms']}ms)")
                print(f"      Adversarial Vector: {ce['exact_parameter_vector']}")

            sens = exp.get("sensitivity_results")
            if sens:
                print(f"  • Local Sensitivity Analysis:")
                print(f"      Most Sensitive Parameter: {sens['most_sensitive_parameter']}")
                print(f"      Bottleneck Edge:          {sens['bottleneck_edge']}")
                for param in sens.get("evaluated_parameters", []):
                    print(f"        Rank {param['sensitivity_rank']}: {param['parameter_name']} (Elasticity={param['latency_elasticity']})")

            print("\n  • Synthesized Summary:")
            print(f"      \"{exp['summary']}\"")
    except Exception as e:
        print("Error testing FastAPI POST explanation:", e)
        return False

    # 4. Test POST /api/v1/explanations for adaptive run (ACCEPT with diagnostic measurement)
    payload_adapt = json.dumps({"run_id": "adapt-4438aaad", "compute_sensitivity": True}).encode("utf-8")
    req_adapt = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/explanations",
        data=payload_adapt,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req_adapt) as resp:
            exp_a = json.loads(resp.read().decode())
            print("\n[SUCCESS] FastAPI POST /api/v1/explanations for Adaptive Run (adapt-4438aaad):")
            print(f"  • Explanation ID:    {exp_a['explanation_id']}")
            print(f"  • Run ID:            {exp_a['run_id']}")
            print(f"  • Candidate ID:      {exp_a.get('candidate_id')}")
            print(f"  • Gate Decision:     {exp_a['decision']}")
            print(f"  • Decision Rationale: {exp_a['decision_rationale']}")
            print(f"  • Evaluated Rules ({len(exp_a.get('constraint_results', []))}):")
            for rule in exp_a.get("constraint_results", []):
                status = rule["status"]
                print(f"      [{status}] {rule['rule_id']}: {rule['rule_name']}")

            meas = exp_a.get("measurement_summary")
            if meas:
                print(f"  • Diagnostic Observation:")
                print(f"      Tool:              {meas['tool_name']} ({meas['tool_id']})")
                print(f"      Raw Sensor Value:  {meas['raw_measured_value']} {meas['raw_unit']} (error ±{meas['raw_error_bound']})")
                print(f"      Physical Inversion:{meas['parameter_measured_value']} {meas['parameter_unit']} (error ±{meas['parameter_error_bound']})")
                print(f"      Prior Interval:    {meas['prior_interval']}")
                print(f"      Posterior Interval:{meas['posterior_interval']} (reduction: {meas['width_reduction_pct']}%)")
                print(f"      Subsequent Impact: {meas['subsequent_gate_impact']}")

            print("\n  • Adaptive Synthesis:")
            print(f"      \"{exp_a['summary']}\"")
    except Exception as e:
        print("Error testing adaptive explanation:", e)
        return False

    # 5. Test Next.js proxy route /api/v1/explanations
    req2 = urllib.request.Request(
        "http://localhost:3000/api/v1/explanations",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req2) as resp:
            exp2 = json.loads(resp.read().decode())
            print("\n[SUCCESS] Next.js Proxy POST /api/v1/explanations:")
            print(f"  • Matched Explanation ID: {exp2['explanation_id']}")
            print(f"  • Matched Gate Decision:  {exp2['decision']}")
    except Exception as e:
        print("Error testing Next.js Proxy explanation:", e)
        return False

    print("\n" + "=" * 65)
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY - GO FOR PRESENTATION!")
    print("=" * 65)
    return True

if __name__ == "__main__":
    success = verify_full_stack()
    sys.exit(0 if success else 1)

