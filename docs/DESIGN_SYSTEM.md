# FidelityGate — Design System & Tokens Specification

This document establishes the official semantic design system, token dictionary, accessibility standards, 3D visualization parameters, and interaction guidelines for FidelityGate.

---

## 1. Dual-Theme Semantic Token System

FidelityGate employs independent, high-contrast token dictionaries for Light and Dark modes. Tokens share unified semantic names across CSS variables and Tailwind classes.

### A. Ground, Paper & Surface Tokens

| Semantic Token | Light Mode Value | Dark Mode Value | Usage & Visual Role |
| :--- | :--- | :--- | :--- |
| `paper` / `--paper` | `#F7F8FA` (Cool Ice Paper) | `#08111F` (Deep Navy Ground) | Application body canvas ground |
| `surface` / `--surface` | `#FFFFFF` (Pure Card Surface) | `#0D1B2A` (Elevated Navy) | Primary panel containers, elevated cards |
| `surface-2` / `--surface-2` | `#F0F3F7` | `#111F34` (Secondary Well) | Inner wells, input fields, nested components |
| `hairline` / `--hairline` | `#E2E6ED` (Subtle Divider) | `#22334A` (Dark Hairline) | 1px border dividers, subtle component edges |
| `hairline-strong` | `#CBD3E0` | `#334A6A` | High-emphasis borders, active tab outlines |

### B. Typography & Contrast Tokens

| Semantic Token | Light Mode Value | Dark Mode Value | Contrast Standard |
| :--- | :--- | :--- | :--- |
| `ink` / `--ink` | `#111827` (Near-Black Ink) | `#F2F5FA` (Bright Off-White) | WCAG AAA primary titles, headings, active figures |
| `muted` / `--muted` | `#657387` (Balanced Slate) | `#9AA9BD` (Subtle Silver) | WCAG AA secondary labels, helper descriptions |

### C. Accent, Energy & Brand Tokens

| Semantic Token | Hex / HSL Value | Usage & Visual Role |
| :--- | :--- | :--- |
| `cobalt` / `--cobalt` | `#4169F5` (Royal Cobalt) | Primary CTAs, active tab indicators, authoritative badges |
| `cobalt-hover` | `#3154D4` | Hover state for cobalt buttons |
| `cyan` / `--cyan` | `#55D9F4` (Electric Cyan) | Active signal packets, globe atmosphere, live telemetry nodes |
| `cobalt-subtle` | `rgba(65, 105, 245, 0.08)` | Background tint for active cards, information wells |

### D. Scientific Decision Verdict Semantics

| Verdict State | Accent Hex | Subtle Background | Meaning & Enforcement |
| :--- | :--- | :--- | :--- |
| `ACCEPT` | `#10B981` (Emerald) | `rgba(16, 185, 129, 0.10)` | All swept variations strictly satisfy SLO latency (<= 45 ms) |
| `GATHER_EVIDENCE` | `#F59E0B` (Amber) | `rgba(245, 158, 11, 0.10)` | Nominal satisfies SLO, but adversarial counterexample breach found |
| `ABSTAIN` | `#EF4444` (Rose) | `rgba(239, 68, 68, 0.10)` | Structural invalidity, severe capacity overload, or empty intersection |

---

## 2. Atmospheric Pure CSS Mesh Gradients

Rather than loading large JavaScript canvas animation libraries or heavy image assets, FidelityGate implements GPU-accelerated fixed-attachment pure CSS radial gradients:

### Dark Theme Mesh Gradient (`.dark-mesh-bg`)
```css
.dark-mesh-bg {
  background-color: #08111F;
  background-image: 
    radial-gradient(at 0% 0%, rgba(65, 105, 245, 0.12) 0px, transparent 55%),
    radial-gradient(at 100% 0%, rgba(85, 217, 244, 0.08) 0px, transparent 50%),
    radial-gradient(at 50% 100%, rgba(13, 27, 42, 0.8) 0px, transparent 70%);
  background-attachment: fixed;
}
```

### Workspace Floating Enclosure Mesh (`.workspace-mesh-bg`)
```css
.workspace-mesh-bg {
  background-color: #08111F;
  background-image: 
    radial-gradient(at 0% 0%, rgba(65, 105, 245, 0.08) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(85, 217, 244, 0.06) 0px, transparent 50%),
    radial-gradient(at 50% 50%, rgba(13, 27, 42, 0.5) 0px, transparent 100%);
  background-attachment: fixed;
}
```

---

## 3. Interactive 3D Network Globe Specification

The central hero visual is an interactive Three.js network globe (`InteractiveNetworkGlobe.tsx`) designed with restrained enterprise aesthetics:

