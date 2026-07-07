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

  // STABLE SIMULATION: Adaptive spacing and simulation bounds
  const { processedNodes, processedLinks } = useMemo(() => {
    const rawNodes: Node[] = overlay.nodes || [];
    const rawLinks: Link[] = overlay.links || [];
    const nodeCount = rawNodes.length;

    const nodes = rawNodes.map((n, i) => ({ ...n, id: n.id || `node-${i}` }));
    const links = rawLinks.map((l, i) => ({ ...l, id: l.id || `link-${i}` }));

    // Adaptive Simulation Parameters based on node count
    const distance = interpolate(nodeCount, [3, 15], [400, 250], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const charge = interpolate(nodeCount, [3, 15], [-6000, -3000], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const collisionRadius = interpolate(nodeCount, [3, 15], [300, 180], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

    const simulation = d3.forceSimulation<Node>(nodes)
      .force("link", d3.forceLink<Node, Link>(links).id(d => d.id).distance(distance))
      .force("charge", d3.forceManyBody().strength(charge))
      .force("center", d3.forceCenter(0, 0))
      .force("collision", d3.forceCollide().radius(collisionRadius))
      // Force viewport boundaries (approximate)
      .force("x", d3.forceX().strength(0.08))
      .force("y", d3.forceY().strength(0.08))
      .stop();

    for (let i = 0; i < 400; ++i) simulation.tick();

    return { processedNodes: nodes, processedLinks: links };
  }, [overlay.id]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) return null;

  const relativeFrame = frame - overlay.start;
  const centerX = overlay.position?.x ?? width / 2;
  const centerY = overlay.position?.y ?? height / 2;

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

        <rect width="100%" height="100%" fill="url(#ultraGrid)" opacity={masterProgress * 0.6} />

        <g transform={`
            translate(${centerX}, ${centerY})
            rotate(${Math.sin(frame * 0.01) * 2})
            scale(${0.9 + masterProgress * 0.1})
        `}>
          {/* Living Semantic Edges */}
          {processedLinks.map((link, i) => (
            <LivingEdge
                key={`link-${i}`}
                link={link}
                progress={masterProgress}
                relativeFrame={relativeFrame}
                globalFrame={frame}
            />
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
              globalFrame={frame}
              font={overlay.font}
            />
          ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};

const LivingEdge: React.FC<{
    link: Link,
    progress: number,
    relativeFrame: number,
    globalFrame: number
}> = ({ link, progress, relativeFrame, globalFrame }) => {
  const s = link.source as Node;
  const t = link.target as Node;

  if (!s.x || !s.y || !t.x || !t.y) return null;

  // Narration Awareness: Active if both nodes are active or past
  const sActiveAt = (s as any).active_at || 0;
  const tActiveAt = (t as any).active_at || 0;
  const isEdgeActive = globalFrame >= sActiveAt && globalFrame >= tActiveAt;

  const relColor = CATEGORY_COLORS[link.relationship || ''] || '#00F5FF';
  const edgeAlpha = interpolate(progress, [0.6, 1.0], [0, isEdgeActive ? 0.4 : 0.15], { extrapolateLeft: 'clamp' });

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
        strokeWidth={isEdgeActive ? 1.5 : 0.5}
        strokeDasharray={dist}
        strokeDashoffset={dist * (1 - progress)}
      />
      {/* Cinematic Data Stream - Active Links only */}
      {isEdgeActive && (
        <path
            d={path}
            fill="none"
            stroke="white"
            strokeWidth="1.2"
            strokeDasharray={`10, ${dist / 2}`}
            strokeDashoffset={-globalFrame * 5}
            style={{ filter: 'blur(3px)', mixBlendMode: 'screen' }}
            opacity={0.8}
        />
      )}
      {link.display_label && isEdgeActive && progress > 0.95 && (
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

const CinematicNode: React.FC<{
    node: Node,
    i: number,
    total: number,
    progress: number,
    relativeFrame: number,
    globalFrame: number,
    font?: string
}> = ({ node, i, total, progress, relativeFrame, globalFrame, font }) => {
  const nodeReveal = spring({
      frame: relativeFrame - (i * 3),
      fps: 30,
      config: { damping: 25, stiffness: 60 }
  });

  const scaleProgress = nodeReveal * progress;
  if (!node.x || !node.y || scaleProgress <= 0) return null;

  // Narration Awareness
  const activeAt = (node as any).active_at || 0;
  const isPast = globalFrame > activeAt + 60;
  const isActive = globalFrame >= activeAt && globalFrame <= activeAt + 60;
  const isFuture = globalFrame < activeAt;

  const nodeOpacity = isActive ? 1.0 : isPast ? 0.45 : 0.1;
  const importance = node.importance || 1.0;
  const color = CATEGORY_COLORS[node.category || ''] || '#FFFFFF';

  // Adaptive Geometry
  const baseRadius = interpolate(importance, [1.0, 5.0], [50, 100], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  const driftX = Math.sin(globalFrame / 80 + i) * 8;
  const driftY = Math.cos(globalFrame / 75 + i) * 8;

  // Semantic animations derived from relativeFrame
  let pulse = 1;
  if (isActive || node.category === 'threat') {
      pulse = 1 + Math.pow(Math.sin(globalFrame * 0.12 + i), 4) * (isActive ? 0.08 : 0.03);
  }

  const Icon = TYPE_ICONS[node.type || 'concept'] || Brain;
  const showIcon = node.type === 'hero' || node.type === 'statistic' || node.type === 'warning' || isActive;
  const isBangla = /[\u0980-\u09FF]/.test(node.label);

  // Dynamic Label Width
  const labelWidth = Math.max(180, node.label.length * (isBangla ? 22 : 14));

  return (
    <g opacity={nodeOpacity} transform={`translate(${node.x + driftX}, ${node.y + driftY}) scale(${scaleProgress * pulse})`}>
      {/* Ghost Aura */}
      <circle r={baseRadius + 30} fill={color} opacity={isActive ? 0.03 : 0.01} style={{ filter: 'url(#cinematicGlow)' }} />

      {/* HUD Disc */}
      <circle r={baseRadius} fill="rgba(2, 2, 2, 0.88)" style={{ backdropFilter: 'blur(12px)' }} />
      <circle r={baseRadius} fill="none" stroke={color} strokeWidth={isActive ? 2 : 1} strokeOpacity={0.5} />

      {/* Category Details */}
      {node.category === 'mechanism' && (
          <g transform={`rotate(${globalFrame * 1.5})`}>
              <path d={`M ${baseRadius + 12} 0 A ${baseRadius + 12} ${baseRadius + 12} 0 0 1 0 ${baseRadius + 12}`} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" opacity={0.6} />
              <circle cx={baseRadius + 12} cy="0" r="3" fill={color} />
          </g>
      )}

      {node.category === 'threat' && isActive && (
          <g>
              <circle r={baseRadius + 10} fill="none" stroke="#f43f5e" strokeWidth="2" strokeDasharray="4,12" opacity={0.6} />
              <circle r={baseRadius + 5} fill="none" stroke="#f43f5e" strokeWidth="0.5" opacity={0.3} />
          </g>
      )}

      {/* Primary Icon - Selective Visibility */}
      {showIcon && (
        <g transform={`translate(0, -12)`}>
            <Icon size={baseRadius * 0.6} color={color} strokeWidth={isActive ? 2 : 1.5} style={{ filter: isActive ? 'drop-shadow(0 0 10px ' + color + ')' : 'none' }} />
        </g>
      )}

      {/* DETACHED Modern Label - Technical HUD Plate */}
      <g transform={`translate(0, ${baseRadius + 40})`}>
          <rect x={-labelWidth/2} y="-20" width={labelWidth} height="40" rx="4" fill="rgba(0,0,0,0.9)" stroke={color} strokeWidth="0.5" strokeOpacity={isActive ? 0.4 : 0.15} />
          <rect x={-labelWidth/2} y="-20" width="3" height="40" fill={color} opacity={isActive ? 1 : 0.4} />
          <text
            fill="white"
            fontSize={isActive ? "20" : "17"}
            fontWeight="900"
            textAnchor="middle"
            dy="8"
            style={{
                fontFamily: font ? `${font}, Inter, sans-serif` : 'Inter, "Segoe UI", sans-serif',
                letterSpacing: isBangla ? '0px' : '4px',
                textTransform: isBangla ? 'none' : 'uppercase',
                paintOrder: 'stroke',
                stroke: 'black',
                strokeWidth: 5
            }}
          >
            {node.label}
          </text>
      </g>

      {node.type === 'hero' && (
        <g transform={`rotate(${globalFrame * -0.5})`}>
            <circle r={baseRadius + 25} fill="none" stroke={color} strokeWidth="1.5" strokeDasharray="20,40" opacity={0.3} />
        </g>
      )}
    </g>
  );
};
