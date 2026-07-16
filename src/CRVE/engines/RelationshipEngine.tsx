import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate, AbsoluteFill } from 'remotion';
import * as d3 from 'd3';
import { CRVENodeData, CRVELinkData } from '../lib/types';
import { CRVENode } from '../components/CRVENode';
import { ParticleStream, EnergyBeam, HUDConnector, ElectricArc, LiquidFlow, LaserSweep, SankeyLink } from '../components/RelationshipLayers';
import { getGrammar } from '../lib/styleRegistry';
import { getBezierPath } from '../lib/pathUtils';

interface CRVEEngineProps {
  nodes: CRVENodeData[];
  links: CRVELinkData[];
  start: number;
  duration: number;
  position?: { x: number, y: number };
  font?: string;
  layout_type?: string;
}

export const CRVEEngine: React.FC<CRVEEngineProps> = ({ nodes: rawNodes, links: rawLinks, start, duration, position, font, layout_type = 'force' }) => {
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
                if (n) { (n as any).x = d.x - 400; (n as any).y = d.y - 300; }
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
    <AbsoluteFill className="pointer-events-none">
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <g transform={`translate(${centerX}, ${centerY}) scale(${0.8 + progress * 0.2})`}>
          {/* 1. Relationship Layer */}
          {links.map((link, i) => {
            const s = link.source as any;
            const t = link.target as any;
            const grammar = getGrammar(link.relationship);
            const path = getBezierPath({ x: s.x, y: s.y }, { x: t.x, y: t.y });
            const active = isActive(link) || isActive(s) || isActive(t);

            if (grammar.style === 'particle_stream') {
                return <ParticleStream key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
            }
            if (grammar.style === 'pulse_line' || grammar.style === 'laser_beam') {
                return <EnergyBeam key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
            }
            if (grammar.style === 'electric_arc') {
                return <ElectricArc key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
            }
            if (grammar.style === 'liquid_flow') {
                return <LiquidFlow key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
            }
            if (grammar.style === 'laser_sweep') {
                return <LaserSweep key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
            }
            if (grammar.style === 'sankey_link') {
                return <SankeyLink key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
            }
            return <HUDConnector key={link.id} path={path} grammar={grammar} progress={progress} active={active} />;
          })}

          {/* 2. Node Layer */}
          {nodes.map((node: any) => (
            <CRVENode
                key={node.id}
                node={node}
                x={node.x}
                y={node.y}
                progress={progress}
                active={isActive(node)}
                font={font}
            />
          ))}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
