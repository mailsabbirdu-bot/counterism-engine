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

  // STABLE SIMULATION: Keyed by overlay ID to ensure stability
  const { processedNodes, processedLinks } = useMemo(() => {
    const rawNodes: Node[] = overlay.nodes || [];
    const rawLinks: Link[] = overlay.links || [];

    const nodes = rawNodes.map((n, i) => ({ ...n, id: n.id || `node-${i}` }));
    const links = rawLinks.map((l, i) => ({ ...l, id: l.id || `link-${i}` }));

    // ULTIMATE SPACING: Enforce extreme collision radius to completely eliminate overlap
    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(450))
      .force("charge", d3.forceManyBody().strength(-6000))
      .force("center", d3.forceCenter(0, 0))
      .force("collision", d3.forceCollide().radius(320))
      .stop();

    // Deeper stabilization
    for (let i = 0; i < 500; ++i) simulation.tick();

    return { processedNodes: nodes, processedLinks: links };
  }, [overlay.id]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) return null;

  const relativeFrame = frame - overlay.start;
  const centerX = overlay.position?.x ?? width / 2;
  const centerY = overlay.position?.y ?? height / 2;

  // ULTRA-SLEEK ENTRANCE: High damping, no overshoot
  const masterEntrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 30, stiffness: 40, mass: 2.0 }
  });

  const exitFrame = overlay.duration - 15;
  const exit = interpolate(relativeFrame, [exitFrame, exitFrame + 15], [1, 0], { extrapolateLeft: 'clamp' });
  const masterProgress = masterEntrance * exit;

  return (
    <AbsoluteFill className="pointer-events-none overflow-hidden" style={{ zIndex: overlay.zIndex ?? 50 }}>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <filter id="cinematicGlow" x="-200%" y="-200%" width="500%" height="500%">
            <feGaussianBlur stdDeviation="40" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <pattern id="ultraGrid" width="120" height="120" patternUnits="userSpaceOnUse">
            <circle cx="0" cy="0" r="1" fill="rgba(255,255,255,0.06)" />
            <path d="M 120 0 L 0 0 0 120" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="0.5" />
          </pattern>
        </defs>

        {/* HUD Grid Background */}
        <rect width="100%" height="100%" fill="url(#ultraGrid)" opacity={masterProgress * 0.6} />

        {/* Global Cinematic Orbit - Now a very subtle wavering instead of constant rotation */}
        <g transform={`
            translate(${centerX}, ${centerY})
            rotate(${Math.sin(frame * 0.01) * 2})
            scale(${0.9 + masterProgress * 0.1})
        `}>
          {/* Living Semantic Edges */}
          {processedLinks.map((link, i) => (
            <LivingEdge key={`link-${i}`} link={link} progress={masterProgress} relativeFrame={relativeFrame} />
          ))}

          {/* Floating Conceptual Discs */}
          {processedNodes.map((node, i) => (
            <CinematicNode
              key={node.id}
              node={node}
              i={i}
              total={processedNodes.length}
              progress={masterProgress}
              relativeFrame={relativeFrame}
              font={overlay.font}
            />
          ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};

const LivingEdge: React.FC<{ link: Link, progress: number, relativeFrame: number }> = ({ link, progress, relativeFrame }) => {
  const s = link.source as Node;
  const t = link.target as Node;

  if (!s.x || !s.y || !t.x || !t.y) return null;

  const relColor = CATEGORY_COLORS[link.relationship || ''] || '#00F5FF';
  const edgeAlpha = interpolate(progress, [0.6, 1.0], [0, 0.25], { extrapolateLeft: 'clamp' });

  const dx = t.x - s.x;
  const dy = t.y - s.y;
  const dist = Math.sqrt(dx*dx + dy*dy);
  const midX = (s.x + t.x) / 2 + (dy * 0.3);
  const midY = (s.y + t.y) / 2 - (dx * 0.3);

  const path = `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
  const pathId = `p-${link.id.replace(/\s/g, '-')}`;

  return (
    <g opacity={edgeAlpha}>
      <path
        id={pathId}
        d={path}
        fill="none"
        stroke={relColor}
        strokeWidth="0.5"
        strokeDasharray={dist}
        strokeDashoffset={dist * (1 - progress)}
      />
      {/* Cinematic Data Stream */}
      <path
        d={path}
        fill="none"
        stroke="white"
        strokeWidth="1"
        strokeDasharray={`8, ${dist / 2}`}
        strokeDashoffset={-relativeFrame * 6}
        style={{ filter: 'blur(3px)', mixBlendMode: 'screen' }}
        opacity={0.8}
      />
      {link.display_label && progress > 0.95 && (
        <text
          dy="-15"
          textAnchor="middle"
          style={{
              fontSize: '11px',
              fontWeight: 900,
              fill: relColor,
              fontFamily: 'Inter, sans-serif',
              letterSpacing: '6px',
              textTransform: 'uppercase',
              filter: 'drop-shadow(0 0 3px black)'
          }}
        >
          <textPath href={`#${pathId}`} startOffset="50%">
            {link.display_label}
          </textPath>
        </text>
      )}
    </g>
  );
};

