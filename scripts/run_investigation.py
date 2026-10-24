#!/usr/bin/env python3
"""
scripts/run_investigation.py
CLI runner for Layer 3: Bounded Agentic Investigation, Tool Use and Diagnostic Planning.
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from fidelitygate.investigation.orchestrator import InvestigationOrchestrator
from fidelitygate.investigation.models import AgentMode, InvestigationRequest
from fidelitygate.storage import StorageEngine


def main():
    parser = argparse.ArgumentParser(description="Run bounded agentic investigation and diagnostic planning.")
    parser.add_argument(
        "--triage-id",
        default=None,
        help="Target Layer 2 triage run ID (if omitted, most recent triage run is used)"
    )
    parser.add_argument(
        "--scenario-id",
        default=None,
        help="Optional network scenario ID context"
    )
    parser.add_argument(
        "--mode",
        choices=["live_llm", "deterministic_planner", "deterministic_baseline"],
        default=None,
        help="Explicit execution mode override"
    )
    parser.add_argument(
        "--execute-probe",
        action="store_true",
        help="Authorize orchestrator to execute the top-ranked diagnostic probe"
    )
    parser.add_argument(
        "--output-json",
        default=None,
        help="Optional file path to persist full investigation JSON payload"
    )
    args = parser.parse_args()

    storage = StorageEngine()
    orchestrator = InvestigationOrchestrator(storage)

    triage_id = args.triage_id
    if not triage_id:
        summaries = storage.list_triage_summaries(limit=1)
        if not summaries:
            print("[ERROR] No triage runs found in database. Run Layer 2 triage first via scripts/run_triage.py.", file=sys.stderr)
            sys.exit(1)
        triage_id = summaries[0].triage_run_id

    mode_map = {
        "live_llm": AgentMode.LIVE_LLM_AGENT,
        "deterministic_planner": AgentMode.DETERMINISTIC_PLANNER,
        "deterministic_baseline": AgentMode.DETERMINISTIC_BASELINE,
    }
    preferred_mode = mode_map.get(args.mode) if args.mode else None

    req = InvestigationRequest(
        triage_run_id=triage_id,
        scenario_id=args.scenario_id,
        agent_mode=preferred_mode,
    )

    print(f"Executing Agentic Investigation on triage_run_id='{triage_id}'...")
    try:
        summary, report, plan, events = orchestrator.run_investigation(
            request=req,
            execute_selected_probe=args.execute_probe,
        )
    except Exception as exc:
        print(f"\n[ERROR] Investigation execution failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== Investigation Run Summary ({summary.investigation_id}) ===")
    print(f"Status:                      {summary.status.value}")
    print(f"Agent Execution Mode:        {summary.agent_mode.value}")
    print(f"Triage Run Ref:              {summary.triage_run_id}")
    print(f"Hypotheses Formed (Agent A): {summary.hypotheses_count}")
    print(f"Diagnostic Candidates (B):   {summary.candidate_diagnostics_count}")
    print(f"Selected Diagnostic:         {summary.selected_diagnostic_id or 'None'}")
    if summary.fallback_reason:
        print(f"Fallback Reason:             {summary.fallback_reason}")

    print("\n--- Agent A: Formulated Hypotheses ---")
    for i, h in enumerate(report.hypotheses, 1):
        print(f"  {i}. [{h.hypothesis_type.value}] {h.statement}")
        print(f"     Status: {h.uncertainty_status} | Conf: {h.confidence_score*100:.0f}% | Origin: {h.label_origin.value}")
        print(f"     Supporting Evidence IDs: {h.supporting_evidence_ids[:4]}")
        if h.limitations:
            print(f"     Limitations: {h.limitations[0]}")

    print("\n--- Agent B: Diagnostic & Mitigation Plan ---")
    print(f"Plan ID: {plan.plan_id} (Status: {plan.status.value})")
    if plan.proposed_interventions:
        print(f"Proposed Interventions: {plan.proposed_interventions}")

    print("Ranked Diagnostic Candidates:")
    for c in plan.candidate_diagnostics:
        sel_marker = " [SELECTED]" if c.diagnostic_id == plan.selected_diagnostic_id else ""
        print(f"  • Rank {c.rank}: {c.tool_name} ({c.diagnostic_id}){sel_marker}")
        print(f"    Target: {c.target_entity} -> {c.target_parameter}")
        print(f"    Purpose: {c.purpose}")
        print(f"    Expected: {c.expected_information_type} | Est Cost: ${c.estimated_cost_usd:.4f}")

    print("\nRemaining Budgets:")
    for k, v in plan.budget_remaining.items():
        print(f"  • {k}: {v}")

    print("\nAudit Event Trace (Sample):")
    for ev in events[:6]:
        print(f"  • [{ev.actor}] {ev.event_type} - {json.dumps(ev.details)[:80]}")

    if args.output_json:
        out_p = Path(args.output_json)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "summary": summary.model_dump(),
            "report": report.model_dump(),
            "plan": plan.model_dump(),
            "events": [e.model_dump() for e in events],
        }
        with open(out_p, "w", encoding="utf-8") as f_out:
            json.dump(payload, f_out, indent=2)
        print(f"\nFull investigation payload saved to: {out_p.resolve()}")

    print("\n[SUCCESS] Layer 3 agentic investigation execution complete.")
    sys.exit(0)


if __name__ == "__main__":
    main()

