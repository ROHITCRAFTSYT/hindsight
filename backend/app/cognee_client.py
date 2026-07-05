"""
Cognee lifecycle wrapper for Hindsight.

This module is the single place that talks to Cognee. It exposes async methods
that mirror the hackathon's required memory lifecycle:

    remember()  ->  POST /api/v1/remember        (cloud) | add+cognify | demo
    recall()    ->  POST /api/v1/recall          (cloud) | search       | demo
    improve()   ->  POST /api/v1/remember/entry  (typed QA feedback)    | demo
                ->  POST /api/v1/improve          (dataset enrichment "Memify")
    forget()    ->  POST /api/v1/forget          (cloud) | prune         | demo

It chooses a mode at import time:

    * "cloud" — COGNEE_CLOUD_API_KEY is set. Hindsight talks to the **Cognee
                Cloud REST API** directly over HTTP (X-Api-Key auth), exactly
                like the SDK's own CloudClient. This is the hackathon Cloud
                track, and it exercises Cognee Cloud's hosted memory engine.
    * "local" — LLM_API_KEY is set (self-hosted, embedded Cognee SDK).
    * "demo"  — no keys / DEMO_MODE=true: a dependency-free in-memory mock so
                the UI is fully clickable without any credentials.

Everything is defensive: if a real Cognee call raises, we log it and the local
mirror graph still updates, so a live demo never hard-crashes.
"""

from __future__ import annotations

import asyncio
import hashlib
import logging
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger("hindsight.cognee")

# ──────────────────────────────────────────────────────────────────────────
# Mode detection
# ──────────────────────────────────────────────────────────────────────────


def _truthy(val: Optional[str]) -> bool:
    return str(val or "").strip().lower() in {"1", "true", "yes", "on"}


# On-theme "what happened in Vegas" memory used to pre-populate DEMO_MODE so the
# public demo is never empty and recall works out of the box.
DEMO_SEED_NOTES = [
    "Hindsight is an AI second brain built on Cognee's memory layer for the "
    "WeMakeDevs hackathon. It demonstrates remember, recall, improve, and forget.",
    "On Friday night the team landed in Las Vegas and checked into The Mirage. "
    "Priya booked the hotel rooms and Alex rented a red convertible.",
    "Cognee converts text, files, and URLs into a hybrid graph and vector memory. "
    "remember ingests data, recall answers questions, improve enriches memory.",
    "At the blackjack table Sam won 400 dollars but later lost it on roulette. "
    "Priya kept the receipt from the Bellagio fountain show.",
    "The prize for Best Use of Cognee Cloud is an Apple iPhone 17 per team member. "
    "Use code COGNEE-35 to redeem the free Cognee Cloud developer plan.",
]


def _cloud_base_url() -> str:
    """Resolve the Cognee Cloud service base URL from the environment."""
    return (
        os.getenv("COGNEE_SERVICE_URL")
        or os.getenv("COGNEE_API_URL")
        or "https://api.cognee.ai"
    ).rstrip("/")


def detect_mode() -> str:
    if _truthy(os.getenv("DEMO_MODE")):
        return "demo"
    if os.getenv("COGNEE_CLOUD_API_KEY"):
        return "cloud"
    if os.getenv("LLM_API_KEY"):
        return "local"
    logger.warning("No COGNEE_CLOUD_API_KEY or LLM_API_KEY found — falling back to DEMO_MODE.")
    return "demo"


# Try to import the embedded cognee SDK; only needed for "local" mode.
try:  # pragma: no cover - depends on environment
    import cognee  # type: ignore

    _COGNEE_IMPORTED = True
except Exception as exc:  # noqa: BLE001
    cognee = None  # type: ignore
    _COGNEE_IMPORTED = False
    logger.info("cognee package not importable (%s); cloud/demo modes still available.", exc)

# httpx powers the cloud transport (it is always installed; see requirements.txt).
try:
    import httpx  # type: ignore

    _HTTPX = True
except Exception:  # noqa: BLE001
    httpx = None  # type: ignore
    _HTTPX = False


def _search_type(name: Optional[str]):
    """Resolve a SearchType enum by name (local SDK mode), default GRAPH_COMPLETION."""
    if not _COGNEE_IMPORTED:
        return None
    try:
        from cognee.modules.search.types import SearchType  # type: ignore
    except Exception:  # noqa: BLE001
        try:
            from cognee import SearchType  # type: ignore
        except Exception:  # noqa: BLE001
            return None
    target = (name or "GRAPH_COMPLETION").upper()
    return getattr(SearchType, target, getattr(SearchType, "GRAPH_COMPLETION", None))


# ──────────────────────────────────────────────────────────────────────────
# Cognee Cloud REST transport
#
# Mirrors cognee/api/v1/serve/cloud_client.py byte-for-byte on the wire:
#   auth header  X-Api-Key
#   remember     POST /api/v1/remember        (multipart: datasetName + data file)
#   entry        POST /api/v1/remember/entry  (json: typed MemoryEntry)
#   recall       POST /api/v1/recall          (json)
#   improve      POST /api/v1/improve         (json: dataset_name | dataset_id)
#   forget       POST /api/v1/forget          (json: data_id | dataset | everything)
#   datasets     GET  /api/v1/datasets
#   graph        GET  /api/v1/datasets/{id}/graph
#   data         GET  /api/v1/datasets/{id}/data
#   health       GET  /health
# ──────────────────────────────────────────────────────────────────────────


