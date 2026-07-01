# Building an AI that doesn't wake up with amnesia

*How I built Hindsight — a second-brain copilot on Cognee's memory layer — for the "Hangover Part AI" hackathon.*

---

## The problem: every chatbot has a hangover

You know the feeling. You explain your whole project to an AI assistant, it gives you a brilliant answer, and the next morning it remembers *nothing*. New session, blank stare, "Could you give me more context?" It's the Vegas hangover of software: a powerful brain that woke up with no idea what happened last night.

LLMs are stateless by design. We bolt on memory with RAG pipelines — chunk the docs, embed them, stuff the top-k into the prompt — but that's recall without *understanding*. Pure vector search finds text that *looks* similar; it doesn't know that "Priya" booked the rooms and "Alex" rented the car and that both happened "on Friday in Vegas." Relationships get lost in the embedding soup.

That's the gap [Cognee](https://www.cognee.ai) fills, and it's what I built **Hindsight** to show off.

## What Cognee actually does

Cognee is an open-source memory layer for AI agents. Instead of a flat vector index, it builds a **hybrid graph + vector memory**: it ingests your text, files, and URLs, chunks them, extracts entities and the relationships between them, and stores the result as a knowledge graph *alongside* embeddings. When you query, it can reason over connections, not just match strings.

The API is refreshingly small — a four-verb memory lifecycle:

```python
import cognee

# 🟢 remember — ingest into the graph
await cognee.remember("Priya booked the rooms; Alex rented a red convertible in Vegas.")

# 🔵 recall — ask in natural language
answer = await cognee.recall("Who rented the car?")

# 🟣 improve — enrich / weight memory from feedback
await cognee.improve("User confirmed Alex handled transport.")

# 🔴 forget — prune what's stale or wrong
await cognee.forget(dataset_name="old_trip")
```

That maps perfectly onto a human mental model of memory: take something in, recall it, reinforce it, let go of it.

## Hindsight: making the memory visible

A memory API is invisible by nature, and invisible things don't demo well. So the core idea of Hindsight is: **make the AI's memory something you can watch.**

Hindsight is a three-panel second-brain copilot:

- **🟢 Remember** — drop in a note, a file path, or a URL. It goes straight into Cognee.
- **🕸️ Knowledge graph** — a live, force-directed view of the memory. Every time you remember something, new nodes bloom; every time you forget, they vanish. You can literally click a node to forget it.
- **🔵 Recall & 🟣 Improve** — ask anything in natural language. Each answer comes with its sources and a 👍/👎. The vote feeds straight into `improve()` to re-weight memory.

The whole thing is one FastAPI service wrapping the Cognee lifecycle, plus a React front end. The backend endpoints are a thin, honest mapping:

| Endpoint | Cognee call |
|----------|-------------|
| `POST /api/remember` | `cognee.remember()` |
| `POST /api/recall` | `cognee.recall()` |
| `POST /api/improve` | `cognee.improve()` |
| `POST /api/forget` | `cognee.forget()` |
| `GET /api/graph` | graph export for visualization |

## Three lessons from building on Cognee

**1. The graph is the demo.** I almost shipped a plain chat UI. The moment I added the force-directed graph that grows and shrinks as memory changes, the project went from "another RAG bot" to something people *get* in three seconds. If you build on a memory system, surface the memory.

**2. Design for graceful degradation.** Cognee's lifecycle API is new, so I wrote the client to try `remember()`/`recall()` first and fall back to the legacy `add()` + `cognify()` + `search()` path automatically. I also added a zero-key **demo mode** with an in-memory graph, so anyone can clone the repo and click around before wiring up keys. A judge should never hit a blank screen because of a missing env var.

**3. Cloud vs. self-hosted is a one-line switch.** Cognee runs fully embedded (SQLite + LanceDB) for the open-source story, *or* against Cognee Cloud for a managed graph. Hindsight picks its mode from `.env`: set `COGNEE_CLOUD_API_KEY` for Cloud (grab the free Developer plan with code **`COGNEE-35`**), or `LLM_API_KEY` to self-host. Same code path either way.

## Why memory changes how you build agents

Once memory is a first-class primitive, a lot of agent architecture simplifies. You stop hand-rolling conversation buffers and bespoke vector stores. "Remember this," "what do you know about X," "you were wrong, here's the fix," and "forget that" become *API calls*, not infrastructure projects. The agent accumulates a real, queryable model of its world that survives restarts.

That's the whole pitch of Hindsight, and of Cognee: **an AI that doesn't wake up with amnesia.**

## Try it

Hindsight is open source under MIT. Clone it, run the backend and frontend, and either flip on demo mode or point it at Cognee Cloud:

```bash
# backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
# frontend
cd frontend && npm install && npm run dev
```

Then go remember something — and watch your AI keep it.

---

*Built for the WeMakeDevs × Cognee "Hangover Part AI: Where's My Context?" hackathon. Code: [github.com/your-handle/hindsight](#). Powered by [Cognee](https://www.cognee.ai).*
