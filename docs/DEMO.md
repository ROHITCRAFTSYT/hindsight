# Demo video guide

Everything you need to record the submission video in one clean take. The narration runs about 2 minutes 50 seconds, which leaves headroom under the 3 minute limit. Spoken lines are in quotes. Say them your way, they are a guide and not a teleprompter.

The form wants the video to cover four things. This script hits all of them in order: what the project is, the tech stack and architecture, a live demo, and what you learned.

## Before you hit record

Record against the local app in Cognee Cloud mode. That shows the real integration, which is the whole point of the Cloud track. The deployed link at https://hindsight-phi.vercel.app is the keyless demo for judges to click later, but its answers are simpler, so it is not what you want on camera.

- Start the backend in cloud mode: `uvicorn app.main:app --port 8000`. Start the frontend: `npm run dev`. Confirm the badge in the top right says "Cognee Cloud".
- Your `.env` is already set to the `vegas_trip` dataset, which is already populated with the Vegas story from testing. So the graph is full the moment you open the app and recall works right away.
- Warm the tenant before recording. Run one recall ("Who rented the car?") and wait for the answer. Cognee Cloud pods sleep when idle and the first request after a nap can be slow or fail once. Waking it up now means it stays warm for the take.
- Have one fresh note on your clipboard so you can show live ingestion: `Sam won 400 dollars at blackjack but lost it all on roulette.`
- Close other tabs, hide bookmarks, and keep your `.env` and terminal off screen.
- Screen record at 1080p. A headset mic beats laptop speakers.

## Shot by shot

| Time | On screen | What you click | The point you are making |
|------|-----------|----------------|--------------------------|
| 0:00 | Full app, graph already populated | nothing, let it breathe | What it is |
| 0:20 | Same | nothing | Tech stack and architecture |
| 0:40 | Remember panel | paste the Sam note, hit Remember | remember(), live graph growth |
| 1:05 | Recall panel | type "Who rented the car?" | recall() reasons over the graph |
| 1:25 | Graph | click the `alex` node, pick "Ask about this" | node_name scoped recall |
| 1:50 | Recall answer | thumbs up, then Memify in the header | improve() feedback and enrichment |
| 2:15 | Forget panel | delete one memory | forget() by record id |
| 2:30 | Header | hit Recap | the morning-after briefing |
| 2:45 | Same | nothing | Learnings and close |

## The narration

**0:00 — What it is**

> "Every AI assistant has the same problem. Close the tab and it forgets everything you told it. This hackathon's theme was an AI that woke up in Vegas with no memory of last night, so I built the opposite. This is Hindsight. It's a second brain that keeps its memory in Cognee, and instead of hiding that memory in a database, it shows it to you as a graph you can watch and query."

**0:20 — Tech stack and architecture**

> "Quick look under the hood. The frontend is React and Vite. The backend is FastAPI, and it talks to Cognee Cloud over its REST API. Every button you're about to see maps to a real Cognee call. There's one integration file that auto-detects whether it's running against Cognee Cloud, a self-hosted Cognee, or a keyless demo mode, so the same code runs three ways. It's Dockerized, it has tests, and CI runs on every push."

**0:40 — Remember**

Paste the Sam note, hit Remember.

> "So let me add a memory. This goes straight to Cognee Cloud, which chunks the text, pulls out the entities, and wires them into the knowledge graph. It takes a moment because there's a real extraction pipeline behind it. While that runs, notice the graph is already full from earlier notes, and each entity is colored by the type Cognee gave it. People, places, events. There's the legend in the corner."

**1:05 — Recall**

Type: *"Who rented the car?"*

> "Now let me ask it something. Who rented the car. And there it is. Alex. It pulled that from one note and connected it across others through the graph. A plain keyword search would have missed that."

**1:25 — Scoped recall**

Click the `alex` node, pick "Ask about this".

> "Here's the part I like most. I can click a node in the graph and ask about it directly. That question is scoped to the Alex entity using Cognee's node_name filter. So the graph isn't just a picture of the memory. It's how you query it."

**1:50 — Improve**

Thumbs up the answer, then hit Memify.

> "If an answer is good, I tell it. That vote is stored as rated feedback so future recalls lean toward what I've confirmed. And this Memify button re-runs Cognee's enrichment over everything, which surfaces connections that weren't in any single note."

**2:15 — Forget**

Delete a memory from the Forget panel.

> "When something's wrong or stale, it goes. This calls Cognee's forget with the record id, and you can watch the nodes drop out of the graph live."

**2:30 — Recap**

Hit the Recap button.

> "And the finale. Recap asks the memory to brief me on everything it knows. A summary, the most connected people and things, the counts. The theme was a hangover, so of course it needed a morning-after report."

**2:45 — Learnings and close**

> "The biggest thing I learned was that building on a live memory layer means dealing with real edge cases. Cold starts, duplicate handling, a tenant that got into a bad state mid-week. Fixing those taught me how Cognee actually works far better than the docs did. It's open source and MIT licensed. Thanks for watching."

## If something goes wrong on camera

- Recall comes back empty or errors once: the tenant went cold. Wait five seconds and ask again, it retries on its own. This is why you warm it up first.
- Ingestion hangs past 30 seconds: stop the take, run the query once in the terminal to confirm the tenant is up, then restart the take.
- Worst case: record against https://hindsight-phi.vercel.app instead. It's seeded and instant. The answers are simpler but nothing will fail live.

## YouTube title

Pick one:

- Hindsight: an AI second brain that never wakes up with amnesia (Cognee hackathon)
- Building a second brain you can watch, on Cognee Cloud

## YouTube description

```
Hindsight is an AI second brain built on Cognee's memory layer for the WeMakeDevs x Cognee "Hangover Part AI" hackathon.

Drop in notes, files, or URLs and Hindsight stores them in Cognee as a knowledge graph you can actually see. Ask it anything and it answers by reasoning over the graph instead of matching keywords. Click a node to ask about that entity directly. Rate answers to shape future recalls. Delete what's stale and watch the graph shrink. And a one-click "Morning After" recap briefs you on everything it remembers.

Every feature maps to a real Cognee Cloud call: remember, recall, feedback entries, cognify, forget, and the dataset graph export.

Tech stack: React + Vite frontend, FastAPI backend, Cognee Cloud over REST. Runs against Cognee Cloud, self-hosted, or a keyless demo mode. Dockerized, tested, CI on every push.

Live demo (keyless): https://hindsight-phi.vercel.app
Code (MIT): https://github.com/ROHITCRAFTSYT/hindsight

Built with Cognee. https://www.cognee.ai
```

## How this maps to the judging criteria

| Criterion | Where it shows up |
|-----------|-------------------|
| Impact | A personal memory tool people would actually use; the pattern works for any agent that needs memory across sessions. |
| Creativity | The memory is visible. Most memory demos are a chat box; this one shows the graph growing, shrinking, and being queried directly. |
| Technical | FastAPI + React, three runtime modes, cold-start retries, dedup handling, tests and CI. Recap and node-scoped recall combine recall, graph analytics, and the node_name filter rather than wrapping a single endpoint. |
| Use of Cognee's APIs | remember, recall, remember/entry feedback, cognify, forget, and the dataset graph export all fire from user actions during the demo. |
| UX | One screen, four lifecycle actions, a live graph. Nothing buried in a settings page. |
| Presentation | This script, the blog post, and the README with an animated demo. |

## One-liner

> Hindsight: a second brain on Cognee that never wakes up with amnesia.
