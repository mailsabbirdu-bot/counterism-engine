import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill } from 'remotion';
import * as d3 from 'd3';
import Xarrow, { Xwrapper } from 'react-xarrows';
import { CRVENodeData, CRVELinkData } from '../lib/types';
import { CRVENode } from '../components/CRVENode';
import {
    ParticleStream, EnergyBeam, HUDConnector, ElectricArc, LiquidFlow,
    LaserSweep, SankeyLink, ElectricDischarge, EnergyRibbon, BreakingLine
} from '../components/RelationshipLayers';
import { DNAEdge, CircuitEdge, NeuralEdge } from '../components/UniqueEdges';
import { EnvironmentEngine } from '../components/EnvironmentEngine';
import { getGrammar } from '../lib/styleRegistry';
import { getBezierPath } from '../lib/pathUtils';
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

  const { nodes, links } = useMemo(() => {
    const nodes = rawNodes.map(n => ({ ...n }));

    // Defensive Filter: Remotion can sometimes pass incomplete data during hot-reload or large renders
    // D3-force link initialize will CRASH if a source/target node is missing.
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
    return { nodes, links };
  }, [rawNodes, rawLinks, layout_type]);

  if (frame < start || frame > start + duration) return null;

  const relativeFrame = frame - start;
  const centerX = position?.x ?? width / 2;
  const centerY = position?.y ?? height / 2;

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
      <Xwrapper>
        {/* SVG Nodes and High-Fidelity Animated Connections Layer */}
        <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} style={{ position: 'absolute', top: 0, left: 0, zIndex: 10 }}>
          <g transform={`translate(${centerX}, ${centerY}) scale(${0.8 + progress * 0.2})`}>
            {/* 1. SVG Custom High-Fidelity Animated Connections */}
            {links.map((link) => {
              const s = link.source as any;
              const t = link.target as any;
              const active = isActive(link) || isActive(s) || isActive(t);
              if (!active) return null;

              if (typeof s === 'object' && typeof t === 'object') {
                const grammar = getGrammar(link.relationship);
                const customGrammar = {
                  ...grammar,
                  color: cinematic_mood === 'cyberpunk' ? mood.colors.secondary :
                         cinematic_mood === 'danger' ? mood.colors.accent :
                         grammar.color
                };

                const path = getBezierPath(s, t);

                switch (grammar.style) {
                  case 'particle_stream':
                    return <ParticleStream key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  case 'laser_beam':
                    return <EnergyBeam key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  case 'electric_arc':
                    return <ElectricArc key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  case 'liquid_flow':
                    return <LiquidFlow key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  case 'laser_sweep':
                    return <LaserSweep key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  case 'sankey_link':
                    return <SankeyLink key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  case 'pulse_line':
                    return <ElectricDischarge key={`svg-link-${link.id}`} path={path} grammar={customGrammar} progress={progress} active={active} />;
                  default:
                    return (
                      <path
                        key={`svg-link-${link.id}`}
                        d={path}
                        fill="none"
                        stroke={customGrammar.color}
                        strokeWidth={customGrammar.width}
                        strokeOpacity={active ? 0.8 * progress : 0.2 * progress}
                      />
                    );
                }
              }
              return null;
            })}

            {/* 2. SVG Nodes */}
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

        {/* Dynamic Connections Layer using react-xarrows */}
        {links.map((link, i) => {
          const s = link.source as any;
          const t = link.target as any;
          const startId = typeof s === 'object' ? s.id : s;
          const endId = typeof t === 'object' ? t.id : t;
          const active = isActive(link) || isActive(s) || isActive(t);

          if (!active) return null;

          // 1. Dynamic headShape based on relationship type (must be supported arrow shapes: arrow1, circle, heart)
          let headShape: "arrow1" | "circle" = "arrow1";
          const rel = link.relationship.toLowerCase();
          if (rel === 'causes' || rel === 'threatens' || rel === 'danger' || rel === 'energy_transfer') {
              headShape = "arrow1";
          } else if (rel === 'is_a' || rel === 'containment' || rel === 'located_in') {
              headShape = "circle";
          } else if (rel === 'forms' || rel === 'aggregation' || rel === 'construction_flow') {
              headShape = "circle";
          }

          // 2. Dynamic dashness (animation speed & patterns) unique per scene and mood
          let dashness: any = false;
          if (cinematic_mood === 'cyberpunk') {
              dashness = { strokeLen: 15, nonStrokeLen: 5, animation: 1.0 };
          } else if (cinematic_mood === 'military') {
              dashness = { strokeLen: 4, nonStrokeLen: 4, animation: 2.0 };
          } else if (cinematic_mood === 'scientific') {
              dashness = { strokeLen: 8, nonStrokeLen: 4, animation: 0.5 };
          } else if (cinematic_mood === 'danger') {
              dashness = { strokeLen: 6, nonStrokeLen: 3, animation: 0.3 };
          } else if (rel === 'builds' || rel === 'produces' || rel === 'construction_flow') {
              dashness = { strokeLen: 12, nonStrokeLen: 8, animation: 1.0 };
          } else if (rel === 'causes' || rel === 'energy_transfer') {
              dashness = { strokeLen: 10, nonStrokeLen: 4, animation: 0.6 };
          }

          // 3. Dynamic strokeWidth & color based on mood
          let strokeWidth = active ? 4 : 2;
          let arrowColor = mood.colors.primary;
          if (cinematic_mood === 'cyberpunk') {
              strokeWidth = active ? 6 : 3;
              arrowColor = mood.colors.secondary;
          } else if (cinematic_mood === 'danger') {
              strokeWidth = active ? 5 : 2;
              arrowColor = mood.colors.accent;
          }

          // 4. Dynamic Label Sizes based on connection strength
          const strength = link.strength || 1.0;
          const fontSize = Math.max(12, Math.min(22, Math.round(strength * 15)));
          const paddingY = Math.max(2, Math.round(strength * 4));
          const paddingX = Math.max(6, Math.round(strength * 10));

          return (
            <Xarrow
              key={link.id}
              start={startId}
              end={endId}
              color={arrowColor}
              strokeWidth={strokeWidth}
              dashness={dashness}
              showHead={true}
              headShape={headShape}
              headSize={active ? 6 : 4}
              path={layout_type === 'timeline' ? 'grid' : 'smooth'}
              curveness={0.3}
              labels={{
                middle: (
                  <div
                    style={{
                      background: 'rgba(5, 5, 5, 0.85)',
                      backdropFilter: 'blur(8px)',
                      border: `1.5px solid ${arrowColor}`,
                      borderRadius: '8px',
                      padding: `${paddingY}px ${paddingX}px`,
                      color: '#ffffff',
                      fontSize: `${fontSize}px`,
                      fontWeight: 900,
                      fontFamily: font || 'Inter, sans-serif',
                      textTransform: 'uppercase',
                      boxShadow: `0 0 12px ${arrowColor}66`,
                    }}
                  >
                    {link.relationship}
                  </div>
                )
              }}
              divContainerStyle={{
                zIndex: 5,
              }}
              SVGcanvasStyle={{
                zIndex: 5,
              }}
            />
          );
        })}
      </Xwrapper>
    </AbsoluteFill>
  );
};
