'use client';

import React from 'react';
import { ArrowUpRight, ArrowRight, ShieldCheck, Sparkles } from 'lucide-react';
import { playTick, playConfirmation } from '@/lib/sound';
import { InteractiveNetworkGlobe } from './InteractiveNetworkGlobe';

interface HeroSectionProps {
  onOpenWorkspace: () => void;
  onExploreWorkflow: () => void;
  soundEnabled: boolean;
}

export function HeroSection({
  onOpenWorkspace,
  onExploreWorkflow,
  soundEnabled,
}: HeroSectionProps) {
  const handlePrimaryClick = () => {
    playConfirmation(soundEnabled);
    onOpenWorkspace();
  };

  const handleSecondaryClick = () => {
    playTick(soundEnabled);
    onExploreWorkflow();
  };

  return (
    <section id="hero" className="relative pt-8 pb-16 md:pt-14 md:pb-24 overflow-hidden">
      {/* Background atmospheric radial glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[600px] bg-gradient-to-b from-cyan-500/10 via-cobalt/5 to-transparent dark:from-cyan-900/15 dark:via-cobalt/10 pointer-events-none blur-3xl" />

      <div className="max-w-7xl mx-auto px-6 relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 items-center">
          {/* Left Column: Simple, Bold, Minimal Hero Typography */}
          <div className="lg:col-span-6 space-y-6 text-left">
            {/* Minimal Capability Eyebrow */}
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full text-xs font-mono font-medium border border-hairline dark:border-hairline-dark bg-surface/80 dark:bg-surface-dark/80 backdrop-blur-md text-ink dark:text-ink-dark shadow-sm">
              <span className="w-2 h-2 rounded-full bg-cyan-accent" />
              <span className="tracking-wider uppercase text-[11px] font-semibold text-cobalt dark:text-cyan-accent">
                Decision Assurance Platform
              </span>
            </div>

            {/* Dominant Clean Product Heading */}
            <div>
              <h1 className="text-4xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-ink dark:text-ink-dark">
                FidelityGate
              </h1>
              <p className="mt-4 text-base sm:text-lg text-muted-fg dark:text-muted-dark max-w-lg leading-relaxed font-sans">
                Counterexample-guided decision assurance for agentic network operations under model uncertainty.
              </p>
            </div>

            {/* Core Principle Callout */}
            <div className="p-4 rounded-xl border border-hairline dark:border-hairline-dark bg-surface/60 dark:bg-surface-dark/60 backdrop-blur-sm max-w-lg">
              <p className="text-xs text-muted-fg dark:text-muted-dark leading-relaxed font-mono">
                <strong className="text-ink dark:text-ink-dark">Operating Rule:</strong> Agents investigate and recommend. Deterministic software calculates and enforces. Explanations expose the evidence. A human authorizes consequential actions.
              </p>
            </div>

            {/* Primary & Secondary Action CTAs */}
            <div className="flex flex-wrap items-center gap-3 pt-2">
              <button
                onClick={handlePrimaryClick}
                className="inline-flex items-center gap-2 px-6 h-12 rounded-xl bg-cobalt hover:bg-cobalt-hover text-white text-sm font-semibold transition-all shadow-fine active:scale-[0.98] group"
              >
                <span>Explore the platform</span>
                <ArrowUpRight className="w-4 h-4 group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform" />
              </button>

              <button
                onClick={handleSecondaryClick}
                className="inline-flex items-center gap-2 px-5 h-12 rounded-xl border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark hover:bg-paper dark:hover:bg-paper-dark text-ink dark:text-ink-dark text-sm font-semibold transition-all active:scale-[0.98]"
              >
                <span>How it works</span>
                <ArrowRight className="w-4 h-4 text-muted-fg" />
              </button>
            </div>

            {/* Compact Capability Tags */}
            <div className="pt-2 flex flex-wrap items-center gap-2 text-[11px] font-mono text-muted-fg dark:text-muted-dark">
              {['Deterministic Gate Policy', 'Counterexample Search', 'Measurement Error Models', 'Isolated Twin Simulation'].map((tag) => (
                <span
                  key={tag}
                  className="px-2.5 py-1 rounded-md bg-paper dark:bg-paper-dark border border-hairline dark:border-hairline-dark"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          {/* Right Column: Interactive 3D Network Globe */}
          <div className="lg:col-span-6 flex items-center justify-center">
            <InteractiveNetworkGlobe soundEnabled={soundEnabled} />
          </div>
        </div>
      </div>
    </section>
  );
}
