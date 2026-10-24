# FidelityGate --- Antigravity Master Prompt

Act as a principal product designer, frontend architect, motion
designer, and full-stack engineer with 15+ years of experience in
premium web experiences, enterprise products, scientific visualization,
and AI-assisted engineering systems.

## Mission

Improve the existing FidelityGate repository into a polished product
inspired closely by the *observable* visual language and interaction
quality of https://billodesign.webflow.io/. Study the live reference
directly. Translate its layout rhythm, typography, motion, sound
controls, 3D storytelling, hover feedback, scroll transitions, and sense
of craft into an original FidelityGate experience. Do not copy
proprietary source code, private assets, or the original logo.

This is an implementation task: inspect the actual repository, edit real
files, run the project, verify it, and document all changes. Do not stop
at mockups or a plan.

## Inspect first

1.  Inspect routes, package files, dependencies, assets, API clients,
    backend services, tests, and documentation.
2.  Confirm actual stack and versions. Expected candidates may include
    Next.js, React, TypeScript, Python/FastAPI, but do not assume;
    preserve the existing architecture unless a migration is justified.
3.  Record API endpoints, request/response schemas, persistence,
    workflows, and pre-existing failures.
4.  Write `docs/IMPLEMENTATION_PLAN.md`, then proceed with
    implementation.

## Reference audit

Browse the live reference at desktop and mobile sizes. Observe the real
hero, palette, type, layout, preloader, cursor response, 3D focal
object, sound controls, hover states, scroll-triggered animation,
transitions, mobile behavior, and fallback behavior. Record only
verified observations in `docs/REFERENCE_AUDIT.md`. Mark anything
unverified rather than guessing.

## Visual direction

Follow the reference's premium, minimal, futuristic, editorial style:
expressive typography, intentional whitespace, restrained dark/neutral
surfaces and accents based on observed colors, fine borders, nuanced
depth, and polished responsive composition. Do not blindly retain the
previous theme if it differs from the live reference. Define semantic
CSS variables for color, type, spacing, radii, shadows, layers, and
motion. Keep gate-state colors legible and distinct.

## Stack and keywords

Inspect dependencies first. Use only what is justified: - Next.js App
Router or the existing router - React + TypeScript - CSS
variables/design tokens; Tailwind only if already present or useful -
GSAP + ScrollTrigger for coordinated scroll/timeline motion -
Motion/Framer Motion for component transitions only if appropriate;
avoid competing animation engines - Spline for a lightweight
cursor-reactive 3D focal visual only if verified useful, with static
fallback - Lottie for small vector animations where appropriate -
Howler.js or Web Audio API for opt-in interface sound - Existing icon
library or Lucide - Existing network visualization, or one appropriate
library such as React Flow, Cytoscape.js, or D3 - Existing chart
library, or Recharts/Visx when justified - Typed API service layer for
FastAPI - Existing validation library, or Zod when useful - Playwright
for browser smoke tests if available - Existing unit/component test
framework, ESLint, Prettier, TypeScript checks, and production build

Do not install every named tool by default. Avoid duplicate libraries
and explain any new dependency.

## Landing page

Create a distinctive, premium landing page with: - Refined navigation,
FidelityGate brand, key product links, docs, optional sound toggle,
theme toggle, and "Explore the platform" CTA. - Hero headline: **"Make
every network decision earn its confidence."** - An original animated
network-intelligence visual that communicates routes, uncertainty,
counterexamples, and evidence. - A short explanation of why nominal
assumptions are fragile. - A scroll-led sequence: Investigate →
Challenge → Gather evidence → Verify → Evaluate. - A product preview
based on actual product patterns. - Evidence/methodology section. -
Final CTA and concise footer.

Avoid endless same-shaped cards, generic AI dashboard layouts,
decorative metrics, fake customer logos, and unsupported performance
claims.

## Motion and effects

