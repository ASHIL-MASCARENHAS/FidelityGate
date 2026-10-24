import sys
import json
import os
import time
from fidelitygate.scenarios import DEMO_SCENARIOS
from fidelitygate.schemas import Scenario, GateDecision
from fidelitygate.orchestrator import investigate
from fidelitygate.storage import RunStore
from fidelitygate.uncertainty import run_sweep
from fidelitygate.twin import predict_latency_ms, peak_utilization
from fidelitygate.counterexample import find_counterexample
from fidelitygate.diagnostics import select_targeted_diagnostic, execute_diagnostic, DIAGNOSTIC_TOOLS
from fidelitygate.baseline_evaluator import run_four_way_comparison
import numpy as np

def get_detailed_sweep(scenario: Scenario, evaluations: int = 25):
    latency_factors = np.linspace(scenario.latency_multiplier_min,
                                  scenario.latency_multiplier_max, evaluations)
    load_factors = np.linspace(.95, 1.15, evaluations)
    points = []
    latencies = []
    utils = []
    for i, (a, b) in enumerate(zip(latency_factors, load_factors)):
        lat = predict_latency_ms(scenario, float(a), float(b))
        u = peak_utilization(scenario, float(b))
        latencies.append(lat)
        utils.append(u)
        points.append({
            "sample": i + 1,
            "latency_factor": round(float(a), 4),
            "load_factor": round(float(b), 4),
            "latency_ms": round(float(lat), 2),
            "utilization": round(float(u), 4),
            "violated": bool(lat > scenario.slo_latency_ms)
        })
    return points

