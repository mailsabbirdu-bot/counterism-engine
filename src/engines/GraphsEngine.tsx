import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring } from 'remotion';
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

  const nodeCount = overlay.nodes || 30;
  const linkCount = overlay.links || 40;

  // Heavy calculation happens only once per scene instantiation
  const { processedNodes, processedLinks } = useMemo(() => {
    const nodes: Node[] = Array.from({ length: nodeCount }, (_, i) => ({ id: i }));
    const links: Link[] = Array.from({ length: linkCount }, () => ({
      source: Math.floor(Math.random() * nodeCount),
      target: Math.floor(Math.random() * nodeCount)
    }));

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(200))
      .force("charge", d3.forceManyBody().strength(-150))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .stop();

    // Pre-calculate final positions for high performance
    for (let i = 0; i < 150; ++i) simulation.tick();

    return {
      processedNodes: nodes,
      processedLinks: links
    };
  }, [nodeCount, linkCount, width, height]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  // Entrance animation
  const entrance = spring({
    frame: frame - overlay.start,
    fps,
    config: { damping: 20 },
  });

  // Smooth container animation
  const rotation = frame * (overlay.speed || 0.05);
  const scale = 1 + Math.sin(frame / 60) * 0.03;
  const driftY = Math.sin(frame / 45) * 10;
  const driftX = Math.cos(frame / 50) * 10;

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      style={{ opacity: entrance }}
    >
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${width/2 + driftX}, ${height/2 + driftY}) scale(${scale}) rotate(${rotation}) translate(${-width/2}, ${-height/2})`}>
          {/* Render links first (under nodes) */}
          {processedLinks.map((link, i) => (
            <line
              key={`link-${i}`}
              x1={(link.source as Node).x}
              y1={(link.source as Node).y}
              x2={(link.target as Node).x}
              y2={(link.target as Node).y}
              stroke={overlay.linkColor || "rgba(255,255,255,0.15)"}
              strokeWidth="1.5"
            />
          ))}
          {/* Render nodes */}
          {processedNodes.map((node, i) => (
            <circle
              key={`node-${i}`}
              cx={node.x}
              cy={node.y}
              r="6"
              fill={overlay.nodeColor || "#3b82f6"}
              style={{ filter: "drop-shadow(0 0 10px rgba(59,130,246,0.6))" }}
            />
          ))}
        </g>
      </svg>
    </div>
  );
};