- **Core Geometry:** Dark spherical core of radius R = 2.0 with `MeshPhongMaterial` (`#0A1220`).
- **Atmospheric Glow:** Concentric thin outer sphere (R = 2.04) with additive blending and opacity 0.12 in electric cyan (`#55D9F4`).
- **Dotted Continents:** 4,312 distinct geographical point coordinates generated via latitude/longitude sampling (step 3 deg) filtered by a deterministic bounding polygon model (`isLand(lat, lon)`). Rendered via `THREE.Points` with `THREE.PointsMaterial` (size 0.024, opacity 0.55).
- **Reference Grid:** Spherical latitude and longitude ring lines at 30 deg increments using low-opacity dark cyan lines (`#2A4B6E`).
- **Global Network Hubs:** 10 real-world strategic data centers:
  - Frankfurt (50.11 N, 8.68 E)
  - London (51.51 N, -0.13 W)
  - New York (40.71 N, -74.01 W)
  - Silicon Valley (37.39 N, -122.08 W)
  - Tokyo (35.68 N, 139.69 E)
  - Singapore (1.35 N, 103.82 E)
  - Zurich (47.38 N, 8.54 E)
  - São Paulo (-23.55 S, -46.63 W)
  - Sydney (-33.87 S, 151.21 E)
  - Mumbai (19.08 N, 72.88 E)
- **Curved 3D Bézier Arcs:** Great-circle arcs elevated radially above the globe surface (midpoint R = 2.45) connecting hub pairs.
- **Travelling Signal Packets:** Animated glowing cyan and blue particles travelling continuously along the 3D curves.
- **Interactivity & Damping:** Smooth mouse and touch drag rotation with inertia damping (`lerp(current, target, 0.05)`). Automatic gentle orbital rotation when idle.
- **Accessibility & Fallback:** Respects `prefers-reduced-motion` by halting continuous rotation. Displays a 2D SVG canvas fallback if WebGL context creation fails.
- **Scientific Integrity Badge:** Displays an explicit footnote disclaimer: *"Illustrative Network Simulation · Illustrative Topology Arcs"*.

---

## 4. Typography Hierarchy & Micro-Interactions

| Role | Font Family | Size / Leading | Weight / Tracking | Context |
| :--- | :--- | :--- | :--- | :--- |
| **Hero Product Name** | `Geist Sans`, sans-serif | `clamp(2.5rem, 6vw, 4.5rem)` / 1.05 | Bold (700) / `-0.03em` | Dominant bold product title **FidelityGate** |
| **Section Title** | `Geist Sans`, sans-serif | `1.5rem` (24px) / 1.25 | SemiBold (600) / `-0.02em` | Workspace and User Guide view headings |
| **Card / Panel Title**| `Geist Sans`, sans-serif | `0.9375rem` (15px) / 1.35 | SemiBold (600) / `-0.01em` | Panel titles and metric group cards |
| **Body Copy** | `Geist Sans`, sans-serif | `0.875rem` (14px) / 1.6 | Normal (400) / Normal | Explanatory descriptions, audit notes |
| **Code & Formulas** | `Geist Mono`, monospace | `0.8125rem` (13px) / 1.4 | Medium (500) / Normal | LaTeX math, JSON keys, routing paths |
| **Micro Badges** | `Geist Mono`, monospace | `0.6875rem` (11px) / 1.2 | SemiBold (600) / `tracking-wider` | Stage badges, verdict tags, node status |

---

## 5. Micro-Audio Feedback Design

- **Synthesizer Implementation:** Native browser Web Audio API oscillator (`AudioContext`) with zero external asset dependencies.
- **Tick Sound (`playTick`):** Short sine wave burst, 800 Hz decaying to 200 Hz over 40 ms at low gain (0.04), providing subtle mechanical keypress feedback.
- **Confirmation Sound (`playConfirmation`):** Harmonic two-tone chord (523 Hz to 659 Hz) over 120 ms at low gain (0.06) indicating successful state transition or gate authorization.
- **Consent Rule:** Muted by default. Activated only upon explicit user toggle and persisted in `localStorage`.

---

## 6. Auto Demo Component Tokens & Interaction Design

The Auto Demo subsystem introduces structured, high-visibility interactive controls conforming to the dual-theme token dictionary:

### A. Navigation Bar Auto Demo Button (`WorkspaceApp.tsx`)
- **Idle State:** Compact rounded-lg pill with `Play` icon (`w-3.5 h-3.5 text-cobalt`), subtle border (`hairline`), muted label (`Auto Demo`), and hover highlight (`hover:border-cobalt/40 hover:text-ink`).
- **Active State:** Vibrant cobalt/cyan badge (`bg-cobalt/15 text-cobalt border border-cobalt/40 shadow-sm shadow-cobalt/20`) with animated pulsing indicator dot (`w-1.5 h-1.5 rounded-full bg-cobalt animate-ping`), `Square` stop icon, and label `Demo Running`.