_COLD_START_RETRY = 3
_GATEWAY_STATUSES = {502, 503, 504}


class CloudTransport:
    def __init__(self, base_url: str, api_key: str) -> None:
        self.base = base_url.rstrip("/")
        self.api_key = api_key
        self.headers = {"X-Api-Key": api_key}

    def _client(self, timeout: float = 120.0):
        # follow_redirects handles FastAPI's trailing-slash 307s (which preserve
        # method + body on POST).
        return httpx.AsyncClient(
            base_url=self.base, headers=self.headers, timeout=timeout, follow_redirects=True
        )

    async def _send(self, method: str, path: str, *, idempotent: bool = False,
                    timeout: float = 120.0, **kw):
        """Send a request, retrying through Cognee Cloud cold-starts.

        Freshly-woken tenants transiently return nginx 404s (upstream not up
        yet); idempotent reads also retry gateway 5xx. Backs off between tries.
        """
        delay = 1.2
        last: Any = None
        for attempt in range(_COLD_START_RETRY):
            try:
                async with self._client(timeout=timeout) as c:
                    resp = await c.request(method, path, **kw)
            except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout,
                    httpx.ReadError) as exc:
                last = exc
                if attempt < _COLD_START_RETRY - 1:
                    await asyncio.sleep(delay)
                    delay *= 1.7
                    continue
                raise
            retriable = resp.status_code == 404 or (
                idempotent and resp.status_code in _GATEWAY_STATUSES
            )
            if retriable and attempt < _COLD_START_RETRY - 1:
                logger.info("Cloud %s %s -> %s; retrying (cold start).", method, path, resp.status_code)
                await asyncio.sleep(delay)
                delay *= 1.7
                continue
            resp.raise_for_status()
            return resp
        if last:
            raise last
        return resp  # pragma: no cover

    async def health(self) -> bool:
        try:
            resp = await self._send("GET", "/api/health", idempotent=True, timeout=15.0)
            return resp.status_code < 400
        except Exception as exc:  # noqa: BLE001
            logger.info("Cloud health probe failed for %s: %s", self.base, exc)
            return False

    async def remember(self, data: str, dataset_name: str, session_id: Optional[str] = None) -> dict:
        form: dict[str, Any] = {"datasetName": dataset_name}
        if session_id:
            form["session_id"] = session_id
        # Pass raw bytes (not BytesIO) so a retry can re-send the body.
        files = {"data": ("data.txt", data.encode("utf-8"), "text/plain")}
        resp = await self._send("POST", "/api/v1/remember", data=form, files=files)
        return _safe_json(resp)

    async def remember_entry(
        self, entry: dict, dataset_name: str, session_id: Optional[str] = None
    ) -> dict:
        payload = {
            "entry": entry,
            "dataset_name": dataset_name,
            "session_id": session_id,
            "skill_improvement": None,
        }
        resp = await self._send("POST", "/api/v1/remember/entry", json=payload)
        return _safe_json(resp)

    async def recall(
        self,
        query_text: str,
        search_type: Optional[str] = None,
        top_k: int = 10,
        datasets: Optional[list[str]] = None,
        session_id: Optional[str] = None,
        node_name: Optional[list[str]] = None,
    ) -> Any:
        payload: dict[str, Any] = {"query": query_text}
        if search_type:
            payload["search_type"] = search_type
        if datasets:
            payload["datasets"] = datasets
        if top_k:
            payload["top_k"] = top_k
        if session_id:
            payload["session_id"] = session_id
        if node_name:
            # Scope retrieval to specific named graph entities.
            payload["node_name"] = node_name
        resp = await self._send("POST", "/api/v1/recall", json=payload)
        return _safe_json(resp)

    async def cognify(self, datasets: Optional[list[str]] = None) -> dict:
        """POST /api/v1/cognify — (re)build & enrich the knowledge graph."""
        payload: dict[str, Any] = {}
        if datasets:
            payload["datasets"] = datasets
        resp = await self._send("POST", "/api/v1/cognify", json=payload, timeout=300.0)
        return _safe_json(resp)

    async def forget(
        self,
        data_id: Optional[str] = None,
        dataset: Optional[str] = None,
        dataset_id: Optional[str] = None,
        everything: bool = False,
        memory_only: bool = False,
    ) -> dict:
        # NB: this Cognee Cloud build's forget DTO uses camelCase field names.
        payload: dict[str, Any] = {}
        if everything:
            payload["everything"] = True
        if dataset:
            payload["dataset"] = str(dataset)
        if dataset_id:
            payload["datasetId"] = str(dataset_id)
        if data_id:
            payload["dataId"] = str(data_id)
        if memory_only:
            payload["memoryOnly"] = True
        resp = await self._send("POST", "/api/v1/forget", json=payload)
        return _safe_json(resp)

    async def list_datasets(self) -> list[dict]:
        resp = await self._send("GET", "/api/v1/datasets", idempotent=True, timeout=30.0)
        data = _safe_json(resp)
        return data if isinstance(data, list) else data.get("datasets", [])

    async def dataset_graph(self, dataset_id: str) -> dict:
        resp = await self._send(
            "GET", f"/api/v1/datasets/{dataset_id}/graph", idempotent=True, timeout=60.0
        )
        return _safe_json(resp)

    async def dataset_data(self, dataset_id: str) -> list[dict]:
        resp = await self._send(
            "GET", f"/api/v1/datasets/{dataset_id}/data", idempotent=True, timeout=30.0
        )
        data = _safe_json(resp)
        return data if isinstance(data, list) else []

    async def data_raw(self, dataset_id: str, data_id: str) -> str:
        """Fetch a data record's raw text — used to label memories meaningfully."""
        resp = await self._send(
            "GET", f"/api/v1/datasets/{dataset_id}/data/{data_id}/raw",
            idempotent=True, timeout=30.0,
        )
        return resp.text


