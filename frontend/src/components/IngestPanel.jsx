import React, { useState } from "react";

const SAMPLES = [
  "Cognee turns documents into a hybrid graph + vector memory for AI agents.",
  "https://en.wikipedia.org/wiki/Knowledge_graph",
  "Our Q3 launch is in September; Priya owns marketing and Alex owns infra.",
];

// remember() — ingest text, a file path, or a URL into Cognee memory.
export default function IngestPanel({ onRemember, busy }) {
  const [text, setText] = useState("");
  const [dataset, setDataset] = useState("main");

  const submit = async () => {
    const value = text.trim();
    if (!value) return;
    await onRemember(value, dataset);
    setText("");
  };

  return (
    <div className="panel">
      <h2>🟢 Remember</h2>
      <p className="hint">
        Drop in text, a file path, or a URL. Cognee chunks it, extracts entities, and grows
        the knowledge graph.
      </p>

      <textarea
        rows={5}
        placeholder="Paste a note, a URL, or a file path…"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
        }}
      />

      <div className="field-label">Dataset</div>
      <div className="row">
        <input
          type="text"
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
          placeholder="main"
        />
        <button className="btn-remember" onClick={submit} disabled={busy || !text.trim()}>
          {busy ? <span className="spinner" /> : "Remember"}
        </button>
      </div>

      <div className="field-label">Quick add</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {SAMPLES.map((s, i) => (
          <button
            key={i}
            className="btn-ghost"
            style={{ textAlign: "left", fontWeight: 400, fontSize: 12 }}
            onClick={() => setText(s)}
          >
            {s.length > 54 ? s.slice(0, 54) + "…" : s}
          </button>
        ))}
      </div>
    </div>
  );
}
