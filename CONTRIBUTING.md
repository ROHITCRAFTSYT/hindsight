# Contributing to Hindsight

Thanks for your interest! Hindsight is a small, focused codebase — this guide
gets you productive fast.

## Project layout

```
backend/    FastAPI service (app/) + tests + Dockerfile
frontend/   Vite + React app
docs/       Demo script, blog, social, assets
```

`backend/app/cognee_client.py` is the single integration point with Cognee —
if you're changing how memory works, that's the file.

## Local setup

```bash
# Backend (Python 3.10+)
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp ../.env.example .env      # optional: fill in for cloud/self-hosted, or leave blank for demo
uvicorn app.main:app --reload --port 8000

# Frontend (Node 18+)
cd frontend
npm install
npm run dev
```

No API keys? The app auto-runs in **demo mode** (a zero-dependency in-memory
mock), so you can develop the whole UI offline.

## Before you open a PR

Run the same checks CI runs:

```bash
cd backend && ruff check app tests && DEMO_MODE=true python -m pytest
cd frontend && npm run build
```

- **Style:** ruff (config in `backend/pyproject.toml`, 100-col lines) for Python;
  keep React components small and focused.
- **Tests:** add or update tests in `backend/tests/` for behavior changes. They
  run in demo mode so they need no credentials.
- **Commits:** clear, imperative subject lines ("Add …", "Fix …").

## Reporting issues

Include repro steps, the mode you were in (cloud / self-hosted / demo), and any
backend logs. For cloud issues, note that fresh Cognee Cloud tenants cold-start
and may return transient errors on the first request.
