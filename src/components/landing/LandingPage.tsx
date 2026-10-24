'use client';

import React from 'react';
import { Navbar } from './Navbar';
import { HeroSection } from './HeroSection';
import { ServicesShowcase } from './ServicesShowcase';
import { WorkflowSequence } from './WorkflowSequence';
import { EvidenceCredibility } from './EvidenceCredibility';
import { ProductPreview } from './ProductPreview';
import { LandingFooter } from './LandingFooter';

interface LandingPageProps {
  theme: 'light' | 'dark';
  setTheme: (t: 'light' | 'dark') => void;
  soundEnabled: boolean;
  setSoundEnabled: (s: boolean) => void;
  onOpenWorkspace: (targetTab?: string) => void;
}

export function LandingPage({
  theme,
  setTheme,
  soundEnabled,
  setSoundEnabled,
  onOpenWorkspace,
}: LandingPageProps) {
  const handleScrollTo = (sectionId: string) => {
    const el = document.getElementById(sectionId);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <div className="min-h-screen bg-paper dark:bg-paper-dark text-ink dark:text-ink-dark transition-colors duration-200">
      {/* Top Refined Sticky Header */}
      <Navbar
        theme={theme}
        setTheme={setTheme}
        soundEnabled={soundEnabled}
        setSoundEnabled={setSoundEnabled}
        onOpenWorkspace={(tab) => onOpenWorkspace(tab || 'decision')}
        onNavigateSection={handleScrollTo}
      />

      {/* Main Narrative Structure */}
      <main>
        {/* Hero Section with Interactive Conceptual Topology */}
        <HeroSection
          onOpenWorkspace={() => onOpenWorkspace('decision')}
          onExploreWorkflow={() => handleScrollTo('workflow')}
          soundEnabled={soundEnabled}
        />

        {/* BilloDesign-Style 9 Services Showcase Grid */}
        <ServicesShowcase
          soundEnabled={soundEnabled}
          onOpenWorkspace={(tab) => onOpenWorkspace(tab)}
        />

        {/* 5-Stage Guided Sequence: Investigate -> Challenge -> Gather -> Verify -> Evaluate */}
        <WorkflowSequence
          soundEnabled={soundEnabled}
          onOpenWorkspace={() => onOpenWorkspace('decision')}
        />

        {/* Defensibility & Scientific Credibility (6 Pillars) */}
        <EvidenceCredibility
          soundEnabled={soundEnabled}
          onOpenWorkspace={() => onOpenWorkspace('decision')}
        />

        {/* Workspace Product Previews (Interactive Tabs) */}
        <ProductPreview
          soundEnabled={soundEnabled}
          onOpenWorkspace={(tab) => onOpenWorkspace(tab || 'decision')}
        />
      </main>

      {/* Final CTA & Project Documentation Footer */}
      <LandingFooter
        soundEnabled={soundEnabled}
        onOpenWorkspace={(tab) => onOpenWorkspace(tab || 'decision')}
      />
    </div>
  );
}
