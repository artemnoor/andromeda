# BMSTU contract-first frontend

This frontend is a small TypeScript/Vite client for the same OpenAPI contract exposed by the backend.

```powershell
cd frontend
npm install
npm run generate-api                 # uses OPENAPI_FILE or http://127.0.0.1:8000/openapi.json
npm run build
npm run check-api-drift              # set OPENAPI_FILE=openapi.json for an offline check
npm run dev
```

With the backend running on port 8000, open:

- `http://localhost:5173/` — two-program comparison;
- `http://localhost:5173/?program=program%3A09.03.01-02` — one program card;
- `http://localhost:5173/?program=program%3A09.03.01-02&view=curriculum` — one curriculum.

`src/api/generated.ts` is generated from `openapi.json`/`/openapi.json`; it is not a hand-maintained DTO copy.
