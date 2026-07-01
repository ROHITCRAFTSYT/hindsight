import React from "react";

// forget() — prune individual memories or wipe everything.
export default function MemoryPanel({ memories = [], onForgetNode, onForgetAll, busy }) {
  const documents = memories;

  return (
    <div className="panel" style={{ flex: 1 }}>
      <h2>🔴 Forget</h2>
      <p className="hint">
        Memories Cognee is holding. Remove stale or wrong ones with <code>forget()</code> — the
        graph updates instantly.
      </p>

      <div className="mem-list">
        {documents.length === 0 && (
          <div className="empty-state">No memories yet.</div>
        )}
        {documents.map((d) => (
          <div className="mem-item" key={d.id}>
            <div style={{ overflow: "hidden" }}>
              <div className="label">{d.label}</div>
              <div className="ds">{d.id}</div>
            </div>
            <button className="x-btn" onClick={() => onForgetNode(d.id)} disabled={busy}>
              forget
            </button>
          </div>
        ))}
      </div>

      <button
        className="btn-danger"
        style={{ marginTop: 12 }}
        onClick={() => {
          if (window.confirm("Forget ALL memories? This prunes the entire graph.")) onForgetAll();
        }}
        disabled={busy || documents.length === 0}
      >
        Wipe all memory
      </button>
    </div>
  );
}
