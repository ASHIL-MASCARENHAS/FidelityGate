import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export function formatMs(val?: number): string {
  if (val === undefined || isNaN(val)) return '0.0 ms';
  return `${val.toFixed(1)} ms`;
}

export function formatPct(val?: number): string {
  if (val === undefined || isNaN(val)) return '0.0%';
  return `${(val * 100).toFixed(1)}%`;
}
