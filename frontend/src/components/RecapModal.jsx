import React from "react";

// 🌅 The Morning After — one-shot briefing over everything in memory.
export default function RecapModal({ recap, onClose }) {
  if (!recap) return null;
  return (
    <div className="recap-overlay" onClick={onClose}>
      <div className="recap-card" onClick={(e) => e.stopPropagation()}>
        <div className="recap-head">
          <h2>🌅 The Morning After</h2>
          <button className="recap-close" onClick={onClose} aria-label="Close">
            ✕
          </button>
        </div>
        <p className="recap-sub">Everything your second brain remembers — no hangover.</p>

        <div className="recap-summary">{recap.summary}</div>

        {recap.top_entities?.length > 0 && (
          <>
            <div className="recap-label">Most connected memories</div>
            <div className="recap-entities">
              {recap.top_entities.map((e) => (
                <span key={e.label} className="recap-chip">
                  {e.label}
                  <em>{e.connections}</em>
                </span>
              ))}
            </div>
          </>
        )}

        <div className="recap-stats">
          <div>
            <strong>{recap.node_count}</strong>
            <span>nodes</span>
          </div>
          <div>
            <strong>{recap.edge_count}</strong>
            <span>edges</span>
          </div>
          <div>
            <strong>{recap.memory_count}</strong>
            <span>memories</span>
          </div>
          <div>
            <strong>{recap.feedback_count}</strong>
            <span>votes</span>
          </div>
        </div>
      </div>
    </div>
  );
}
