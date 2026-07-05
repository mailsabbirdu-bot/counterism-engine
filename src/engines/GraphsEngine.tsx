import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, AbsoluteFill } from 'remotion';
import * as d3 from 'd3';
import { LucideIcon, Zap, Activity, Brain, Target, ShieldAlert, BarChart3, Image as ImageIcon, MapPin, Clock, Database, ArrowRightLeft } from 'lucide-react';

interface Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type?: 'hero' | 'data' | 'concept' | 'relationship' | 'image' | 'statistic';
  importance?: number;
  emotion?: 'intense' | 'calm' | 'alert' | 'growing';
  category?: string;
}

interface Link extends d3.SimulationLinkDatum<Node> {
  source: string | Node;
  target: string | Node;
  relationship?: string;
  display_label?: string;
}

const CATEGORY_COLORS: Record<string, string> = {
  'why': '#f43f5e', 'how': '#8b5cf6', 'when': '#fbbf24',
  'how_many': '#10b981', 'reason': '#f97316', 'input': '#3b82f6',
  'output': '#06b6d4', 'result': '#ec4899', 'dependency': '#a855f7',
  'what': '#00F5FF', 'where': '#FFD700', 'causes': '#ef4444'
};

const EMOTION_GLOW: Record<string, number> = {
  'intense': 60, 'stable': 15, 'alert': 80, 'calm': 8, 'growing': 40
};

const TYPE_ICONS: Record<string, LucideIcon> = {
  'hero': Target, 'data': Database, 'concept': Brain,
  'relationship': ArrowRightLeft, 'image': ImageIcon, 'statistic': BarChart3
};

export const GraphsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const centerX = overlay.position?.x ?? width / 2;
  const centerY = overlay.position?.y ?? height / 2;

  const { processedNodes, processedLinks } = useMemo(() => {
    const rawNodes: Node[] = overlay.nodes || [];
    const rawLinks: Link[] = overlay.links || [];

    const nodes = rawNodes.map(n => ({ ...n }));
    const links = rawLinks.map(l => ({ ...l }));

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(300))
      .force("charge", d3.forceManyBody().strength(-1500))
      .force("center", d3.forceCenter(centerX, centerY))
      .force("collision", d3.forceCollide().radius(120))
      .stop();

    for (let i = 0; i < 250; ++i) simulation.tick();

    return { processedNodes: nodes, processedLinks: links };
  }, [overlay.nodes, overlay.links, centerX, centerY]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) return null;

  const relativeFrame = frame - overlay.start;
  const revealProgress = interpolate(relativeFrame, [0, 60], [0, 1], {
    extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 1, 0.68, 1)
  });

  return (
    <AbsoluteFill className="pointer-events-none overflow-hidden" style={{ zIndex: overlay.zIndex ?? 50 }}>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <filter id="cinematicGlow" x="-100%" y="-100%" width="300%" height="300%">
            <feGaussianBlur stdDeviation="20" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        <g transform={`translate(${centerX}, ${centerY}) rotate(${frame * 0.01}) translate(${-centerX}, ${-centerY})`}>
          {/* Edges */}
          {processedLinks.map((link, i) => (
            <LivingEdge key={`link-${i}`} link={link} revealProgress={revealProgress} />
          ))}

          {/* Nodes */}
          {processedNodes.map((node, i) => (
            <CinematicNode key={node.id} node={node} i={i} total={processedNodes.length} revealProgress={revealProgress} font={overlay.font} />
          ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};

const LivingEdge: React.FC<{ link: Link, revealProgress: number }> = ({ link, revealProgress }) => {
  const s = link.source as Node;
  const t = link.target as Node;
  const frame = useCurrentFrame();

  if (!s.x || !s.y || !t.x || !t.y) return null;

  const edgeReveal = interpolate(revealProgress, [0.1, 0.9], [0, 1], { extrapolateRight: 'clamp' });
  const relColor = CATEGORY_COLORS[link.relationship || ''] || '#00F5FF';

  const length = Math.sqrt((t.x - s.x) ** 2 + (t.y - s.y) ** 2);
  const dashOffset = -frame * 2;

  return (
    <g opacity={edgeReveal}>
      <path
        d={`M ${s.x} ${s.y} Q ${(s.x + t.x) / 2 + 50} ${(s.y + t.y) / 2 - 50} ${t.x} ${t.y}`}
        fill="none"
        stroke={relColor}
        strokeWidth="2"
        strokeDasharray="10 5"
        strokeDashoffset={dashOffset}
        opacity={0.3}
      />
      {link.display_label && edgeReveal > 0.8 && (
        <text
          x={(s.x + t.x) / 2}
          y={(s.y + t.y) / 2 - 20}
          fill={relColor}
          fontSize="16"
          fontWeight="900"
          textAnchor="middle"
          className="uppercase tracking-[0.2em]"
          style={{ paintOrder: 'stroke', stroke: 'black', strokeWidth: 4 }}
        >
          {link.display_label}
        </text>
      )}
    </g>
  );
};

const CinematicNode: React.FC<{ node: Node, i: number, total: number, revealProgress: number, font?: string }> = ({ node, i, total, revealProgress, font }) => {
  const frame = useCurrentFrame();
  const nodeReveal = interpolate(revealProgress, [i / (total + 1), (i + 1) / (total + 1)], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  if (!node.x || !node.y) return null;

  const imp = node.importance || 1.0;
  const color = CATEGORY_COLORS[node.category || ''] || '#FFFFFF';
  const glowIntensity = EMOTION_GLOW[node.emotion || ''] || 20;

  // Breathe micro-animation
  const breathe = Math.sin(frame / 20 + i) * 0.05 + 1;
  const floatY = Math.sin(frame / 30 + i) * 10;

  const Icon = TYPE_ICONS[node.type || 'concept'] || Brain;

  return (
    <g transform={`translate(${node.x}, ${node.y + floatY}) scale(${nodeReveal * breathe * imp})`}>
      {/* Dynamic Aura */}
      <circle r={40 + glowIntensity} fill={color} opacity={0.1 * nodeReveal} style={{ filter: 'blur(30px)' }} />

      {/* Glassmorphism Card */}
      <rect x="-80" y="-40" width="160" height="80" rx="20" fill="rgba(10, 10, 10, 0.8)" stroke={color} strokeWidth="2" style={{ filter: 'url(#cinematicGlow)' }} />

      <g transform="translate(-60, 0)">
        <Icon size={24} color={color} />
      </g>

      <text
        x="10"
        y="5"
        fill="white"
        fontSize="18"
        fontWeight="900"
        textAnchor="middle"
        className="uppercase"
        style={{ fontFamily: font || 'Inter', letterSpacing: '1px' }}
      >
        {node.label}
      </text>

      {node.type === 'hero' && (
        <circle r={90} fill="none" stroke={color} strokeWidth="1" strokeDasharray="4 4" opacity={0.5}>
          <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" dur="10s" repeatCount="indefinite" />
        </circle>
      )}
    </g>
  );
};
