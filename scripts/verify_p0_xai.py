"""scripts/verify_p0_xai.py
Live full-stack verification script for FidelityGate P0 XAI runtime & data-contract repair.
Tests both FastAPI (:8000) and Next.js (:3000) endpoints for:
1. HTTP 404 on nonexistent evaluation IDs (eval-209).
2. HTTP 400 on missing/None parameters.
3. HTTP 201 on valid scenario / evaluation explanation generation.
4. Parity of single explanation lookup (?id= and /[id]) returning full constraint_results.
"""

import sys
import json
import urllib.request
import urllib.error

FASTAPI_URL = "http://127.0.0.1:8000"
NEXTJS_URL = "http://localhost:3000"


def make_request(url: str, method: str = "GET", payload: dict = None):
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, json.loads(body) if body else {}
    except urllib.error.HTTPError as err:
        body = err.read().decode("utf-8")
        try:
            parsed = json.loads(body)
        except Exception:
            parsed = {"raw": body}
        return err.code, parsed
    except Exception as exc:
        return 0, {"error": str(exc)}


def main():
    print("=" * 70)
    print("FIDELITYGATE — P0 XAI RUNTIME & CONTRACT REPAIR VERIFICATION")
    print("=" * 70)

    # 1. FastAPI direct checks
    print("\n[1] Checking FastAPI Backend (:8000)...")
    s, h = make_request(f"{FASTAPI_URL}/api/v1/health")
    if s != 200:
        print(f"FAILED: FastAPI backend is not running at {FASTAPI_URL} (status {s})")
        sys.exit(1)
    print(f" -> Health Status: {s} OK ({h.get('status')})")

    # 1a. Verify nonexistent evaluation ID returns 404
    s, d404 = make_request(f"{FASTAPI_URL}/api/v1/explanations", "POST", {"evaluation_id": "eval-209"})
    assert s == 404, f"Expected 404 for eval-209, got {s}: {d404}"
    print(f" -> Nonexistent evaluation_id 'eval-209': {s} 404 (Correct detail: {d404.get('detail')})")

    # 1b. Verify missing/None parameters returns 400
    s, d400 = make_request(f"{FASTAPI_URL}/api/v1/explanations", "POST", {"evaluation_id": "None", "scenario_id": "None"})
    assert s == 400, f"Expected 400 for None parameters, got {s}: {d400}"
    print(f" -> Missing / None parameters: {s} 400 (Correct detail: {d400.get('detail')})")

    # 1c. Verify valid explanation generation returns 201 with constraint_results
    s, d201 = make_request(f"{FASTAPI_URL}/api/v1/explanations", "POST", {"scenario_id": "wan_congestion"})
    assert s == 201, f"Expected 201, got {s}: {d201}"
    expl_id = d201.get("explanation_id")
    rules = d201.get("constraint_results", [])
    assert expl_id and len(rules) == 5, f"Expected 5 rules, got {len(rules)}"
    print(f" -> Valid POST explanation: {s} 201 (ID: {expl_id}, Rules: {len(rules)})")

    # 1d. Verify single detail lookup returns full model
    s, d_get = make_request(f"{FASTAPI_URL}/api/v1/explanations/{expl_id}")
    assert s == 200 and "constraint_results" in d_get
    print(f" -> Direct GET explanation: {s} 200 (Has constraint_results: True)")

    # 2. Next.js proxy checks
    print("\n[2] Checking Next.js Proxy & Frontend (:3000)...")
    s, n_health = make_request(f"{NEXTJS_URL}/api/v1/health")
    if s != 200:
        print(f"FAILED: Next.js dev server is not running at {NEXTJS_URL} (status {s})")
        sys.exit(1)
    print(f" -> Next.js Proxy Health: {s} OK")

    # 2a. Verify proxy returns 404 for eval-209
    s, np404 = make_request(f"{NEXTJS_URL}/api/v1/explanations", "POST", {"evaluation_id": "eval-209"})
    assert s == 404, f"Expected Next.js proxy 404, got {s}: {np404}"
    print(f" -> Next.js POST 'eval-209': {s} 404 (Correctly forwarded from FastAPI)")

    # 2b. Verify proxy returns 201 for valid scenario
    s, np201 = make_request(f"{NEXTJS_URL}/api/v1/explanations", "POST", {"scenario_id": "wan_congestion"})
    assert s == 201, f"Expected Next.js proxy 201, got {s}: {np201}"
    n_expl_id = np201.get("explanation_id")
    n_rules = np201.get("constraint_results", [])
    assert n_expl_id and len(n_rules) == 5
    print(f" -> Next.js POST 'wan_congestion': {s} 201 (ID: {n_expl_id}, Rules: {len(n_rules)})")

    # 2c. Verify query param ?id= returns single detail dictionary (NOT list)
    s, np_query = make_request(f"{NEXTJS_URL}/api/v1/explanations?id={n_expl_id}")
    assert s == 200 and isinstance(np_query, dict) and "constraint_results" in np_query
    print(f" -> Next.js GET '?id={n_expl_id}': {s} 200 (Single detail object, Has constraint_results: True)")

    # 2d. Verify dynamic route /[id] returns single detail
    s, np_path = make_request(f"{NEXTJS_URL}/api/v1/explanations/{n_expl_id}")
    assert s == 200 and isinstance(np_path, dict) and "constraint_results" in np_path
    print(f" -> Next.js GET '/{n_expl_id}': {s} 200 (REST dynamic route, Has constraint_results: True)")

    # 2e. Verify list endpoint returns list of summaries
    s, np_list = make_request(f"{NEXTJS_URL}/api/v1/explanations?limit=3")
    assert s == 200 and isinstance(np_list, list)
    print(f" -> Next.js GET list: {s} 200 (List of {len(np_list)} summaries)")

    # 3. Check workspace page HTML rendering
    print("\n[3] Checking Next.js Workspace Page...")
    s, _ = make_request(f"{NEXTJS_URL}/workspace")
    assert s == 200, f"Expected 200 for /workspace, got {s}"
    print(f" -> /workspace HTTP Status: {s} OK")

    print("\n" + "=" * 70)
    print("ALL P0 RUNTIME & DATA-CONTRACT CHECKS VERIFIED SUCCESSFULLY (100%)!")
    print("=" * 70)


if __name__ == "__main__":
    main()

