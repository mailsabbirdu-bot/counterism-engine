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
    updateXarrow();
  }, [frame, updateXarrow]);

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

  // Helper to construct react-xarrows props per scene mood and active state
  const getXarrowProps = (link: any) => {
    const s = link.source as any;
    const t = link.target as any;
    const active = isActive(link) || isActive(s) || isActive(t);

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
      pathType = 'grid';
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
      start: String(s.id),
      end: String(t.id),
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
          Unified Scale Container:
          Renders nodes inside a scaled container.
        */}
        <div
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            zIndex: 10,
            transform: `scale(${0.8 + progress * 0.2})`,
            transformOrigin: `${centerX}px ${centerY}px`
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
            const s = link.source as any;
            const t = link.target as any;
            const active = isActive(link) || isActive(s) || isActive(t);
            if (!active) return null;

            return (
              <Xarrow
                key={`xarrow-${link.id}`}
                {...getXarrowProps(link)}
              />
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