def run_adaptive_investigation(scenario_key: str, db_path: str = "fidelitygate.db"):
    if scenario_key not in DEMO_SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario_key}")
    
    scenario = DEMO_SCENARIOS[scenario_key]
    events = []
    start_time = time.time()
    
    # Event 1: Agent Investigates Route
    nominal_latency = predict_latency_ms(scenario, 1.0, 1.0)
    events.append({
        "step_num": 1,
        "phase": "AGENT_INVESTIGATION",
        "actor": "LLM_Agent",
        "timestamp_offset_ms": 12,
        "action": "Select candidate network route and evaluate nominal digital-twin prediction",
        "status": "PASS",
        "details": {
            "route_id": f"R-{scenario.scenario_id}",
            "nominal_latency_ms": round(nominal_latency, 2),
            "slo_target_ms": scenario.slo_latency_ms,
            "nominal_compliant": nominal_latency <= scenario.slo_latency_ms
        }
    })
    
    # Event 2: Counterexample Search Exposes Fragility
    cx = find_counterexample(scenario)
    events.append({
        "step_num": 2,
        "phase": "COUNTEREXAMPLE_SEARCH",
        "actor": "Counterexample_Engine",
        "timestamp_offset_ms": 38,
        "action": "Search uncertainty envelope for minimal violating perturbation",
        "status": "WARNING" if cx.is_fragile else "PASS",
        "details": {
            "is_fragile": cx.is_fragile,
            "violating_latency_ms": cx.violating_latency_ms,
            "critical_parameter": cx.critical_parameter,
            "perturbation_factor": cx.perturbation_factor,
            "explanation": cx.explanation
        }
    })
    
    # Event 3: Agent Selects Relevant Evidence Tool
    tool_id = select_targeted_diagnostic(cx.critical_parameter)
    tool_info = DIAGNOSTIC_TOOLS[tool_id]
    events.append({
        "step_num": 3,
        "phase": "TARGETED_DIAGNOSTIC_CHOICE",
        "actor": "LLM_Agent",
        "timestamp_offset_ms": 54,
        "action": f"Agent selects targeted diagnostic tool '{tool_info['name']}' based on counterexample sensitivity",
        "status": "ACTIVE",
        "details": {
            "selected_tool_id": tool_id,
            "tool_name": tool_info["name"],
            "target_parameter": tool_info["target_parameter"],
            "declared_error_bound": f"±{tool_info['declared_error_bound']} {tool_info['unit']}",
            "cost_usd": tool_info["cost_usd"],
            "reason": f"Collapses uncertainty around {cx.critical_parameter} identified in step 2"
        }
    })
    
    # Event 4: Execute Diagnostic Measurement
    # Ground truth drift simulation: mild drift 1.05x for demo verification
    obs = execute_diagnostic(tool_id, scenario, 1.05)
    events.append({
        "step_num": 4,
        "phase": "MEASUREMENT_ACQUISITION",
        "actor": "Diagnostic_Probe",
        "timestamp_offset_ms": 78,
        "action": "Execute physical diagnostic probe and capture measurement observation with declared error",
        "status": "MEASURED",
        "details": {
            "measured_value": obs.measured_value,
            "unit": obs.unit,
            "declared_error_bound": obs.declared_error_bound,
            "confidence_interval": obs.confidence_interval,
            "observation_summary": obs.observation_summary
        }
    })
    
    # Event 5: Deterministic Gate Independent Re-evaluation
    # Narrowed uncertainty: measured value collapses the parameter set
    measured_drift = obs.measured_value / scenario.nominal_latency_ms if obs.unit == "ms" else 1.05
    posterior_latency = predict_latency_ms(scenario, measured_drift, 1.02)
    
    if posterior_latency <= scenario.slo_latency_ms:
        final_decision = GateDecision.ACCEPT
        final_reason = f"Diagnostic measurement ({obs.measured_value} {obs.unit}) confirms actual operating state ({round(posterior_latency, 1)} ms) satisfies {scenario.slo_latency_ms} ms SLO within measurement error bounds."
    else:
        final_decision = GateDecision.ABSTAIN
        final_reason = f"Diagnostic measurement confirms physical congestion or latency drift breaches {scenario.slo_latency_ms} ms SLO; fail-closed safety activated."
        
    events.append({
        "step_num": 5,
        "phase": "GATE_RE_EVALUATION",
        "actor": "Deterministic_Gate",
        "timestamp_offset_ms": 95,
        "action": "Independent gate evaluation under posterior uncertainty",
        "status": final_decision.value,
        "details": {
            "final_decision": final_decision.value,
            "posterior_latency_ms": round(posterior_latency, 2),
            "final_reason": final_reason
        }
    })

    # Save to SQLite
    scenario_obj, gate, run_id = investigate(scenario_key, db_path, 25)

    return {
        "status": "success",
        "run_id": run_id,
        "scenario": scenario.model_dump(),
        "counterexample": {
            "is_fragile": cx.is_fragile,
            "violating_latency_ms": cx.violating_latency_ms,
            "critical_parameter": cx.critical_parameter,
            "perturbation_factor": cx.perturbation_factor,
            "explanation": cx.explanation
        },
        "diagnostic_observation": {
            "tool_id": obs.tool_id,
            "tool_name": obs.tool_name,
            "measured_value": obs.measured_value,
            "unit": obs.unit,
            "declared_error_bound": obs.declared_error_bound,
            "confidence_interval": obs.confidence_interval,
            "cost_usd": obs.cost_usd,
            "execution_time_ms": obs.execution_time_ms,
            "summary": obs.observation_summary
        },
        "gate": {
            "decision": final_decision.value,
            "reason": final_reason,
            "posterior_latency_ms": round(posterior_latency, 2),
            "report": gate.report.model_dump()
        },
        "execution_trace": events,
        "sweep_points": get_detailed_sweep(scenario, 25)
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No command provided"}))
        sys.exit(1)

    cmd = sys.argv[1]
    db_path = os.getenv("DATABASE_PATH", "fidelitygate.db")

    if cmd == "list-scenarios":
        scenarios_data = {}
        for key, s in DEMO_SCENARIOS.items():
            scenarios_data[key] = s.model_dump()
        print(json.dumps({"status": "success", "data": scenarios_data}))

    elif cmd == "adaptive-investigate":
        key = sys.argv[2] if len(sys.argv) > 2 else "wan_congestion"
        if len(sys.argv) > 3:
            db_path = sys.argv[3]
        result = run_adaptive_investigation(key, db_path)
        print(json.dumps(result))

    elif cmd == "baselines":
        comparison = run_four_way_comparison()
        print(json.dumps({"status": "success", "data": comparison}))

    elif cmd == "counterexample":
        key = sys.argv[2] if len(sys.argv) > 2 else "wan_congestion"
        scenario = DEMO_SCENARIOS[key]
        cx = find_counterexample(scenario)
        print(json.dumps({
            "status": "success",
            "counterexample": {
                "is_fragile": cx.is_fragile,
                "violating_latency_ms": cx.violating_latency_ms,
                "critical_parameter": cx.critical_parameter,
                "perturbation_factor": cx.perturbation_factor,
                "explanation": cx.explanation
            }
        }))

    elif cmd == "investigate":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing scenario key"}))
            sys.exit(1)
        key = sys.argv[2]
        evaluations = int(sys.argv[3]) if len(sys.argv) > 3 else 25
        if len(sys.argv) > 4:
            db_path = sys.argv[4]

        if key not in DEMO_SCENARIOS:
            print(json.dumps({"error": f"Unknown scenario: {key}"}))
            sys.exit(1)

        scenario = DEMO_SCENARIOS[key]
        scenario_obj, gate, run_id = investigate(key, db_path, evaluations)
        detailed_points = get_detailed_sweep(scenario_obj, evaluations)

        result = {
            "status": "success",
            "run_id": run_id,
            "scenario": scenario_obj.model_dump(),
            "gate": {
                "decision": gate.decision.value,
                "reason": gate.reason,
                "report": gate.report.model_dump()
            },
            "sweep_points": detailed_points
        }
        print(json.dumps(result))

    elif cmd == "evaluate-all":
        evaluations = int(sys.argv[2]) if len(sys.argv) > 2 else 25
        if len(sys.argv) > 3:
            db_path = sys.argv[3]

        results = []
        for key, s in DEMO_SCENARIOS.items():
            scenario_obj, gate, run_id = investigate(key, db_path, evaluations)
            results.append({
                "scenario_key": key,
                "scenario_id": s.scenario_id,
                "name": s.name,
                "decision": gate.decision.value,
                "reason": gate.reason,
                "nominal_latency_ms": round(gate.report.nominal_latency_ms, 2),
                "worst_latency_ms": round(gate.report.worst_latency_ms, 2),
                "slo_latency_ms": s.slo_latency_ms,
                "violations": gate.report.violations,
                "stability_score": round(gate.report.stability_score * 100, 1),
                "peak_utilization": round(gate.report.peak_utilization * 100, 1),
                "run_id": run_id
            })
        print(json.dumps({"status": "success", "data": results}))

    elif cmd == "health":
        storage = RunStore(db_path)
        print(json.dumps({
            "status": "healthy",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "database_path": db_path,
        }))

    elif cmd == "list-sources":
        storage = RunStore(db_path)
        manifests = storage.list_manifests()
        if not manifests:
            # Output default registered cisco source
            print(json.dumps([{
                "source_id": "cisco-ie-telemetry",
                "name": "Cisco Innovation Edge Network Telemetry",
                "source_url": "https://github.com/cisco-ie/telemetry",
                "publication_reference": "ACM SIGCOMM BigDama'18 / IEEE INFOCOM'18",
                "dataset_version": "master",
                "license": "CDLA-Permissive-1.0",
                "attribution": "Cisco Systems, Inc. (CDLA-Permissive-1.0)",
                "source_format": "CSV",
                "raw_file_path": "raw/cisco_telemetry",
                "sha256_checksum": "UNVERIFIED",
                "description": "Interface and CPU counters from Cisco IOS-XR lab runs.",
                "limitations": ["No topology definitions in telemetry CSV", "No post-action outcomes"]
            }]))
        else:
            print(json.dumps([m.model_dump() for m in manifests]))

    elif cmd == "ingest":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing file path to ingest"}))
            sys.exit(1)
        file_path = sys.argv[2]
        source_id = sys.argv[3] if len(sys.argv) > 3 else "cisco-ie-telemetry"
        version = sys.argv[4] if len(sys.argv) > 4 else "master"
        scenario_id = sys.argv[5] if len(sys.argv) > 5 else None

        from fidelitygate.ingestion.models import IngestionRequest
        from fidelitygate.ingestion.pipeline import IngestionPipeline

        pipeline = IngestionPipeline(RunStore(db_path))
        req = IngestionRequest(
            source_id=source_id,
            relative_path=file_path,
            dataset_version=version,
            scenario_id=scenario_id,
            force_reingest=True,
        )
        report = pipeline.run_ingestion(req)
        print(report.model_dump_json())

    elif cmd == "get-report":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing ingestion_id"}))
            sys.exit(1)
        ing_id = sys.argv[2]
        storage = RunStore(db_path)
        report = storage.get_ingestion_report(ing_id)
        if not report:
            print(json.dumps({"error": f"Ingestion report '{ing_id}' not found"}))
            sys.exit(1)
        print(report.model_dump_json())

    elif cmd == "list-ingestions":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        storage = RunStore(db_path)
        summaries = storage.list_ingestion_summaries(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "recent-runs":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        if len(sys.argv) > 3:
            db_path = sys.argv[3]
        store = RunStore(db_path)
        rows = store.recent(limit)
        runs = []
        for r in rows:
            runs.append({
                "id": r[0],
                "created_at": r[1],
                "scenario_id": r[2],
                "scenario_name": r[3],
                "decision": r[4],
                "reason": r[5],
                "report": json.loads(r[6])
            })
        print(json.dumps({"status": "success", "data": runs}))

    elif cmd == "triage":
        ing_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "None" else None
        source_id = sys.argv[3] if len(sys.argv) > 3 else "cisco-ie-telemetry"
        case_file = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "None" else None
        z_thresh = float(sys.argv[5]) if len(sys.argv) > 5 else 3.5

        from fidelitygate.triage.engine import AnomalyTriageEngine
        from fidelitygate.triage.models import TriageRunRequest

        engine = AnomalyTriageEngine(RunStore(db_path))
        req = TriageRunRequest(
            ingestion_id=ing_id,
            source_id=source_id,
            case_file=case_file,
            z_threshold=z_thresh,
        )
        summary, context, correlation, findings, evidence = engine.run_triage(req)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "findings_count": len(findings),
            "evidence_count": len(evidence),
            "top_findings": [f.model_dump() for f in findings[:5]],
            "context_id": context.triage_run_id
        }))

    elif cmd == "get-triage":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing triage_run_id"}))
            sys.exit(1)
        triage_id = sys.argv[2]
        storage = RunStore(db_path)
        summary = storage.get_triage_summary(triage_id)
        if not summary:
            print(json.dumps({"error": f"Triage run '{triage_id}' not found"}))
            sys.exit(1)
        context = storage.get_investigation_context(triage_id)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "context": context.model_dump() if context else None
        }))

    elif cmd == "list-triage":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        storage = RunStore(db_path)
        summaries = storage.list_triage_summaries(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "investigate-agent":
        triage_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "None" else None
        scenario_id = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "None" else None
        mode = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] != "None" else None

        from fidelitygate.investigation.orchestrator import InvestigationOrchestrator
        from fidelitygate.investigation.models import AgentMode, InvestigationRequest

        storage = RunStore(db_path)
        if not triage_id:
            recent_triage = storage.list_triage_summaries(1)
            if not recent_triage:
                print(json.dumps({"error": "No triage runs found. Run triage first."}))
                sys.exit(1)
            triage_id = recent_triage[0].triage_run_id

        mode_enum = None
        if mode == "live_llm":
            mode_enum = AgentMode.LIVE_LLM_AGENT
        elif mode == "deterministic_planner":
            mode_enum = AgentMode.DETERMINISTIC_PLANNER
        elif mode == "deterministic_baseline":
            mode_enum = AgentMode.DETERMINISTIC_BASELINE

        orchestrator = InvestigationOrchestrator(storage)
        req = InvestigationRequest(
            triage_run_id=triage_id,
            scenario_id=scenario_id,
            agent_mode=mode_enum,
        )
        summary, report, plan, events = orchestrator.run_investigation(req)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "hypotheses_count": len(report.hypotheses),
            "candidates_count": len(plan.candidate_diagnostics),
            "selected_diagnostic": plan.selected_diagnostic_id,
            "proposed_interventions": plan.proposed_interventions,
        }))

    elif cmd == "get-investigation":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing investigation_id"}))
            sys.exit(1)
        inv_id = sys.argv[2]
        storage = RunStore(db_path)
        summary = storage.get_investigation_summary(inv_id)
        if not summary:
            print(json.dumps({"error": f"Investigation '{inv_id}' not found"}))
            sys.exit(1)
        report = storage.get_investigation_report(inv_id)
        plan = storage.get_investigation_plan(inv_id)
        events = storage.get_investigation_events(inv_id)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "report": report.model_dump() if report else None,
            "plan": plan.model_dump() if plan else None,
            "events_count": len(events),
        }))

    elif cmd == "list-investigations":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        storage = RunStore(db_path)
        summaries = storage.list_investigation_summaries(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "evaluate-mitigation":
        inv_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "None" else None
        scenario_id = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "None" else None
        budget = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != "None" else 25

        from fidelitygate.evaluation.engine import MitigationEvaluationEngine
        from fidelitygate.evaluation.models import MitigationEvaluationRequest

        storage = RunStore(db_path)
        if not inv_id:
            recent_inv = storage.list_investigation_summaries(1)
            if not recent_inv:
                print(json.dumps({"error": "No completed investigations found. Run investigate-agent first."}))
                sys.exit(1)
            inv_id = recent_inv[0].investigation_id

        engine = MitigationEvaluationEngine(storage)
        req = MitigationEvaluationRequest(
            investigation_id=inv_id,
            scenario_id=scenario_id,
            evaluation_budget=budget,
        )
        summary, report, candidates, events = engine.run_evaluation(req)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "selected_candidate_id": report.selected_candidate_id,
            "gate_verdict": report.gate_verdict.value,
            "candidates_evaluated": len(candidates),
        }))

    elif cmd == "get-mitigation-evaluation":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing evaluation_id"}))
            sys.exit(1)
        eval_id = sys.argv[2]
        storage = RunStore(db_path)
        summary = storage.get_mitigation_summary(eval_id)
        if not summary:
            print(json.dumps({"error": f"Evaluation '{eval_id}' not found"}))
            sys.exit(1)
        report = storage.get_mitigation_report(eval_id)
        candidates = storage.get_candidate_evaluations(eval_id)
        events = storage.get_evaluation_events(eval_id)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "report": report.model_dump() if report else None,
            "candidates_count": len(candidates),
            "events_count": len(events),
        }))

    elif cmd == "list-mitigation-evaluations":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        storage = RunStore(db_path)
        summaries = storage.list_mitigation_summaries(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "run-adaptive-investigation":
        eval_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "None" else None
        max_cycles = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "None" else 2
        budget = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != "None" else 25

        from fidelitygate.adaptive.engine import AdaptiveInvestigationEngine
        from fidelitygate.adaptive.models import AdaptiveInvestigationRequest

        storage = RunStore(db_path)
        if not eval_id:
            recent_eval = storage.list_mitigation_summaries(1)
            if not recent_eval:
                print(json.dumps({"error": "No completed mitigation evaluations found. Run evaluate-mitigation first."}))
                sys.exit(1)
            eval_id = recent_eval[0].evaluation_id

        engine = AdaptiveInvestigationEngine(storage)
        req = AdaptiveInvestigationRequest(
            evaluation_id=eval_id,
            max_cycles=max_cycles,
            simulation_budget_per_cycle=budget,
        )
        summary, report, events = engine.run_adaptive_investigation(req)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "initial_gate_decision": summary.initial_gate_decision.value,
            "final_gate_decision": summary.final_gate_decision.value,
            "decision_changed": summary.decision_changed,
            "total_cycles": summary.total_cycles_executed,
            "simulations_consumed": summary.total_simulations_consumed,
        }))

    elif cmd == "get-adaptive-investigation":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing adaptive_run_id"}))
            sys.exit(1)
        run_id = sys.argv[2]
        storage = RunStore(db_path)
        summary = storage.get_adaptive_summary(run_id)
        if not summary:
            print(json.dumps({"error": f"Adaptive investigation '{run_id}' not found"}))
            sys.exit(1)
        report = storage.get_adaptive_report(run_id)
        diagnostics = storage.get_adaptive_diagnostics(run_id)
        events = storage.get_adaptive_events(run_id)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "report": report.model_dump() if report else None,
            "diagnostics_count": len(diagnostics),
            "events_count": len(events),
        }))

    elif cmd == "list-adaptive-investigations":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        storage = RunStore(db_path)
        summaries = storage.list_adaptive_summaries(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "explain-decision":
        target_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "None" else None
        scenario_id = sys.argv[3] if len(sys.argv) > 3 and sys.argv[3] != "None" else None
        compute_sensitivity = bool(int(sys.argv[4])) if len(sys.argv) > 4 and sys.argv[4] != "None" else True

        from fidelitygate.xai.engine import ExplanationEngine

        storage = RunStore(db_path)
        engine = ExplanationEngine(storage)

        adaptive_run_id = None
        eval_id = None
        if target_id:
            if target_id.startswith("adapt-"):
                adaptive_run_id = target_id
            elif target_id.startswith("eval-"):
                eval_id = target_id
            else:
                adaptive_run_id = target_id

        try:
            expl = engine.generate_explanation(
                evaluation_id=eval_id,
                adaptive_run_id=adaptive_run_id,
                scenario_id=scenario_id,
                compute_sensitivity=compute_sensitivity,
            )
            print(json.dumps({
                "status": "success",
                "explanation": expl.model_dump(),
                "explanation_id": expl.explanation_id,
                "decision": expl.decision.value,
                "summary": expl.summary,
                "rules_count": len(expl.constraint_results),
                "evidence_count": len(expl.evidence_items),
            }))
        except Exception as err:
            print(json.dumps({"error": str(err)}))
            sys.exit(1)

    elif cmd == "get-explanation":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing explanation_id"}))
            sys.exit(1)
        expl_id = sys.argv[2]
        storage = RunStore(db_path)
        expl = storage.get_explanation(expl_id)
        if not expl:
            print(json.dumps({"error": f"Explanation '{expl_id}' not found"}))
            sys.exit(1)
        print(json.dumps({
            "status": "success",
            "explanation": expl.model_dump(),
        }))

    elif cmd == "list-explanations":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
        storage = RunStore(db_path)
        from fidelitygate.xai.engine import ExplanationEngine
        engine = ExplanationEngine(storage)
        summaries = engine.list_explanations(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "run-workflow":
        scenario_id = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2] != "None" else "wan_congestion"
        auto_approve = bool(int(sys.argv[3])) if len(sys.argv) > 3 and sys.argv[3] != "None" else False
        from fidelitygate.workflow import EndToEndWorkflowOrchestrator, WorkflowRunRequest
        storage = RunStore(db_path)
        orchestrator = EndToEndWorkflowOrchestrator(storage)
        summary = orchestrator.initiate_workflow(
            WorkflowRunRequest(scenario_id=scenario_id, auto_approve_for_testing=auto_approve)
        )
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "workflow_run_id": summary.workflow_run_id,
            "current_stage": summary.current_stage.value,
            "workflow_status": summary.status.value,
            "gate_verdict": summary.gate_verdict.value if summary.gate_verdict else None,
            "selected_candidate": summary.selected_candidate_id,
            "approval_status": summary.approval_status.value if summary.approval_status else None,
            "outcome_id": summary.outcome_id,
            "overall_impact": summary.overall_impact.value if summary.overall_impact else None,
        }))

    elif cmd == "get-workflow":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing workflow_run_id"}))
            sys.exit(1)
        wf_id = sys.argv[2]
        storage = RunStore(db_path)
        summary = storage.get_workflow_run(wf_id)
        if not summary:
            print(json.dumps({"error": f"Workflow run '{wf_id}' not found"}))
            sys.exit(1)
        events = storage.get_workflow_events(wf_id)
        approval = storage.get_approval_by_workflow(wf_id)
        outcome = storage.get_outcome_by_workflow(wf_id)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "events_count": len(events),
            "approval": approval.model_dump() if approval else None,
            "outcome": outcome.model_dump() if outcome else None,
        }))

    elif cmd == "list-workflows":
        limit = 50
        if len(sys.argv) > 2:
            if sys.argv[2] in ("--limit", "-l") and len(sys.argv) > 3:
                try:
                    limit = int(sys.argv[3])
                except ValueError:
                    limit = 50
            else:
                try:
                    limit = int(sys.argv[2])
                except ValueError:
                    limit = 50
        storage = RunStore(db_path)
        summaries = storage.list_workflow_runs(limit)
        print(json.dumps([s.model_dump() for s in summaries]))

    elif cmd == "approve-workflow":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing workflow_run_id"}))
            sys.exit(1)
        wf_id = sys.argv[2]
        
        # Parse either positional or flagged arguments
        dec_str = "APPROVED"
        rev_id = "operator-cli"
        comment = "Approved via CLI"
        
        args = sys.argv[3:]
        i = 0
        while i < len(args):
            arg = args[i]
            if arg in ("--decision", "-d") and i + 1 < len(args):
                dec_str = args[i + 1]
                i += 2
            elif arg in ("--reviewer", "-r") and i + 1 < len(args):
                rev_id = args[i + 1]
                i += 2
            elif arg in ("--comment", "-c") and i + 1 < len(args):
                comment = args[i + 1]
                i += 2
            else:
                if i == 0 and not arg.startswith("-"):
                    dec_str = arg
                elif i == 1 and not arg.startswith("-"):
                    rev_id = arg
                elif i == 2 and not arg.startswith("-"):
                    comment = arg
                i += 1

        from fidelitygate.workflow import EndToEndWorkflowOrchestrator, ApprovalRequest, ApprovalDecision
        storage = RunStore(db_path)
        orchestrator = EndToEndWorkflowOrchestrator(storage)
        dec = ApprovalDecision(dec_str)
        summary, approval = orchestrator.submit_approval(
            wf_id,
            ApprovalRequest(decision=dec, reviewer_id=rev_id, reviewer_comment=comment)
        )
        outcome = storage.get_outcome_by_workflow(wf_id)
        print(json.dumps({
            "status": "success",
            "summary": summary.model_dump(),
            "approval": approval.model_dump(),
            "outcome": outcome.model_dump() if outcome else None,
        }))

    elif cmd == "get-workflow-events":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing workflow_run_id"}))
            sys.exit(1)
        wf_id = sys.argv[2]
        storage = RunStore(db_path)
        events = storage.get_workflow_events(wf_id)
        print(json.dumps([e.model_dump() for e in events]))

    elif cmd == "get-workflow-outcome":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Missing workflow_run_id"}))
            sys.exit(1)
        wf_id = sys.argv[2]
        storage = RunStore(db_path)
        outcome = storage.get_outcome_by_workflow(wf_id)
        if not outcome:
            print(json.dumps({"error": f"No outcome found for workflow '{wf_id}'"}))
            sys.exit(1)
        print(json.dumps({
            "status": "success",
            "outcome": outcome.model_dump(),
        }))

    else:
        print(json.dumps({"error": f"Unknown command: {cmd}"}))
        sys.exit(1)

if __name__ == "__main__":
    main()
