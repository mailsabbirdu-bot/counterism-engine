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

  // Identify the active Scene ID
  const activeSceneId = rawNodes[0]?.scene_id || "SCENE_1";

  // Dynamic Scene-Level Style, Mood, & Layout Planning Override
  // This guarantees that every scene has a completely unique visual theme, color scheme, and topology!
  const { resolvedMood, resolvedLayout } = useMemo(() => {
    let resolvedMood: CinematicMood = cinematic_mood;
    let resolvedLayout = layout_type;

    if (activeSceneId === 'SCENE_1') {
      resolvedMood = 'scientific';
      resolvedLayout = 'solar_system';
    } else if (activeSceneId === 'SCENE_2') {
      resolvedMood = 'cyberpunk';
      resolvedLayout = 'radial';
    } else if (activeSceneId === 'SCENE_3') {
      resolvedMood = 'danger';
      resolvedLayout = 'force';
    } else if (activeSceneId === 'SCENE_4') {
      resolvedMood = 'luxury_hud';
      resolvedLayout = 'timeline';
    }

    return { resolvedMood, resolvedLayout };
  }, [activeSceneId, cinematic_mood, layout_type]);

  const { nodes, links } = useMemo(() => {
    const nodes = rawNodes.map(n => ({ ...n }));

    // Defensive Filter: Remotion can sometimes pass incomplete data during hot-reload or large renders
    const nodeIds = new Set(nodes.map(n => n.id));
    const validLinks = rawLinks.filter(l => nodeIds.has(l.source) && nodeIds.has(l.target));
    const links = validLinks.map(l => ({ ...l }));

    if (resolvedLayout === 'tree' || resolvedLayout === 'hierarchy') {
        try {
            const root = d3.stratify<any>().id(d => d.id).parentId(d => {
                const link = links.find(l => l.target === d.id);
                return link ? link.source : null;
            })(nodes);
            const treeLayout = d3.tree().size([800, 500]);
            treeLayout(root);
            root.descendants().forEach(d => {
                const n = nodes.find(node => node.id === d.id);
                if (n) { (n as any).x = (d.x ?? 0) - 400; (n as any).y = (d.y ?? 0) - 250; }
            });
        } catch (e) {
            console.error("D3 Stratify failed", e);
        }
    } else if (resolvedLayout === 'radial') {
        const simulation = d3.forceSimulation<any>(nodes)
            .force("link", d3.forceLink<any, any>(links).id(d => d.id).distance(220))
            .force("charge", d3.forceManyBody().strength(-1200))
            .force("r", d3.forceRadial(260))
            .stop();
        for (let i = 0; i < 300; ++i) simulation.tick();
    } else if (resolvedLayout === 'timeline') {
        nodes.forEach((n, i) => {
            (n as any).x = (i - (nodes.length - 1)/2) * 280;
            (n as any).y = (i % 2 === 0 ? -80 : 80);
        });
    } else if (resolvedLayout === 'solar_system' || resolvedLayout === 'orbit') {
        // Place the title / disconnected node first, orbit others around
        const orbitingNodes = nodes.filter(n => {
            const hasLinks = links.some(l => l.source === n.id || l.target === n.id);
            return hasLinks;
        });
        orbitingNodes.forEach((n, i) => {
            const angle = (i / orbitingNodes.length) * Math.PI * 2 + Math.PI / 4;
            const dist = 240;
            (n as any).x = Math.cos(angle) * dist;
            (n as any).y = Math.sin(angle) * dist + 60; // offset downwards to leave space for Title
        });
    } else if (resolvedLayout === 'hex_grid') {
        nodes.forEach((n, i) => {
            const row = Math.floor(i / 3);
            const col = i % 3;
            (n as any).x = (col - 1) * 300 + (row % 2) * 150;
            (n as any).y = (row - 1) * 220;
        });
    } else {
        const simulation = d3.forceSimulation<any>(nodes)
          .force("link", d3.forceLink<any, any>(links).id(d => d.id).distance(280))
          .force("charge", d3.forceManyBody().strength(-1800))
          .force("center", d3.forceCenter(0, 40))
          .stop();

        for (let i = 0; i < 300; ++i) simulation.tick();
    }

    // Programmatic Title anchoring: Identify completely disconnected nodes (like "প্ল্যানেট" in Scene 1)
    // and lock them perfectly as high-importance title nodes centered at the top, avoiding random D3 drifting
    nodes.forEach((n: any) => {
        const hasLinks = links.some(l => l.source === n.id || l.target === n.id ||
                                        (l.source as any).id === n.id || (l.target as any).id === n.id);
        if (!hasLinks) {
            n.isHeaderNode = true;
            n.x = 0;
            n.y = -260; // Beautiful central title header positioning!
        }
    });

    // Programmatic Broadcast Safe-Zone clamping to guarantee 100% visibility of all text labels inside 1920x1080 bounds
    nodes.forEach((n: any) => {
        if (n.isHeaderNode) return; // Header node is already perfectly positioned

        const absX = centerX + (n.x ?? 0);
        const absY = centerY + (n.y ?? 0);

        const minAbsX = 260;
        const maxAbsX = 1660;
        const minAbsY = 160;
        const maxAbsY = 920;

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
  }, [rawNodes, rawLinks, resolvedLayout, centerX, centerY]);

  if (frame < start || frame > start + duration) return null;

  const mood = MOOD_REGISTRY[resolvedMood] || MOOD_REGISTRY['documentary'];

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
        This eliminates coordinate mismatching, offsets, and measurement jitter,
        and guarantees pixel-perfect rendering and perfect tracking even with camera zoom/scale changes!
      */}
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ position: 'absolute', top: 0, left: 0, zIndex: 10 }}>
        <g transform={`translate(${centerX}, ${centerY}) scale(${0.8 + progress * 0.2})`}>

          {/* Unified Connections (Arrows & Floating Knowledge Packets) */}
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

            // TIGHT, COMPACT start/end offsets to bring connectors extremely close to node labels
            const sourceLabelLen = s.label ? s.label.length : 5;
            const targetLabelLen = t.label ? t.label.length : 5;

            // Bring connection lines perfectly close to the text boundaries
            const offsetStart = Math.max(25, sourceLabelLen * 8.5);
            const offsetEnd = Math.max(30, targetLabelLen * 8.5);

            // Safe guard against line overlap
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
            if (resolvedMood === 'cyberpunk') {
                strokeWidth = active ? 5 : 2.5;
                arrowColor = mood.colors.secondary;
            } else if (resolvedMood === 'danger') {
                strokeWidth = active ? 5 : 2.5;
                arrowColor = mood.colors.accent;
            } else if (resolvedMood === 'luxury_hud') {
                strokeWidth = active ? 4.5 : 2;
                arrowColor = mood.colors.primary;
            }

            // Staggered draw-in math: line starts drawing after both of its endpoint nodes have stagger-entered!
            const sourceIdx = nodes.findIndex(n => n.id === s.id);
            const targetIdx = nodes.findIndex(n => n.id === t.id);
            const maxStagger = Math.max(sourceIdx, targetIdx) * 15;

            const lineAge = Math.max(0, relativeFrame - maxStagger - 5);
            const drawProgress = spring({
                frame: lineAge,
                fps: 30,
                config: { damping: 16, stiffness: 50 }
            });

            // Dynamic line write-in using dash offsets
            const lineDashArray = `${length}`;
            const lineDashOffset = length * (1 - drawProgress);

            // Traveling glowing information packet: moves continuously from source to target
            const packetCycle = resolvedMood === 'cyberpunk' ? 35 : resolvedMood === 'danger' ? 25 : 55; // cyber & danger flow faster
            const travelProgress = ((relativeFrame - maxStagger) % packetCycle) / packetCycle;
            const px = x1_opt + (x2_opt - x1_opt) * travelProgress;
            const py = y1_opt + (y2_opt - y1_opt) * travelProgress;

            const isDrawing = drawProgress > 0.01;

            return (
              <g key={`unified-link-${link.id}`}>
                {/* Dynamic connection glow backing line */}
                {active && isDrawing && (
                  <path
                    d={`M ${x1_opt} ${y1_opt} L ${x2_opt} ${y2_opt}`}
                    fill="none"
                    stroke={arrowColor}
                    strokeWidth={strokeWidth * 3}
                    strokeDasharray={lineDashArray}
                    strokeDashoffset={lineDashOffset}
                    opacity={0.15}
                    style={{ filter: 'blur(4px)' }}
                  />
                )}

                {/* Connection Line */}
                <path
                  d={`M ${x1_opt} ${y1_opt} L ${x2_opt} ${y2_opt}`}
                  fill="none"
                  stroke={arrowColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={lineDashArray}
                  strokeDashoffset={lineDashOffset}
                  opacity={active ? 0.9 : 0.3}
                />

                {/* Arrow Head Point (Smoothly scales up with the line write-in) */}
                <polygon
                  points="0,0 -12,-5 -12,5"
                  fill={arrowColor}
                  opacity={active ? 0.9 * drawProgress : 0.3 * drawProgress}
                  transform={`translate(${x2_opt}, ${y2_opt}) rotate(${(angle * 180) / Math.PI}) scale(${drawProgress})`}
                />

                {/* Highly dynamic traveling glowing packet (draws user eye attention) */}
                {active && isDrawing && travelProgress >= 0 && (
                  <g>
                    {/* Outer soft aura */}
                    <circle
                      cx={px}
                      cy={py}
                      r={resolvedMood === 'danger' ? 12 : 9}
                      fill={arrowColor}
                      opacity={0.5}
                      style={{ filter: 'blur(3px)' }}
                    />
                    {/* Inner intense core */}
                    <circle
                      cx={px}
                      cy={py}
                      r={4}
                      fill="#ffffff"
                    />
                  </g>
                )}
              </g>
            );
          })}

          {/* Unified Nodes Layer */}
          {nodes.map((node: any, i: number) => (
            <CRVENode
                key={node.id}
                node={node}
                x={node.x}
                y={node.y}
                progress={progress}
                active={isActive(node)}
                font={node.font || font}
                cinematic_mood={resolvedMood}
                index={i}
            />
          ))}

        </g>
      </svg>
    </AbsoluteFill>
  );
};
