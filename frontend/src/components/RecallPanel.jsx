import React, { useState, useRef, useEffect } from "react";

const SEARCH_TYPES = [
  "GRAPH_COMPLETION",
  "RAG_COMPLETION",
  "INSIGHTS",
  "CHUNKS",
  "SUMMARIES",
  "TEMPORAL",
];

// recall() — ask questions answered from the knowledge graph.
// improve() — thumbs up/down on each answer feeds feedback back into memory.
export default function RecallPanel({ messages, onRecall, onVote, busy }) {
  const [query, setQuery] = useState("");
  const [searchType, setSearchType] = useState("GRAPH_COMPLETION");
  const chatRef = useRef(null);

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight;
  }, [messages, busy]);

  const submit = async () => {
    const q = query.trim();
    if (!q) return;
    setQuery("");
    await onRecall(q, searchType);
  };

  return (
    <div className="panel" style={{ flex: 1 }}>
      <h2>🔵 Recall &amp; 🟣 Improve</h2>
      <p className="hint">
        Ask anything. Rate answers with 👍 / 👎 — feedback is sent to <code>improve()</code> to
        re-weight memory.
      </p>

      <div className="chat" ref={chatRef}>
        {messages.length === 0 && (
          <div className="empty-state">
            Nothing recalled yet.
            <br />
            Remember a few things, then ask me what I know.
          </div>
        )}
        {messages.map((m, i) => (
          <React.Fragment key={i}>
            <div className="msg user">{m.query}</div>
            <div className="msg ai">
              {m.pending ? <span className="spinner" /> : m.answer}
              {!m.pending && (
                <>
                  {m.sources?.length > 0 && (
                    <div className="source">
                      {m.sources.slice(0, 2).map((s, j) => (
                        <div key={j}>↳ {s.text}</div>
                      ))}
                    </div>
                  )}
                  <div className="meta">
                    <span>{m.search_type}</span>
                    <span style={{ marginLeft: "auto" }}>
                      <button
                        className={`btn-vote up ${m.vote === "up" ? "active-up" : ""}`}
                        onClick={() => onVote(i, "up")}
                        title="Helpful — reinforce this memory"
                      >
                        👍
                      </button>{" "}
                      <button
                        className={`btn-vote down ${m.vote === "down" ? "active-down" : ""}`}
                        onClick={() => onVote(i, "down")}
                        title="Wrong — down-weight this memory"
                      >
                        👎
                      </button>
                    </span>
                  </div>
                </>
              )}
            </div>
          </React.Fragment>
        ))}
      </div>

      <div className="row" style={{ marginBottom: 8 }}>
        <select value={searchType} onChange={(e) => setSearchType(e.target.value)} style={{ maxWidth: 190 }}>
          {SEARCH_TYPES.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>
      </div>
      <div className="row">
        <input
          type="text"
          placeholder="Ask your second brain…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
        />
        <button className="btn-recall" onClick={submit} disabled={busy || !query.trim()}>
          {busy ? <span className="spinner" /> : "Recall"}
        </button>
      </div>
    </div>
  );
}
