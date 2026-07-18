import React, { useEffect } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import Xarrow, { Xwrapper, useXarrow } from 'react-xarrows';

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
  preset: 'quantum' | 'tech_grid' | 'organic_flow' | 'electric_pulse' | 'double_trace' | 'neural_synapse';
  label?: string;
  startAnchorPosition?: 'top' | 'bottom' | 'left' | 'right' | 'middle';
  endAnchorPosition?: 'top' | 'bottom' | 'left' | 'right' | 'middle';
}

const DEFAULT_NODES: NodeConfig[] = [
  { id: 'node_core', label: 'QUANTUM CORE', x: 960, y: 540, type: 'system', importance: 3.0 },
  { id: 'node_sensor_1', label: 'SENSORY NODE A', x: 400, y: 300, type: 'concept', importance: 1.5 },
  { id: 'node_sensor_2', label: 'SENSORY NODE B', x: 400, y: 780, type: 'concept', importance: 1.5 },
  { id: 'node_analytics', label: 'ANALYTICS ENGINE', x: 1520, y: 540, type: 'metric', importance: 2.5 },
  { id: 'node_aux', label: 'AUXILIARY MATRIX', x: 960, y: 150, type: 'system', importance: 2.0 },
  { id: 'node_external', label: 'EXTERNAL GATE', x: 1520, y: 150, type: 'concept', importance: 1.8 }
];

const DEFAULT_LINKS: LinkConfig[] = [
  {
    id: 'link_s1_core',
    source: 'node_sensor_1',
    target: 'node_core',
    preset: 'quantum',
    label: 'QUANTUM_STREAM',
    startAnchorPosition: 'right',
    endAnchorPosition: 'top',
  },
  {
    id: 'link_s2_core',
    source: 'node_sensor_2',
    target: 'node_core',
    preset: 'tech_grid',
    label: 'BUS_TRACE_0X7F',
    startAnchorPosition: 'right',
    endAnchorPosition: 'bottom',
  },
  {
    id: 'link_core_analytics',
    source: 'node_core',
    target: 'node_analytics',
    preset: 'organic_flow',
    startAnchorPosition: 'right',
    endAnchorPosition: 'left',
  },
  {
    id: 'link_aux_core',
    source: 'node_aux',
    target: 'node_core',
    preset: 'double_trace',
    label: 'STABLE_TRUNK',
    startAnchorPosition: 'bottom',
    endAnchorPosition: 'top',
  },
  {
    id: 'link_aux_external',
    source: 'node_aux',
    target: 'node_external',
    preset: 'electric_pulse',
    label: 'DISCHARGE_02',
    startAnchorPosition: 'right',
    endAnchorPosition: 'left',
  },
  {
    id: 'link_external_analytics',
    source: 'node_external',
    target: 'node_analytics',
    preset: 'neural_synapse',
    label: 'SYNAPSE_SIGNAL',
    startAnchorPosition: 'bottom',
    endAnchorPosition: 'top',
  }
];

