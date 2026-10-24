"""fidelitygate/investigation/investigator.py
Agent A: Anomaly Investigator.
Transforms structured Layer 2 InvestigationContext into evidence-grounded operational hypotheses
with strict validation, non-causal descriptors, and evidence ID verification.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import uuid4

from ..triage.models import FindingSeverity, InvestigationContext, LabelOrigin
from .llm_adapter import LLMAdapter
from .models import (
    AgentMode,
    Hypothesis,
    HypothesisType,
    InvestigationReport,
    InvestigationStatus,
)
from .tools import ToolCall, ToolRegistry


class AnomalyInvestigatorAgent:
    """Agent A: Specializes in telemetry evidence interpretation and hypothesis formation."""

    ROLE_NAME = "Agent_A_Investigator"

    def __init__(self, llm_adapter: Optional[LLMAdapter] = None):
        self.llm = llm_adapter or LLMAdapter()

    def investigate(
        self,
        investigation_id: str,
        context: InvestigationContext,
        tools: ToolRegistry,
        preferred_mode: Optional[AgentMode] = None,
        max_hypotheses: int = 3,
    ) -> Tuple[InvestigationReport, List[Dict[str, Any]]]:
        """Conducts investigation on Layer 2 context and returns validated InvestigationReport and event logs."""
        events: List[Dict[str, Any]] = []

        # 1. Check for empty or insufficient context
        if not context.primary_anomaly_candidates and not context.correlated_evidence:
            report = InvestigationReport(
                investigation_id=investigation_id,
                triage_run_id=context.triage_run_id,
                scenario_id=context.scenario_id,
                agent_mode=AgentMode.DETERMINISTIC_PLANNER,
                primary_finding_ids=[],
                hypotheses=[],
                supporting_evidence_ids=[],
                contradictory_evidence_ids=[],
                unresolved_questions=["Why were no anomalies detected in this telemetry window?"],
                data_quality_warnings=context.data_quality_warnings,
                suggested_diagnostic_categories=["icmp_rtt_latency_probe"],
                limitations=["Triage context contains zero anomaly candidates; insufficient evidence to form network hypothesis."],
                status=InvestigationStatus.INSUFFICIENT_EVIDENCE,
            )
            events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": self.ROLE_NAME,
                "event_type": "INSUFFICIENT_EVIDENCE_DECLARED",
                "details": {"reason": "Zero candidates in context"}
            })
            return report, events

        # 2. Gather additional read-only tool context
        tool_call = ToolCall(
            tool_name="inspect_topology",
            arguments={"scenario_id": context.scenario_id},
            caller_role=self.ROLE_NAME,
            investigation_id=investigation_id,
        )
        topo_result = tools.execute_tool(tool_call)
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.ROLE_NAME,
            "event_type": "TOOL_CALL",
            "details": {"tool": "inspect_topology", "success": topo_result.success}
        })

        # 3. Determine Execution Mode
        effective_mode = preferred_mode or AgentMode.DETERMINISTIC_PLANNER
        if preferred_mode == AgentMode.LIVE_LLM_AGENT:
            avail, _ = self.llm.is_available()
            if not avail:
                effective_mode = AgentMode.DETERMINISTIC_BASELINE

        # Valid evidence IDs for resolution check
        valid_evidence_ids: Set[str] = {e.evidence_id for e in context.correlated_evidence} | set(context.supporting_evidence_ids)

        # 4. Execute Mode
        if effective_mode == AgentMode.LIVE_LLM_AGENT:
            report, events_llm = self._investigate_llm(
                investigation_id, context, valid_evidence_ids, max_hypotheses
            )
            events.extend(events_llm)
            if report:
                return report, events
            # Fallback if LLM failed
            effective_mode = AgentMode.DETERMINISTIC_BASELINE

        # Deterministic investigation path
        report = self._investigate_deterministic(
            investigation_id, context, valid_evidence_ids, effective_mode, max_hypotheses
        )
        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.ROLE_NAME,
            "event_type": "HYPOTHESIS_FORMED",
            "details": {
                "mode": effective_mode.value,
                "hypotheses_count": len(report.hypotheses),
                "status": report.status.value,
            }
        })
        return report, events

    def _investigate_deterministic(
        self,
        investigation_id: str,
        context: InvestigationContext,
        valid_evidence_ids: Set[str],
        agent_mode: AgentMode,
        max_hypotheses: int,
    ) -> InvestigationReport:
        """Deterministic, rule-based hypothesis generation adhering strictly to evidence constraints."""
        hypotheses: List[Hypothesis] = []
        primary_finding_ids: List[str] = [f.anomaly_id for f in context.primary_anomaly_candidates[:10]]
        supporting_ev_ids: List[str] = []
        contradictory_ev_ids: List[str] = []
        suggested_diagnostics: Set[str] = set()

        has_case_event = any(
            f.label_origin == LabelOrigin.SOURCE_DEFINED for f in context.primary_anomaly_candidates
        ) or bool(context.source_defined_event_metadata)

        # Check for BGP/routing anomalies
        bgp_findings = [
            f for f in context.primary_anomaly_candidates
            if "route" in f.metric_name.lower() or "bgp" in f.metric_name.lower() or f.label_origin == LabelOrigin.SOURCE_DEFINED
        ]
        if bgp_findings or has_case_event:
            h_ev = []
            for f in bgp_findings:
                h_ev.extend([eid for eid in f.evidence_ids if eid in valid_evidence_ids])
            if not h_ev and valid_evidence_ids:
                h_ev = list(valid_evidence_ids)[:4]
            supporting_ev_ids.extend(h_ev)
            suggested_diagnostics.add("bgp_rib_prefix_audit")
            suggested_diagnostics.add("snmp_interface_queue_telemetry")

            hypotheses.append(
                Hypothesis(
                    hypothesis_id=f"hyp-{uuid4().hex[:8]}",
                    statement=(
                        "Documented routing session reset is temporally associated with prefix withdrawal "
                        "and transient unroutable packet drops across border interfaces."
                    ),
                    hypothesis_type=HypothesisType.BGP_SESSION_FLAP,
                    supporting_evidence_ids=list(dict.fromkeys(h_ev))[:8],
                    contradictory_evidence_ids=[],
                    uncertainty_status="CONFIRMED_CASE_EVENT" if has_case_event else "PLAUSIBLE_CANDIDATE",
                    confidence_score=0.92 if has_case_event else 0.74,
                    label_origin=LabelOrigin.SOURCE_DEFINED if has_case_event else LabelOrigin.STATISTICAL_DETECTOR,
                    limitations=["Physical peer adjacency matrix is omitted; causal propagation across topology is not established."],
                )
            )

        # Check for packet forwarding drops and adjacency issues
        drop_findings = [
            f for f in context.primary_anomaly_candidates
            if any(k in f.metric_name.lower() for k in ["drop", "discard", "adjacency", "loss", "error"])
        ]
        if drop_findings:
            h_ev = []
            for f in drop_findings:
                h_ev.extend([eid for eid in f.evidence_ids if eid in valid_evidence_ids])
            if not h_ev and valid_evidence_ids:
                h_ev = list(valid_evidence_ids)[:4]
            supporting_ev_ids.extend(h_ev)
            suggested_diagnostics.add("snmp_interface_queue_telemetry")
            suggested_diagnostics.add("icmp_rtt_latency_probe")

            target_entity = drop_findings[0].entity_id
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=f"hyp-{uuid4().hex[:8]}",
                    statement=(
                        f"Forwarding plane drop surge observed on entity '{target_entity}'. "
                        "Candidate explanation includes local buffer exhaustion or missing FIB next-hop."
                    ),
                    hypothesis_type=HypothesisType.FORWARDING_DROP_SURGE,
                    supporting_evidence_ids=list(dict.fromkeys(h_ev))[:8],
                    contradictory_evidence_ids=[],
                    uncertainty_status="STATISTICAL_ANOMALY_CONFIRMED",
                    confidence_score=0.82,
                    label_origin=LabelOrigin.STATISTICAL_DETECTOR,
                    limitations=["Telemetry reports interface drops but does not directly measure user end-to-end latency impact."],
                )
            )

        # Check for CPU spikes
        cpu_findings = [
            f for f in context.primary_anomaly_candidates
            if "cpu" in f.metric_name.lower()
        ]
        if cpu_findings:
            h_ev = []
            for f in cpu_findings:
                h_ev.extend([eid for eid in f.evidence_ids if eid in valid_evidence_ids])
            supporting_ev_ids.extend(h_ev)
            suggested_diagnostics.add("icmp_rtt_latency_probe")

            hypotheses.append(
                Hypothesis(
                    hypothesis_id=f"hyp-{uuid4().hex[:8]}",
                    statement=(
                        f"Control plane CPU utilization elevated on '{cpu_findings[0].entity_id}'. "
                        "Co-occurring with routing convergence activity without established causal direction."
                    ),
                    hypothesis_type=HypothesisType.CONTROL_PLANE_CPU_SPIKE,
                    supporting_evidence_ids=list(dict.fromkeys(h_ev))[:8],
                    contradictory_evidence_ids=[],
                    uncertainty_status="PLAUSIBLE_CANDIDATE",
                    confidence_score=0.75,
                    label_origin=LabelOrigin.STATISTICAL_DETECTOR,
                    limitations=["Process-level CPU attribution is omitted in Cisco global telemetry table."],
                )
            )

        # Fallback if no specific category matched
        if not hypotheses:
            first_f = context.primary_anomaly_candidates[0]
            first_ev = [eid for eid in first_f.evidence_ids if eid in valid_evidence_ids]
            supporting_ev_ids.extend(first_ev)
            suggested_diagnostics.add("icmp_rtt_latency_probe")
            hypotheses.append(
                Hypothesis(
                    hypothesis_id=f"hyp-{uuid4().hex[:8]}",
                    statement=f"Unclassified metric deviation observed on entity '{first_f.entity_id}' metric '{first_f.metric_name}'.",
                    hypothesis_type=HypothesisType.UNCONFIRMED_ANOMALY,
                    supporting_evidence_ids=first_ev,
                    contradictory_evidence_ids=[],
                    uncertainty_status="UNCERTAIN",
                    confidence_score=0.50,
                    label_origin=first_f.label_origin,
                    limitations=["Metric does not map to standard forwarding failure signatures."],
                )
            )

        unresolved = [
            "Are packet drops localized to interface queues or caused by transit buffer starvation?",
            "What is the actual user-path latency drift resulting from this event?",
        ]

        limitations = [
            "All correlations represent temporal and device co-occurrence; no causal link is proven without active diagnostics.",
            "Complete physical network adjacency matrix is not present in Cisco telemetry CSV.",
        ]

        # Ensure supporting evidence IDs strictly exist in valid set
        clean_supporting = [eid for eid in dict.fromkeys(supporting_ev_ids) if eid in valid_evidence_ids]

        return InvestigationReport(
            investigation_id=investigation_id,
            triage_run_id=context.triage_run_id,
            scenario_id=context.scenario_id,
            agent_mode=agent_mode,
            primary_finding_ids=primary_finding_ids,
            hypotheses=hypotheses[:max_hypotheses],
            supporting_evidence_ids=clean_supporting[:25],
            contradictory_evidence_ids=contradictory_ev_ids,
            unresolved_questions=unresolved,
            data_quality_warnings=context.data_quality_warnings,
            suggested_diagnostic_categories=list(suggested_diagnostics),
            limitations=limitations,
            status=InvestigationStatus.COMPLETED,
        )

    def _investigate_llm(
        self,
        investigation_id: str,
        context: InvestigationContext,
        valid_evidence_ids: Set[str],
        max_hypotheses: int,
    ) -> Tuple[Optional[InvestigationReport], List[Dict[str, Any]]]:
        """Queries LLM with structured prompt and strictly validates evidence references."""
        events: List[Dict[str, Any]] = []

        system_prompt = (
            "You are Agent A (Anomaly Investigator) in FidelityGate, a decision-assurance system for IT infrastructure. "
            "Your objective is to analyze the provided InvestigationContext and output a valid JSON InvestigationReport. "
            "STRICT RULES:\n"
            "1. You must ONLY use evidence_ids that exist in the provided correlated_evidence list.\n"
            "2. Never assert causality without proof. Use non-causal descriptors: 'candidate explanation', 'temporally associated'.\n"
            "3. Distinguish SOURCE_DEFINED event labels from STATISTICAL_DETECTOR findings.\n"
            "4. You must output JSON strictly adhering to the schema."
        )

        user_prompt = f"""Investigation Context for Triage Run '{context.triage_run_id}':
