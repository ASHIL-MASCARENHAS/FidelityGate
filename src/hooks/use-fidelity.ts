'use client';

import { useState, useEffect, useCallback } from 'react';
import { Scenario, InvestigationResult, RunHistoryItem, BaselineMetrics } from '@/types';
import { DEFAULT_SCENARIOS, siteConfig } from '@/config/site';

export function useFidelity() {
  const [scenarios, setScenarios] = useState<Record<string, Scenario>>(DEFAULT_SCENARIOS);
  const [selectedKey, setSelectedKey] = useState<string>(siteConfig.defaultScenarioKey);
  const [evaluations, setEvaluations] = useState<number>(siteConfig.defaultEvaluations);
  const [investigationResult, setInvestigationResult] = useState<InvestigationResult | null>(null);
  const [adaptiveResult, setAdaptiveResult] = useState<InvestigationResult | null>(null);
  const [runs, setRuns] = useState<RunHistoryItem[]>([]);
  const [baselines, setBaselines] = useState<Record<string, BaselineMetrics> | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [adaptiveLoading, setAdaptiveLoading] = useState<boolean>(false);

  const runInvestigation = useCallback(async (key: string, count: number) => {
    setLoading(true);
    try {
      const res = await fetch('/api/investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_key: key, evaluations: count }),
      });
      if (res.ok) {
        const json = await res.json();
        setInvestigationResult(json);
      }
    } catch (err) {
      console.warn('Failed to run investigation:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  const runAdaptiveInvestigation = useCallback(async (key: string) => {
    setAdaptiveLoading(true);
    try {
      const res = await fetch('/api/adaptive-investigate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scenario_key: key }),
      });
      if (res.ok) {
        const json = await res.json();
        setAdaptiveResult(json);
      }
    } catch (err) {
      console.warn('Failed to run adaptive investigation:', err);
    } finally {
      setAdaptiveLoading(false);
    }
  }, []);

  const fetchBaselines = useCallback(async () => {
    try {
      const res = await fetch('/api/baselines');
      if (res.ok) {
        const json = await res.json();
        if (json.data?.baselines) {
          setBaselines(json.data.baselines);
        }
      }
    } catch (err) {
      console.warn('Failed to fetch baselines:', err);
    }
  }, []);

  useEffect(() => {
    runInvestigation(siteConfig.defaultScenarioKey, siteConfig.defaultEvaluations);
    runAdaptiveInvestigation(siteConfig.defaultScenarioKey);
    fetchBaselines();
  }, [runInvestigation, runAdaptiveInvestigation, fetchBaselines]);

  return {
    scenarios,
    selectedKey,
    setSelectedKey,
    evaluations,
    setEvaluations,
    investigationResult,
    adaptiveResult,
    runs,
    baselines,
    loading,
    adaptiveLoading,
    runInvestigation,
    runAdaptiveInvestigation,
    fetchBaselines,
  };
}
