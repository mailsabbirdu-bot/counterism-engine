import React, { useEffect, useState } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import Xarrow, { Xwrapper, useXarrow } from 'react-xarrows';

// Interfaces for our Configuration driven structures
export interface NodeConfig {
  id: string;
  label: string;
  x: number;
  y: number;
  type: 'concept' | 'metric' | 'system';
  importance: number;
}

export interface LinkConfig {
  id: string;
  source: string;
  target: string;
  preset: 'quantum' | 'tech_grid' | 'organic_flow';
  label?: string;
  startAnchorPosition?: 'top' | 'bottom' | 'left' | 'right' | 'middle';
  endAnchorPosition?: 'top' | 'bottom' | 'left' | 'right' | 'middle';
}

interface XarrowMasteryDemoProps {
  nodes?: NodeConfig[];
  links?: LinkConfig[];
}

// Mock Data representing a realistic JSON configuration
const DEFAULT_NODES: NodeConfig[] = [
  { id: 'node_core', label: 'QUANTUM CORE', x: 960, y: 540, type: 'system', importance: 3.0 },
  { id: 'node_sensor_1', label: 'SENSORY NODE A', x: 400, y: 300, type: 'concept', importance: 1.5 },
  { id: 'node_sensor_2', label: 'SENSORY NODE B', x: 400, y: 780, type: 'concept', importance: 1.5 },
  { id: 'node_analytics', label: 'ANALYTICS ENGINE', x: 1520, y: 540, type: 'metric', importance: 2.5 },
];

const DEFAULT_LINKS: LinkConfig[] = [
  // Preset 1: Quantum pipeline from sensor 1 to core
  {
    id: 'link_s1_core',
    source: 'node_sensor_1',
    target: 'node_core',
    preset: 'quantum',
    label: 'SIGNAL_STREAM_A',
    startAnchorPosition: 'right',
    endAnchorPosition: 'top',
  },
  // Preset 2: Tech grid layout from sensor 2 to core
  {
    id: 'link_s2_core',
    source: 'node_sensor_2',
    target: 'node_core',
    preset: 'tech_grid',
    label: 'BUS_TRACE_0X7F',
    startAnchorPosition: 'right',
    endAnchorPosition: 'bottom',
  },
  // Preset 3: Organic minimal flow from core to analytics
  {
    id: 'link_core_analytics',
    source: 'node_core',
    target: 'node_analytics',
    preset: 'organic_flow',
    startAnchorPosition: 'right',
    endAnchorPosition: 'left',
  },
];

