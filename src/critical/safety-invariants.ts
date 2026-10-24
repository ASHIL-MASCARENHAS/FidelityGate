/**
 * @file /src/critical/safety-invariants.ts
 * @description Core deterministic safety invariants for FidelityGate.
 * Critical security and safety module governed by strict change control.
 */

import { Scenario, SweepReport, GateDecision } from '@/types';

export interface SafetyThresholds {
  minStabilityScore: number;
  maxAllowableViolations: number;
  maxLatencyCapMs: number;
}

export const DEFAULT_SAFETY_THRESHOLDS: SafetyThresholds = {
  minStabilityScore: 0.9,
  maxAllowableViolations: 0,
  maxLatencyCapMs: 250.0,
};

export class SafetyInvariantViolationError extends Error {
  constructor(public invariantName: string, message: string) {
    super(`[SAFETY_INVARIANT_VIOLATION: ${invariantName}] ${message}`);
    this.name = 'SafetyInvariantViolationError';
  }
}

/**
 * Invariant 1: Fail-Closed Decision Invariant
 * If any uncertainty perturbation exceeds the scenario SLO latency,
 * the gate MUST NOT return 'ACCEPT'.
 */
export function assertFailClosedInvariant(
  decision: GateDecision,
  report: SweepReport,
  scenario: Scenario
): void {
  if (report.violations > 0 && decision === 'ACCEPT') {
    throw new SafetyInvariantViolationError(
      'FAIL_CLOSED_BREACH',
      `Detected ${report.violations} SLO violations exceeding ${scenario.slo_latency_ms}ms, but decision was marked ACCEPT.`
    );
  }
}

/**
 * Invariant 2: Stability Score Lower Bound
 * If stability score falls below the scenario threshold, decision cannot be ACCEPT.
 */
export function assertStabilityThresholdInvariant(
  decision: GateDecision,
  stabilityScore: number,
  stabilityThreshold: number
): void {
  if (stabilityScore < stabilityThreshold && decision === 'ACCEPT') {
    throw new SafetyInvariantViolationError(
      'STABILITY_THRESHOLD_BREACH',
      `Stability score (${(stabilityScore * 100).toFixed(1)}%) is below required threshold (${(
        stabilityThreshold * 100
      ).toFixed(1)}%), but decision was marked ACCEPT.`
    );
  }
}

/**
 * Invariant 3: Sanity and Monotonicity Bound
 * Nominal latency must always be strictly less than or equal to worst-case latency.
 */
export function assertMonotonicityBound(
  nominalLatencyMs: number,
  worstLatencyMs: number
): void {
  if (worstLatencyMs < nominalLatencyMs - 1e-4) {
    throw new SafetyInvariantViolationError(
      'MONOTONICITY_INVERSION',
      `Worst-case latency (${worstLatencyMs.toFixed(2)}ms) cannot be lower than nominal latency (${nominalLatencyMs.toFixed(2)}ms).`
    );
  }
}
