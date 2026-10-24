#!/usr/bin/env python3
"""scripts/run_workflow.py
Standalone CLI runner to execute and demonstrate the complete Layer 7 end-to-end workflow:
Triage -> Investigation -> Evaluation -> Counterexamples -> Adaptive Diagnostics ->
Explanation -> Gate Review -> Human Approval -> Simulation -> Outcome Reporting.
"""

import argparse
import json
import sys
from pathlib import Path

# Ensure root workspace is on PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fidelitygate.storage import StorageEngine
from fidelitygate.workflow import (
    ApprovalDecision,
    ApprovalRequest,
    EndToEndWorkflowOrchestrator,
    OutcomeReporter,
    WorkflowRunRequest,
    WorkflowStage,
    WorkflowStatus,
)


def main():
    parser = argparse.ArgumentParser(description="FidelityGate Layer 7 End-to-End Workflow Runner")
    parser.add_argument("--scenario", default="wan_congestion", help="Scenario ID (default: wan_congestion)")
    parser.add_argument("--auto-approve", action="store_true", help="Automatically approve intervention for testing")
    parser.add_argument("--reject", action="store_true", help="Simulate human rejection of proposed intervention")
    parser.add_argument("--reviewer", default="operator-cli", help="Reviewer identity for approval audit")
    parser.add_argument("--output-json", default=None, help="Save final outcome to JSON file")
    args = parser.parse_args()

    storage = StorageEngine()
    orchestrator = EndToEndWorkflowOrchestrator(storage)

    print("=" * 65)
    print("FidelityGate -- Layer 7 End-to-End Workflow Execution")
    print(f"  Target Scenario Context: {args.scenario}")
    print("=" * 65)

    # 1. Initiate Workflow
    summary = orchestrator.initiate_workflow(
        WorkflowRunRequest(
            scenario_id=args.scenario,
            auto_approve_for_testing=False,
            reviewer_id=args.reviewer,
        )
    )

    print(f"\n[+] Workflow Initiated: {summary.workflow_run_id}")
    print(f"    Current Stage:       {summary.current_stage.value}")
    print(f"    Lifecycle Status:    {summary.status.value}")
    print(f"    Selected Candidate:  {summary.selected_candidate_id}")
    print(f"    Gate Verdict:        {summary.gate_verdict.value if summary.gate_verdict else 'N/A'}")

    events = storage.get_workflow_events(summary.workflow_run_id)
    print(f"\n[+] Pipeline Stages Executed ({len(events)} events):")
    for e in events:
        print(f"    #{e.sequence_number:02d} [{e.stage.value:<22}] {e.event_type}")

    if summary.status == WorkflowStatus.ABSTAINED:
        print("\n[!] Workflow halted at GATE_REVIEW: Gate evaluated ABSTAIN.")
        print(f"    Reason: {summary.termination_reason}")
        return

    # 2. Human Authorization Boundary
    print("\n" + "-" * 65)
    print("Human Authorization Boundary")
    print(f"  Candidate Proposed:    {summary.selected_candidate_id}")
    print(f"  Gate Recommendation:   {summary.gate_verdict.value}")
    print(f"  Explanation Snapshot:  {summary.explanation_id}")
    print("  Scope: Isolated Digital-Twin Simulation (No physical configuration enacted)")
    print("-" * 65)

    if args.reject:
        print("\n[*] Processing Human Decision: REJECT")
        summary_rej, appr = orchestrator.submit_approval(
            summary.workflow_run_id,
            ApprovalRequest(decision=ApprovalDecision.REJECTED, reviewer_id=args.reviewer, reviewer_comment="Rejected by CLI flag."),
        )
        print(f"[OK] Intervention REJECTED. Workflow terminated safely ({summary_rej.status.value}).")
        print(f"    Termination Notice: {summary_rej.termination_reason}")
        return

    # Approve
    print(f"\n[*] Processing Human Decision: APPROVED (Reviewer: {args.reviewer})")
    final_summary, approval = orchestrator.submit_approval(
        summary.workflow_run_id,
        ApprovalRequest(decision=ApprovalDecision.APPROVED, reviewer_id=args.reviewer, reviewer_comment="Approved for isolated simulation."),
    )

    outcome = storage.get_outcome_by_workflow(summary.workflow_run_id)
    if outcome:
        print("\n" + "=" * 65)
        print("Pre-Action vs Post-Action Intervention Outcome Report")
        print("=" * 65)
        print(OutcomeReporter.format_text_summary(outcome))
        print(f"\n* Overall Impact Assessment: {outcome.overall_impact.value}")
        print(f"* Bottleneck Edge:           {outcome.bottleneck_link}")
        print(f"* Total Workflow Latency:    {final_summary.duration_ms} ms")

        if args.output_json:
            with open(args.output_json, "w", encoding="utf-8") as f:
                json.dump(outcome.model_dump(), f, indent=2)
            print(f"\n[OK] Outcome report exported to '{args.output_json}'.")

    print("\n[OK] Layer 7 End-to-End Workflow Completed Successfully.")


if __name__ == "__main__":
    main()
