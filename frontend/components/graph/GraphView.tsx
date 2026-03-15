"use client";

import { useEffect, useRef } from "react";
import * as d3 from "d3";

interface GraphNode {
  id: string;
  display_name?: string;
  [key: string]: unknown;
}

interface GraphEdge {
  source: string;
  target: string;
  strength?: number;
  [key: string]: unknown;
}

interface Props {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edge: GraphEdge) => void;
}

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4"];

export default function GraphView({ nodes, edges, onNodeClick, onEdgeClick }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement>(null);

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
      .on("click", (_: any, d: any) => onNodeClick?.(d.id));

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
  }, [nodes, edges, onNodeClick, onEdgeClick]);

  return (
    <div ref={containerRef} className="relative w-full h-full min-h-[400px] bg-slate-950">
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-slate-500">
          No graph data available
        </div>
      )}
      <svg ref={svgRef} className="w-full h-full" />
    </div>
  );
}
