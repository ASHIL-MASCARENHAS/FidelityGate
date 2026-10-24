'use client';

import React, { useState, useEffect } from 'react';
import { LandingPage } from '@/components/landing/LandingPage';
import { WorkspaceApp } from '@/components/workspace/WorkspaceApp';

export default function Home() {
  const [viewMode, setViewMode] = useState<'landing' | 'workspace'>('landing');
  const [initialWorkspaceTab, setInitialWorkspaceTab] = useState<string>('decision');
  const [theme, setTheme] = useState<'light' | 'dark'>('light');
  const [soundEnabled, setSoundEnabled] = useState<boolean>(false);

  // Apply theme class to document root
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [theme]);

  // Check URL query param ?view=workspace on initial mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search);
      if (params.get('view') === 'workspace') {
        const tab = params.get('tab') || 'decision';
        setInitialWorkspaceTab(tab);
        setViewMode('workspace');
      }
    }
  }, []);

  const handleOpenWorkspace = (targetTab: string = 'decision') => {
    setInitialWorkspaceTab(targetTab);
    setViewMode('workspace');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleBackToLanding = () => {
    setViewMode('landing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  if (viewMode === 'landing') {
    return (
      <LandingPage
        theme={theme}
        setTheme={setTheme}
        soundEnabled={soundEnabled}
        setSoundEnabled={setSoundEnabled}
        onOpenWorkspace={handleOpenWorkspace}
      />
    );
  }

  return (
    <WorkspaceApp
      initialTab={initialWorkspaceTab}
      theme={theme}
      setTheme={setTheme}
      soundEnabled={soundEnabled}
      setSoundEnabled={setSoundEnabled}
      onBackToLanding={handleBackToLanding}
    />
  );
}