### B. Transition Modal (`AutoDemoModal.tsx`)
- **Backdrop:** Screen-filling frosted overlay (`backdrop-blur-md bg-black/60 z-50`).
- **Surface Elevation:** Centered modal container with elevated dark surface (`bg-[#0D1B2A] border border-[#22334A] rounded-2xl shadow-2xl p-6`).
- **Header Dynamics:** Color-coded status accents reflecting true workflow state:
  - `COMPLETED` / `OUTCOME_REPORTED`: Emerald accent (`#10B981`)
  - `AWAITING_HUMAN_APPROVAL` / `GATHER_EVIDENCE`: Amber accent (`#F59E0B`)
  - `ABSTAIN` / `REJECTED_BY_HUMAN`: Rose accent (`#EF4444`)
  - `IN_PROGRESS` / Default: Cobalt accent (`#4169F5`)
- **Countdown Indicator:** Visual 4-second auto-advance progress bar and live numeric countdown pill (`Advancing in 4s...`).

### C. Floating Viewing Dwell Bar (`AutoDemoFloatingControl.tsx`)
- **Placement:** Floating fixed pill anchored at bottom center (`fixed bottom-6 left-1/2 -translate-x-1/2 z-50`).
- **Enclosure:** Glassmorphic container with deep navy background (`bg-[#0D1B2A]/90 backdrop-blur-md border border-[#22334A] rounded-full shadow-2xl px-5 py-2.5`).
- **Elements:**
  - Active Step Counter Pill: Monospace step indicator (`Step 2 of 8`).
  - Active Run Badge: Truncated canonical ID chip (`wf-241aa77c`).
  - Dwell Countdown Bar: 5-second linear progress timer.
  - Interactive Action Buttons: `Pause` / `Resume` toggle, `Next Tab` forward skip, and `Stop` close button.

### D. Keyboard Accessibility Standards
- <kbd>Escape</kbd>: Immediately stops the Auto Demo tour and closes any open modal.
- <kbd>Space</kbd>: Pauses or resumes the active dwell timer.
- <kbd>Enter</kbd>: Advances immediately through the modal or jumps to the next tab without waiting for countdowns.


---

## 7. Enterprise Report Typography & Restrained Footer System

### A. Report Typography Hierarchy Specification
To guarantee consistent, legible, and un-crowded presentation across all decision reports, outcome summaries, and XAI findings, FidelityGate enforces the following report typography hierarchy:

| Hierarchy Role | Semantic Class | Size & Line Height | Weight & Tracking | Role & Visual Treatment |
| :--- | :--- | :--- | :--- | :--- |
| **Report Title** | `.t-report-title` | `1.25rem` (20px) / `1.30` | Bold (`700`) / `-0.02em` | Main report document header (e.g. Post-Intervention Outcome Report, XAI Decision Attribution). Clearly distinct from metadata. |
| **Section Heading** | `.t-section-heading` | `1.00rem` (16px) / `1.35` | Bold (`700`) / `-0.015em` | Major report division header (e.g. Metric Comparison, Gate Rules, Counterexample Replay). |
| **Card / Panel Title** | `.t-panel-title` | `0.9375rem` (15px) / `1.40` | Bold (`700`) / `-0.012em` | Card-level container titles, diagnostic cycles. |
| **Field Labels** | `.t-field-label` | `0.75rem` (12px) / `1.45` | SemiBold (`600`) / `0.025em` uppercase | Table headers, property labels, metric descriptors. |
| **Key Values & Figures** | `.t-key-value`, `.t-metric` | `0.875rem` (14px) / `1.40` | Bold (`700`) / `-0.01em` tabular | Important metrics, latency numbers, delta shifts, breach counts, stability scores. |
| **Body & Prose Text** | `.t-report-body` | `0.8125rem` (13px) / `1.65` | Regular (`400`) / Normal | Executive summaries, plain-language explanations, limitation descriptions. Never uniformly extra-bold. |
| **Metadata & Provenance** | `.t-report-meta` | `0.6875rem` (11px) / `1.50` | Medium (`500`) / Monospace | Run IDs, observation hashes, ISO-8601 UTC timestamps, execution twin IDs. |

### B. Un-Crowding & Spacing Principles
- **2x2 Metric Grids**: Expanded card padding (`p-4` with `rounded-xl`), elevated surfaces (`bg-surface/70 dark:bg-surface-dark/70`), and distinct key-value separation.
- **Table Padding**: Table headers and data cells use `py-3.5 px-4` to `py-4 px-4` with vertical alignment, preventing cramped borders and overflowing text.
- **Prose Contrast**: Plain-language summaries and limitation narratives use proportional fonts (`font-sans`) with generous line-height (`leading-relaxed`) rather than dense raw monospace.

### C. Restrained Platform Footer (Zero False Claims)
- Removed all decorative, unsupported technology badges (`Docker`, `Kubernetes`, `Linux eBPF`, `OpenConfig`, `BGP-EVPN`, `SNMPv3`) from the platform workspace footer.
- Replaced with an authentic, restrained enterprise baseline:
  - Brand mark: `◈ FidelityGate`
  - Subtitle: `Pre-Production Digital-Twin Validation`
  - Functional navigation: `User Guide & Criteria`, `Workflow & Approval`
  - Software version: `v1.0.0`
