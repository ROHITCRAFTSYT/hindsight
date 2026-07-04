import React, { useEffect, useState, useCallback } from "react";
import { api } from "./api.js";
import GraphView from "./components/GraphView.jsx";
import IngestPanel from "./components/IngestPanel.jsx";
import RecallPanel from "./components/RecallPanel.jsx";
import MemoryPanel from "./components/MemoryPanel.jsx";
import RecapModal from "./components/RecapModal.jsx";

export default function App() {
  const [health, setHealth] = useState(null);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [memories, setMemories] = useState([]);
  const [messages, setMessages] = useState([]);
  const [toast, setToast] = useState(null);
  const [recap, setRecap] = useState(null);
  const [busy, setBusy] = useState({
    remember: false,
    recall: false,
    forget: false,
    memify: false,
    recap: false,
  });

  const flash = useCallback((msg) => {
    setToast(msg);
    setTimeout(() => setToast(null), 2600);
  }, []);

  const refreshGraph = useCallback(async () => {
    try {
      const [g, m] = await Promise.all([api.graph(), api.memories()]);
      setGraph(g);
      setMemories(m.memories || []);
    } catch (e) {
      console.error(e);
    }
  }, []);

  useEffect(() => {
    api.health().then(setHealth).catch(() => setHealth({ mode: "offline" }));
    refreshGraph();
  }, [refreshGraph]);

  const handleMemify = async () => {
    setBusy((b) => ({ ...b, memify: true }));
    try {
      const res = await api.improveEnrich();
      flash(`🟣 ${res.detail}`);
      await refreshGraph();
    } catch (e) {
      flash("⚠️ memify failed");
    } finally {
      setBusy((b) => ({ ...b, memify: false }));
    }
  };

  const handleRecap = async () => {
    setBusy((b) => ({ ...b, recap: true }));
    try {
      setRecap(await api.recap());
    } catch (e) {
      flash("⚠️ recap failed");
    } finally {
      setBusy((b) => ({ ...b, recap: false }));
    }
  };

  const handleRemember = async (data, dataset) => {
    setBusy((b) => ({ ...b, remember: true }));
    try {
      const res = await api.remember(data, dataset);
      flash(`🟢 Remembered · +${res.nodes_added} nodes`);
      await refreshGraph();
    } catch (e) {
      flash("⚠️ remember failed");
    } finally {
      setBusy((b) => ({ ...b, remember: false }));
    }
  };

  const handleRecall = async (query, searchType, nodeName) => {
    setBusy((b) => ({ ...b, recall: true }));
    const idx = messages.length;
    setMessages((m) => [...m, { query, pending: true, scoped: nodeName }]);
    try {
      const res = await api.recall(query, searchType, nodeName);
      setMessages((m) =>
        m.map((msg, i) =>
          i === idx
            ? {
                query,
                answer: res.answer,
                sources: res.sources,
                search_type: res.search_type,
                scoped: nodeName,
                pending: false,
              }
            : msg
        )
      );
    } catch (e) {
      setMessages((m) =>
        m.map((msg, i) =>
          i === idx ? { query, answer: "⚠️ recall failed", pending: false, search_type: "error" } : msg
        )
      );
    } finally {
      setBusy((b) => ({ ...b, recall: false }));
    }
  };

  const handleVote = async (idx, vote) => {
    const m = messages[idx];
    if (!m) return;
    setMessages((arr) => arr.map((x, i) => (i === idx ? { ...x, vote } : x)));
    try {
      const res = await api.improve(m.query, m.answer, vote);
      flash(`🟣 ${res.detail}`);
    } catch (e) {
      flash("⚠️ improve failed");
    }
  };

  const handleAskNode = (label) => {
    // Entity-scoped recall: the query is scoped to this graph node via
    // Cognee's node_name filter.
    handleRecall(`What do I know about "${label}"?`, "GRAPH_COMPLETION", [label]);
  };

  const handleForgetNode = async (nodeId) => {
    setBusy((b) => ({ ...b, forget: true }));
    try {
      const res = await api.forget({ node_id: nodeId });
      flash(`🔴 Forgot · -${res.nodes_removed} nodes`);
      await refreshGraph();
    } catch (e) {
      flash("⚠️ forget failed");
    } finally {
      setBusy((b) => ({ ...b, forget: false }));
    }
  };

  const handleForgetAll = async () => {
    setBusy((b) => ({ ...b, forget: true }));
    try {
      await api.forget({ all: true });
      flash("🔴 Memory wiped");
      setMessages([]);
      await refreshGraph();
    } catch (e) {
      flash("⚠️ forget failed");
    } finally {
      setBusy((b) => ({ ...b, forget: false }));
    }
  };

  const mode = health?.mode || "…";

  return (
    <div className="app">
      <header className="header">
        <div className="brand">
          <h1>Hindsight</h1>
          <span className="tag">the AI second brain that never wakes up with amnesia</span>
        </div>
        <div className="lifecycle-legend">
          <span className="pill remember">remember</span>
          <span className="pill recall">recall</span>
          <span className="pill improve">improve</span>
          <span className="pill forget">forget</span>
        </div>
        <button className="btn-memify" onClick={handleMemify} disabled={busy.memify} title="Run Cognee's enrichment pass over your memory">
          {busy.memify ? <span className="spinner" /> : "Memify ✨"}
        </button>
        <button className="btn-recap" onClick={handleRecap} disabled={busy.recap} title="The Morning After — a one-shot recap of everything in memory">
          {busy.recap ? <span className="spinner" /> : "Recap 🌅"}
        </button>
        <div className="mode-badge">
          <span className={`mode-dot ${mode}`} />
          <span>
            {mode === "cloud" && "Cognee Cloud"}
            {mode === "local" && "Self-hosted Cognee"}
            {mode === "demo" && "Demo mode"}
            {mode === "offline" && "Backend offline"}
            {!["cloud", "local", "demo", "offline"].includes(mode) && "connecting…"}
          </span>
        </div>
      </header>

      <div className="grid">
        <div className="col">
          <IngestPanel onRemember={handleRemember} busy={busy.remember} />
          <MemoryPanel
            memories={memories}
            onForgetNode={handleForgetNode}
            onForgetAll={handleForgetAll}
            busy={busy.forget}
          />
        </div>

        <div className="col">
          <div className="panel graph" style={{ flex: 1 }}>
            <div className="graph-overlay">
              <h2>🕸️ Knowledge graph</h2>
              <p className="hint">Click a node to ask about it — or forget it</p>
            </div>
            <GraphView graph={graph} onForgetNode={handleForgetNode} onAskNode={handleAskNode} />
            <div className="graph-stats">
              {graph.nodes.length} nodes · {graph.edges.length} edges · {memories.length} memories
            </div>
          </div>
        </div>

        <div className="col">
          <RecallPanel
            messages={messages}
            onRecall={handleRecall}
            onVote={handleVote}
            busy={busy.recall}
          />
        </div>
      </div>

      {toast && <div className="toast">{toast}</div>}
      <RecapModal recap={recap} onClose={() => setRecap(null)} />
    </div>
  );
}
