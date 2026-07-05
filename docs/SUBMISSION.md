# Submission form answers

Copy-paste answers for the hackathon Google Form. Written for the Cognee Cloud track.

**Email**
`ytrohitcrafts@gmail.com`

**Team name** (your name, since solo)
`Rohit`

**Name of the person submitting**
`Rohit`

**Track**
Track 2: Best Use of Cognee Cloud

**Project description**
> Hindsight is a second brain that never wakes up with amnesia. You drop in notes, files, or URLs, and it stores them in Cognee's memory layer as a knowledge graph you can actually see. Ask it anything and it answers by reasoning over the graph instead of matching keywords. Click any node in the graph to ask about that entity directly. Rate its answers and future recalls lean toward what you confirmed. Delete what's stale and watch the nodes drop out live. There's also a one-click Morning After recap that briefs you on everything it remembers, a summary, the most connected entities, and how it's all linked. Tech stack is a React and Vite frontend with a live force directed graph, and a FastAPI backend talking to Cognee Cloud over REST. It's Dockerized, tested, and runs CI on every push. Same code runs against Cognee Cloud, fully self hosted, or in a keyless demo mode.

**GitHub link**
`https://github.com/ROHITCRAFTSYT/hindsight`

**Deployed link**
`https://hindsight-phi.vercel.app`

**YouTube demo link**
Record first using docs/DEMO.md, then paste the link here.

**Describe how you have used Cognee in your project**
> Hindsight is built directly on the Cognee Cloud REST API, and every feature in the UI fires a real Cognee call. Remember posts to /api/v1/remember, where Cognee's pipeline chunks the text, extracts entities, and builds the knowledge graph. Recall hits /api/v1/recall with GRAPH_COMPLETION, and you can switch search types in the UI. Clicking a node in the graph runs an entity scoped recall using Cognee's node_name filter. Thumbs up and down votes are stored as typed Q&A feedback entries through /api/v1/remember/entry, so recall re-weights toward answers I've confirmed. A Memify button re-runs enrichment through /api/v1/cognify. Forget calls /api/v1/forget with the record id. The live graph in the app is Cognee's own data, pulled from /api/v1/datasets/{id}/graph. I also handled the realities of a live cloud tenant: cold start retries, treating content dedup 409s as success instead of errors, and a fallback that deletes records one by one when a bulk wipe fails. All verified end to end against a live tenant, not just demo mode.

**Link to the PR** (this track only, leave for the Cloud track)
`Nil`

**Blog link** (this track only)
`Nil`

**How was your hackathon experience?**
> The best part was that the hard problems were real ones, not toy bugs. Testing against a live Cognee Cloud tenant meant I ran into cold starts, dedup conflicts, and even a corrupted dataset partway through the week, and fixing those taught me more about how Cognee actually works than reading the docs did. Seeing the knowledge graph grow from my own notes for the first time was the moment it clicked. Good theme, good docs, would do this again.

---

## Notes

- The PR/Blog track is a separate submission. Submit the form a second time for it, with your topoteretes/cognee PR links, and put `Nil` in the project description, GitHub, YouTube, and deployed link fields.
- A project can't be entered in both main tracks, so this project goes in the Cloud track only.
