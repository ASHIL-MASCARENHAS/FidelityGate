'use client';

import { useEffect, useState } from 'react';

export interface ChartTheme {
  isDark: boolean;
  /** Chart chrome */
  grid: string;
  axis: string;
  axisTick: string;
  reference: string;
  surface: string;
  surfaceBorder: string;
  tooltipBg: string;
  tooltipBorder: string;
  tooltipText: string;
  /** Verdict + series colours, tuned per mode for legible contrast */
  accept: string;
  evidence: string;
  abstain: string;
  cobalt: string;
  cyan: string;
  violet: string;
}

const LIGHT: ChartTheme = {
  isDark: false,
  grid: '#E5E5E0',
  axis: '#B6B8BE',
  axisTick: '#686D78',
  reference: '#C8CAD0',
  surface: '#FFFFFF',
  surfaceBorder: '#E5E5E0',
  tooltipBg: '#FFFFFF',
  tooltipBorder: '#E5E5E0',
  tooltipText: '#17191F',
  accept: '#059669',
  evidence: '#B07420',
  abstain: '#DC2626',
  cobalt: '#315CF5',
  cyan: '#0E7490',
  violet: '#7C3AED',
};

const DARK: ChartTheme = {
  isDark: true,
  grid: '#232A38',
  axis: '#4B5566',
  axisTick: '#9CA3AF',
  reference: '#3A4356',
  surface: '#191C23',
  surfaceBorder: '#2A2E38',
  tooltipBg: '#191C23',
  tooltipBorder: '#2A2E38',
  tooltipText: '#F3F4F6',
  accept: '#34D399',
  evidence: '#F5B544',
  abstain: '#F87171',
  cobalt: '#6B8CFF',
  cyan: '#38D7EC',
  violet: '#A78BFA',
};

/**
 * Tracks the `dark` class on <html> and returns a matching chart palette, so
 * every chart stays readable in both themes without hardcoding hex per chart.
 */
export function useChartTheme(): ChartTheme {
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const root = document.documentElement;
    const sync = () => setIsDark(root.classList.contains('dark'));

    sync();
    const observer = new MutationObserver(sync);
    observer.observe(root, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  return isDark ? DARK : LIGHT;
}

/** Shared Recharts tooltip styling for the current theme. */
export function tooltipStyle(t: ChartTheme) {
  return {
    backgroundColor: t.tooltipBg,
    borderColor: t.tooltipBorder,
    borderWidth: 1,
    borderStyle: 'solid' as const,
    borderRadius: 10,
    color: t.tooltipText,
    fontFamily: 'var(--font-mono), monospace',
    fontSize: 11,
    boxShadow: t.isDark
      ? '0 10px 30px -10px rgba(0, 0, 0, 0.6)'
      : '0 10px 30px -10px rgba(23, 25, 31, 0.15)',
  };
}
