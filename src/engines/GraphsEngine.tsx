import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, Easing, AbsoluteFill } from 'remotion';
import * as d3 from 'd3';
import { LucideIcon, Zap, Activity, Brain, Target, ShieldAlert, BarChart3, Image as ImageIcon, MapPin, Clock, Database, ArrowRightLeft } from 'lucide-react';

interface Node extends d3.SimulationNodeDatum {
  id: string;
  label: string;
  type?: 'hero' | 'data' | 'concept' | 'relationship' | 'image' | 'statistic' | 'warning';
  importance?: number;
  emotion?: 'intense' | 'calm' | 'alert' | 'growing' | 'scientific' | 'historical';
  category?: string;
  active_at?: number;
  active_windows?: [number, number][];
  semantic_zone?: 'input' | 'process' | 'result' | 'threat' | 'context';
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
  'what': '#00F5FF', 'where': '#FFD700', 'causes': '#ef4444',
  'threat': '#f43f5e', 'mechanism': '#06b6d4', 'context': '#fbbf24', 'data': '#3b82f6'
};

const EMOTION_COLORS: Record<string, string> = {
    'alert': '#ef4444',
    'intense': '#f43f5e',
    'growing': '#10b981',
    'scientific': '#22d3ee',
    'historical': '#f59e0b',
    'calm': '#3b82f6'
};

const EMOTION_GLOW: Record<string, number> = {
  'intense': 60, 'stable': 15, 'alert': 80, 'calm': 8, 'growing': 40, 'scientific': 30, 'historical': 25
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
      .force("collision", d3.forceCollide().radius(node => {
          const imp = node.importance || 1.0;
          const radius = interpolate(imp, [1.0, 5.0], [50, 100], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
          // COLLISION AWARENESS: Expand radius vertically to account for label plate
          return radius + 60;
      }))
      // Force viewport boundaries
      .force("x", d3.forceX().strength(0.1))
      .force("y", d3.forceY().strength(0.1))
      // SEMANTIC ZONING: Push nodes toward their assigned zones
      .force("semantic", (alpha) => {
          for (const node of nodes) {
              if (!node.semantic_zone) continue;
              const target = { x: 0, y: 0 };
              switch (node.semantic_zone) {
                  case 'context': target.x = -600; target.y = -350; break;
                  case 'input':   target.x = -600; target.y = 0; break;
                  case 'process': target.x = 0;    target.y = 0; break;
                  case 'result':  target.x = 600;  target.y = 0; break;
                  case 'threat':  target.x = 0;    target.y = 400; break;
              }
              node.vx! += (target.x - node.x!) * 0.05 * alpha;
              node.vy! += (target.y - node.y!) * 0.05 * alpha;
          }
      })
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

          {/* Active Node Position Tracking (for CameraEngine) */}
          <ActiveNodeTracker nodes={processedNodes} globalFrame={frame} centerX={centerX} centerY={centerY} />

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

  // Helper for multi-window activation check
  const isConceptActive = (node: Node) => {
      const activeAt = node.active_at ?? 0;
      const windows = node.active_windows || [[activeAt, activeAt + 60]];
      for (const [start] of windows) {
          if (globalFrame >= start) return true;
      }
      return false;
  };

  // Narration Awareness: Edge becomes active when BOTH nodes have been introduced
  const isEdgeActive = isConceptActive(s) && isConceptActive(t);

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

// Component to communicate current active node position to the DOM
// This allows the CameraEngine to potentially find and track the element
const ActiveNodeTracker: React.FC<{ nodes: Node[], globalFrame: number, centerX: number, centerY: number }> = ({ nodes, globalFrame, centerX, centerY }) => {
    const activeNode = nodes.find(n => {
        const activeAt = (n as any).active_at || 0;
        const windows = (n as any).active_windows || [[activeAt, activeAt + 60]];
        for (const [start, end] of windows) {
            if (globalFrame >= start && globalFrame <= end) return true;
        }
        return false;
    });

    if (!activeNode || !activeNode.x || !activeNode.y) return null;

    return (
        <div
            id="active-node-pos"
            data-x={centerX + activeNode.x}
            data-y={centerY + activeNode.y}
            style={{ display: 'none' }}
        />
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

  // Multi-Window Narration Awareness Logic
  const getActivation = () => {
      const activeAt = node.active_at ?? 0;
      const windows = node.active_windows || [[activeAt, activeAt + 60]];

      let isActive = false;
      let isPast = globalFrame > windows[windows.length - 1][1];
      let isFuture = globalFrame < windows[0][0];

      for (const [start, end] of windows) {
          if (globalFrame >= start && globalFrame <= end) {
              isActive = true;
              isPast = false;
              isFuture = false;
              break;
          }
      }
      return { isActive, isPast, isFuture };
  };

  const { isActive, isPast, isFuture } = getActivation();
  const nodeOpacity = isActive ? 1.0 : isPast ? 0.45 : 0.1;
  const importance = node.importance || 1.0;

  // Color is influenced by both Category and Emotion
  const color = EMOTION_COLORS[node.emotion || ''] || CATEGORY_COLORS[node.category || ''] || '#FFFFFF';

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

      {/* Category & Emotion Visual Details */}
      {(node.category === 'mechanism' || node.emotion === 'growing') && (
          <g transform={`rotate(${globalFrame * (node.emotion === 'growing' ? 0.8 : 1.5)})`}>
              <path d={`M ${baseRadius + 12} 0 A ${baseRadius + 12} ${baseRadius + 12} 0 0 1 0 ${baseRadius + 12}`} fill="none" stroke={color} strokeWidth="2" strokeLinecap="round" opacity={0.6} />
              <circle cx={baseRadius + 12} cy="0" r="3" fill={color} />
          </g>
      )}

      {(node.category === 'threat' || node.emotion === 'alert' || node.emotion === 'intense') && isActive && (
          <g>
              <circle r={baseRadius + 10} fill="none" stroke={color} strokeWidth="2" strokeDasharray="4,12" opacity={0.6} />
              <circle r={baseRadius + 5} fill="none" stroke={color} strokeWidth="0.5" opacity={0.3} />
              {/* Alert Scanline */}
              <line x1={-baseRadius} y1={Math.sin(globalFrame * 0.2) * baseRadius} x2={baseRadius} y2={Math.sin(globalFrame * 0.2) * baseRadius} stroke={color} strokeWidth="1" opacity="0.2" />
          </g>
      )}

      {(node.emotion === 'scientific' || node.type === 'statistic') && (
          <g>
              <rect x={-baseRadius} y={-baseRadius} width={baseRadius*2} height={baseRadius*2} fill="none" stroke={color} strokeWidth="0.5" strokeDasharray="2,10" opacity="0.3" />
              <path d={`M ${-baseRadius} 0 L ${baseRadius} 0 M 0 ${-baseRadius} L 0 ${baseRadius}`} stroke={color} strokeWidth="0.5" opacity="0.2" />
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
