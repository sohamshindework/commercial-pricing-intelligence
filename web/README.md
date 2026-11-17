# Commercial Analytics & Pricing Strategy — web frontend

React + TypeScript + Vite frontend with two explicit data modes. Local mode renders
typed FastAPI responses over the read-only DuckDB warehouse. Portfolio-demo mode
renders deterministic, precomputed aggregate responses and makes no backend call.

## Develop

Start the backend (from the repo root, with the pipeline already run):

```bash
.venv/bin/uvicorn api.main:app --reload --port 8000
```

Then the frontend:

```bash
cd web
npm install
npm run dev        # http://localhost:5173 (proxies /api to :8000)
```

## Checks

```bash
npm run lint
npm run typecheck
npm run test
npm run build
npm run build:demo
```

## Verified static demo

From the repository root, after rebuilding the full analytical pipeline:

```bash
python scripts/export_static_demo.py
cd web && npm ci && npm run build:demo
cd .. && python scripts/check_static_artifact.py web/dist
cd web && npm run preview:demo
```

The demo snapshot is aggregate-only. Market/family filtering, pagination, analytical
lenses and the 5-point pricing-scenario sliders are precomputed exactly. Date inputs
are disabled with an explanation because fine-grained public data is intentionally
excluded. `vercel.json` documents a future static-host configuration; it does not
deploy the project.

## Notes

- Design system: ivory canvas, iris primary, lavender / terracotta / sage
  accents; Plus Jakarta Sans (headings) + DM Sans (body), tabular numerals.
- `VITE_API_BASE` sets the backend origin for local/API production builds; no secrets
  are bundled. `.env.demo` selects static mode for `build:demo`.
- All five routes use verified historical results. The static build has no raw data,
  customer records, transaction rows, backend, warehouse or third-party tracking.
