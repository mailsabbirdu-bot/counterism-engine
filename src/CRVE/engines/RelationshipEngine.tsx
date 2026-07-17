import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill } from 'remotion';
import * as d3 from 'd3';
import { CRVENodeData, CRVELinkData } from '../lib/types';
import { CRVENode } from '../components/CRVENode';
import { EnvironmentEngine } from '../components/EnvironmentEngine';
import { MOOD_REGISTRY, CinematicMood } from '../lib/moodRegistry';

interface CRVEEngineProps {
  nodes: CRVENodeData[];
  links: CRVELinkData[];
  start: number;
  duration: number;
  position?: { x: number, y: number };
  font?: string;
  layout_type?: string;
  cinematic_mood?: CinematicMood;
  lighting_style?: string;
  background_fx?: string;
}

export const CRVEEngine: React.FC<CRVEEngineProps> = ({
    nodes: rawNodes,
    links: rawLinks,
    start,
    duration,
    position,
    font,
    layout_type = 'force',
    cinematic_mood = 'documentary',
    lighting_style = 'ambient',
    background_fx = 'grid'
}) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const relativeFrame = frame - start;
  const centerX = position?.x ?? width / 2;
  const centerY = position?.y ?? height / 2;

  const { nodes, links } = useMemo(() => {
    const nodes = rawNodes.map(n => ({ ...n }));

    // Defensive Filter: Remotion can sometimes pass incomplete data during hot-reload or large renders
    const nodeIds = new Set(nodes.map(n => n.id));
    const validLinks = rawLinks.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
    const links = validLinks.map(l => ({ ...l }));

    if (layout_type === 'tree' || layout_type === 'hierarchy') {
        try {
            const root = d3.stratify<any>().id(d => d.id).parentId(d => {
                const link = links.find(l => l.target === d.id);
                return link ? link.source : null;
            })(nodes);
            const treeLayout = d3.tree().size([800, 600]);
            treeLayout(root);
            root.descendants().forEach(d => {
                const n = nodes.find(node => node.id === d.id);
                if (n) { (n as any).x = (d.x ?? 0) - 400; (n as any).y = (d.y ?? 0) - 300; }
            });
        } catch (e) {
            console.error("D3 Stratify failed", e);
        }
    } else if (layout_type === 'radial') {
        const simulation = d3.forceSimulation<any>(nodes)
            .force("link", d3.forceLink<any, any>(links).id(d => d.id).distance(200))
            .force("charge", d3.forceManyBody().strength(-1000))
            .force("r", d3.forceRadial(300))
            .stop();
        for (let i = 0; i < 300; ++i) simulation.tick();
    } else if (layout_type === 'timeline') {
        nodes.forEach((n, i) => {
            (n as any).x = (i - nodes.length/2) * 200;
            (n as any).y = (i % 2 === 0 ? -100 : 100);
        });
    } else if (layout_type === 'solar_system' || layout_type === 'orbit') {
        nodes.forEach((n, i) => {
            if (i === 0) {
                (n as any).x = 0;
                (n as any).y = 0;
            } else {
                const angle = (i / (nodes.length - 1)) * Math.PI * 2;
                const dist = 300 + (i % 2) * 50;
                (n as any).x = Math.cos(angle) * dist;
                (n as any).y = Math.sin(angle) * dist;
            }
        });
    } else if (layout_type === 'hex_grid') {
        nodes.forEach((n, i) => {
            const row = Math.floor(i / 3);
            const col = i % 3;
            (n as any).x = (col - 1) * 300 + (row % 2) * 150;
            (n as any).y = (row - 1) * 250;
        });
    } else {
        const simulation = d3.forceSimulation<any>(nodes)
          .force("link", d3.forceLink<any, any>(links).id(d => d.id).distance(350))
          .force("charge", d3.forceManyBody().strength(-2000))
          .force("center", d3.forceCenter(0, 0))
          .stop();

        for (let i = 0; i < 300; ++i) simulation.tick();
    }

    // Programmatic Broadcast Safe-Zone clamping to guarantee 100% visibility of all text labels inside 1920x1080 bounds
    nodes.forEach((n: any) => {
        const absX = centerX + (n.x ?? 0);
        const absY = centerY + (n.y ?? 0);

        const minAbsX = 250;
        const maxAbsX = 1670;
        const minAbsY = 150;
        const maxAbsY = 930;

        if (absX < minAbsX) {
            n.x = minAbsX - centerX;
        } else if (absX > maxAbsX) {
            n.x = maxAbsX - centerX;
        }

        if (absY < minAbsY) {
            n.y = minAbsY - centerY;
        } else if (absY > maxAbsY) {
            n.y = maxAbsY - centerY;
        }
    });

    return { nodes, links };
  }, [rawNodes, rawLinks, layout_type, centerX, centerY]);

  if (frame < start || frame > start + duration) return null;

  const mood = MOOD_REGISTRY[cinematic_mood] || MOOD_REGISTRY['documentary'];

  const progress = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 20, stiffness: 40 }
  }) * interpolate(relativeFrame, [duration - 15, duration], [1, 0], { extrapolateLeft: 'clamp' });

  // Function to check if a relationship or node is currently "active" based on narration
  const isActive = (item: any) => {
      if (!item.active_windows) return true; // Default to active if no windows defined
      return item.active_windows.some(([s, e]: [number, number]) => frame >= s && frame <= e);
  };

  return (
    <AbsoluteFill className="pointer-events-none" style={{ position: 'relative' }}>
      <EnvironmentEngine fx={background_fx} lighting={lighting_style} color={mood.colors.primary} />

      {/*
        Unified SVG Layer:
        Renders BOTH nodes and arrows in the exact same SVG coordinate container.
        This eliminates coordinate mismatching, floating offsets, and measurement jitter,
        and guarantees pixel-perfect rendering and perfect tracking even with camera zoom/scale changes!
      */}
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ position: 'absolute', top: 0, left: 0, zIndex: 10 }}>
        <g transform={`translate(${centerX}, ${centerY}) scale(${0.8 + progress * 0.2})`}>

          {/* Unified Connections (Arrows & Middle Labels) */}
          {links.map((link) => {
            const s = link.source as any;
            const t = link.target as any;

            const x1 = s.x ?? 0;
            const y1 = s.y ?? 0;
            const x2 = t.x ?? 0;
            const y2 = t.y ?? 0;

            const active = isActive(link) || isActive(s) || isActive(t);
            if (!active) return null;

            const dx = x2 - x1;
            const dy = y2 - y1;
            const length = Math.sqrt(dx * dx + dy * dy);

            if (length < 20) return null;

            // Dynamic offset based on label length to avoid overlapping with the text
            const sourceLabelLen = s.label ? s.label.length : 5;
            const targetLabelLen = t.label ? t.label.length : 5;

            const offsetStart = Math.max(50, sourceLabelLen * 15);
            const offsetEnd = Math.max(60, targetLabelLen * 15);

            // Safe guard against extremely short lines overlapping
            const startFactor = length > offsetStart + offsetEnd ? offsetStart / length : 0.1;
            const endFactor = length > offsetStart + offsetEnd ? offsetEnd / length : 0.1;

            const x1_opt = x1 + dx * startFactor;
            const y1_opt = y1 + dy * startFactor;
            const x2_opt = x2 - dx * endFactor;
            const y2_opt = y2 - dy * endFactor;

            const angle = Math.atan2(y2_opt - y1_opt, x2_opt - x1_opt);

            // Style connections per relationship and mood
            let strokeWidth = active ? 4 : 2;
            let arrowColor = mood.colors.primary;
            if (cinematic_mood === 'cyberpunk') {
                strokeWidth = active ? 5 : 2;
                arrowColor = mood.colors.secondary;
            } else if (cinematic_mood === 'danger') {
                strokeWidth = active ? 5 : 2;
                arrowColor = mood.colors.accent;
            }

            // Dash array styling based on relationship type
            let dasharray = "none";
            const rel = link.relationship.toLowerCase();
            if (rel === 'causes' || rel === 'threatens' || rel === 'danger' || rel === 'energy_transfer') {
                dasharray = "5,5";
            } else if (rel === 'is_a' || rel === 'containment' || rel === 'located_in') {
                dasharray = "10,5";
            } else if (rel === 'forms' || rel === 'aggregation' || rel === 'construction_flow') {
                dasharray = "2,2";
            }

            const mx = (x1_opt + x2_opt) / 2;
            const my = (y1_opt + y2_opt) / 2;
            const labelText = link.relationship;
            const rectW = Math.max(80, labelText.length * 11 + 20);
            const rectH = 32;

            return (
              <g key={`unified-link-${link.id}`}>
                {/* Connection Line */}
                <path
                  d={`M ${x1_opt} ${y1_opt} L ${x2_opt} ${y2_opt}`}
                  fill="none"
                  stroke={arrowColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={dasharray}
                  opacity={active ? 0.9 : 0.3}
                />

                {/* Arrow Head / Terminal Point */}
                { (rel === 'causes' || rel === 'threatens' || rel === 'danger' || rel === 'energy_transfer') ? (
                  <polygon
                    points="0,0 -12,-6 -12,6"
                    fill={arrowColor}
                    opacity={active ? 0.9 : 0.3}
                    transform={`translate(${x2_opt}, ${y2_opt}) rotate(${(angle * 180) / Math.PI})`}
                  />
                ) : (
                  <circle
                    cx={x2_opt}
                    cy={y2_opt}
                    r={6}
                    fill={arrowColor}
                    opacity={active ? 0.9 : 0.3}
                  />
                )}

                {/* Glassmorphic/HUD Middle Label Box */}
                <g transform={`translate(${mx}, ${my})`}>
                  <rect
                    x={-rectW / 2}
                    y={-rectH / 2}
                    width={rectW}
                    height={rectH}
                    rx={6}
                    fill="rgba(5, 5, 5, 0.9)"
                    stroke={arrowColor}
                    strokeWidth={1.5}
                    opacity={active ? 0.95 : 0.4}
                    style={{ filter: 'drop-shadow(0 0 8px rgba(0,0,0,0.6))' }}
                  />
                  <text
                    fill="white"
                    textAnchor="middle"
                    dy="5"
                    style={{
                      fontSize: '14px',
                      fontWeight: 800,
                      fontFamily: font || 'Inter, sans-serif',
                      letterSpacing: '1px',
                      textTransform: 'uppercase',
                      opacity: active ? 1.0 : 0.5
                    }}
                  >
                    {labelText}
                  </text>
                </g>
              </g>
            );
          })}

          {/* Unified Nodes Layer */}
          {nodes.map((node: any) => (
            <CRVENode
                key={node.id}
                node={node}
                x={node.x}
                y={node.y}
                progress={progress}
                active={isActive(node)}
                font={node.font || font}
                cinematic_mood={cinematic_mood}
            />
          ))}

        </g>
      </svg>
    </AbsoluteFill>
  );
};
