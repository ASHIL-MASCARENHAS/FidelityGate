/**
 * @file /src/critical/decision-gate.ts
 * @description Zero-drift deterministic gate decision rules and validation engine.
 * Critical safety module governed by strict change control.
 */

import { Scenario, SweepReport, GateReport, GateDecision } from '@/types';
import {
  assertFailClosedInvariant,
  assertStabilityThresholdInvariant,
  assertMonotonicityBound,
} from './safety-invariants';

export interface GateEvaluationOptions {
  enforceStrictInvariants?: boolean;
}

/**
 * Evaluates the deterministic FidelityGate decision based on digital-twin sweep outcomes.
 *
 * Rules:
 * 1. Nominal > SLO => ABSTAIN (Candidate fundamentally breaches latency budget).
 * 2. Nominal <= SLO AND Violations > 0 => GATHER_EVIDENCE (Counterexample exposes fragility under drift).
 * 3. Nominal <= SLO AND Violations == 0 AND Stability >= Threshold => ACCEPT (Robustly verified).
 * 4. Otherwise => ABSTAIN (Fail-closed fallback).
 */
export function evaluateDeterministicGate(
  report: SweepReport,
  scenario: Scenario,
  options: GateEvaluationOptions = { enforceStrictInvariants: true }
): GateReport {
  assertMonotonicityBound(report.nominal_latency_ms, report.worst_latency_ms);

  const slo = scenario.slo_latency_ms;
  const nominal = report.nominal_latency_ms;
  const breaches = report.violations;
  const stability = report.stability_score;
  const threshold = scenario.stability_threshold;

  let decision: GateDecision = 'ABSTAIN';
  let reason = '';

  if (nominal > slo) {
    decision = 'ABSTAIN';
    reason = `Nominal latency (${nominal.toFixed(1)} ms) exceeds the strict SLO bound (${slo.toFixed(1)} ms); fail closed.`;
  } else if (breaches > 0) {
    decision = 'GATHER_EVIDENCE';
    reason = `Nominal prediction (${nominal.toFixed(1)} ms) passes SLO, but uncertainty variations reveal fragility (${breaches} breaches reaching ${report.worst_latency_ms.toFixed(1)} ms); targeted diagnostics required.`;
  } else if (stability >= threshold) {
    decision = 'ACCEPT';
    reason = `All ${report.evaluations} evaluated variations remain compliant within the ${slo.toFixed(1)} ms SLO (stability score: ${(stability * 100).toFixed(1)}%). Candidate intervention approved.`;
  } else {
    decision = 'ABSTAIN';
    reason = `Stability score (${(stability * 100).toFixed(1)}%) is insufficient to satisfy the ${(threshold * 100).toFixed(1)}% threshold; fail closed.`;
  }

  if (options.enforceStrictInvariants) {
    assertFailClosedInvariant(decision, report, scenario);
    assertStabilityThresholdInvariant(decision, stability, threshold);
  }

  return {
    decision,
    reason,
    report,
  };
}
