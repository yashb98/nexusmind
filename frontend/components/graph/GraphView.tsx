"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import * as d3 from "d3";

interface GraphNode {
  id: string;
  display_name?: string;
  lora_archetype?: string;
  communication_style?: string;
  interests?: string[];
  is_mock?: boolean;
  openness?: number;
  extraversion?: number;
  trust_level?: number;
  [key: string]: unknown;
}

interface GraphEdge {
  source: string;
  target: string;
  strength?: number;
  type?: string;
  [key: string]: unknown;
}

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  data: GraphNode | null;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4"];

const ARCHETYPE_LABELS: Record<string, string> = {
  analytical: "The Investigator",
  creative: "The Visionary",
  empathetic: "The Empath",
  pragmatic: "The Strategist",
  contrarian: "The Challenger",
};

function clampPosition(x: number, y: number, containerW: number, containerH: number) {
  const tooltipW = 260;
  const tooltipH = 180;
  const pad = 12;
  const clampedX = Math.min(Math.max(x + pad, 0), containerW - tooltipW);
  const clampedY = Math.min(Math.max(y + pad, 0), containerH - tooltipH);
  return { x: clampedX, y: clampedY };
}

export default function GraphView({ nodes, edges, onNodeClick, onEdgeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<TooltipState>({
    visible: false,
    x: 0,
    y: 0,
    data: null,
  });

  const handleMouseOver = useCallback(
    (event: MouseEvent, d: GraphNode) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const mx = event.clientX - rect.left;
      const my = event.clientY - rect.top;
      const clamped = clampPosition(mx, my, rect.width, rect.height);

      // Find trust level from KNOWS edges pointing to this node
      const knowsEdge = edges.find(
        (e) =>
          ((typeof e.source === "string" ? e.source : (e.source as any)?.id) !== d.id &&
            (typeof e.target === "string" ? e.target : (e.target as any)?.id) === d.id &&
            (e.type === "KNOWS" || e.strength !== undefined))
      );
      const trustLevel = d.trust_level ?? knowsEdge?.strength ?? null;

      setTooltip({
        visible: true,
        x: clamped.x,
        y: clamped.y,
        data: { ...d, trust_level: trustLevel } as GraphNode,
      });
    },
    [edges],
  );

  const handleMouseOut = useCallback(() => {
    setTooltip((prev) => ({ ...prev, visible: false }));
  }, []);

  useEffect(() => {
    if (!svgRef.current || !containerRef.current || nodes.length === 0) return;

    const width = containerRef.current.clientWidth || 800;
    const height = containerRef.current.clientHeight || 600;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    svg.attr("width", width).attr("height", height);

    const g = svg.append("g");

    svg.call(
      d3.zoom<SVGSVGElement, unknown>()
        .scaleExtent([0.2, 4])
        .on("zoom", (event) => g.attr("transform", event.transform))
    );

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const simNodes: any[] = nodes.map((n) => ({ ...n }));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const simEdges: any[] = edges.map((e) => ({ ...e }));

    const simulation = d3.forceSimulation(simNodes)
      .force("link", d3.forceLink(simEdges).id((d: any) => d.id).distance(120))
      .force("charge", d3.forceManyBody().strength(-250))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide(35));

    const link = g.selectAll("line").data(simEdges).join("line")
      .attr("stroke", "#475569")
      .attr("stroke-width", (d: any) => Math.max(1, (d.strength || 0.3) * 4))
      .attr("stroke-opacity", 0.6)
      .style("cursor", "pointer")
      .on("click", (_: any, d: any) => onEdgeClick?.(d));

    const node = g.selectAll("g.node").data(simNodes).join("g")
      .attr("class", "node")
      .style("cursor", "pointer")
      .on("click", (_: any, d: any) => onNodeClick?.(d.id))
      .on("mouseover", (event: any, d: any) => handleMouseOver(event, d))
      .on("mouseout", handleMouseOut);

    node.append("circle")
      .attr("r", 18)
      .attr("fill", (_: any, i: number) => COLORS[i % COLORS.length])
      .attr("stroke", "#1e293b")
      .attr("stroke-width", 2);

    node.append("text")
      .text((d: any) => d.display_name || d.id?.slice(0, 6) || "?")
      .attr("text-anchor", "middle")
      .attr("dy", 32)
      .attr("fill", "#cbd5e1")
      .attr("font-size", "11px")
      .attr("pointer-events", "none");

    const drag = d3.drag<SVGGElement, any>()
      .on("start", (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x; d.fy = d.y;
      })
      .on("drag", (event, d) => { d.fx = event.x; d.fy = event.y; })
      .on("end", (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null; d.fy = null;
      });
    node.call(drag as any);

    simulation.on("tick", () => {
      link
        .attr("x1", (d: any) => d.source.x)
        .attr("y1", (d: any) => d.source.y)
        .attr("x2", (d: any) => d.target.x)
        .attr("y2", (d: any) => d.target.y);
      node.attr("transform", (d: any) => `translate(${d.x},${d.y})`);
    });

    return () => { simulation.stop(); };
  }, [nodes, edges, onNodeClick, onEdgeClick, handleMouseOver, handleMouseOut]);

  const ttData = tooltip.data;
  const archetype = ttData?.lora_archetype as string | undefined;
  const archetypeLabel = archetype
    ? ARCHETYPE_LABELS[archetype] || archetype
    : null;
  const interests = ttData?.interests as string[] | undefined;
  const commStyle = ttData?.communication_style as string | undefined;
  const trustLevel = ttData?.trust_level as number | null | undefined;

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[400px] bg-slate-950">
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-500">
          No graph data available
        </div>
      )}
      <svg ref={svgRef} className="w-full h-full" />

      {/* Hover tooltip */}
      {tooltip.visible && ttData && (
        <div
          className="absolute z-50 pointer-events-none bg-slate-800 border border-slate-600 rounded-lg p-3 shadow-xl max-w-[260px]"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <div className="flex items-center gap-2 mb-1.5">
            <span className="text-sm font-bold text-slate-100">
              {ttData.display_name || ttData.id?.slice(0, 8)}
            </span>
            {ttData.is_mock && (
              <span className="text-[9px] font-semibold uppercase tracking-wide bg-amber-500/20 text-amber-400 border border-amber-500/40 px-1.5 py-px rounded">
                Mock Agent
              </span>
            )}
          </div>

          {archetypeLabel && (
            <p className="text-xs text-indigo-400 font-medium mb-1">{archetypeLabel}</p>
          )}

          {commStyle && (
            <p className="text-xs text-slate-400 mb-1">
              <span className="text-slate-500">Style:</span> {commStyle}
            </p>
          )}

          {interests && interests.length > 0 && (
            <p className="text-xs text-slate-400 mb-1">
              <span className="text-slate-500">Interests:</span>{" "}
              {interests.join(", ")}
            </p>
          )}

          {trustLevel != null && (
            <div className="mt-1.5 flex items-center gap-2">
              <span className="text-xs text-slate-500">Trust:</span>
              <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${Math.round(trustLevel * 100)}%` }}
                />
              </div>
              <span className="text-[10px] text-slate-400">
                {(trustLevel * 100).toFixed(0)}%
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
