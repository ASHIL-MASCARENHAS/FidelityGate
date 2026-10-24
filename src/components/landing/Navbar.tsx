'use client';

import React, { useState } from 'react';
import { Moon, Sun, Volume2, VolumeX, Menu, X, ArrowUpRight, ShieldCheck } from 'lucide-react';
import { playTick } from '@/lib/sound';

interface NavbarProps {
  theme: 'light' | 'dark';
  setTheme: (t: 'light' | 'dark') => void;
  soundEnabled: boolean;
  setSoundEnabled: (s: boolean) => void;
  onOpenWorkspace: (tab?: string) => void;
  onNavigateSection?: (sectionId: string) => void;
}

export function Navbar({
  theme,
  setTheme,
  soundEnabled,
  setSoundEnabled,
  onOpenWorkspace,
  onNavigateSection,
}: NavbarProps) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleNavClick = (sectionId: string) => {
    playTick(soundEnabled);
    setMobileMenuOpen(false);
    if (onNavigateSection) {
      onNavigateSection(sectionId);
    } else {
      const el = document.getElementById(sectionId);
      if (el) el.scrollIntoView({ behavior: 'smooth' });
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-hairline dark:border-hairline-dark bg-paper/90 dark:bg-paper-dark/90 backdrop-blur-md transition-colors select-none">
      <div className="max-w-7xl mx-auto px-6 h-[72px] flex items-center justify-between gap-6">
        {/* Brandmark */}
        <div
          className="flex items-center gap-2.5 cursor-pointer shrink-0"
          onClick={() => handleNavClick('hero')}
        >
          <div className="w-10 h-10 rounded-xl bg-cobalt flex items-center justify-center text-white shadow-fine">
            <span className="text-base leading-none">◈</span>
          </div>
          <div className="flex items-baseline gap-1.5">
            <span className="font-bold text-xl tracking-[-0.02em] text-ink dark:text-ink-dark">
              FidelityGate
            </span>
            <span className="w-1.5 h-1.5 rounded-full bg-cyan-accent" />
          </div>
        </div>

        {/* Desktop Navigation Links */}
        <nav className="hidden md:flex items-center gap-7 text-[13px] font-medium text-muted-fg dark:text-muted-dark">
          <button
            onClick={() => handleNavClick('workflow')}
            className="py-2 hover:text-ink dark:hover:text-ink-dark transition-colors"
          >
            Workflow Sequence
          </button>
          <button
            onClick={() => handleNavClick('evidence')}
            className="py-2 hover:text-ink dark:hover:text-ink-dark transition-colors"
          >
            Evidence &amp; Rigor
          </button>
          <button
            onClick={() => {
              playTick(soundEnabled);
              onOpenWorkspace('guide');
            }}
            className="py-2 hover:text-cobalt dark:hover:text-cyan-accent font-semibold transition-colors"
          >
            User Guide
          </button>
        </nav>

        {/* Action Controls & CTA */}
        <div className="flex items-center space-x-3">
          {/* Sound Toggle */}
          <button
            onClick={() => {
              const next = !soundEnabled;
              setSoundEnabled(next);
              playTick(next);
            }}
            className="w-10 h-10 inline-flex items-center justify-center rounded-lg border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark transition-colors"
            title={soundEnabled ? 'Disable interface sounds' : 'Enable interface sounds'}
            aria-label="Toggle audio"
          >
            {soundEnabled ? (
              <Volume2 className="w-4 h-4 text-cobalt" />
            ) : (
              <VolumeX className="w-4 h-4" />
            )}
          </button>

          {/* Theme Toggle */}
          <button
            onClick={() => {
              playTick(soundEnabled);
              setTheme(theme === 'dark' ? 'light' : 'dark');
            }}
            className="w-10 h-10 inline-flex items-center justify-center rounded-lg border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark text-muted-fg dark:text-muted-dark hover:text-ink dark:hover:text-ink-dark transition-colors"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle theme"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-amber-warning" />
            ) : (
              <Moon className="w-4 h-4 text-muted-fg" />
            )}
          </button>

          {/* Primary CTA */}
          <button
            onClick={() => {
              playTick(soundEnabled);
              onOpenWorkspace('decision');
            }}
            className="hidden sm:inline-flex items-center gap-1.5 px-4 h-10 rounded-lg bg-cobalt hover:bg-cobalt-hover text-white text-[13px] font-semibold transition-all shadow-fine active:scale-[0.98]"
          >
            <span>Explore the platform</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </button>

          {/* Mobile menu button */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-lg border border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark text-ink dark:text-ink-dark"
            aria-label="Toggle mobile menu"
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-t border-hairline dark:border-hairline-dark bg-surface dark:bg-surface-dark px-6 py-4 space-y-2 text-[13px] font-medium text-ink dark:text-ink-dark animate-in fade-in duration-150">
          <button
            onClick={() => handleNavClick('workflow')}
            className="block w-full text-left py-2 text-muted-fg dark:text-muted-dark"
          >
            Workflow Sequence
          </button>
          <button
            onClick={() => handleNavClick('evidence')}
            className="block w-full text-left py-2 text-muted-fg dark:text-muted-dark"
          >
            Evidence &amp; Rigor
          </button>
          <button
            onClick={() => {
              setMobileMenuOpen(false);
              onOpenWorkspace('guide');
            }}
            className="block w-full text-left py-2 text-cobalt font-semibold"
          >
            User Guide &amp; Judging Alignment
          </button>
          <div className="pt-2">
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                onOpenWorkspace('decision');
              }}
              className="w-full py-2.5 rounded-lg bg-cobalt text-white text-[13px] font-semibold text-center"
            >
              Explore the platform
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
