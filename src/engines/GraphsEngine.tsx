import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing } from 'remotion';
import * as d3 from 'd3';

interface Node extends d3.SimulationNodeDatum {
  id: string | number;
  label?: string;
  importance?: number;
  type?: string;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | number | Node;
  target: string | number | Node;
  label?: string;
}

export const GraphsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const centerX = overlay.position?.x ?? width / 2;
  const centerY = overlay.position?.y ?? height / 2;

  const { processedNodes, processedLinks } = useMemo(() => {
    const rawNodes: Node[] = overlay.nodes || [];
    const rawLinks: Link[] = overlay.links || [];

    // Deep copy to avoid mutating props
    const nodes = rawNodes.map(n => ({ ...n }));
    const links = rawLinks.map(l => ({ ...l }));

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(250))
      .force("charge", d3.forceManyBody().strength(-800))
      .force("center", d3.forceCenter(centerX, centerY))
      .force("collision", d3.forceCollide().radius(80))
      .stop();

    for (let i = 0; i < 200; ++i) simulation.tick();

    return {
      processedNodes: nodes,
      processedLinks: links
    };
  }, [overlay.nodes, overlay.links, centerX, centerY]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const relativeFrame = frame - overlay.start;
  const entrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 20 },
  });

  const revealProgress = interpolate(
    relativeFrame,
    [0, 60],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.25, 0.1, 0.25, 1) }
  );

  const rotation = frame * (overlay.speed || 0.02);
  const scale = 0.9 + entrance * 0.1 + Math.sin(frame / 120) * 0.02;

  return (
    <div
      className="absolute inset-0 pointer-events-none overflow-hidden"
      style={{ opacity: entrance, zIndex: overlay.zIndex ?? 50 }}
    >
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <filter id="nodeGlow" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="15" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <linearGradient id="edgeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#00F5FF" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#FF3E6C" stopOpacity="0.8" />
          </linearGradient>
        </defs>

        <g transform={`translate(${centerX}, ${centerY}) scale(${scale}) rotate(${rotation}) translate(${-centerX}, ${-centerY})`}>
          {/* Links */}
          {processedLinks.map((link, i) => {
            const s = link.source as Node;
            const t = link.target as Node;
            const linkReveal = interpolate(
              revealProgress,
              [0.2, 0.8],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            if (!s.x || !s.y || !t.x || !t.y) return null;

            return (
              <g key={`link-group-${i}`} opacity={linkReveal}>
                <line
                  x1={s.x}
                  y1={s.y}
                  x2={t.x}
                  y2={t.y}
                  stroke="url(#edgeGradient)"
                  strokeWidth="2"
                  strokeDasharray="8 4"
                  opacity={0.4}
                />
                {link.label && revealProgress > 0.7 && (
                   <text
                     x={(s.x + t.x) / 2}
                     y={(s.y + t.y) / 2}
                     fill="white"
                     fontSize="14"
                     fontWeight="bold"
                     textAnchor="middle"
                     style={{ paintOrder: 'stroke', stroke: 'black', strokeWidth: 3, opacity: revealProgress }}
                   >
                     {link.label}
                   </text>
                )}
              </g>
            );
          })}

          {/* Nodes */}
          {processedNodes.map((node, i) => {
            const nodeReveal = interpolate(
              revealProgress,
              [i / (processedNodes.length + 1), (i + 1) / (processedNodes.length + 1)],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            const imp = node.importance || 1.0;
            const radius = 15 * imp * nodeReveal;
            const color = node.type === 'concept' ? "#FF3E6C" : "#00F5FF";

            if (!node.x || !node.y) return null;

            return (
              <g key={`node-group-${node.id}`} opacity={nodeReveal}>
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius}
                  fill={color}
                  filter="url(#nodeGlow)"
                  style={{
                    boxShadow: `0 0 20px ${color}`
                  }}
                />
                <circle
                  cx={node.x}
                  cy={node.y}
                  r={radius + 5}
                  fill="none"
                  stroke={color}
                  strokeWidth="1"
                  strokeOpacity={0.3}
                />
                {node.label && (
                   <text
                     x={node.x}
                     y={node.y + radius + 25}
                     fill="white"
                     fontSize={20 * imp}
                     fontWeight="black"
                     textAnchor="middle"
                     className="uppercase tracking-tighter"
                     style={{
                        fontFamily: overlay.font || 'Audiowide-Regular_english',
                        textShadow: '0 4px 10px rgba(0,0,0,0.8)'
                     }}
                   >
                     {node.label}
                   </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
};
