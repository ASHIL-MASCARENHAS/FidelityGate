import { Scenario } from '@/types';

export const siteConfig = {
  name: 'FidelityGate',
  description: 'Counterexample-Guided Decision Assurance for Agentic Network Operations',
  version: '2.5.0',
  defaultScenarioKey: 'wan_congestion',
  defaultEvaluations: 25,
};

export const DEFAULT_SCENARIOS: Record<string, Scenario> = {
  wan_congestion: {
    scenario_id: 'WAN-042',
    name: 'WAN congestion / reroute',
    description: 'Illustrative branch-to-core traffic burst with a proposed reroute.',
    nominal_latency_ms: 18.0,
    capacity_mbps: 1000.0,
    offered_load_mbps: 760.0,
    slo_latency_ms: 45.0,
    latency_multiplier_min: 0.85,
    latency_multiplier_max: 1.35,
    stability_threshold: 0.9,
  },
  fiber_drift: {
    scenario_id: 'FIBER-017',
    name: 'Fiber latency calibration drift',
    description: 'Illustrative route where the twin may understate propagation delay.',
    nominal_latency_ms: 24.0,
    capacity_mbps: 900.0,
    offered_load_mbps: 690.0,
    slo_latency_ms: 40.0,
    latency_multiplier_min: 0.85,
    latency_multiplier_max: 1.6,
    stability_threshold: 0.9,
  },
  traffic_burst: {
    scenario_id: 'BURST-006',
    name: 'Hidden traffic burst',
    description: 'Illustrative load spike used to exercise conservative gate behavior.',
    nominal_latency_ms: 15.0,
    capacity_mbps: 800.0,
    offered_load_mbps: 730.0,
    slo_latency_ms: 35.0,
    latency_multiplier_min: 0.9,
    latency_multiplier_max: 1.5,
    stability_threshold: 0.9,
  },
};
