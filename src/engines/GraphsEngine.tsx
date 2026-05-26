import React, { useEffect, useRef, useMemo } from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';
import * as d3 from 'd3';

interface Node extends d3.SimulationNodeDatum {
  id: number;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: number | Node;
  target: number | Node;
}

export const GraphsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const svgRef = useRef<SVGSVGElement>(null);

  const nodeCount = overlay.nodes || 30;
  const linkCount = overlay.links || 40;

  // Stable data generation
  const { nodes, links } = useMemo(() => {
    const nodes: Node[] = Array.from({ length: nodeCount }, (_, i) => ({ id: i }));
    const links: Link[] = Array.from({ length: linkCount }, () => ({
      source: Math.floor(Math.random() * nodeCount),
      target: Math.floor(Math.random() * nodeCount)
    }));
    return { nodes, links };
  }, [nodeCount, linkCount]);

  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(150))
      .force("charge", d3.forceManyBody().strength(-100))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .stop();

    // Pre-calculate positions
    for (let i = 0; i < 100; ++i) simulation.tick();

    const g = svg.append("g");

    // Links with flow animation
    const linkElements = g.selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", overlay.linkColor || "rgba(255,255,255,0.1)")
      .attr("stroke-width", 1)
      .attr("x1", d => (d.source as Node).x!)
      .attr("y1", d => (d.source as Node).y!)
      .attr("x2", d => (d.target as Node).x!)
      .attr("y2", d => (d.target as Node).y!);

    // Nodes with glow
    const nodeElements = g.selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", 4)
      .attr("fill", overlay.nodeColor || "#3b82f6")
      .attr("cx", d => d.x!)
      .attr("cy", d => d.y!)
      .style("filter", "drop-shadow(0 0 5px rgba(59,130,246,0.8))");

    // Animate container
    const rotation = frame * (overlay.speed || 0.1);
    const scale = 1 + Math.sin(frame / 30) * 0.05;
    g.attr("transform", `translate(${width/2}, ${height/2}) scale(${scale}) rotate(${rotation}) translate(${-width/2}, ${-height/2})`);

  }, [nodes, links, frame, width, height, overlay]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden bg-transparent">
      <svg ref={svgRef} width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} />
    </div>
  );
};
