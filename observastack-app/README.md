# observastack-app (monorepo)

App monorepo for ObservaStack: **frontend** (React/TypeScript) + **bff** (FastAPI) + **contracts** + **e2e**.

## Quickstart (dev)
```bash
# Frontend
yarn --version >/dev/null 2>&1 || npm i -g yarn >/dev/null || true
cd frontend && npm i && npm run dev

# BFF
cd ../bff && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --reload
```