const CinematicNode: React.FC<{ node: Node, i: number, total: number, progress: number, relativeFrame: number, font?: string }> = ({ node, i, total, progress, relativeFrame, font }) => {
  const nodeReveal = spring({
      frame: relativeFrame - (i * 4), // Staggered reveal
      fps: 30,
      config: { damping: 25, stiffness: 60 }
  });

  const scale = nodeReveal * progress;
  if (!node.x || !node.y || scale <= 0) return null;

  const importance = node.importance || 1.0;
  const color = CATEGORY_COLORS[node.category || ''] || '#FFFFFF';

  // Sleek organic drift - Now even more subtle to prevent "jumping"
  const driftX = Math.sin(relativeFrame / 80 + i) * 8;
  const driftY = Math.cos(relativeFrame / 75 + i) * 8;

  // Semantic animations
  let pulse = 1;
  if (node.category === 'threat' || node.emotion === 'alert' || node.emotion === 'intense') {
      pulse = 1 + Math.pow(Math.sin(relativeFrame * 0.1 + i), 4) * 0.05; // Heartbeat pulse
  } else {
      pulse = 1 + Math.sin(relativeFrame * 0.05 + i) * 0.02; // Calm breathing
  }

  const Icon = TYPE_ICONS[node.type || 'concept'] || Brain;
  const isBangla = /[\u0980-\u09FF]/.test(node.label);

  return (
    <g transform={`translate(${node.x + driftX}, ${node.y + driftY}) scale(${scale * pulse * (0.9 + importance * 0.1)})`}>
      {/* Ghost Aura - Large, subtle glow */}
      <circle r={100} fill={color} opacity={0.015} style={{ filter: 'url(#cinematicGlow)' }} />

      {/* Glass HUD Disc - Multi-layered & Refined */}
      <circle r="60" fill="rgba(5, 5, 5, 0.75)" style={{ backdropFilter: 'blur(15px)' }} />
      <circle r="60" fill="none" stroke={color} strokeWidth="1" strokeOpacity={0.4} />

      {/* Category Specific Technical Details */}
      {node.category === 'threat' && (
          <g>
              <circle r="68" fill="none" stroke="#f43f5e" strokeWidth="2" strokeDasharray="4,16" opacity={0.6}>
                  <animate attributeName="stroke-opacity" values="0.6;0.2;0.6" dur="2s" repeatCount="indefinite" />
              </circle>
          </g>
      )}

      {node.category === 'mechanism' && (
          <g transform={`rotate(${relativeFrame * 2})`}>
              <path d="M 72 0 A 72 72 0 0 1 0 72" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" opacity={0.5} />
              <path d="M -72 0 A 72 72 0 0 1 0 -72" fill="none" stroke={color} strokeWidth="3" strokeLinecap="round" opacity={0.5} />
          </g>
      )}

      {/* Rotating Data Rings */}
      <g transform={`rotate(${relativeFrame * 0.4 * (i % 2 === 0 ? 1 : -1)})`}>
          <path d="M 68 0 A 68 68 0 0 1 0 68" fill="none" stroke={color} strokeWidth="1" strokeLinecap="round" opacity={0.3} />
          <circle cx="68" cy="0" r="2" fill={color} />
      </g>

      {/* Primary Icon - Elevated */}
      <g transform="translate(0, -12)">
        <Icon size={34} color={color} strokeWidth={1.5} style={{ filter: 'drop-shadow(0 0 12px ' + color + '66)' }} />
      </g>

      {/* DETACHED Modern Label - Technical HUD Plate */}
      <g transform="translate(0, 95)">
          {/* Transparent plate with glow border */}
          <rect x="-100" y="-18" width="200" height="36" rx="2" fill="rgba(0,0,0,0.8)" stroke="rgba(255,255,255,0.05)" strokeWidth="0.5" />
          <rect x="-100" y="-18" width="2" height="36" fill={color} /> {/* Technical Side-bar */}
          <text
            fill="white"
            fontSize="16"
            fontWeight="900"
            textAnchor="middle"
            dy="6"
            style={{
                fontFamily: font ? `${font}, Inter, sans-serif` : 'Inter, "Segoe UI", sans-serif',
                letterSpacing: isBangla ? '0px' : '4px',
                textTransform: isBangla ? 'none' : 'uppercase',
                paintOrder: 'stroke',
                stroke: 'black',
                strokeWidth: 4
            }}
          >
            {node.label}
          </text>
      </g>

      {node.type === 'hero' && (
        <g>
            <circle r={85} fill="none" stroke={color} strokeWidth="2" strokeDasharray="20,60" opacity={0.4}>
              <animateTransform attributeName="transform" type="rotate" from="0 0 0" to="360 0 0" dur="12s" repeatCount="indefinite" />
            </circle>
            <circle r={92} fill="none" stroke={color} strokeWidth="0.5" opacity={0.2} />
        </g>
      )}
    </g>
  );
};
