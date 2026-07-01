---
version: 1.0
name: Warmy AgentTest Design System
description: A warm editorial design system for an AI agent testing platform — adapted from Cursor's quietly-confident developer-tools brand language. Cream canvas, warm near-black ink, single brand voltage (Warmy Orange), hairline-only depth, and Inter/JetBrains Mono typography.

colors:
  primary: "#f54e00"
  primary-active: "#d04200"
  primary-subtle: "#fff0e8"
  ink: "#26251e"
  body: "#5a5852"
  muted: "#807d72"
  muted-soft: "#a09c92"
  canvas: "#f7f7f4"
  canvas-soft: "#fafaf7"
  surface: "#ffffff"
  surface-strong: "#e6e5e0"
  hairline: "#e6e5e0"
  hairline-soft: "#efeee8"
  hairline-strong: "#cfcdc4"

  semantic-success: "#1f8a65"
  semantic-success-subtle: "#dafbe1"
  semantic-warning: "#9a6700"
  semantic-warning-subtle: "#fff1c2"
  semantic-error: "#cf2d56"
  semantic-error-subtle: "#ffebe9"

  overlay: "rgb(38 37 30 / 0.45)"

typography:
  font-sans: "'Inter', system-ui, 'Helvetica Neue', Helvetica, Arial, sans-serif"
  font-code: "'JetBrains Mono', 'Fira Code', monospace"
  display-lg:
    fontSize: 28px
    fontWeight: 500
    lineHeight: 1.25
    letterSpacing: -0.35px
  display-md:
    fontSize: 22px
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: -0.22px
  title-md:
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
  title-sm:
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.4
  body-md:
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.5
  body-sm:
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.45
  caption:
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.4
  caption-uppercase:
    fontSize: 11px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0.66px
    textTransform: uppercase
  code:
    fontFamily: "'JetBrains Mono', 'Fira Code', monospace"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
  button:
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.0
  nav-link:
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1.4

rounded:
  none: 0px
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  pill: 9999px

spacing:
  xxs: 4px
  xs: 8px
  sm: 12px
  base: 16px
  md: 20px
  lg: 24px
  xl: 32px
  xxl: 48px
  section: 80px

components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "#ffffff"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 8px 16px
    height: 36px
  button-primary-active:
    backgroundColor: "{colors.primary-active}"
    textColor: "#ffffff"
  button-secondary:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline-strong}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 7px 15px
    height: 36px
  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.muted}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 8px 12px
    hoverBackground: "{colors.canvas-soft}"
    hoverTextColor: "{colors.ink}"
  button-danger:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.semantic-error}"
    border: "1px solid {colors.semantic-error}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: 7px 15px
    height: 36px

  text-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    placeholderColor: "{colors.muted-soft}"
    border: "1px solid {colors.hairline}"
    focusBorder: "{colors.primary}"
    focusRing: "rgb(245 78 0 / 0.2)"
    rounded: "{rounded.md}"
    padding: 8px 12px
    height: 40px

  badge:
    backgroundColor: "{colors.surface-strong}"
    textColor: "{colors.ink}"
    typography: "{typography.caption-uppercase}"
    rounded: "{rounded.pill}"
    padding: 2px 8px
  badge-accent:
    backgroundColor: "{colors.primary-subtle}"
    textColor: "{colors.primary}"
  badge-success:
    backgroundColor: "{colors.semantic-success-subtle}"
    textColor: "{colors.semantic-success}"
  badge-warning:
    backgroundColor: "{colors.semantic-warning-subtle}"
    textColor: "{colors.semantic-warning}"
  badge-danger:
    backgroundColor: "{colors.semantic-error-subtle}"
    textColor: "{colors.semantic-error}"

  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.ink}"
    border: "1px solid {colors.hairline}"
    rounded: "{rounded.lg}"
    padding: 20px
  card-hover:
    backgroundColor: "{colors.canvas-soft}"

  dialog:
    backgroundColor: "{colors.surface}"
    border: "1px solid {colors.hairline}"
    rounded: "{rounded.lg}"
    padding: 24px
    overlayColor: "{colors.overlay}"

  top-nav:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    height: 56px
    borderBottom: "1px solid {colors.hairline}"

  sidebar:
    backgroundColor: "{colors.surface}"
    borderRight: "1px solid {colors.hairline}"
    width: 224px
    navItemHeight: 36px
    navItemActive:
      backgroundColor: "{colors.primary-subtle}"
      textColor: "{colors.primary}"
    navItemInactive:
      textColor: "{colors.muted}"
      hoverBackground: "{colors.canvas-soft}"
      hoverTextColor: "{colors.ink}"

  table:
    headerTextColor: "{colors.muted}"
    headerTypo: "{typography.caption}"
    rowBorder: "1px solid {colors.hairline}"
    cellHeight: 44px

  empty-state:
    textColor: "{colors.ink}"
    descriptionColor: "{colors.muted}"

  section-header:
    titleTypo: "{typography.display-md}"
    titleColor: "{colors.ink}"
    descriptionColor: "{colors.muted}"
