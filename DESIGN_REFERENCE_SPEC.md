# FidelityGate --- Reference Audit Specification

Reference: https://billodesign.webflow.io/

The Webflow showcase describes BilloDesign as a minimal futuristic
portfolio with motion, sound, 3D, micro-interactions, glass-like
accents, an animated preloader, and a cursor-reactive Spline orb. Treat
this as a research lead; verify the current live site before
implementing details.

## Audit checklist

For desktop and mobile, record verified observations about: - Layout
rhythm, content width, typography, line breaks, and spacing -
Background, foreground, accent, borders, glass, shadows, and depth -
Header behavior and navigation - Hero focal object and animation -
Preloader or initial entrance - Scroll reveals, pinned sections, and
transitions - Cursor, hover, focus, click, and press feedback - Sound
toggle and consent - 3D behavior and fallback - Project/service section
layout and CTA patterns - Mobile/touch behavior and accessibility

For each item, document trigger, visible response, timing impression,
responsive behavior, and FidelityGate adaptation. Mark anything not
verified as unknown. Do not invent exact font names, hex values, timing,
or easing curves.

## FidelityGate translation

-   The focal object becomes an original network-intelligence
    visualization.
-   Portfolio sections become a clear product narrative.
-   Project/service cards become product capabilities and business
    outcomes.
-   Interactions reveal evidence and workflow affordances.
-   Sound remains optional and never communicates state alone.
-   3D never replaces a required interactive network topology.
-   Motion explains hierarchy and relationships, not fake data.

## Tokens to define after audit

Create semantic tokens for background, surface, elevated surface, text,
muted text, accent, border, focus, accept, gather-evidence, abstain,
error, display/body/monospace fonts, spacing, radius, shadows, layers,
duration, and easing. Test contrast in both themes.

## Motion rules

Use a small consistent set of timings/easings; prefer opacity/transform;
avoid competing animation engines on the same property; keep preloaders
brief and skippable; support `prefers-reduced-motion`; keep content
available if animation fails; avoid scroll hijacking; test
mobile/low-power fallback.

This is an original implementation inspired by publicly observable
design qualities. Do not copy proprietary source code or private assets.
Do not claim pixel-perfect fidelity unless measured and verified.
