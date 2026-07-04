"""Hindsight FastAPI app — HTTP surface over the Cognee memory lifecycle."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # read backend/.env before the client picks a mode

logging.basicConfig(level=logging.INFO)

from . import __version__  # noqa: E402
from .cognee_client import _COGNEE_IMPORTED, client  # noqa: E402
from .models import (  # noqa: E402
    ForgetRequest,
    ForgetResponse,
    GraphResponse,
    HealthResponse,
    ImproveEnrichRequest,
    ImproveRequest,
    ImproveResponse,
    MemoriesResponse,
    RecallRequest,
    RecallResponse,
    RecapResponse,
    RememberRequest,
    RememberResponse,
)

app = FastAPI(
    title="Hindsight",
    description="An AI second brain on the Cognee memory layer. remember · recall · improve · forget",
    version=__version__,
)

_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    cloud_connected = await client.cloud_ok() if client.is_cloud else False
    return HealthResponse(
        ok=True,
        mode=client.mode,
        cognee_available=_COGNEE_IMPORTED,
        lifecycle_api=client.lifecycle_api,
        cloud_connected=cloud_connected,
        version=__version__,
    )


@app.post("/api/remember", response_model=RememberResponse)
async def remember(req: RememberRequest) -> RememberResponse:
    result = await client.remember(
        data=req.data,
        dataset=req.dataset,
        session_id=req.session_id,
        self_improvement=req.self_improvement,
    )
    return RememberResponse(
        ok=True,
        dataset=req.dataset,
        ingested_chars=len(req.data),
        detail=result["detail"],
        nodes_added=result.get("nodes_added", 0),
    )


@app.post("/api/recall", response_model=RecallResponse)
async def recall(req: RecallRequest) -> RecallResponse:
    result = await client.recall(
        query=req.query,
        search_type=req.search_type,
        top_k=req.top_k,
        session_id=req.session_id,
        dataset=req.dataset,
        node_name=req.node_name,
    )
    return RecallResponse(
        ok=True,
        query=req.query,
        answer=result["answer"],
        sources=result.get("sources", []),
        search_type=result["search_type"],
    )


@app.post("/api/improve", response_model=ImproveResponse)
async def improve(req: ImproveRequest) -> ImproveResponse:
    result = await client.improve(
        query=req.query, answer=req.answer, vote=req.vote, note=req.note
    )
    return ImproveResponse(ok=True, detail=result["detail"])


@app.post("/api/improve/enrich", response_model=ImproveResponse)
async def improve_enrich(req: ImproveEnrichRequest) -> ImproveResponse:
    result = await client.enrich(dataset=req.dataset)
    return ImproveResponse(ok=True, detail=result["detail"])


@app.get("/api/memories", response_model=MemoriesResponse)
async def memories() -> MemoriesResponse:
    return MemoriesResponse(memories=await client.list_memories())


@app.get("/api/recap", response_model=RecapResponse)
async def recap() -> RecapResponse:
    """The Morning-After briefing — a one-shot recap of everything in memory."""
    result = await client.recap()
    return RecapResponse(ok=True, **result)


@app.post("/api/forget", response_model=ForgetResponse)
async def forget(req: ForgetRequest) -> ForgetResponse:
    result = await client.forget(node_id=req.node_id, dataset=req.dataset, all=req.all)
    return ForgetResponse(
        ok=True, detail=result["detail"], nodes_removed=result.get("nodes_removed", 0)
    )


@app.get("/api/graph", response_model=GraphResponse)
async def graph() -> GraphResponse:
    data = await client.get_graph()
    return GraphResponse(nodes=data["nodes"], edges=data["edges"])


@app.get("/")
async def root() -> dict:
    return {
        "name": "Hindsight",
        "tagline": "the AI second brain that never wakes up with amnesia",
        "mode": client.mode,
        "docs": "/docs",
        "lifecycle": ["/api/remember", "/api/recall", "/api/improve", "/api/forget"],
    }
