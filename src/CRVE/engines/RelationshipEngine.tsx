import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill } from 'remotion';
import * as d3 from 'd3';
import Xarrow, { Xwrapper, useXarrow } from 'react-xarrows';
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
  const updateXarrow = useXarrow();

  React.useEffect(() => {
    const handle = requestAnimationFrame(() => {
      updateXarrow();
    });
    return () => cancelAnimationFrame(handle);
  }, [frame, updateXarrow]);

  const relativeFrame = frame - start;
  const centerX = position?.x ?? width / 2;
  const centerY = position?.y ?? height / 2;

  // Identify the active Scene ID
  const activeSceneId = rawNodes[0]?.scene_id || "SCENE_1";

  // Dynamic Scene-Level Style, Mood, & Layout Planning Override
  // This guarantees that every scene has a completely unique visual theme, color scheme, and topology!
  // Supports both English (SCENE_N) and Bangla (দৃশ্য_N) identifiers robustly.
  const { resolvedMood, resolvedLayout } = useMemo(() => {
    let resolvedMood: CinematicMood = cinematic_mood;
    let resolvedLayout = layout_type;

    const isScene1 = activeSceneId === 'SCENE_1' || activeSceneId === 'দৃশ্য_১' || activeSceneId === 'দৃশ্য ১' || activeSceneId.includes('1') || activeSceneId.includes('১');
    const isScene2 = activeSceneId === 'SCENE_2' || activeSceneId === 'দৃশ্য_২' || activeSceneId === 'দৃশ্য ২' || activeSceneId.includes('2') || activeSceneId.includes('২');
    const isScene3 = activeSceneId === 'SCENE_3' || activeSceneId === 'দৃশ্য_৩' || activeSceneId === 'দৃশ্য ৩' || activeSceneId.includes('3') || activeSceneId.includes('৩');
    const isScene4 = activeSceneId === 'SCENE_4' || activeSceneId === 'দৃশ্য_৪' || activeSceneId === 'দৃশ্য ৪' || activeSceneId.includes('4') || activeSceneId.includes('৪');

    if (isScene1) {
      resolvedMood = 'scientific';
      resolvedLayout = 'solar_system';
    } else if (isScene2) {
      resolvedMood = 'cyberpunk';
      resolvedLayout = 'radial';
    } else if (isScene3) {
      resolvedMood = 'danger';
      resolvedLayout = 'force';
    } else if (isScene4) {
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

    // Topological ranking relaxation algorithm for flow of information
    const ranks: { [id: string]: number } = {};
    nodes.forEach(n => {
        ranks[n.id] = 0;
    });

    // Relax up to 10 times to propagate ranks correctly (DAG structure)
    for (let i = 0; i < 10; i++) {
        let changed = false;
        links.forEach(l => {
            const srcId = typeof l.source === 'object' ? (l.source as any).id : l.source;
            const tgtId = typeof l.target === 'object' ? (l.target as any).id : l.target;
            if (ranks[srcId] !== undefined && ranks[tgtId] !== undefined) {
                const targetRank = ranks[srcId] + 1;
                if (targetRank > ranks[tgtId]) {
                    ranks[tgtId] = targetRank;
                    changed = true;
                }
            }
        });
        if (!changed) break;
    }

    // Attach ranks to nodes
    nodes.forEach((n: any) => {
        n.rank = ranks[n.id] ?? 0;
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

  // Function to calculate smooth continuous opacity based on active window and transition cushion
  const getActiveOpacity = (item: any) => {
      if (!item.active_windows) return 1.0; // Default to active if no windows defined

      // Calculate a smooth 10-frame cushion for fading in/out
      let maxOpacity = 0.0;
      const cushion = 10;
      for (const [s, e] of item.active_windows) {
          if (frame >= s && frame <= e) {
              const fromStart = frame - s;
              const fromEnd = e - frame;
              const fadeIn = interpolate(fromStart, [0, cushion], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
              const fadeOut = interpolate(fromEnd, [0, cushion], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
              const currentOpacity = Math.min(fadeIn, fadeOut);
              if (currentOpacity > maxOpacity) {
                  maxOpacity = currentOpacity;
              }
          }
      }
      return maxOpacity;
  };

  const isActive = (item: any) => {
      if (!item.active_windows) return true;
      return getActiveOpacity(item) > 0.0;
  };

  const getNodeOpacityAtFrame = (node: any) => {
    if (!node) return 0;
    const isHeader = node.isHeaderNode;
    const nodeRank = node.rank ?? 0;
    const rankDelay = isHeader ? 0 : nodeRank * 35;
    const entryFrame = Math.max(0, relativeFrame - rankDelay);

    const entryScale = spring({
        frame: entryFrame,
        fps,
        config: { damping: 16, stiffness: 60 }
    });

    let windowOpacity = 1.0;
    if (node.active_windows) {
        let maxOpacity = 0.0;
        const cushion = 10;
        for (const [s, e] of node.active_windows) {
            if (frame >= s && frame <= e) {
                const fromStart = frame - s;
                const fromEnd = e - frame;
                const fadeIn = interpolate(fromStart, [0, cushion], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                const fadeOut = interpolate(fromEnd, [0, cushion], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                const currentOpacity = Math.min(fadeIn, fadeOut);
                if (currentOpacity > maxOpacity) {
                    maxOpacity = currentOpacity;
                }
            }
        }
        windowOpacity = maxOpacity;
    }

    const nodeOpacity = interpolate(entryScale, [0, 1], [0, windowOpacity]);
    return nodeOpacity * progress;
  };

  const getLinkOpacityAtFrame = (link: any, sourceNode: any, targetNode: any) => {
    const linkActiveOpacity = getActiveOpacity(link);
    const sourceOpacity = getNodeOpacityAtFrame(sourceNode);
    const targetOpacity = getNodeOpacityAtFrame(targetNode);
    return linkActiveOpacity * sourceOpacity * targetOpacity;
  };

  // Helper to construct react-xarrows props per scene mood and active state
  const getXarrowProps = (link: any) => {
    const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
    const targetId = typeof link.target === 'object' ? link.target.id : link.target;

    const sourceNode = nodes.find(n => n.id === sourceId);
    const targetNode = nodes.find(n => n.id === targetId);

    const active = isActive(link) || (sourceNode ? isActive(sourceNode) : false) || (targetNode ? isActive(targetNode) : false);

    let arrowColor = mood.colors.primary;
    let pathType: 'smooth' | 'grid' | 'straight' = 'smooth';
    let dashnessSetting: any = { strokeLen: 10, nonStrokeLen: 5, animation: 1.5 };
    let strokeWidth = active ? 4 : 2;
    let headSize = 6;

    if (resolvedMood === 'scientific') {
      arrowColor = mood.colors.primary;
      pathType = 'straight';
      dashnessSetting = { strokeLen: 12, nonStrokeLen: 6, animation: 1 };
      strokeWidth = active ? 4 : 1.5;
    } else if (resolvedMood === 'cyberpunk') {
      arrowColor = mood.colors.secondary;
      pathType = 'smooth';
      dashnessSetting = { strokeLen: 6, nonStrokeLen: 12, animation: 3 };
      strokeWidth = active ? 5 : 2;
      headSize = 8;
    } else if (resolvedMood === 'danger') {
      arrowColor = mood.colors.accent;
      pathType = 'smooth'; // Smooth paths prevent awkward disjointed orthogonal turns in scene 3
      dashnessSetting = { strokeLen: 15, nonStrokeLen: 5, animation: 2 };
      strokeWidth = active ? 5 : 2;
      headSize = 9;
    } else if (resolvedMood === 'luxury_hud') {
      arrowColor = mood.colors.primary;
      pathType = 'smooth';
      dashnessSetting = { strokeLen: 20, nonStrokeLen: 10, animation: 0.5 };
      strokeWidth = active ? 3.5 : 1.5;
      headSize = 5;
    }

    return {
      start: String(sourceId),
      end: String(targetId),
      lineColor: arrowColor,
      headColor: arrowColor,
      strokeWidth,
      showHead: true,
      headSize,
      path: pathType,
      dashness: dashnessSetting,
      animateDrawing: 1.2,
      zIndex: 10
    };
  };

  return (
    <AbsoluteFill className="pointer-events-none" style={{ position: 'relative' }}>
      <EnvironmentEngine fx={background_fx} lighting={lighting_style} color={mood.colors.primary} />

      <Xwrapper>
        {/*
          Unified Node Container:
          Renders nodes inside a 1x-scaled absolute container so that DOM coordinates
          measured via getBoundingClientRect() exactly match the react-xarrows viewport coordinates.
        */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 10
          }}
        >
          {/* Nodes Layer (Each Node is represented as a beautifully placed HTML component) */}
          {nodes.map((node: any, i: number) => {
            const floatY = Math.sin(frame * (node.isHeaderNode ? 0.02 : 0.035) + hashString(node.id)) * (node.isHeaderNode ? 3 : 5);
            const floatX = Math.cos(frame * (node.isHeaderNode ? 0.015 : 0.025) + hashString(node.id)) * (node.isHeaderNode ? 2 : 3);

            return (
              <div
                key={node.id}
                id={String(node.id)}
                style={{
                  position: 'absolute',
                  left: `${centerX + node.x + floatX}px`,
                  top: `${centerY + node.y + floatY}px`,
                  transform: 'translate(-50%, -50%)',
                  zIndex: 20,
                  pointerEvents: 'none'
                }}
              >
                <CRVENode
                  node={node}
                  progress={progress}
                  active={isActive(node)}
                  font={node.font || font}
                  cinematic_mood={resolvedMood}
                  index={i}
                  startFrame={start}
                />
              </div>
            );
          })}
        </div>

        {/*
          react-xarrows connections layer (rendered outside the scaled container, at 1x scale)
          This ensures react-xarrows calculates screen-space coordinates perfectly and tracks beautifully!
        */}
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%', zIndex: 15 }}>
          {links.map((link) => {
            const sourceId = typeof link.source === 'object' ? (link.source as any).id : link.source;
            const targetId = typeof link.target === 'object' ? (link.target as any).id : link.target;

            const sourceNode = (nodes as any[]).find((n: any) => n.id === sourceId);
            const targetNode = (nodes as any[]).find((n: any) => n.id === targetId);

            // Determine if both source and target have begun revealing to follow information flow
            const sourceRank = sourceNode ? ((sourceNode as any).rank ?? 0) : 0;
            const targetRank = targetNode ? ((targetNode as any).rank ?? 0) : 0;
            const isSourceRevealed = relativeFrame >= (sourceNode?.isHeaderNode ? 0 : sourceRank * 35);
            const isTargetRevealed = relativeFrame >= (targetNode?.isHeaderNode ? 0 : targetRank * 35);

            const active = (isActive(link) || (sourceNode ? isActive(sourceNode) : false) || (targetNode ? isActive(targetNode) : false)) &&
                           isSourceRevealed && isTargetRevealed;

            if (!active) return null;

            // Calculate precise smooth connection line opacity based on parent and child node visibility
            const linkOpacity = getLinkOpacityAtFrame(link, sourceNode, targetNode);

            if (linkOpacity <= 0.01) return null;

            return (
              <div
                key={`xarrow-wrapper-${link.id}`}
                style={{
                  opacity: linkOpacity,
                  transition: 'opacity 0.25s ease-out'
                }}
              >
                <Xarrow
                  key={`xarrow-${link.id}`}
                  {...getXarrowProps(link)}
                />
              </div>
            );
          })}
        </div>
      </Xwrapper>
    </AbsoluteFill>
  );
};

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return hash;
}
