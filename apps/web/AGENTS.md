# Web Application Instructions

Read the repository root `AGENTS.md` first.

## Commands

```bash
pnpm --filter @warmy/web lint
pnpm --filter @warmy/web typecheck
pnpm --filter @warmy/web test
pnpm --filter @warmy/web build
```

## Boundaries

- Features expose public imports from their `index.ts`.
- Do not import another feature's internal files.
- Pages compose features and do not contain business rules.
- Shared UI components do not depend on feature modules.
- Server data uses the generated API Client and TanStack Query.

## UI Quality

- Use semantic design tokens; do not add raw product colors in pages.
- Every asynchronous screen defines loading, empty, error and permission states.
- Interactive controls support keyboard focus and accessible names.
- New shared components require tests and usage examples.