export const XarrowMasteryDemo: React.FC<XarrowMasteryDemoProps> = ({
  nodes = DEFAULT_NODES,
  links = DEFAULT_LINKS,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const updateXarrow = useXarrow();

  // Standard React hook to update Xarrows coordinates recursively inside Remotion frame-loop.
  // This solves any coordinate lagging or state sync offset errors!
  useEffect(() => {
    let animationFrameId: number;
    const forceUpdate = () => {
      updateXarrow();
      animationFrameId = requestAnimationFrame(forceUpdate);
    };
    animationFrameId = requestAnimationFrame(forceUpdate);
    return () => cancelAnimationFrame(animationFrameId);
  }, [updateXarrow, frame]);

  // SVG Glow Definition Filter children
  const svgDefinitions = (
    <defs>
      {/* Laser Cyan cyber glow */}
      <filter id="cyberpunk-neon-cyan" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="6" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
      {/* Luxury Gold HUD glow */}
      <filter id="luxury-neon-gold" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="4" result="blur" />
        <feMerge>
          <feMergeNode in="blur" />
          <feMergeNode in="SourceGraphic" />
        </feMerge>
      </filter>
    </defs>
  );

  return (
    <div
      style={{
        position: 'absolute',
        width: '1920px',
        height: '1080px',
        background: '#040406',
        color: '#ffffff',
        overflow: 'hidden',
        fontFamily: 'system-ui, -apple-system, sans-serif',
      }}
    >
      {/* Subtle tech background grid pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          opacity: 0.8,
        }}
      />

      <Xwrapper>
        {/* Render absolute positioned HTML nodes */}
        {nodes.map((node, index) => {
          // Stagger node entry reveal beautifully
          const nodeDelay = index * 12;
          const scaleSpring = spring({
            frame: Math.max(0, frame - nodeDelay),
            fps,
            config: { damping: 15, stiffness: 75 },
          });

          const isCore = node.type === 'system';

          return (
            <div
              key={node.id}
              id={node.id}
              style={{
                position: 'absolute',
                left: `${node.x}px`,
                top: `${node.y}px`,
                transform: `translate(-50%, -50%) scale(${scaleSpring})`,
                zIndex: 20,
                // Premium glassmorphic container styling
                background: isCore
                  ? 'linear-gradient(135deg, rgba(0, 243, 255, 0.08), rgba(0, 243, 255, 0.01))'
                  : 'rgba(10, 10, 14, 0.85)',
                border: isCore
                  ? '1px solid rgba(0, 243, 255, 0.3)'
                  : '1px solid rgba(255, 255, 255, 0.08)',
                boxShadow: isCore
                  ? '0 10px 40px rgba(0, 243, 255, 0.15), inset 0 0 15px rgba(0, 243, 255, 0.05)'
                  : '0 10px 30px rgba(0, 0, 0, 0.5)',
                padding: '16px 28px',
                borderRadius: isCore ? '16px' : '8px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                userSelect: 'none',
              }}
            >
              {/* Technical category label */}
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: 'monospace',
                  textTransform: 'uppercase',
                  letterSpacing: '0.25em',
                  color: isCore ? '#00f3ff' : 'rgba(255, 255, 255, 0.4)',
                  marginBottom: '6px',
                }}
              >
                {node.type} // size:{node.importance.toFixed(1)}
              </span>

              {/* Node Title label */}
              <h3
                style={{
                  fontSize: `${14 + node.importance * 3}px`,
                  fontWeight: 800,
                  margin: 0,
                  letterSpacing: '0.08em',
                  textShadow: isCore ? '0 0 15px rgba(0, 243, 255, 0.4)' : 'none',
                }}
              >
                {node.label}
              </h3>
            </div>
          );
        })}

        {/* Dynamic Frame-bound Connection Vectors */}
        {links.map((link) => {
          // Dynamic calculation for reveal starting frame
          const drawProgress = interpolate(frame, [25, 75], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          // Setup presets using detailed low level configs
          if (link.preset === 'quantum') {
            return (
              <Xarrow
                key={link.id}
                start={link.source}
                end={link.target}
                startAnchor={{ position: link.startAnchorPosition || 'auto', offset: { x: 5, y: 0 } }}
                endAnchor={{ position: link.endAnchorPosition || 'auto', offset: { x: 0, y: -5 } }}
                color="#00f3ff"
                strokeWidth={3}
                path="smooth"
                curveness={0.8}
                headSize={6}
                // Custom high fidelity arrowhead
                arrowHeadProps={{
                  fill: '#00f3ff',
                  stroke: 'none',
                }}
                // Dynamic drawing progress + custom glowing filter
                arrowBodyProps={{
                  strokeDasharray: '12, 18',
                  strokeDashoffset: (drawProgress * 800 + frame * 1.5).toString(), // Tied to frame for moving waves
                  filter: 'url(#cyberpunk-neon-cyan)',
                  strokeLinecap: 'round',
                }}
                labels={{
                  middle: (
                    <div
                      style={{
                        fontSize: '9px',
                        fontFamily: 'monospace',
                        color: '#00f3ff',
                        background: '#040406',
                        padding: '2px 8px',
                        border: '1px solid rgba(0, 243, 255, 0.2)',
                        borderRadius: '4px',
                        transform: 'translateY(-15px)',
                        letterSpacing: '0.1em',
                        boxShadow: '0 4px 10px rgba(0,0,0,0.5)',
                      }}
                    >
                      {link.label}
                    </div>
                  ),
                }}
                SVGcanvasProps={{
                  children: svgDefinitions,
                }}
              />
            );
          }

          if (link.preset === 'tech_grid') {
            return (
              <Xarrow
                key={link.id}
                start={link.source}
                end={link.target}
                startAnchor={{ position: link.startAnchorPosition || 'auto', offset: { x: 5, y: 0 } }}
                endAnchor={{ position: link.endAnchorPosition || 'auto', offset: { x: 0, y: 5 } }}
                color="rgba(255, 198, 0, 0.4)"
                strokeWidth={1.5}
                path="grid"
                gridBreak="40%"
                headSize={4}
                // Frame-locked dash movement (marching data packets style)
                arrowBodyProps={{
                  strokeDasharray: '6, 6',
                  strokeDashoffset: (-frame * 2.5).toString(),
                  filter: 'url(#luxury-neon-gold)',
                }}
                labels={{
                  middle: (
                    <div
                      style={{
                        fontSize: '9px',
                        fontFamily: 'monospace',
                        color: '#ffc600',
                        background: '#0a0a0e',
                        padding: '1px 6px',
                        borderRadius: '3px',
                        border: '1px solid rgba(255, 198, 0, 0.2)',
                        transform: 'translate(-50%, -50%)',
                        letterSpacing: '0.12em',
                      }}
                    >
                      {link.label}
                    </div>
                  ),
                }}
                SVGcanvasProps={{
                  children: svgDefinitions,
                }}
              />
            );
          }

          // Default fallback: organic minimalist flow preset
          return (
            <Xarrow
              key={link.id}
              start={link.source}
              end={link.target}
              startAnchor={link.startAnchorPosition || 'auto'}
              endAnchor={link.endAnchorPosition || 'auto'}
              color="rgba(255, 255, 255, 0.12)"
              strokeWidth={5}
              path="smooth"
              curveness={0.5}
              headSize={0} // No arrowhead
              arrowBodyProps={{
                strokeLinecap: 'round',
                strokeDasharray: '800',
                strokeDashoffset: (drawProgress * 800).toString(), // Smooth drawing write-on reveal
              }}
            />
          );
        })}
      </Xwrapper>
    </div>
  );
};
export default XarrowMasteryDemo;
