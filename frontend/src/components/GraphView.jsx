import React, { useMemo, useRef, useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const COLORS = {
  document: "#25f4ee",
  entity: "#9d4edd",
  default: "#ff4dd2",
};

// Live force-directed view of the Cognee knowledge graph.
export default function GraphView({ graph, onForgetNode }) {
  const wrapRef = useRef(null);
  const fgRef = useRef(null);
  const [size, setSize] = useState({ w: 600, h: 400 });

  useEffect(() => {
    const el = wrapRef.current;
    if (!el) return;
    const ro = new ResizeObserver(() => {
      setSize({ w: el.clientWidth, h: el.clientHeight });
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  // react-force-graph mutates the data objects it's given, so clone each render.
  const data = useMemo(
    () => ({
      nodes: graph.nodes.map((n) => ({ ...n })),
      links: graph.edges.map((e) => ({ ...e })),
    }),
    [graph]
  );

  return (
    <div ref={wrapRef} style={{ width: "100%", height: "100%" }}>
      <ForceGraph2D
        ref={fgRef}
        width={size.w}
        height={size.h}
        graphData={data}
        backgroundColor="rgba(0,0,0,0)"
        nodeRelSize={5}
        linkColor={() => "rgba(157,78,221,0.35)"}
        linkDirectionalParticles={1}
        linkDirectionalParticleWidth={1.6}
        linkDirectionalParticleColor={() => "#25f4ee"}
        cooldownTicks={120}
        onNodeClick={(node) => {
          if (onForgetNode && window.confirm(`Forget "${node.label}"?`)) {
            onForgetNode(node.id);
          }
        }}
        nodeCanvasObject={(node, ctx, scale) => {
          const color = COLORS[node.type] || COLORS.default;
          const r = node.type === "document" ? 6 : 4;
          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, 2 * Math.PI);
          ctx.fillStyle = color;
          ctx.shadowColor = color;
          ctx.shadowBlur = 12;
          ctx.fill();
          ctx.shadowBlur = 0;

          const label = node.label || node.id;
          const fontSize = Math.max(10 / scale, 2.5);
          ctx.font = `${fontSize}px Inter, sans-serif`;
          ctx.fillStyle = "rgba(236,231,245,0.9)";
          ctx.textAlign = "center";
          ctx.textBaseline = "top";
          if (scale > 1.1 || node.type === "document") {
            ctx.fillText(label, node.x, node.y + r + 1);
          }
        }}
      />
    </div>
  );
}