Recreate the *quality and interaction principles* of the reference with
an original implementation: - Brief, skippable entrance sequence. -
Staggered hero text reveal with refined easing. - Scroll-triggered
section reveals and limited scroll-linked storytelling. - Subtle
pointer-reactive hero visual. - Thoughtful hover, focus, and press
states. - Smooth anchor navigation and transitions. - Consistent motion
tokens and easing. - Prefer transform/opacity over layout-heavy
animation. - No scroll hijacking, long blocking preloader, or perpetual
distracting effects. - Respect `prefers-reduced-motion`; content must
remain available without animation.

## Sound

Sound must be optional, off by default or activated by explicit user
choice, controlled by a visible toggle, persisted if appropriate, and
never autoplay on page load or during scrolling. Use short, quiet sounds
for a few meaningful actions only. All functionality must work without
sound and obey browser autoplay restrictions.

## Explore the platform: not a simulator dashboard

Redesign the workspace as a premium, calm, practical engineering
application: - Clean application shell and clear navigation. - One
dominant working area at a time. - Progressive disclosure for advanced
parameters. - Contextual evidence panels rather than dozens of
equal-weight cards. - Refined topology with selected route emphasis. -
Expandable execution trace and diagnostics. - Compact metrics with
provenance. - Clear deterministic gate outcome and explanation. - Honest
loading, error, empty, running, completed, and unavailable states.

Preserve these views where supported: Decision Workspace, Execution
Trace, Evaluation Lab, Run History, Settings/Docs. Avoid excessive
sidebars, competing alert banners, fake "engine active" states,
decorative charts, and fabricated live data.

## Backend integrity --- non-negotiable

-   Python/FastAPI remains authoritative for investigation logic and
    official deterministic gate outcomes.
-   Browser code may render and format but must not invent or
    independently decide the official gate outcome.
-   Preserve API endpoints, schemas, payloads, and persistence contracts
    unless a documented change is necessary.
-   Use typed API service functions.
-   Distinguish measured, derived, demo, and missing data.
-   Never show mock values as real output or claim success before
    backend confirmation.
-   Preserve counterexample-guided investigation, uncertainty-aware
    diagnostics, measurement-error handling, independent deterministic
    verification, and comparison against nominal-only, fixed-margin, and
    non-adaptive sweep baselines.
-   Evaluation charts use actual backend results.
-   If a feature/API is missing, show an honest unavailable state and
    document it.
-   Never expose secrets in client code.

## Hackathon use case and oversight

Primary domain: **IT Infrastructure**. Focus the demo on human-approved
network rerouting during a traffic surge. Demonstrate data ingestion →
agent investigation/decision → action proposal → human approval →
outcome reporting. Do not silently execute a consequential network
change. If no real action executor exists, clearly label execution
unavailable and stop at an approval-ready proposal. Do not claim broad
coverage of all organizer domains.

## Quality

Target WCAG 2.2 AA principles. Ensure keyboard support, visible focus,
accessible icon buttons, readable diagrams, reduced motion, responsive
layouts, no horizontal overflow, and performance appropriate for
ordinary hardware.

Run available lint, type-check, tests, production build, and browser
smoke tests. Do not claim a check passed unless it was actually run.
Document blockers and pre-existing failures.

## Required documentation

Create/update: - `README.md` - `docs/REFERENCE_AUDIT.md` -
`docs/DESIGN_SYSTEM.md` - `docs/ARCHITECTURE.md` -
`docs/IMPLEMENTATION_PLAN.md` - `docs/CHANGELOG.md` -
`docs/TEST_REPORT.md` - `docs/HACKATHON_ALIGNMENT.md` -
`docs/DECISIONS.md`

Documentation must reflect actual implementation, not aspirations. At
completion report major changes, motion/sound behavior, backend
contracts, exact checks run and results, files changed, and remaining
limitations. Implement, run, verify, and document; do not stop after
planning.