def _safe_json(resp) -> Any:
    try:
        return resp.json()
    except Exception:  # noqa: BLE001
        return {"detail": resp.text}


# ──────────────────────────────────────────────────────────────────────────
# In-memory graph (powers DEMO_MODE and an optimistic visualization mirror)
# ──────────────────────────────────────────────────────────────────────────

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "at", "for",
    "with", "is", "are", "was", "were", "be", "been", "this", "that", "these",
    "those", "it", "its", "as", "by", "from", "into", "about", "over", "after",
    "i", "you", "he", "she", "they", "we", "my", "your", "their", "our",
}


def _extract_entities(text: str, limit: int = 6) -> list[str]:
    """Tiny heuristic entity extractor for the demo/mirror graph."""
    entities: list[str] = []
    for match in re.findall(r"\b([A-Z][a-zA-Z0-9]+(?:\s+[A-Z][a-zA-Z0-9]+)*)\b", text):
        phrase = match.strip()
        if phrase.lower() not in _STOPWORDS and phrase not in entities:
            entities.append(phrase)
    if len(entities) < 2:
        words = [w.lower() for w in re.findall(r"\b[a-zA-Z]{4,}\b", text)]
        freq: dict[str, int] = {}
        for w in words:
            if w not in _STOPWORDS:
                freq[w] = freq.get(w, 0) + 1
        for w, _ in sorted(freq.items(), key=lambda kv: -kv[1]):
            if w.capitalize() not in entities:
                entities.append(w.capitalize())
            if len(entities) >= limit:
                break
    return entities[:limit]


