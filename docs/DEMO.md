# Demo script

Runs about two and a half minutes. Spoken lines are in quotes; say them however feels natural, they're a guide, not a teleprompter.

## Before you hit record

- Backend running in cloud mode (`uvicorn app.main:app --port 8000`), frontend on `npm run dev`. Check the badge says "Cognee Cloud".
- Remember one note ahead of time so the graph isn't empty when you start. An empty canvas is a boring first frame.
- Have your second note ready to paste: `Priya booked the hotel rooms and Alex rented a red convertible in Las Vegas.`
- Know the timing: cloud ingest takes about 20 seconds, recall about 10. The script talks over both waits. Don't stand there in silence.
- If the tenant has been idle, the first request can fail once while it wakes up. The app retries on its own. Click, wait a beat, keep talking.
- Keep `.env` out of frame.

## The script

**0:00 — Hook**

> "Every AI assistant has the same problem: close the tab and it forgets everything. This hackathon's theme is an AI that woke up in Vegas with no memory of last night. So I built the opposite. Hindsight keeps its memory in Cognee, and it shows you that memory as a graph you can actually watch."

Show the app. Don't explain the panels yet, just let it sit on screen.

**0:15 — 🟢 Remember**

Paste the Vegas note, hit Remember.

> "This is going to Cognee Cloud right now. It chunks the text, pulls out the entities, and wires them into a knowledge graph. Takes about twenty seconds because there's a real extraction pipeline behind it, so while that runs..."

Point at the existing graph. Mention the colors: each entity is colored by the type Cognee extracted for it. Person, location, event. The legend is bottom-left. By the time you've said this, the new nodes should be landing.

**0:45 — 🔵 Recall**

Ask: *"Who rented the car?"*

> "Ten seconds or so... and there it is. Alex. It joined my two separate notes through the graph. A plain vector search wouldn't have made that connection."

Now click the `alex` node, pick "Ask about this".

> "This is the part I like. Clicking a node scopes the question to that entity. Cognee has a node_name filter for exactly this, so the graph isn't just a picture. You can query through it."

**1:20 — 🟣 Improve**

Thumbs-up the good answer.

> "That vote gets stored as a rated Q&A entry in the session, and future recalls lean toward answers I've confirmed."

Hit the Memify button.

> "Memify re-runs the enrichment pipeline over the whole dataset. New connections show up that weren't in any single note."

**1:45 — 🔴 Forget**

Delete a memory from the Forget panel.

> "And when something's stale or wrong, it goes. This calls Cognee's forget with the record id. Watch the graph, the nodes drop out."

**2:00 — Recap**

Hit the Recap button.

> "Last thing, and honestly my favorite. Recap asks the memory to brief me on everything it knows. A summary, the most connected entities, the counts. The theme is a hangover, so it needed a morning-after report."

**2:20 — Close**

> "Everything you just saw ran against Cognee Cloud. The same code runs self-hosted with a local LLM, and there's a keyless demo mode if you just want to click around. MIT licensed. Thanks for watching."

## How this maps to the judging criteria

| Criterion | Where it shows up in the demo |
|-----------|-------------------------------|
| Impact | A personal memory tool people would actually use; the same pattern works for any agent that needs memory across sessions. |
| Creativity | The memory is visible. Most memory demos are a chat box; this one shows the graph growing, shrinking, and being queried directly. |
| Technical | FastAPI + React, three runtime modes, cold-start retries, dedup handling, tests and CI. The recap and node-scoped recall aren't wrappers around one endpoint; they combine recall, graph analytics, and the node_name filter. |
| Use of Cognee's APIs | remember, recall, remember/entry (feedback), cognify (Memify), forget, and the dataset graph export all fire from user actions during the demo. |
| UX | One screen, four lifecycle actions, live graph. Nothing is buried in a settings page. |
| Presentation | This script, the blog post, and the README with the animated demo. |

## Track eligibility

- Best Use of Cognee Cloud: the demo runs against a live tenant.
- Best Use of Open Source: MIT licensed, runs fully self-hosted.
- Best Blog: `docs/BLOG.md`.
- Social Buzz: `docs/SOCIAL.md`.

## One-liner

> Hindsight: a second brain on Cognee that never wakes up with amnesia.
