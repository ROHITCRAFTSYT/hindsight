"""Seed Hindsight with a fun, on-theme demo memory.

Run with:  python -m app.seed

Works in any mode. In demo mode it populates the in-memory graph so the UI has
something to show immediately; in cloud/local mode it ingests into real Cognee.
"""

from __future__ import annotations

import asyncio

from dotenv import load_dotenv

load_dotenv()

from .cognee_client import client  # noqa: E402

# An on-theme "what happened in Vegas" memory the copilot can reconstruct.
DEMO_NOTES = [
    "Hindsight is an AI second brain built on Cognee's memory layer for the "
    "WeMakeDevs hackathon. It demonstrates remember, recall, improve, and forget.",
    "On Friday night the team landed in Las Vegas and checked into The Mirage. "
    "Priya booked the rooms and Alex rented a red convertible.",
    "Cognee converts text, files, and URLs into a hybrid graph and vector memory. "
    "remember() ingests data, recall() answers questions, improve() enriches memory.",
    "At the blackjack table, Sam won 400 dollars but later lost it on roulette. "
    "Priya kept the receipt from the Bellagio fountain show.",
    "The hackathon prize for Best Use of Cognee Cloud is an Apple iPhone 17 per team member. "
    "Use code COGNEE-35 to redeem the free Cognee Cloud developer plan.",
    "Knowledge graphs link entities by relationships, so recall can reason over connections "
    "instead of just matching keywords. This is why Hindsight never wakes up with amnesia.",
]


async def main() -> None:
    print(f"Seeding Hindsight memory in '{client.mode}' mode…")
    for i, note in enumerate(DEMO_NOTES, 1):
        result = await client.remember(note, dataset="vegas_trip")
        print(f"  [{i}/{len(DEMO_NOTES)}] {result['detail']} (+{result.get('nodes_added', 0)} nodes)")

    graph = await client.get_graph()
    print(f"\nMemory graph now has {len(graph['nodes'])} nodes and {len(graph['edges'])} edges.")

    print("\nTry a recall:")
    answer = await client.recall("What happened in Vegas and who was there?")
    print("  Q: What happened in Vegas and who was there?")
    print(f"  A: {answer['answer'][:300]}")
    print("\nDone. Start the API with: uvicorn app.main:app --reload")


if __name__ == "__main__":
    asyncio.run(main())
