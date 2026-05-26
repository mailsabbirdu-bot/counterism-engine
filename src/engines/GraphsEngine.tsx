import React, { useEffect, useRef } from 'react';
import { useCurrentFrame } from 'remotion';
import * as d3 from 'd3';

export const GraphsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const svgRef = useRef<SVGSVGElement>(null);
  const relativeFrame = frame - overlay.start;

  useEffect(() => {
    if (!svgRef.current) return;

    const width = 1920;
    const height = 1080;
    const svg = d3.select(svgRef.current);

    // Simple force-directed-like static graph for D3 showcase
    const nodes = Array.from({ length: overlay.nodes || 20 }, (_, i) => ({ id: i }));
    const links = Array.from({ length: overlay.links || 30 }, () => ({
      source: Math.floor(Math.random() * nodes.length),
      target: Math.floor(Math.random() * nodes.length)
    }));

    svg.selectAll("*").remove();

    const g = svg.append("g").attr("transform", `translate(${width/2}, ${height/2})`);

    g.selectAll("line")
      .data(links)
      .enter()
      .append("line")
      .attr("stroke", "#ffffff20")
      .attr("x1", d => Math.cos(d.source) * 300)
      .attr("y1", d => Math.sin(d.source) * 300)
      .attr("x2", d => Math.cos(d.target) * 300)
      .attr("y2", d => Math.sin(d.target) * 300);

    g.selectAll("circle")
      .data(nodes)
      .enter()
      .append("circle")
      .attr("r", 4)
      .attr("fill", "#3b82f6")
      .attr("cx", d => Math.cos(d.id) * 300)
      .attr("cy", d => Math.sin(d.id) * 300)
      .attr("opacity", 0.6);

    // Procedural rotation based on frame
    g.attr("transform", `translate(${width/2}, ${height/2}) rotate(${frame * 0.2})`);

  }, [overlay.nodes, overlay.links, frame]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  return (
    <div className="absolute inset-0 pointer-events-none opacity-40">
      <svg ref={svgRef} width="100%" height="100%" viewBox="0 0 1920 1080" />
    </div>
  );
};
