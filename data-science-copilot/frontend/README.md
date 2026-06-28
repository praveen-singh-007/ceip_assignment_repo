# Frontend — Autonomous Data Science Co-Pilot

Next.js (App Router, TypeScript) UI for the agent. See the [top-level README](../README.md) for
the full picture (architecture, backend setup, the 5 use cases).

## Run

Requires the FastAPI backend running on `http://localhost:8000` (see `../backend`).

```bash
npm install
npm run dev
```

Open http://localhost:3000.

## Structure

- `src/app/page.tsx` — the whole app: dataset panel, tabs (Preview / Data Quality / Ask),
  quick actions, question form, results history.
- `src/components/` — `Header`, `DatasetPanel` (upload + sample picker), `DataTable`,
  `DataQualityPanel`, `QuickActions`, `QuestionForm`, `AnalysisResultCard` (chart + insights +
  result table + report download/preview + attempt trace), `Spinner`.
- `src/lib/api.ts` — fetch wrappers for every backend endpoint.
- `src/lib/types.ts` — TypeScript types mirroring the backend's Pydantic schemas.
- `tailwind.config.ts` — the fixed monochrome color palette (loaded into Tailwind v4 via the
  `@config` directive in `globals.css`). The UI uses only these colors; success/failure states
  are shown with icons/borders/weight, not hue.

## Config

`.env.local`:

```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Scripts

```bash
npm run dev     # dev server
npm run build   # production build (also type-checks)
npm run lint    # eslint
```
