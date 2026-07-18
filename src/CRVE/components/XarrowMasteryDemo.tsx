import React, { useEffect, useMemo } from 'react';
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
  revealFrameStart?: number; // Decoupled frame control
  revealDuration?: number;   // Decoupled frame speed
}

interface XarrowMasteryDemoProps {
  nodes?: NodeConfig[];
  links?: LinkConfig[];
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
    revealFrameStart: 15,
    revealDuration: 40
  },
  {
    id: 'link_s2_core',
    source: 'node_sensor_2',
    target: 'node_core',
    preset: 'tech_grid',
    label: 'BUS_TRACE_0X7F',
    startAnchorPosition: 'right',
    endAnchorPosition: 'bottom',
    revealFrameStart: 25,
    revealDuration: 35
  },
  {
    id: 'link_core_analytics',
    source: 'node_core',
    target: 'node_analytics',
    preset: 'organic_flow',
    startAnchorPosition: 'right',
    endAnchorPosition: 'left',
    revealFrameStart: 45,
    revealDuration: 50
  },
  {
    id: 'link_aux_core',
    source: 'node_aux',
    target: 'node_core',
    preset: 'double_trace',
    label: 'STABLE_TRUNK',
    startAnchorPosition: 'bottom',
    endAnchorPosition: 'top',
    revealFrameStart: 5,
    revealDuration: 30
  },
  {
    id: 'link_aux_external',
    source: 'node_aux',
    target: 'node_external',
    preset: 'electric_pulse',
    label: 'DISCHARGE_02',
    startAnchorPosition: 'right',
    endAnchorPosition: 'left',
    revealFrameStart: 20,
    revealDuration: 45
  },
  {
    id: 'link_external_analytics',
    source: 'node_external',
    target: 'node_analytics',
    preset: 'neural_synapse',
    label: 'SYNAPSE_SIGNAL',
    startAnchorPosition: 'bottom',
    endAnchorPosition: 'top',
    revealFrameStart: 35,
    revealDuration: 40
  }
];