@dataclass
class MemoryGraph:
    """A minimal nodes/edges store used for demo mode and graph fallback."""

    nodes: dict[str, dict] = field(default_factory=dict)
    edges: list[dict] = field(default_factory=list)
    feedback: list[dict] = field(default_factory=list)

    def add_document(self, text: str, dataset: str = "main") -> int:
        snippet = text.strip().replace("\n", " ")
        # Content-hashed id: deterministic across processes, so seeded demo
        # memories get the same ids on every serverless instance (and re-adding
        # the same text is idempotent rather than duplicating).
        doc_id = "doc:" + hashlib.sha1(snippet.encode("utf-8")).hexdigest()[:10]
        if doc_id in self.nodes:
            return 0
        self.nodes[doc_id] = {
            "id": doc_id,
            "label": (snippet[:40] + "…") if len(snippet) > 40 else snippet or "memory",
            "type": "document",
            "dataset": dataset,
            "text": snippet,
        }
        added = 1
        for ent in _extract_entities(text):
            ent_id = f"ent:{ent.lower()}"
            if ent_id not in self.nodes:
                self.nodes[ent_id] = {"id": ent_id, "label": ent, "type": "entity"}
                added += 1
            self.edges.append({"source": doc_id, "target": ent_id, "label": "mentions"})
        return added

    def forget_node(self, node_id: str) -> int:
        removed = 0
        if node_id in self.nodes:
            del self.nodes[node_id]
            removed += 1
        before = len(self.edges)
        self.edges = [e for e in self.edges if e["source"] != node_id and e["target"] != node_id]
        connected = {e["source"] for e in self.edges} | {e["target"] for e in self.edges}
        for nid in list(self.nodes):
            if self.nodes[nid]["type"] == "entity" and nid not in connected:
                del self.nodes[nid]
                removed += 1
        removed += before - len(self.edges)
        return removed

    def forget_dataset(self, dataset: str) -> int:
        doomed = [nid for nid, n in self.nodes.items() if n.get("dataset") == dataset]
        removed = 0
        for nid in doomed:
            removed += self.forget_node(nid)
        return removed

    def clear(self) -> int:
        n = len(self.nodes)
        self.nodes.clear()
        self.edges.clear()
        return n

    def documents(self) -> list[dict]:
        return [
            {"id": n["id"], "label": n["label"]}
            for n in self.nodes.values()
            if n["type"] == "document"
        ]

    def naive_recall(self, query: str, top_k: int = 10) -> tuple[str, list[dict]]:
        """Keyword overlap search used only in demo mode."""
        q_terms = {w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", query)}
        scored: list[tuple[int, dict]] = []
        for n in self.nodes.values():
            if n["type"] != "document":
                continue
            text = n.get("text", "")
            terms = {w.lower() for w in re.findall(r"\b[a-zA-Z]{3,}\b", text)}
            overlap = len(q_terms & terms)
            if overlap:
                scored.append((overlap, n))
        scored.sort(key=lambda s: -s[0])
        hits = [n for _, n in scored[:top_k]]
        if hits:
            joined = " ".join(h["text"] for h in hits[:3])
            answer = (
                f"Based on what I remember: {joined[:400]}"
                + ("…" if len(joined) > 400 else "")
            )
        else:
            answer = (
                "I don't have anything in memory about that yet. Try remembering some "
                "notes, files, or URLs first."
            )
        sources = [{"text": h["text"][:200], "origin": "graph"} for h in hits]
        return answer, sources


# ──────────────────────────────────────────────────────────────────────────
# The client
# ──────────────────────────────────────────────────────────────────────────


class CogneeClient:
    def __init__(self) -> None:
        self.mode = detect_mode()
        self.graph = MemoryGraph()
        self.default_dataset = os.getenv("DEFAULT_DATASET", "main")
        # Stable session id for this server run — links recalls to their
        # feedback so Cognee Cloud can re-weight future answers.
        self.session_id = f"hindsight-{uuid.uuid4().hex[:8]}"
        self.lifecycle_api = bool(_COGNEE_IMPORTED and hasattr(cognee, "remember"))
        self._configured = False
        # Resolved dataset name -> dataset_id (UUID) cache for cloud mode.
        self._dataset_ids: dict[str, str] = {}
        # data_id -> human label cache (avoids refetching raw content).
        self._label_cache: dict[str, str] = {}

        self.cloud: Optional[CloudTransport] = None
        if self.mode == "cloud":
            if not _HTTPX:
                logger.error("httpx is required for cloud mode but is not installed.")
            else:
                self.cloud = CloudTransport(_cloud_base_url(), os.getenv("COGNEE_CLOUD_API_KEY", ""))

        # Demo mode has no backing store, and on serverless each request may hit
        # a fresh process. Seeding at construction gives every instance the same
        # populated graph, so recall/recap/graph are consistent everywhere.
        if self.mode == "demo" and not _truthy(os.getenv("DEMO_NO_SEED")):
            for note in DEMO_SEED_NOTES:
                self.graph.add_document(note, dataset=self.default_dataset)

        logger.info(
            "Hindsight memory mode=%s | cloud_url=%s | cognee_imported=%s | lifecycle_api=%s",
            self.mode,
            _cloud_base_url() if self.mode == "cloud" else "-",
            _COGNEE_IMPORTED,
            self.lifecycle_api,
        )

    # -- config (local SDK only) -----------------------------------------
    def _ensure_configured(self) -> None:
        if self._configured or self.mode != "local" or not _COGNEE_IMPORTED:
            return
        self._configured = True  # local SDK reads LLM_* straight from env

    @property
    def is_cloud(self) -> bool:
        return self.mode == "cloud" and self.cloud is not None

    @property
    def is_local(self) -> bool:
        return self.mode == "local" and _COGNEE_IMPORTED

    @property
    def is_real(self) -> bool:
        return self.is_cloud or self.is_local

    async def cloud_ok(self) -> bool:
        return bool(self.cloud and await self.cloud.health())

    # -- dataset id resolution (cloud) -----------------------------------
    async def _resolve_dataset_id(self, name: str) -> Optional[str]:
        if not self.cloud:
            return None
        if name in self._dataset_ids:
            return self._dataset_ids[name]
        try:
            for ds in await self.cloud.list_datasets():
                ds_name = ds.get("name")
                ds_id = ds.get("id")
                if ds_name and ds_id:
                    self._dataset_ids[ds_name] = str(ds_id)
            return self._dataset_ids.get(name)
        except Exception as exc:  # noqa: BLE001
            logger.info("Could not resolve dataset id for '%s': %s", name, exc)
            return None

    # -- remember ---------------------------------------------------------
    async def remember(
        self, data: str, dataset: str = "main", session_id: Optional[str] = None,
        self_improvement: bool = True,
    ) -> dict:
        # Always update the optimistic mirror so the UI reflects state instantly.
        nodes_added = self.graph.add_document(data, dataset=dataset)

        if self.is_cloud:
            try:
                resp = await self.cloud.remember(data, dataset_name=dataset, session_id=session_id)
                # Cache the dataset id if the response surfaced it.
                ds_id = _find_id(resp, ("dataset_id", "datasetId"))
                if ds_id:
                    self._dataset_ids[dataset] = str(ds_id)
                await self._register_label(dataset, data)
                return {"detail": f"remembered into '{dataset}' on Cognee Cloud", "nodes_added": nodes_added}
            except Exception as exc:  # noqa: BLE001
                # 409 = identical content already in memory (Cognee dedups by
                # hash) — that's idempotent success, not an error. Don't
                # register a label: the matching record is an OLD row, not the
                # newest unlabeled one.
                if _status_code(exc) == 409:
                    return {
                        "detail": f"already remembered in '{dataset}' (deduplicated)",
                        "nodes_added": nodes_added,
                    }
                logger.exception("cloud remember() failed; mirror still updated: %s", exc)
                return {"detail": f"cloud error ({_short(exc)}); kept in local graph", "nodes_added": nodes_added}

        if self.is_local:
            self._ensure_configured()
            try:
                if self.lifecycle_api:
                    kwargs: dict[str, Any] = {"dataset_name": dataset, "self_improvement": self_improvement}
                    if session_id:
                        kwargs["session_id"] = session_id
                    await cognee.remember(data, **kwargs)  # type: ignore
                    return {"detail": f"remembered into '{dataset}' via remember()", "nodes_added": nodes_added}
                await cognee.add(data, dataset_name=dataset)  # type: ignore
                await cognee.cognify([dataset])  # type: ignore
                return {"detail": f"remembered into '{dataset}' via add()+cognify()", "nodes_added": nodes_added}
            except Exception as exc:  # noqa: BLE001
                logger.exception("local remember() failed: %s", exc)
                return {"detail": f"cognee error ({_short(exc)}); kept in local graph", "nodes_added": nodes_added}

        return {"detail": f"[demo] remembered into '{dataset}'", "nodes_added": nodes_added}

    # -- recall -----------------------------------------------------------
    async def recall(
        self, query: str, search_type: Optional[str] = None, top_k: int = 10,
        session_id: Optional[str] = None, dataset: Optional[str] = None,
        node_name: Optional[list[str]] = None,
    ) -> dict:
        effective_type = (search_type or "GRAPH_COMPLETION").upper()
        ds = dataset or self.default_dataset

        if self.is_cloud:
            try:
                results = await self.cloud.recall(
                    query_text=query, search_type=effective_type, top_k=top_k,
                    datasets=[ds], session_id=session_id or self.session_id,
                    node_name=node_name,
                )
                out = _normalize_results(results, effective_type)
                out["search_type"] = f"cloud:{effective_type}"
                return out
            except Exception as exc:  # noqa: BLE001
                logger.exception("cloud recall() failed, using mirror: %s", exc)
                answer, sources = self.graph.naive_recall(query, top_k=top_k)
                return {"answer": answer, "sources": sources, "search_type": f"fallback:{effective_type}"}

        if self.is_local:
            self._ensure_configured()
            try:
                st = _search_type(search_type)
                if self.lifecycle_api:
                    kwargs: dict[str, Any] = {"query_text": query, "top_k": top_k}
                    if st is not None:
                        kwargs["query_type"] = st
                    if session_id:
                        kwargs["session_id"] = session_id
                    if dataset:
                        kwargs["datasets"] = [dataset]
                    if node_name:
                        kwargs["node_name"] = node_name
                    results = await cognee.recall(**kwargs)  # type: ignore
                else:
                    results = await cognee.search(query_type=st, query_text=query)  # type: ignore
                return _normalize_results(results, effective_type)
            except Exception as exc:  # noqa: BLE001
                logger.exception("local recall() failed, using mirror: %s", exc)
                answer, sources = self.graph.naive_recall(query, top_k=top_k)
                return {"answer": answer, "sources": sources, "search_type": f"fallback:{effective_type}"}

        answer, sources = self.graph.naive_recall(query, top_k=top_k)
        return {"answer": answer, "sources": sources, "search_type": f"demo:{effective_type}"}

    # -- improve (per-answer 👍/👎 feedback) -----------------------------
    async def improve(self, query: str, answer: str, vote: str, note: Optional[str] = None) -> dict:
        score = 1 if vote == "up" else -1
        self.graph.feedback.append({"query": query, "answer": answer, "vote": vote, "note": note})

        if self.is_cloud:
            # Store the Q&A turn + feedback as a typed QAEntry. Cognee Cloud
            # weights future recalls by this feedback signal.
            entry = {
                "type": "qa",
                "question": query,
                "answer": answer,
                "context": "",
                "feedback_text": note,
                "feedback_score": score,
            }
            try:
                await self.cloud.remember_entry(
                    entry, dataset_name=self.default_dataset, session_id=self.session_id
                )
                return {"detail": f"{vote}vote sent to Cognee Cloud — memory re-weighted"}
            except Exception as exc:  # noqa: BLE001
                # 409 = this Q&A + feedback is already recorded for the session.
                if _status_code(exc) == 409:
                    return {"detail": f"{vote}vote already recorded on Cognee Cloud"}
                logger.exception("cloud improve(feedback) failed: %s", exc)
                return {"detail": f"cloud error ({_short(exc)}); feedback kept locally"}

        if self.is_local:
            self._ensure_configured()
            try:
                if _COGNEE_IMPORTED and hasattr(cognee, "remember"):
                    from cognee import FeedbackEntry, QAEntry  # type: ignore

                    qa = await cognee.remember(  # type: ignore
                        QAEntry(question=query, answer=answer, feedback_score=score, feedback_text=note)
                    )
                    qa_id = _find_id(qa, ("entry_id", "qa_id", "id"))
                    if qa_id:
                        await cognee.remember(  # type: ignore
                            FeedbackEntry(qa_id=str(qa_id), feedback_score=score, feedback_text=note)
                        )
                    return {"detail": "feedback stored via remember(QAEntry/FeedbackEntry)"}
                return {"detail": "feedback recorded locally (no entry API on this SDK)"}
            except Exception as exc:  # noqa: BLE001
                logger.exception("local improve() failed: %s", exc)
                return {"detail": f"cognee error ({_short(exc)}); feedback kept locally"}

        return {"detail": f"[demo] recorded {vote} feedback; memory will weight this next recall"}

    # -- enrich (the "Memify" enrichment pass over a dataset) ------------
    async def enrich(self, dataset: Optional[str] = None) -> dict:
        ds = dataset or self.default_dataset

        if self.is_cloud:
            # This deployment exposes graph (re)build via cognify rather than a
            # dedicated improve() endpoint — re-cognifying enriches the graph.
            try:
                await self.cloud.cognify(datasets=[ds])
                return {"detail": f"Memified '{ds}' on Cognee Cloud — graph rebuilt & enriched"}
            except Exception as exc:  # noqa: BLE001
                logger.exception("cloud enrich() failed: %s", exc)
                return {"detail": f"cloud error ({_short(exc)})"}

        if self.is_local:
            self._ensure_configured()
            try:
                if hasattr(cognee, "improve"):
                    await cognee.improve(ds)  # type: ignore
                    return {"detail": f"Memified '{ds}' via improve()"}
                if hasattr(cognee, "memify"):
                    await cognee.memify()  # type: ignore
                    return {"detail": "graph enriched via memify()"}
                return {"detail": "no enrichment API on this SDK"}
            except Exception as exc:  # noqa: BLE001
                logger.exception("local enrich() failed: %s", exc)
                return {"detail": f"cognee error ({_short(exc)})"}

        return {"detail": f"[demo] Memified '{ds}' — (enrichment is a no-op in demo mode)"}

    # -- forget -----------------------------------------------------------
    async def forget(
        self, node_id: Optional[str] = None, dataset: Optional[str] = None, all: bool = False,
    ) -> dict:
        # Update the optimistic mirror.
        if all:
            removed = self.graph.clear()
        elif node_id:
            removed = self.graph.forget_node(node_id)
        elif dataset:
            removed = self.graph.forget_dataset(dataset)
        else:
            removed = 0

        if self.is_cloud:
            try:
                if all:
                    try:
                        await self.cloud.forget(everything=True)
                        return {"detail": "wiped all memory on Cognee Cloud", "nodes_removed": removed}
                    except Exception as exc:  # noqa: BLE001
                        # Some tenant builds 500 on bulk deletion — fall back
                        # to deleting record by record.
                        logger.info(
                            "forget(everything) failed (%s); deleting per record", _short(exc)
                        )
                        deleted = await self._forget_all_records()
                        return {
                            "detail": f"wiped memory record-by-record ({deleted} records)",
                            "nodes_removed": removed,
                        }
                if node_id and _looks_like_uuid(node_id):
                    # This build requires data_id + dataset together.
                    await self.cloud.forget(data_id=node_id, dataset=dataset or self.default_dataset)
                    return {"detail": "forgot memory on Cognee Cloud", "nodes_removed": removed}
                if dataset:
                    await self.cloud.forget(dataset=dataset)
                    return {"detail": f"forgot dataset '{dataset}' on Cognee Cloud", "nodes_removed": removed}
                return {"detail": "removed from local view (no cloud data_id given)", "nodes_removed": removed}
            except Exception as exc:  # noqa: BLE001
                logger.exception("cloud forget() failed: %s", exc)
                return {"detail": f"cloud error ({_short(exc)}); removed from local graph", "nodes_removed": removed}

        if self.is_local:
            self._ensure_configured()
            try:
                if hasattr(cognee, "forget"):
                    kwargs: dict[str, Any] = {}
                    if all:
                        kwargs["everything"] = True
                    elif node_id and _looks_like_uuid(node_id):
                        kwargs["data_id"] = node_id
                    elif dataset:
                        kwargs["dataset"] = dataset
                    await cognee.forget(**kwargs)  # type: ignore
                    return {"detail": "forgotten via forget()", "nodes_removed": removed}
                await cognee.prune.prune_data()  # type: ignore
                if all:
                    await cognee.prune.prune_system(metadata=True)  # type: ignore
                return {"detail": "pruned data", "nodes_removed": removed}
            except Exception as exc:  # noqa: BLE001
                logger.exception("local forget() failed: %s", exc)
                return {"detail": f"cognee error ({_short(exc)}); removed from local graph", "nodes_removed": removed}

        return {"detail": f"[demo] forgot {removed} node(s)", "nodes_removed": removed}

    async def _forget_all_records(self) -> int:
        """Fallback wipe: delete every data record across every dataset."""
        deleted = 0
        for ds in await self.cloud.list_datasets():
            ds_id, ds_name = str(ds.get("id")), ds.get("name") or ""
            try:
                rows = await self.cloud.dataset_data(ds_id)
            except Exception:  # noqa: BLE001
                continue
            for row in rows:
                rid = str(row.get("id"))
                try:
                    await self.cloud.forget(data_id=rid, dataset=ds_name)
                    deleted += 1
                    self._label_cache.pop(rid, None)
                except Exception as exc:  # noqa: BLE001
                    logger.info("per-record forget failed for %s: %s", rid, _short(exc))
        return deleted

    # -- memories list (the Forget panel's source of truth) --------------
    async def list_memories(self) -> list[dict]:
        if self.is_cloud:
            try:
                ds_id = await self._resolve_dataset_id(self.default_dataset)
                if ds_id:
                    rows = await self.cloud.dataset_data(ds_id)
                    out: list[dict] = []
                    for r in rows:
                        rid = r.get("id")
                        if not rid:
                            continue
                        out.append({"id": str(rid), "label": await self._memory_label(ds_id, r)})
                    return out
            except Exception as exc:  # noqa: BLE001
                logger.info("cloud list_memories failed, using mirror: %s", exc)
            return self.graph.documents()
        return self.graph.documents()

    async def _register_label(self, dataset: str, data: str) -> None:
        """Pair the just-ingested text with its cloud data record.

        Cognee stores uploads under a generic filename ('data'), and tenant
        pods can lose raw files across restarts — so the reliable moment to
        capture a human label is ingest time, when we still hold the text.
        """
        try:
            ds_id = self._dataset_ids.get(dataset) or await self._resolve_dataset_id(dataset)
            if not ds_id:
                return
            rows = await self.cloud.dataset_data(ds_id)
            unlabeled = [r for r in rows if str(r.get("id")) not in self._label_cache]
            if not unlabeled:
                return
            newest = max(unlabeled, key=lambda r: str(r.get("createdAt") or ""))
            snippet = data.strip().replace("\n", " ")
            self._label_cache[str(newest.get("id"))] = (
                (snippet[:60] + "…") if len(snippet) > 60 else snippet
            )
        except Exception as exc:  # noqa: BLE001
            logger.info("could not register memory label: %s", exc)

    async def _memory_label(self, dataset_id: str, record: dict) -> str:
        """A human-friendly label for a memory.

        Preference order: label registered at ingest time -> raw content
        fetched from the cloud -> a readable short-id fallback (the stored
        filename is an unhelpful 'data')."""
        rid = str(record.get("id"))
        if rid in self._label_cache:
            return self._label_cache[rid]
        try:
            raw = (await self.cloud.data_raw(dataset_id, rid)).strip().replace("\n", " ")
            if raw:
                label = (raw[:60] + "…") if len(raw) > 60 else raw
                # Cache only successful fetches — a cold-start failure must not
                # pin a fallback label forever.
                self._label_cache[rid] = label
                return label
        except Exception:  # noqa: BLE001
            pass  # raw file may be gone (pod restarts wipe tenant disk)
        name = record.get("name") or ""
        if name and name.lower() not in {"data", "text", "data.txt"}:
            return name
        return f"memory {rid[:8]}"

    # -- recap ("The Morning After" briefing) -----------------------------
    async def recap(self) -> dict:
        """One-shot briefing over everything in memory.

        Combines a real recall() summary with graph analytics (top entities
        by connectivity) and memory/feedback counts — the anti-hangover
        morning-after report.
        """
        graph = await self.get_graph()
        memories = await self.list_memories()

        # Top entities by degree (EntityType/kind nodes excluded — they are
        # categories, not knowledge).
        degree: dict[str, int] = {}
        for e in graph["edges"]:
            degree[e["source"]] = degree.get(e["source"], 0) + 1
            degree[e["target"]] = degree.get(e["target"], 0) + 1
        # Exclude category nodes (cloud "EntityType") and raw document nodes
        # (demo "document") so only real entities are ranked.
        skip_ids = {
            n["id"] for n in graph["nodes"] if n.get("type") in ("EntityType", "document")
        }
        entities = [
            {"label": n["label"], "connections": degree.get(n["id"], 0)}
            for n in graph["nodes"]
            if n["id"] not in skip_ids and degree.get(n["id"], 0) > 0
        ]
        entities.sort(key=lambda x: -x["connections"])
        top_entities = entities[:8]

        if not graph["nodes"] and not memories:
            summary = (
                "Nothing in memory yet — a truly blank morning. "
                "Remember a few things and check back."
            )
        elif self.is_real:
            result = await self.recall(
                "Give me a concise morning-after recap of everything you remember: "
                "the key people, places, plans, and facts, in 2-4 sentences.",
                search_type="GRAPH_COMPLETION",
            )
            summary = result["answer"]
        else:
            docs = self.graph.documents()
            summary = (
                f"You remembered {len(docs)} thing(s). Highlights: "
                + "; ".join(d["label"] for d in docs[:3])
            )

        return {
            "summary": summary,
            "top_entities": top_entities,
            "memory_count": len(memories),
            "node_count": len(graph["nodes"]),
            "edge_count": len(graph["edges"]),
            "feedback_count": len(self.graph.feedback),
            "mode": self.mode,
        }

    # -- graph (for visualization) ---------------------------------------
    async def get_graph(self) -> dict:
        if self.is_cloud:
            try:
                ds_id = await self._resolve_dataset_id(self.default_dataset)
                if ds_id:
                    data = await self.cloud.dataset_graph(ds_id)
                    nodes = []
                    kept: set[str] = set()
                    for n in data.get("nodes", []):
                        label = str(n.get("label") or n.get("id"))
                        ntype = str(n.get("type", "entity"))
                        if _is_structural(label, ntype):
                            continue
                        nid = str(n.get("id"))
                        kept.add(nid)
                        nodes.append({"id": nid, "label": label[:48], "type": ntype})
                    # Keep only edges whose endpoints both survived the filter.
                    edges = [
                        {
                            "source": str(e.get("source")),
                            "target": str(e.get("target")),
                            "label": e.get("label", ""),
                        }
                        for e in data.get("edges", [])
                        if str(e.get("source")) in kept and str(e.get("target")) in kept
                    ]
                    if nodes:
                        return {"nodes": nodes, "edges": edges}
            except Exception as exc:  # noqa: BLE001
                logger.info("cloud graph export unavailable (%s); using mirror.", exc)

        if self.is_local:
            try:
                from cognee.infrastructure.databases.graph import get_graph_engine  # type: ignore

                engine = await get_graph_engine()
                nodes_raw, edges_raw = await engine.get_graph_data()
                nodes = []
                for n in nodes_raw:
                    nid, props = (n if isinstance(n, (list, tuple)) else (n, {}))
                    props = props or {}
                    label = props.get("name") or props.get("text") or str(nid)
                    nodes.append({"id": str(nid), "label": str(label)[:48], "type": props.get("type", "entity")})
                edges = []
                for e in edges_raw:
                    if isinstance(e, (list, tuple)) and len(e) >= 2:
                        rel = e[2] if len(e) > 2 else ""
                        label = rel.get("relationship_name", "") if isinstance(rel, dict) else str(rel)
                        edges.append({"source": str(e[0]), "target": str(e[1]), "label": label})
                if nodes:
                    return {"nodes": nodes, "edges": edges}
            except Exception as exc:  # noqa: BLE001
                logger.info("local graph export unavailable (%s); using mirror.", exc)

        return {
            "nodes": [
                {"id": n["id"], "label": n["label"], "type": n["type"]}
                for n in self.graph.nodes.values()
            ],
            "edges": [
                {"source": e["source"], "target": e["target"], "label": e.get("label", "")}
                for e in self.graph.edges
            ],
        }


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


def _looks_like_uuid(value: str) -> bool:
    return bool(_UUID_RE.match(str(value or "")))


# Internal Cognee graph node kinds that are plumbing, not knowledge — hidden
# from the visualization so the graph reads as entities + relationships.
_STRUCTURAL_PREFIXES = ("documentchunk", "textsummary", "textdocument", "document_", "chunk_")
_STRUCTURAL_TYPES = {"documentchunk", "textsummary", "textdocument", "document"}
_STRUCTURAL_LABELS = {"data", "text", "data.txt"}


def _is_structural(label: str, ntype: str) -> bool:
    low = label.strip().lower()
    if low in _STRUCTURAL_LABELS:
        return True
    if low.startswith(_STRUCTURAL_PREFIXES):
        return True
    if ntype.strip().lower() in _STRUCTURAL_TYPES:
        return True
    return False


def _status_code(exc: Exception) -> Optional[int]:
    """Pull the HTTP status off an httpx error, if present."""
    resp = getattr(exc, "response", None)
    return getattr(resp, "status_code", None) if resp is not None else None


def _short(exc: Exception, limit: int = 160) -> str:
    s = str(exc).replace("\n", " ")
    return s[:limit] + ("…" if len(s) > limit else "")


def _find_id(obj: Any, keys: tuple[str, ...]) -> Optional[str]:
    """Best-effort extraction of an id from a varied response shape."""
    if isinstance(obj, dict):
        for k in keys:
            if obj.get(k):
                return str(obj[k])
        for v in obj.values():
            found = _find_id(v, keys)
            if found:
                return found
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            found = _find_id(item, keys)
            if found:
                return found
    else:
        # bare value (e.g. remember() returns a RememberResult / id)
        attr = getattr(obj, "entry_id", None) or getattr(obj, "id", None)
        if attr:
            return str(attr)
    return None


def _normalize_results(results: Any, search_type: str) -> dict:
    """Coerce Cognee's varied return shapes into {answer, sources, search_type}."""
    answer = ""
    sources: list[dict] = []

    def _coerce(item: Any) -> str:
        if isinstance(item, str):
            return item
        if isinstance(item, dict):
            return str(
                item.get("answer")
                or item.get("text")
                or item.get("content")
                or item.get("result")
                or item
            )
        return str(item)

    if isinstance(results, str):
        answer = results
    elif isinstance(results, dict):
        # Common cloud shapes: {"answer": ...} or {"results": [...]}.
        if results.get("results") and isinstance(results["results"], list):
            texts = [_coerce(r) for r in results["results"] if r is not None]
            answer = _coerce(results.get("answer")) if results.get("answer") else (texts[0] if texts else "")
            sources = [{"text": t[:200], "origin": "graph"} for t in texts[:8]]
        else:
            answer = _coerce(results)
    elif isinstance(results, list):
        texts = [_coerce(r) for r in results if r is not None]
        answer = texts[0] if texts else ""
        sources = [{"text": t[:200], "origin": "graph"} for t in texts[:8]]
    else:
        answer = str(results)

    if not answer:
        answer = "No answer was returned from memory for that query."
    return {"answer": answer, "sources": sources, "search_type": search_type}


# Singleton used by the API layer.
client = CogneeClient()