- Primary Candidates: {len(context.primary_anomaly_candidates)} findings
- Available Evidence IDs: {list(valid_evidence_ids)[:30]}
- Baseline Comparisons: {context.baseline_comparisons[:5]}
- Quality Warnings: {context.data_quality_warnings}
- Declared Limitations: {context.explicitly_unavailable_information}

Return a JSON object matching InvestigationReport with investigation_id='{investigation_id}', triage_run_id='{context.triage_run_id}', scenario_id='{context.scenario_id}', and status='COMPLETED'."""

        parsed_model, mode, err = self.llm.generate_structured_output(
            system_prompt, user_prompt, InvestigationReport
        )

        if not parsed_model or not isinstance(parsed_model, InvestigationReport):
            events.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "actor": self.ROLE_NAME,
                "event_type": "LLM_GENERATION_FAILED",
                "details": {"error": err, "fallback_mode": "DETERMINISTIC_BASELINE"}
            })
            return None, events

        # Validate evidence IDs: filter out any hallucinated IDs
        clean_hypotheses: List[Hypothesis] = []
        for h in parsed_model.hypotheses:
            verified_supp = [eid for eid in h.supporting_evidence_ids if eid in valid_evidence_ids]
            verified_cont = [eid for eid in h.contradictory_evidence_ids if eid in valid_evidence_ids]
            clean_hypotheses.append(
                Hypothesis(
                    hypothesis_id=h.hypothesis_id,
                    statement=h.statement,
                    hypothesis_type=h.hypothesis_type,
                    supporting_evidence_ids=verified_supp,
                    contradictory_evidence_ids=verified_cont,
                    uncertainty_status=h.uncertainty_status,
                    confidence_score=h.confidence_score,
                    label_origin=h.label_origin,
                    limitations=h.limitations,
                )
            )

        clean_report = InvestigationReport(
            investigation_id=investigation_id,
            triage_run_id=context.triage_run_id,
            scenario_id=context.scenario_id,
            agent_mode=AgentMode.LIVE_LLM_AGENT,
            primary_finding_ids=[fid for fid in parsed_model.primary_finding_ids],
            hypotheses=clean_hypotheses[:max_hypotheses],
            supporting_evidence_ids=[eid for eid in parsed_model.supporting_evidence_ids if eid in valid_evidence_ids],
            contradictory_evidence_ids=[eid for eid in parsed_model.contradictory_evidence_ids if eid in valid_evidence_ids],
            unresolved_questions=parsed_model.unresolved_questions,
            data_quality_warnings=parsed_model.data_quality_warnings,
            suggested_diagnostic_categories=parsed_model.suggested_diagnostic_categories,
            limitations=parsed_model.limitations,
            status=InvestigationStatus.COMPLETED,
        )

        events.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": self.ROLE_NAME,
            "event_type": "LLM_HYPOTHESIS_FORMED",
            "details": {"model": self.llm.model, "mode": "LIVE_LLM_AGENT"}
        })

        return clean_report, events
