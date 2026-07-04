"""Pydantic request/response models for the Hindsight API."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class RememberRequest(BaseModel):
    data: str = Field(..., description="Text, a file path, or a URL to ingest into memory.")
    dataset: str = Field("main", description="Target dataset name.")
    session_id: Optional[str] = Field(
        None, description="If set, store as fast session memory instead of the permanent graph."
    )
    self_improvement: bool = Field(
        True, description="Run Cognee's enrichment pass automatically after ingestion."
    )


class RememberResponse(BaseModel):
    ok: bool
    dataset: str
    ingested_chars: int
    detail: str
    nodes_added: int = 0


class RecallRequest(BaseModel):
    query: str = Field(..., description="Natural-language question to answer from memory.")
    search_type: Optional[str] = Field(
        None,
        description="Optional Cognee SearchType, e.g. GRAPH_COMPLETION, RAG_COMPLETION, INSIGHTS, CHUNKS.",
    )
    top_k: int = Field(10, ge=1, le=50)
    session_id: Optional[str] = None
    dataset: Optional[str] = None
    node_name: Optional[list[str]] = Field(
        None, description="Scope retrieval to these named graph entities (Cognee node_name filter)."
    )


class RecallSource(BaseModel):
    text: str
    origin: str = "graph"  # session | graph | trace | graph_context


class RecallResponse(BaseModel):
    ok: bool
    query: str
    answer: str
    sources: list[RecallSource] = []
    search_type: str


class ImproveRequest(BaseModel):
    query: str = Field(..., description="The question the feedback is about.")
    answer: str = Field("", description="The answer being rated.")
    vote: Literal["up", "down"] = Field("up", description="Thumbs up/down feedback signal.")
    note: Optional[str] = Field(None, description="Optional free-text correction or note.")


class ImproveResponse(BaseModel):
    ok: bool
    detail: str


class ImproveEnrichRequest(BaseModel):
    dataset: Optional[str] = Field(None, description="Dataset to enrich/Memify. Defaults to the active dataset.")


class ForgetRequest(BaseModel):
    node_id: Optional[str] = Field(
        None, description="Specific memory to forget (a Cognee data_id UUID in cloud mode)."
    )
    dataset: Optional[str] = Field(None, description="Forget an entire dataset.")
    all: bool = Field(False, description="Prune ALL memory (dangerous; demo reset).")


class ForgetResponse(BaseModel):
    ok: bool
    detail: str
    nodes_removed: int = 0


class Memory(BaseModel):
    id: str
    label: str


class MemoriesResponse(BaseModel):
    memories: list[Memory] = []


class RecapEntity(BaseModel):
    label: str
    connections: int


class RecapResponse(BaseModel):
    ok: bool
    summary: str
    top_entities: list[RecapEntity] = []
    memory_count: int
    node_count: int
    edge_count: int
    feedback_count: int
    mode: str


class GraphNode(BaseModel):
    id: str
    label: str
    type: str = "entity"


class GraphEdge(BaseModel):
    source: str
    target: str
    label: str = ""


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class HealthResponse(BaseModel):
    ok: bool
    mode: str  # cloud | local | demo
    cognee_available: bool
    lifecycle_api: bool
    cloud_connected: bool = False
    version: str
