# GLM Coding Style Frontend Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the complete web application into a GLM Coding-inspired, high-density professional test workspace with consistent light, dark, and system themes while preserving routes, permissions, APIs, and business behavior.

**Architecture:** Keep feature boundaries and generated-client data flow unchanged. Put all visual decisions in semantic CSS tokens and shared UI/layout primitives, then migrate screens through the shared shell and three page patterns so feature pages do not acquire bespoke product colors or duplicated controls.

**Tech Stack:** Next.js 16 App Router, React 19, TypeScript 6 strict, Tailwind CSS 4, Radix UI, Lucide, Vitest/Testing Library, Playwright.

---

## Task 1: Establish the redesign contract and baseline

- [x] Record the approved design specification and unique repository task.
- [x] Create `codex/glm-coding-frontend-redesign` from a clean `main` checkout.
- [x] Add failing contract tests for GLM semantic tokens, grouped navigation, command palette, and three-state theme behavior.
- [x] Run the current frontend test, type, and build baseline and record any pre-existing failure.

## Task 2: Replace the visual foundation

- [x] Replace Apple/blue product tokens with GLM-inspired neutral/coral light and dark semantic tokens.
- [x] Add explicit density, typography, focus, layer, motion, shadow, and workspace layout tokens.
- [x] Add a pre-hydration theme resolver for `light`, `dark`, and `system`, including system-change handling and `color-scheme`.
- [x] Restyle Button, Input, Select/Dropdown, Badge, Table, Dialog, Drawer, EmptyState, cards, links, and feedback surfaces through tokens.
- [x] Consolidate duplicate visual rules without making shared UI depend on feature modules.

## Task 3: Rebuild the application shell

- [x] Replace flat colored-icon navigation with grouped monochrome Lucide navigation and visible active hierarchy.
- [x] Add project context, compact breadcrumb, `Cmd/Ctrl+K` command palette, quick-create menu, run indicator, and existing help/notification/account controls.
- [x] Implement persisted desktop collapse and a true mobile navigation drawer.
- [x] Ensure super-admin navigation remains permission-gated and all routes retain current paths.
- [x] Cover keyboard, focus return, screen-reader names, active state, and reduced motion in component tests.

## Task 4: Apply the three core workspace patterns

- [x] Restyle the Test Agent as history / conversation / plan-evidence workspace with responsive panel behavior.
- [x] Standardize list/detail screens as compact page header / filter toolbar / decision table / detail drawer.
- [x] Standardize run/result screens as summary metrics / result navigation / Trace-evidence-inspection workspace.
- [x] Preserve loading, empty, no-result, permission, error, conflict, and persistent long-task states.

## Task 5: Migrate all core modules

- [x] Apply shared layout and controls to Projects, Overview, Agents, Test Cases, Test Plans, Runs, Environments, Browser Profiles, and Model Configs.
- [x] Apply shared layout and controls to Scorers, Experiments, Reviews, Security, Gates, Users, Account, Help, and authentication surfaces.
- [x] Remove page-level raw product colors and obsolete 3D/colorful navigation styling from active product surfaces.
- [x] Confirm professional test-case forms retain input data, preconditions, ordered steps, step data/expected results, assertions, evidence, execution, and AI/manual editing behavior.

## Task 6: Responsive, accessibility, and visual QA

- [x] Add or update critical Playwright coverage for shell navigation, theme switching, Test Agent, Test Case, Run, and governance routes.
- [x] Check 390/1280/1440/1920 widths with no page-level horizontal overflow or hidden primary actions.
- [x] Check light/dark contrast, keyboard navigation, labels, focus visibility, dialogs/drawers, and reduced-motion behavior.
- [x] Capture representative screenshots for light/dark shell and core workspaces.

## Task 7: Verification and handoff

- [x] Run Prettier, ESLint, TypeScript, all Vitest tests, critical/full Playwright E2E, Next.js build, architecture checks, and bundle budget.
- [x] Run `git diff --check`, inspect the final diff for API/schema/permission drift and unintentional raw colors.
- [x] Update the task ledger with changed modules, exact verification evidence, known limitations, and milestone status.
- [x] Mark this plan and `docs/当前任务.md` complete only after fresh verification succeeds.
- [x] Commit the verified branch with a single scoped implementation commit; do not push unless explicitly requested.
