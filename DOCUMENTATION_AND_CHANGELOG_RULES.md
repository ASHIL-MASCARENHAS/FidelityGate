# FidelityGate --- Documentation and Change Tracking

## Required files

-   `README.md`
-   `docs/REFERENCE_AUDIT.md`
-   `docs/DESIGN_SYSTEM.md`
-   `docs/ARCHITECTURE.md`
-   `docs/IMPLEMENTATION_PLAN.md`
-   `docs/CHANGELOG.md`
-   `docs/TEST_REPORT.md`
-   `docs/HACKATHON_ALIGNMENT.md`
-   `docs/DECISIONS.md`

## Accuracy rules

-   Document implemented behavior, not aspirations.
-   Label incomplete, mock, demo-only, unavailable, and unverified
    features.
-   Never invent passing tests, API endpoints, performance results, or
    benchmark outcomes.
-   Record exact commands, results, and environment limitations.
-   Explain dependency additions and API/persistence changes.
-   Record what was observed on the reference site and how it informed
    an original implementation.
-   State what was actually tested for accessibility, responsiveness,
    reduced motion, and theme behavior.

## Changelog format

Use dated entries with Added, Changed, Fixed, Removed, Backend/API
impact, Accessibility/performance impact, and Verification status.

Example: \## YYYY-MM-DD --- Reference-inspired UI refinement \###
Added - Original pointer-reactive hero visualization. \### Changed -
Reworked workspace hierarchy and navigation. \### Fixed - Reduced theme
flash during initial load. \### Backend/API impact - No API contract
changes; existing routes preserved. \### Verification - `npm run build`
--- PASS only if actually run. - Browser smoke test --- BLOCKED if not
runnable, with reason.

## Implementation plan status

-   `[ ]` Not started
-   `[-]` In progress
-   `[x]` Completed and verified

Code being written is not proof of completion. Mark an item verified
only after the relevant check has been run.

## Final handoff

Summarize visual/structural changes, motion and sound, landing/workspace
relationship, backend contracts, exact tests and outcomes, documentation
files, known limitations, and next steps.