export const XarrowMasteryDemo: React.FC<XarrowMasteryDemoProps> = ({
  nodes = DEFAULT_NODES,
  links = DEFAULT_LINKS,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const updateXarrow = useXarrow();

  // Precise frame alignment matrix
  useEffect(() => {
    updateXarrow();
  }, [frame, updateXarrow]);

  // Global High-Fidelity SVG filters, completely isolated for absolute safety
  const globalSvgDefinitions = useMemo(() => (
    <svg style={{ position: 'absolute', width: 0, height: 0, pointerEvents: 'none' }}>
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
        {/* Fractal Turbulence filter for genuine organic electric currents */}
        <filter id="electric-distortion" x="-20%" y="-20%" width="140%" height="140%">
          <feTurbulence type="fractalNoise" baseFrequency="0.05" numOctaves="3" result="noise" />
          <feDisplacementMap in="SourceGraphic" in2="noise" scale="7" xChannelSelector="R" yChannelSelector="G" />
        </filter>
      </defs>
    </svg>
  ), []);

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
      {globalSvgDefinitions}

      {/* Modern technical mesh grid pattern */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(255, 255, 255, 0.035) 1.5px, transparent 1.5px)',
          backgroundSize: '48px 48px',
          opacity: 0.9,
        }}
      />

      <Xwrapper>
        {/* Nodes Layer */}
        {nodes.map((node, index) => {
          const nodeDelay = index * 8;
          const scaleSpring = spring({
            frame: Math.max(0, frame - nodeDelay),
            fps,
            config: { damping: 14, stiffness: 85 },
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
                  ? 'linear-gradient(135deg, rgba(0, 243, 255, 0.06), rgba(0, 243, 255, 0.01))'
                  : 'rgba(10, 10, 14, 0.92)',
                border: isCore
                  ? '1px solid rgba(0, 243, 255, 0.35)'
                  : '1px solid rgba(255, 255, 255, 0.07)',
                boxShadow: isCore
                  ? '0 15px 45px rgba(0, 243, 255, 0.12), inset 0 0 12px rgba(0, 243, 255, 0.04)'
                  : '0 12px 35px rgba(0, 0, 0, 0.6)',
                padding: '14px 24px',
                borderRadius: isCore ? '14px' : '6px',
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
                  letterSpacing: '0.2em',
                  color: isCore ? '#00f3ff' : 'rgba(255, 255, 255, 0.35)',
                  marginBottom: '4px',
                }}
              >
                {node.type}
              </span>
              {/* Wrapped title protected against complex scripts/joint fonts layout breakage */}
              <h3
                style={{
                  fontSize: `${13 + node.importance * 3.5}px`,
                  fontWeight: 800,
                  margin: 0,
                  letterSpacing: '0.06em',
                  whiteSpace: 'nowrap',
                  textShadow: isCore ? '0 0 12px rgba(0, 243, 255, 0.35)' : 'none',
                }}
              >
                {node.label}
              </h3>
            </div>
          );
        })}

        {/* Multi-Pass Documentary Connections Layer */}
        {links.map((link) => {
          const startFrame = link.revealFrameStart ?? 20;
          const endFrame = startFrame + (link.revealDuration ?? 40);

          const drawProgress = interpolate(frame, [startFrame, endFrame], [1, 0], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });

          const baseProps = {
            start: link.source,
            end: link.target,
            startAnchor: { position: link.startAnchorPosition || 'auto' },
            endAnchor: { position: link.endAnchorPosition || 'auto' },
          };

          // DYNAMIC VISUAL PACK DEFINITIONS
          switch (link.preset) {
            case 'quantum':
              return (
                <React.Fragment key={link.id}>
                  {/* PASS 1: The High-End Diffuse Neon Conduit */}
                  <Xarrow
                    {...baseProps}
                    color="rgba(0, 243, 255, 0.12)"
                    strokeWidth={7}
                    path="smooth"
                    curveness={0.7}
                    showHead={false}
                    arrowBodyProps={{
                      filter: 'url(#cyberpunk-neon-cyan)',
                      strokeLinecap: 'round',
                    }}
                  />
                  {/* PASS 2: The Core Concentrated Particle Flow */}
                  <Xarrow
                    {...baseProps}
                    color="#00f3ff"
                    strokeWidth={2}
                    path="smooth"
                    curveness={0.7}
                    headSize={5}
                    arrowHeadProps={{ fill: '#00f3ff', stroke: 'none' }}
                    arrowBodyProps={{
                      strokeDasharray: '20, 100',
                      strokeDashoffset: (drawProgress * 600 + frame * 3.5).toString(),
                      strokeLinecap: 'round',
                    }}
                    labels={{
                      middle: (
                        <div style={{
                          fontSize: '8px', fontFamily: 'monospace', color: '#00f3ff',
                          background: '#040406', padding: '2px 8px', border: '1px solid rgba(0, 243, 255, 0.3)',
                          borderRadius: '4px', transform: 'translateY(-14px)', letterSpacing: '0.12em'
                        }}>
                          {link.label}
                        </div>
                      ),
                    }}
                  />
                </React.Fragment>
              );

            case 'tech_grid':
              return (
                <Xarrow
                  key={link.id}
                  {...baseProps}
                  color="rgba(255, 198, 0, 0.45)"
                  strokeWidth={1.5}
                  path="grid"
                  gridBreak="50%"
                  headSize={4}
                  arrowBodyProps={{
                    strokeDasharray: '8, 8',
                    strokeDashoffset: (-frame * 2.0).toString(),
                    filter: 'url(#luxury-neon-gold)',
                  }}
                  labels={{
                    middle: (
                      <div style={{
                        fontSize: '9px', fontFamily: 'monospace', color: '#ffc600',
                        background: '#0a0a0e', padding: '2px 6px', borderRadius: '3px',
                        border: '1px solid rgba(255, 198, 0, 0.25)', transform: 'translate(-50%, -50%)'
                      }}>
                        {link.label}
                      </div>
                    ),
                  }}
                />
              );

            case 'double_trace':
              return (
                <React.Fragment key={link.id}>
                  {/* Outer Left Trace */}
                  <Xarrow
                    start={link.source}
                    end={link.target}
                    startAnchor={{ position: link.startAnchorPosition || 'auto', offset: { x: -5, y: -5 } }}
                    endAnchor={{ position: link.endAnchorPosition || 'auto', offset: { x: -5, y: -5 } }}
                    color="rgba(255, 255, 255, 0.22)"
                    strokeWidth={1.2}
                    path="straight"
                    showHead={false}
                    arrowBodyProps={{
                      strokeDasharray: '1000',
                      strokeDashoffset: (drawProgress * 1000).toString(),
                    }}
                  />
                  {/* Outer Right Trace */}
                  <Xarrow
                    start={link.source}
                    end={link.target}
                    startAnchor={{ position: link.startAnchorPosition || 'auto', offset: { x: 5, y: 5 } }}
                    endAnchor={{ position: link.endAnchorPosition || 'auto', offset: { x: 5, y: 5 } }}
                    color="rgba(255, 255, 255, 0.22)"
                    strokeWidth={1.2}
                    path="straight"
                    showHead={false}
                    arrowBodyProps={{
                      strokeDasharray: '1000',
                      strokeDashoffset: (drawProgress * 1000).toString(),
                    }}
                    labels={{
                      middle: (
                        <div style={{
                          fontSize: '8px', fontFamily: 'monospace', color: 'rgba(255,255,255,0.7)',
                          background: '#040406', padding: '2px 5px', border: '1px solid rgba(255,255,255,0.12)',
                          borderRadius: '2px', letterSpacing: '0.05em'
                        }}>
                          {link.label}
                        </div>
                      )
                    }}
                  />
                </React.Fragment>
              );

            case 'electric_pulse':
              return (
                <Xarrow
                  key={link.id}
                  {...baseProps}
                  color="#10b981"
                  strokeWidth={2.0}
                  path="smooth"
                  curveness={0.65}
                  headSize={4}
                  arrowBodyProps={{
                    strokeDasharray: '30, 10, 10, 10',
                    strokeDashoffset: (-frame * 5.5).toString(),
                    filter: 'url(#electric-distortion) url(#discharge-green)',
                  }}
                  labels={{
                    middle: (
                      <div style={{
                        fontSize: '9px', fontFamily: 'monospace', color: '#10b981',
                        fontWeight: 'bold', transform: 'translateY(-14px)', letterSpacing: '0.05em'
                      }}>
                        ⚡ {link.label}
                      </div>
                    )
                  }}
                />
              );

            case 'neural_synapse':
              return (
                <React.Fragment key={link.id}>
                  {/* Translucent under-rail */}
                  <Xarrow
                    {...baseProps}
                    color="rgba(239, 68, 68, 0.08)"
                    strokeWidth={4}
                    path="smooth"
                    curveness={0.8}
                    showHead={false}
                  />
                  {/* Crystalline synapse dots */}
                  <Xarrow
                    {...baseProps}
                    color="#ef4444"
                    strokeWidth={2.2}
                    path="smooth"
                    curveness={0.8}
                    showHead={false}
                    arrowBodyProps={{
                      strokeDasharray: '3, 15',
                      strokeDashoffset: (frame * 2.2).toString(),
                      filter: 'url(#intense-red)',
                      strokeLinecap: 'round',
                    }}
                  />
                </React.Fragment>
              );

            case 'organic_flow':
            default:
              return (
                <Xarrow
                  key={link.id}
                  {...baseProps}
                  color="rgba(255, 255, 255, 0.15)"
                  strokeWidth={4}
                  path="smooth"
                  curveness={0.5}
                  showHead={false}
                  arrowBodyProps={{
                    strokeLinecap: 'round',
                    strokeDasharray: '1000',
                    strokeDashoffset: (drawProgress * 1000).toString(),
                  }}
                />
              );
          }
        })}
      </Xwrapper>
    </div>
  );
};

export default XarrowMasteryDemo;
