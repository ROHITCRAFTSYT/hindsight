# Hindsight — 2-minute demo script & submission notes

A tight script for the demo video / live judging, plus how the project hits each judging criterion.

---

## The 2-minute demo

**0:00 — The hook (10s)**
> "Your AI woke up in Vegas with no memory of last night. Every assistant has this hangover — great answer now, total amnesia next session. This is Hindsight: an AI second brain that never forgets, built on Cognee's memory layer."

Open the app. Point out the three panels and the mode badge (Cognee Cloud).

**0:10 — 🟢 Remember (25s)**
- Paste 2–3 facts: *"Priya booked the rooms; Alex rented a red convertible in Vegas."* / a URL / a file path.
- **Narrate while the graph reacts:** "Each thing I remember gets chunked, entities extracted, and added to a knowledge graph — watch new nodes appear in real time. This isn't a flat vector index; it's relationships."

**0:35 — 🔵 Recall (30s)**
- Ask: *"Who rented the car, and what else happened in Vegas?"*
- Show the answer + cited sources + the `GRAPH_COMPLETION` search type.
- "It didn't keyword-match — it reasoned over the graph. Notice it connects Alex → car → Vegas → Friday across separate notes."
- Switch the SearchType dropdown to show INSIGHTS / RAG_COMPLETION options.

**1:05 — 🟣 Improve (25s)**
- Hit 👍 on a good answer / 👎 on a weak one. "Each vote is stored as a typed Q&A-with-feedback entry on Cognee Cloud, so the next recall re-weights toward what you confirmed."
- Then hit **Memify ✨** in the header. "This kicks off Cognee's `improve()` enrichment pass over the whole dataset — the graph gets richer, new connections surface."

**1:30 — 🔴 Forget (20s)**
- In the Forget panel, click **forget** on a stale memory (sends its Cognee `data_id` to `forget()`); watch the graph shrink. Or **Wipe all memory** to reset live.
- "Stale or wrong? One click and it's surgically pruned. The graph updates instantly."

**1:45 — The close (15s)**
- "Same code runs on Cognee Cloud or fully self-hosted — one env var. Open source, MIT. Remember, recall, improve, forget — the entire memory lifecycle, made visible. An AI that doesn't wake up with amnesia."

---

## How Hindsight maps to the judging criteria

| Criterion | How Hindsight scores |
|-----------|----------------------|
| **Impact** | A genuinely useful personal-knowledge tool; the pattern generalizes to any agent that needs durable memory. |
| **Creativity & innovation** | Makes an invisible memory API *visible* via a live knowledge graph; leans into the hackathon's hangover narrative. |
| **Technical excellence** | Clean FastAPI + React architecture; defensive client with lifecycle→legacy fallback, cloud/local/demo modes, typed Pydantic models. |
| **Effective use of Cognee's APIs** | All four lifecycle ops (`remember`/`recall`/`improve`/`forget`) are first-class, user-triggered actions — plus the graph export. |
| **UX & polish** | Cohesive neon theme, real-time graph, source citations, toasts, responsive layout, zero-key demo mode. |
| **Presentation** | This script + blog + social kit; the graph-in-motion is the memorable visual. |

## Eligibility checklist

- ✅ **Best Use of Cognee Cloud** — runs against Cognee Cloud (`COGNEE-35` dev plan).
- ✅ **Best Use of Open Source** — MIT licensed; runs fully self-hosted.
- ✅ **Best Blog** — `docs/BLOG.md`.
- ✅ **Social Media Buzz** — `docs/SOCIAL.md`.

## One-line pitch

> **Hindsight** — the AI second brain that never wakes up with amnesia. Remember, recall, improve, forget — made visible, on Cognee.
