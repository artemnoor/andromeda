# BMSTU contract-first frontend

This frontend is a TypeScript/Vite client for the Andromeda OpenAPI contract. The comparison page loads the real program list, lets the user choose A/B, switches between the full plan and a semester, groups rows by subject block, and displays workload deltas.

The repository-root command below is the supported full-stack fixture smoke: it ingests the captured source into SQLite, starts FastAPI and Vite, verifies `/openapi.json`, loads the frontend, and calls the compare scenario:

```powershell
python backend/scripts/run_tracer_demo.py --mode fixture --check
```

Prerequisites are Python 3.11+, Node.js 22+, npm, and Poppler's `pdftotext` on `PATH`. Use the command without `--check` for a manual local demo, then open `http://127.0.0.1:5173/`.

```powershell
cd frontend
npm install
npm run generate-api                 # uses OPENAPI_FILE or http://127.0.0.1:8000/openapi.json
npm run build
npm run check-api-drift              # set OPENAPI_FILE=openapi.json for an offline check
npm run test:e2e                     # requires the fixture demo to be running
npm run dev
```

With the backend running on port 8000, open:

- `http://localhost:5173/` — selectable two-program comparison;
- `http://localhost:8000/docs` — the backend contract used by the client.

`src/api/generated.ts` is regenerated from `openapi.json`/`/openapi.json`; it is not a hand-maintained DTO copy. The browser does not read parser output or local files.

`src/api/generated.ts` is generated from `openapi.json`/`/openapi.json`; it is not a hand-maintained DTO copy.
