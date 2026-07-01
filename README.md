# 🧠 Hindsight — the AI second brain that never wakes up with amnesia

> Built for **"The Hangover Part AI: Where's My Context?"** — the Cognee × WeMakeDevs hackathon (Jun 29 – Jul 5, 2026).
> Theme: *Your AI woke up in Vegas with no memory of last night. Build AI that doesn't forget.*

Hindsight is a **second-brain copilot** powered by [Cognee](https://www.cognee.ai)'s memory layer. Throw in your
notes, files, and URLs — Hindsight ingests them into a **hybrid graph + vector memory**, lets you **ask anything in
natural language**, **learns from your feedback**, and **forgets** what's stale. And it shows you the living
**knowledge graph** it builds in real time, so you can literally *see* your AI remembering.

It exercises the entire Cognee memory lifecycle, which is exactly what the hackathon asks for:

| Lifecycle | Cognee Cloud endpoint | In Hindsight |
|-----------|-----------|--------------|
| 🟢 **Remember** | `POST /api/v1/remember` | Ingest panel — drop text, files, or URLs into memory |
| 🔵 **Recall**   | `POST /api/v1/recall`   | Ask-anything chat over your knowledge graph |
| 🟣 **Improve**  | `POST /api/v1/remember/entry` (👍/👎 typed feedback) · `POST /api/v1/improve` ("Memify" enrichment) | Vote on answers to re-weight memory; Memify button enriches the whole graph |
| 🔴 **Forget**   | `POST /api/v1/forget`   | Prune a memory by `data_id`, or wipe everything, with one click |

In **Cognee Cloud** mode, Hindsight calls the Cognee Cloud REST API directly (`X-Api-Key`
auth) — the same contract the Cognee SDK's `CloudClient` uses. The live knowledge-graph
visualization is fetched from `GET /api/v1/datasets/{id}/graph`. In **self-hosted** mode it
calls the embedded Cognee Python SDK (`remember`/`recall`/`improve`/`forget`) instead.

---

## ✨ Why it can win

- **Effective use of Cognee's memory APIs** — all four lifecycle ops are first-class UI actions, not buried calls.
- **Killer demo** — a live, force-directed **knowledge-graph visualization** that grows as you remember and shrinks as you forget.
- **Impact** — a genuinely useful personal knowledge tool, not a toy.
- **Polish** — neon "Vegas" theme that leans into the hangover narrative without being a gimmick.
- **Runs anywhere** — points at **Cognee Cloud** by default (this hackathon's Cloud track) but also runs fully self-hosted, and ships a **zero-key DEMO_MODE** so judges can click around instantly.

---

## 🏗️ Architecture

```
┌─────────────┐     HTTP/JSON      ┌──────────────────┐     Cognee SDK     ┌────────────────┐
│  React UI    │  ───────────────►  │  FastAPI backend │  ───────────────►  │  Cognee memory  │
│  (Vite)      │                    │  app/main.py     │                    │  Cloud or local │
│  graph viz   │  ◄───────────────  │  cognee_client   │  ◄───────────────  │  graph + vector │
└─────────────┘   nodes / edges     └──────────────────┘     results        └────────────────┘
```

- **`backend/`** — FastAPI service wrapping the Cognee lifecycle (`remember` / `recall` / `improve` / `forget`)
  plus a `/graph` endpoint that exports nodes & edges for visualization. Falls back from the new lifecycle API
  to the legacy `add` / `cognify` / `search` API automatically, and to an in-memory **DEMO_MODE** when no keys are set.
- **`frontend/`** — Vite + React app: ingest panel, recall chat, live knowledge-graph canvas, and memory management.

---

## 🚀 Quickstart

### 0. Prerequisites
- Python 3.10–3.14 (tested on 3.11)
- Node 18+ / npm

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:  .venv\Scripts\activate
# macOS/Linux:  source .venv/bin/activate
pip install -r requirements.txt
cp ../.env.example .env   # then edit .env
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for the interactive API.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173.

### 3. (Optional) Seed the demo

```bash
cd backend
python -m app.seed
```

---

## 🔑 Configuration (`.env`)

Hindsight works in three modes, controlled by `.env`. See [`.env.example`](.env.example).

**A) Cognee Cloud (this hackathon's Cloud track — recommended)**
1. Sign up at https://platform.cognee.ai and redeem the free Developer plan with code **`COGNEE-35`**.
2. Create an API key and set:
   ```env
   COGNEE_CLOUD_API_KEY=your_cloud_key
   COGNEE_SERVICE_URL=https://api.cognee.ai   # confirm the host shown in your dashboard
   ```
   Hindsight talks to the Cognee Cloud REST API directly (`X-Api-Key`).

**B) Self-hosted / open source** — runs Cognee embedded (SQLite + LanceDB), only needs an LLM key
(works with Groq, OpenAI, or any supported provider):
```env
LLM_API_KEY=gsk_...                          # e.g. a Groq key
LLM_PROVIDER=groq
LLM_MODEL=groq/llama-3.3-70b-versatile
```

**C) DEMO_MODE** — zero keys, in-memory mock so judges can explore the UI instantly:
```env
DEMO_MODE=true
```

If no keys are present, Hindsight auto-falls back to DEMO_MODE so the app never hard-crashes on a fresh clone.

---

## 🧩 API surface

| Method | Endpoint        | Lifecycle | Body |
|--------|-----------------|-----------|------|
| POST   | `/api/remember` | remember  | `{ "data": "...", "dataset": "main", "session_id"?: "..." }` |
| POST   | `/api/recall`   | recall    | `{ "query": "...", "search_type"?: "GRAPH_COMPLETION", "top_k"?: 10 }` |
| POST   | `/api/improve`  | improve   | `{ "query": "...", "answer": "...", "vote": "up"\|"down", "note"?: "..." }` |
| POST   | `/api/improve/enrich` | improve | `{ "dataset"?: "main" }` — the "Memify" enrichment pass |
| POST   | `/api/forget`   | forget    | `{ "node_id"?: "<data_id>", "dataset"?: "...", "all"?: false }` |
| GET    | `/api/memories` | —         | `{ memories: [{ id, label }] }` — the Forget panel's list |
| GET    | `/api/graph`    | —         | `{ nodes, edges }` for the live visualization |
| GET    | `/api/health`   | —         | mode + cloud connectivity |

---

## 📦 Repo layout

```
hindsight/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes
│   │   ├── cognee_client.py # Cognee lifecycle wrapper (+ fallbacks + demo)
│   │   ├── models.py        # Pydantic request/response models
│   │   └── seed.py          # demo data loader
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/      # GraphView, RecallPanel, IngestPanel, MemoryPanel
│   └── package.json
├── docs/
│   ├── BLOG.md              # Best Blog track submission
│   └── SOCIAL.md            # Social Media Buzz posts
├── .env.example
└── LICENSE                  # MIT (Open Source track)
```

---

## 🏆 Hackathon checklist

- [x] Uses Cognee's `remember` / `recall` / `improve` / `forget` lifecycle
- [x] Works on **Cognee Cloud** (Cloud track)
- [x] Open-source under MIT (Open Source track)
- [x] Knowledge-graph visualization for the demo
- [x] Blog post (`docs/BLOG.md`) for the Best Blog track
- [x] Social posts (`docs/SOCIAL.md`) for the Social Buzz track

## License

MIT — see [LICENSE](LICENSE).
