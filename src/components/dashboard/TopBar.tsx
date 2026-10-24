'use client';

import React, { useState } from 'react';
import { Calendar, ChevronDown, Moon, Sun, Volume2, VolumeX, ArrowLeft } from 'lucide-react';
import { playTick } from '@/lib/sound';

interface TopBarProps {
  activeTitle?: string;
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
  soundEnabled?: boolean;
  setSoundEnabled?: (s: boolean) => void;
  onBackToLanding?: () => void;
  onSelectScenario?: (id: string) => void;
}

export function TopBar({
  activeTitle = 'Overview Dashboard',
  theme,
  setTheme,
  soundEnabled = false,
  setSoundEnabled,
  onBackToLanding,
}: TopBarProps) {
  const [timeRange] = useState('Last 24 Hours');

  return (
    <div className="bg-surface dark:bg-surface-dark border-b border-hairline dark:border-hairline-dark sticky top-0 z-30 select-none transition-colors">
      {/* Top Header Row */}
      <div className="px-6 py-3 flex items-center justify-between border-b border-hairline dark:border-hairline-dark">
        <div className="flex items-center space-x-3">
          {onBackToLanding && (
            <button
              onClick={() => {
                playTick(soundEnabled);
                onBackToLanding();
              }}
              className="md:hidden p-1.5 rounded-lg border border-hairline dark:border-hairline-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark"
              title="Return to Public Landing"
              aria-label="Return to landing"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
          )}
          <h1 className="text-base sm:text-lg font-bold text-ink dark:text-ink-dark tracking-tight">
            {activeTitle}
          </h1>
        </div>

        <div className="flex items-center space-x-3">
          {/* Time Range Selector */}
          <div className="relative hidden sm:block">
            <button className="flex items-center space-x-2 px-3 py-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-xs font-medium text-ink dark:text-ink-dark hover:border-cobalt/40 transition-colors">
              <Calendar className="w-3.5 h-3.5 text-muted-fg dark:text-muted-dark" />
              <span>{timeRange}</span>
              <ChevronDown className="w-3 h-3 text-muted-fg dark:text-muted-dark" />
            </button>
          </div>

          {/* Sound Toggle */}
          {setSoundEnabled && (
            <button
              onClick={() => {
                const next = !soundEnabled;
                setSoundEnabled(next);
                playTick(next);
              }}
              className="p-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark transition-colors"
              title={soundEnabled ? 'Disable interface sounds' : 'Enable interface sounds'}
              aria-label="Toggle sound"
            >
              {soundEnabled ? (
                <Volume2 className="w-4 h-4 text-cobalt" />
              ) : (
                <VolumeX className="w-4 h-4" />
              )}
            </button>
          )}

          {/* Theme Mode Toggle */}
          <button
            onClick={() => {
              playTick(soundEnabled);
              setTheme(theme === 'dark' ? 'light' : 'dark');
            }}
            className="p-1.5 rounded-lg border border-hairline dark:border-hairline-dark bg-paper dark:bg-paper-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark transition-colors"
            title="Toggle Light/Dark Theme"
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-warning" />
            ) : (
              <Moon className="w-4 h-4 text-muted-fg" />
            )}
          </button>
        </div>
      </div>

      {/* Horizontal Alert Marquee Banner */}
      <div className="px-6 py-1.5 bg-paper/60 dark:bg-paper-dark/60 border-b border-hairline dark:border-hairline-dark flex items-center justify-between text-xs overflow-x-auto gap-4">
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="flex items-center space-x-1.5 text-muted-fg dark:text-muted-dark">
            <span className="text-[11px] font-mono">Assurance Alerts:</span>
          </div>

          <div className="flex items-center space-x-1.5 bg-amber-warning-subtle dark:bg-amber-warning-dark border border-amber-warning/30 px-2 py-0.5 rounded-md text-[11px]">
            <span className="font-bold text-amber-warning">● Fragility Alert</span>
            <span className="text-ink dark:text-ink-dark font-medium">
              WAN-042: +19.8% load burst breaches SLO (48.6 ms &gt; 45 ms)
            </span>
          </div>

          <div className="flex items-center space-x-1.5 bg-surface dark:bg-surface-dark border border-hairline dark:border-hairline-dark px-2 py-0.5 rounded-md text-[11px]">
            <span className="font-bold text-cobalt">● Telemetry Check</span>
            <span className="text-muted-fg dark:text-muted-dark font-medium">
              FIBER-017: Latency calibration uncertainty bounded at ±2.4 ms
            </span>
          </div>
        </div>

        <div className="flex items-center space-x-2 flex-shrink-0 text-[11px]">
          <span className="text-amber-warning font-mono font-bold">• Active Gate: GATHER_EVIDENCE</span>
        </div>
      </div>
    </div>
  );
}
export default TopBar;