---

## Overview

Warmy AgentTest is an AI agent testing platform whose interface adopts a warm, editorial design language — adapted from Cursor's quietly-confident developer-tools brand. The base canvas is **warm cream** (`--canvas` / `#f7f7f4`) holding warm near-black ink (`--ink` / `#26251e`) for all text surfaces. The single brand voltage is **Warmy Orange** (`--primary` / `#f54e00`) reserved for primary CTAs and selected states — used scarcely.

Type runs **Inter** as the single sans family (substituting CursorGothic). **JetBrains Mono** carries every code surface — inline snippets, JSON editors, API response previews, and IDE-mockup panes.

**Key Characteristics:**
- Warm cream canvas, not white. Ink is warm (#26251e), not pure black.
- Single CTA color: `--primary` (Warmy Orange #f54e00). Used scarcely.
- Hairline-only depth; no drop shadows anywhere.
- Compact 8px CTA radius (developer dialect), 12px card radius.
- White cards on cream canvas for surface contrast.
- Full dark mode support.

## Colors

### Brand & Accent
- **Warmy Orange** (`--primary` / `#f54e00`): Primary CTA buttons, active nav item accent, focus rings. Used scarcely.
- **Warmy Orange Active** (`--primary-active` / `#d04200`): Button press state, link hover.
- **Warmy Orange Subtle** (`--primary-subtle` / `#fff0e8`): Selected row background, active nav item background.

### Surface
- **Canvas** (`--canvas` / `#f7f7f4`): Warm cream page floor — the body background.
- **Canvas Soft** (`--canvas-soft` / `#fafaf7`): Subtle surface variant for hover states and secondary backgrounds.
- **Surface** (`--surface` / `#ffffff`): Pure white card surface — slight contrast against the cream canvas.
- **Surface Strong** (`--surface-strong` / `#e6e5e0`): Badge default background, separator backgrounds.

### Hairlines
- **Hairline** (`--hairline` / `#e6e5e0`): Default 1px border for cards, inputs, table rows.
- **Hairline Soft** (`--hairline-soft` / `#efeee8`): Lighter dividers.
- **Hairline Strong** (`--hairline-strong` / `#cfcdc4`): Stronger borders for secondary buttons and emphasis outlines.

### Text
- **Ink** (`--ink` / `#26251e`): Default text color. Warm near-black.
- **Body** (`--body` / `#5a5852`): Secondary text, descriptions. Slightly muted from ink.
- **Muted** (`--muted` / `#807d72`): Tertiary text, placeholder labels.
- **Muted Soft** (`--muted-soft` / `#a09c92`): Placeholder text, disabled text.

### Semantic
- **Success** (`--success` / `#1f8a65`, `--success-subtle` / `#dafbe1`)
- **Warning** (`--warning` / `#9a6700`, `--warning-subtle` / `#fff1c2`)
- **Error** (`--danger` / `#cf2d56`, `--danger-subtle` / `#ffebe9`)

### Dark Mode

| Token | Light | Dark |
|---|---|---|
| `--canvas` | `#f7f7f4` | `#1a1a16` |
| `--canvas-soft` | `#fafaf7` | `#21211c` |
| `--surface` | `#ffffff` | `#282824` |
| `--hairline` | `#e6e5e0` | `#3a3a33` |
| `--hairline-strong` | `#cfcdc4` | `#4a4a42` |
| `--ink` | `#26251e` | `#f0efe8` |
| `--body` | `#5a5852` | `#b0aea8` |
| `--muted` | `#807d72` | `#807d72` |
| `--primary-subtle` | `#fff0e8` | `#3d1f0a` |
| `--surface-strong` | `#e6e5e0` | `#353530` |

## Typography

### Font Family
**Inter** is the body and display family. Fallback: `system-ui, "Helvetica Neue", Helvetica, Arial, sans-serif`.
Code surfaces switch to **JetBrains Mono**.

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|---|---|---|---|---|---|
| `display-lg` | 28px | 500 | 1.25 | -0.35px | Page section titles |
| `display-md` | 22px | 500 | 1.3 | -0.22px | Sub-section heads |
| `title-md` | 18px | 600 | 1.4 | 0 | Dialog titles, panel heads |
| `title-sm` | 16px | 600 | 1.4 | 0 | Card titles |
| `body-md` | 14px | 400 | 1.5 | 0 | Body text, form labels |
| `body-sm` | 13px | 400 | 1.45 | 0 | Secondary text |
| `caption` | 12px | 400 | 1.4 | 0 | Metadata, timestamps |
| `caption-uppercase` | 11px | 600 | 1.4 | 0.66px | Badges, section labels |
| `code` | 13px | 400 | 1.5 | 0 | Code — JetBrains Mono |
| `button` | 14px | 500 | 1.0 | 0 | Button labels |
| `nav-link` | 13px | 500 | 1.4 | 0 | Sidebar nav items |

### Principles
- Display weight at 500 (subtle medium, not bold).
- JetBrains Mono on every code surface.
- Body text defaults to 14px for developer-tool density.

## Layout

### Spacing System
- **Base unit:** 4px.
- **Tokens:** 4 / 8 / 12 / 16 / 20 / 24 / 32 / 48 / 80 px.

### Sidebar
- Width: 224px (14rem). Collapses to 64px (4rem) at narrow viewports.
- Nav items: 36px height, 6px border radius, 12px horizontal padding.
- Active state: `--primary-subtle` background + `--primary` text.
- Inactive state: `--muted` text, hover `--canvas-soft`.

### Content Area
- Page content uses generous 32px padding.
- Section headers use 4px spacing between title and description.

## Elevation & Depth

The system uses **hairline-only depth**. No drop shadows. Cards and dialogs float above the canvas via 1px hairlines and white-on-cream contrast.

| Level | Treatment | Use |
|---|---|---|
| Flat (canvas) | `--canvas` | Page background |
| Card | `--surface` + 1px `--hairline` | Content cards, list items |
| Dialog | `--surface` + 1px `--hairline` + `--overlay` backdrop | Modals |
| Sidebar | `--surface` + 1px `--hairline` border-right | Navigation |

## Components

### Button

**`button-primary`** — Signature Warmy Orange CTA. Background `--primary`, text white, height 36px, rounded 8px, padding 8px×16px.

**`button-secondary`** — White card pill on cream canvas. Background `--surface`, text `--ink`, 1px `--hairline-strong` border.

**`button-ghost`** — Transparent background. Text `--muted`, hover `--canvas-soft` background + `--ink` text. Used for toolbar actions and inline links.

**`button-danger`** — Destructive action. Background `--surface`, text `--danger`, 1px `--danger` border. Hover `--danger-subtle` background.

All buttons: 14px / 500, no uppercase, 8px border radius.

### Badge

Small pill-shaped labels. 11px / 600 / uppercase / 0.66px letter spacing. Full pill radius. 2px×8px padding.

Five tones: `neutral` (default, `--surface-strong` bg), `accent` (`--primary-subtle` bg), `success`, `warning`, `danger`.

### Input

White surface, 1px `--hairline` border, 40px height, 8px border radius, 12px padding.
Focus: 1px `--primary` border + 2px `--primary` ring at 20% opacity.
Placeholder: `--muted-soft`.

### Dialog

White surface card with 1px `--hairline` border, 12px border radius, 24px padding.
Semi-transparent warm overlay backdrop (`--overlay`).
No drop shadow — hairline-only depth.

### Card / ListCard

White surface, 1px `--hairline` border, 12px border radius, 16-20px padding.
Hover: `--canvas-soft` background.
Actions visible on hover only (opacity transition).

### Table

Minimal style. Header: 12px, `--muted` text. Rows: 1px `--hairline` bottom border.
Cell height: 44px with 12px horizontal padding.

### Empty State

Centered layout with `--ink` title (14px / 600) and `--muted` description (14px).
Optional action slot below description.

### Top Navigation

56px height, `--canvas` background, 1px `--hairline` bottom border.
Brand name left, search center, user controls right.

### Sidebar

`--surface` background, 1px `--hairline` right border.
Section headers: 12px, `--body` text, uppercase.
Nav items: 36px height, 6px border radius.

## Do's and Don'ts

### Do
- Reserve `--primary` (Warmy Orange) for primary CTAs and active nav items.
- Use the warm cream `--canvas` page floor — never pure white or cool gray.
- Render every code surface in JetBrains Mono.
- Use hairlines for all depth — no shadows.
- Keep semantic colors warm and restrained.

### Don't
- Don't introduce a secondary brand action color. Warmy Orange is the only one.
- Don't add drop shadows to any component.
- Don't use gradient backgrounds or glass morphism.
- Don't use box-shadow for focus rings — use `ring` (outline-based).
- Don't hardcode colors — always reference `var(--token)`.
- Don't use `--primary` on non-interactive decorative elements.

## Responsive Behavior

| Name | Width | Key Changes |
|---|---|---|
| Mobile | < 640px | Sidebar collapses to icon-only; single-column layouts |
| Narrow | 640–1024px | Sidebar collapses; content padding reduces |
| Desktop | 1024–1280px | Full sidebar; content area 32px padding |
| Wide | > 1280px | Content max-width 1200px |

## CSS Token Reference

### Custom Properties

```css
/* === Surface === */
--canvas           /* page background */
--canvas-soft      /* hover / secondary background */
--surface          /* card / dialog / input background */
--surface-strong   /* badge default / separator */

/* === Hairlines === */
--hairline         /* default 1px border */
--hairline-soft    /* lighter border */
--hairline-strong  /* emphasis border */

/* === Text === */
--ink              /* default text */
--body             /* secondary text / descriptions */
--muted            /* tertiary / labels */
--muted-soft       /* placeholder / disabled */

/* === Brand === */
--primary          /* CTA / active state */
--primary-active   /* press state */
--primary-subtle   /* selected background */

/* === Semantic === */
--success / --success-subtle
--warning / --warning-subtle
--danger  / --danger-subtle

/* === Misc === */
--focus-ring       /* focus outline */
--overlay          /* dialog backdrop */
--code-font        /* JetBrains Mono */
--font-sans        /* Inter */

/* === Radius === */
--radius-sm   /* 6px */
--radius-md   /* 8px — buttons, inputs */
--radius-lg   /* 12px — cards, dialogs */
--radius-pill /* 9999px — badges */

/* === Typography (as Tailwind-compatible classes) === */
/* see tokens.css for full @theme definitions */
```
