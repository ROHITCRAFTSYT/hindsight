import React, { useMemo, useRef, useEffect, useState, useCallback } from "react";
import ForceGraph2D from "react-force-graph-2d";

// Stable palette; entity kinds (person, location, …) hash onto it so colors
// stay consistent across reloads.
const KIND_PALETTE = ["#ff4dd2", "#25f4ee", "#ffb703", "#2bd576", "#ff9770", "#c77dff", "#90e0ef"];
const DOC_COLOR = "#25f4ee";
const TYPE_NODE_COLOR = "#6c5a8f";
const DEFAULT_COLOR = "#9d4edd";

function hashColor(label) {
  let h = 0;
  for (let i = 0; i < label.length; i++) h = (h * 31 + label.charCodeAt(i)) >>> 0;
  return KIND_PALETTE[h % KIND_PALETTE.length];
}

// Live force-directed view of the Cognee knowledge graph.
// Click a node for actions (ask / forget); hover to highlight its neighborhood.
export default function GraphView({ graph, onForgetNode, onAskNode }) {
  const wrapRef = useRef(null);
  const fgRef = useRef(null);
  const [size, setSize] = useState({ w: 600, h: 400 });
  const [menu, setMenu] = useState(null); // { x, y, node }
  const [hoverId, setHoverId] = useState(null);

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // Close the action menu whenever the graph data changes (e.g. after forget).
  useEffect(() => setMenu(null), [graph]);

  // Derive each entity's kind (person / location / …) from its edge to an
  // EntityType node, then color by kind. Also build the hover adjacency map.
  const { data, kindById, legend, neighbors } = useMemo(() => {
    const nodes = graph.nodes.map((n) => ({ ...n }));
    const links = graph.edges.map((e) => ({ ...e }));
    const typeLabel = {};
    nodes.forEach((n) => {
      if (n.type === "EntityType") typeLabel[n.id] = n.label;
    });
    const kind = {};
    const adj = {};
    graph.edges.forEach((e) => {
      (adj[e.source] = adj[e.source] || new Set()).add(e.target);
      (adj[e.target] = adj[e.target] || new Set()).add(e.source);
      if (typeLabel[e.target] && !kind[e.source]) kind[e.source] = typeLabel[e.target];
      if (typeLabel[e.source] && !kind[e.target]) kind[e.target] = typeLabel[e.source];
    });
    const kinds = [...new Set(Object.values(kind))].slice(0, 6);
    return {
      data: { nodes, links },
      kindById: kind,
      legend: kinds.map((k) => ({ label: k, color: hashColor(k) })),
      neighbors: adj,
    };
  }, [graph]);

  const colorOf = useCallback(
    (node) => {
      if (node.type === "document") return DOC_COLOR;
      if (node.type === "EntityType") return TYPE_NODE_COLOR;
      const kind = kindById[node.id];
      return kind ? hashColor(kind) : DEFAULT_COLOR;
    },
    [kindById]
  );

  const isDimmed = useCallback(
    (id) => hoverId && id !== hoverId && !(neighbors[hoverId]?.has(id)),
    [hoverId, neighbors]
  );

  const handleNodeClick = useCallback((node, event) => {
    const rect = wrapRef.current?.getBoundingClientRect();
    if (!rect) return;
    setMenu({
      x: Math.min(event.clientX - rect.left, rect.width - 170),
      y: Math.min(event.clientY - rect.top, rect.height - 96),
      node,
    });
  }, []);

  return (
    <div ref={wrapRef} style={{ width: "100%", height: "100%", position: "relative" }}>
      <ForceGraph2D
        ref={fgRef}
        width={size.w}
        height={size.h}
        graphData={data}
        backgroundColor="rgba(0,0,0,0)"
        nodeRelSize={5}
        linkColor={(l) => {
          const s = typeof l.source === "object" ? l.source.id : l.source;
          const t = typeof l.target === "object" ? l.target.id : l.target;
          if (hoverId && (s === hoverId || t === hoverId)) return "rgba(37,244,238,0.75)";
          return hoverId ? "rgba(157,78,221,0.12)" : "rgba(157,78,221,0.35)";
        }}
        linkDirectionalParticles={1}
        linkDirectionalParticleWidth={1.6}
        linkDirectionalParticleColor={() => "#25f4ee"}
        cooldownTicks={120}
        onNodeClick={handleNodeClick}
        onNodeHover={(node) => setHoverId(node ? node.id : null)}
        onBackgroundClick={() => setMenu(null)}
        nodeCanvasObject={(node, ctx, scale) => {
          const color = colorOf(node);
          const dim = isDimmed(node.id);
          const hovered = node.id === hoverId;
          const r = (node.type === "document" ? 6 : node.type === "EntityType" ? 3 : 4.5) * (hovered ? 1.4 : 1);
          ctx.globalAlpha = dim ? 0.18 : 1;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.shadowColor = color;
          ctx.shadowBlur = hovered ? 20 : 12;
          ctx.fill();
          ctx.shadowBlur = 0;

          const label = node.label || node.id;
          const fontSize = Math.max(10 / scale, 2.5);
          ctx.font = `${fontSize}px Inter, sans-serif`;
          ctx.fillStyle = "rgba(236,231,245,0.9)";
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          if ((scale > 1.1 || node.type === "document" || hovered) && node.type !== "EntityType") {
            ctx.fillText(label, node.x, node.y + r + 1);
          }
          ctx.globalAlpha = 1;
        }}
      />

      {legend.length > 0 && (
        <div className="graph-legend">
          {legend.map((k) => (
            <span key={k.label} className="legend-item">
              <span className="legend-dot" style={{ background: k.color }} />
              {k.label}
            </span>
          ))}
        </div>
      )}

      {menu && (
        <div className="node-menu" style={{ left: menu.x, top: menu.y }}>
          <div className="node-menu-title">{menu.node.label}</div>
          {onAskNode && menu.node.type !== "EntityType" && (
            <button
              className="node-menu-btn ask"
              onClick={() => {
                onAskNode(menu.node.label);
                setMenu(null);
              }}
            >
              🔵 Ask about this
            </button>
          )}
          {onForgetNode && (
            <button
              className="node-menu-btn forget"
              onClick={() => {
                onForgetNode(menu.node.id);
                setMenu(null);
              }}
            >
              🔴 Forget
            </button>
          )}
        </div>
      )}
    </div>
  );
}