export const XarrowMasteryDemo: React.FC<XarrowMasteryDemoProps> = ({
  nodes = DEFAULT_NODES,
  links = DEFAULT_LINKS,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const updateXarrow = useXarrow();

  // Clean, deterministic sync with Remotion's step clock (rAF removed for extreme speed optimization)
  useEffect(() => {
    updateXarrow();
  }, [frame, updateXarrow]);

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
      {/* GLOBAL SVG DEFINITIONS: Rendered safely exactly once to prevent tree duplications or performance bottlenecks */}
      <svg style={{ position: 'absolute', width: 0, height: 0 }}>
        <defs>
          <filter id="cyberpunk-neon-cyan" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="luxury-neon-gold" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="4" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="discharge-green" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="5" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
          <filter id="intense-red" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="7" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      </svg>

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
        {/* Nodes Layer */}
        {nodes.map((node, index) => {
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

        {/* Connections Layer (Showcasing Highly Differentiated Documentary Arrow styles) */}
        {links.map((link) => {
          const drawProgress = interpolate(frame, [25, 75], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          // PRESET 1: Quantum Cyber Connector (Moving Glow Line + Laser blue)
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
                arrowHeadProps={{
                  fill: '#00f3ff',
                  stroke: 'none',
                }}
                arrowBodyProps={{
                  strokeDasharray: '12, 18',
                  strokeDashoffset: (drawProgress * 800 + frame * 1.5).toString(),
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
              />
            );
          }

          // PRESET 2: Tech Grid Interface (Orthogonal grid dot trace + Amber)
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
              />
            );
          }

          // PRESET 4: Double Trunk/Trace Line (Johnny Harris Style clean double vector lines)
          if (link.preset === 'double_trace') {
            return (
              <React.Fragment key={link.id}>
                {/* Left Line */}
                <Xarrow
                  start={link.source}
                  end={link.target}
                  startAnchor={{ position: link.startAnchorPosition || 'auto', offset: { x: -4, y: 0 } }}
                  endAnchor={{ position: link.endAnchorPosition || 'auto', offset: { x: -4, y: 0 } }}
                  color="rgba(255, 255, 255, 0.25)"
                  strokeWidth={1.5}
                  path="straight"
                  showHead={false}
                  arrowBodyProps={{
                    strokeDasharray: '800',
                    strokeDashoffset: (drawProgress * 800).toString(),
                  }}
                />
                {/* Right Line */}
                <Xarrow
                  start={link.source}
                  end={link.target}
                  startAnchor={{ position: link.startAnchorPosition || 'auto', offset: { x: 4, y: 0 } }}
                  endAnchor={{ position: link.endAnchorPosition || 'auto', offset: { x: 4, y: 0 } }}
                  color="rgba(255, 255, 255, 0.25)"
                  strokeWidth={1.5}
                  path="straight"
                  showHead={false}
                  arrowBodyProps={{
                    strokeDasharray: '800',
                    strokeDashoffset: (drawProgress * 800).toString(),
                  }}
                  labels={{
                    middle: (
                      <div
                        style={{
                          fontSize: '8px',
                          fontFamily: 'monospace',
                          color: '#ffffff',
                          background: '#040406',
                          border: '1px solid rgba(255,255,255,0.15)',
                          borderRadius: '2px',
                          padding: '1px 4px',
                          opacity: 0.6,
                        }}
                      >
                        {link.label}
                      </div>
                    )
                  }}
                />
              </React.Fragment>
            );
          }

          // PRESET 5: Animated Electric Pulse / Discharge (Glowing Green Electric stream)
          if (link.preset === 'electric_pulse') {
            return (
              <Xarrow
                key={link.id}
                start={link.source}
                end={link.target}
                startAnchor={link.startAnchorPosition || 'auto'}
                endAnchor={link.endAnchorPosition || 'auto'}
                color="#10b981"
                strokeWidth={2.5}
                path="smooth"
                curveness={0.7}
                headSize={5}
                arrowBodyProps={{
                  strokeDasharray: '15, 30',
                  strokeDashoffset: (-frame * 4.0).toString(), // High speed movement
                  filter: 'url(#discharge-green)',
                }}
                labels={{
                  middle: (
                    <div
                      style={{
                        fontSize: '9px',
                        fontFamily: 'monospace',
                        color: '#10b981',
                        textShadow: '0 0 8px #10b981',
                        transform: 'translateY(-12px)',
                      }}
                    >
                      ⚡ {link.label}
                    </div>
                  )
                }}
              />
            );
          }

          // PRESET 6: Neural Synapse (Crystalline dots marching along curved tracks)
          if (link.preset === 'neural_synapse') {
            return (
              <Xarrow
                key={link.id}
                start={link.source}
                end={link.target}
                startAnchor={link.startAnchorPosition || 'auto'}
                endAnchor={link.endAnchorPosition || 'auto'}
                color="#ef4444"
                strokeWidth={2}
                path="smooth"
                curveness={0.9}
                headSize={0}
                arrowBodyProps={{
                  strokeDasharray: '2, 10', // Fine dotted synapse look
                  strokeDashoffset: (frame * 1.8).toString(),
                  filter: 'url(#intense-red)',
                }}
              />
            );
          }

          // PRESET 3: Default fallback: Organic Minimalist Flow (Translucent organic bezier)
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
              headSize={0}
              arrowBodyProps={{
                strokeLinecap: 'round',
                strokeDasharray: '800',
                strokeDashoffset: (drawProgress * 800).toString(),
              }}
            />
          );
        })}
      </Xwrapper>
    </div>
  );
};

export default XarrowMasteryDemo;
