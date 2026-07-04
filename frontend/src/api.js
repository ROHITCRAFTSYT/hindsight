// Thin API client for the Hindsight backend. Uses relative /api paths which the
// Vite dev server proxies to FastAPI (see vite.config.js).

async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

async function get(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} failed: ${res.status}`);
  return res.json();
}

export const api = {
  health: () => get("/api/health"),
  graph: () => get("/api/graph"),
  memories: () => get("/api/memories"),
  recap: () => get("/api/recap"),
  remember: (data, dataset = "main") => post("/api/remember", { data, dataset }),
  recall: (query, search_type, node_name) =>
    post("/api/recall", { query, search_type, top_k: 10, node_name }),
  improve: (query, answer, vote, note) => post("/api/improve", { query, answer, vote, note }),
  improveEnrich: (dataset) => post("/api/improve/enrich", { dataset }),
  forget: ({ node_id, dataset, all } = {}) => post("/api/forget", { node_id, dataset, all }),
};
