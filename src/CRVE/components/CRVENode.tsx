import React from 'react';
import { useCurrentFrame, interpolate, spring } from 'remotion';
import { CRVENodeData } from '../lib/types';
import { MOOD_REGISTRY, CinematicMood } from '../lib/moodRegistry';

interface CRVENodeProps {
  node: CRVENodeData;
  x: number;
  y: number;
  progress: number;
  active: boolean;
  font?: string;
  cinematic_mood?: CinematicMood;
}

import { NODE_PRESETS, CRVENodeStyle } from '../lib/nodeStyles';

export const CRVENode: React.FC<CRVENodeProps> = ({ node, x, y, progress, active, font, cinematic_mood }) => {
  const frame = useCurrentFrame();

  // Custom Preset Assignment (AI/Orchestrator driven, or deterministic)
  let styleKey: CRVENodeStyle = (node as any).style_preset || 'glass_disc';

  // Semantic Type Overrides
  const semanticType = (node as any).semantic_type;
  if (semanticType === 'city' || semanticType === 'location') styleKey = 'satellite_marker';
  else if (semanticType === 'machine' || semanticType === 'technology') styleKey = 'circuit_chip';
  else if (semanticType === 'star' || semanticType === 'planet') styleKey = 'holographic_sphere';
  else if (semanticType === 'human' || semanticType === 'person') styleKey = 'organic_blob';
  else if (semanticType === 'idea' || semanticType === 'concept') styleKey = 'conceptual_symbol';

  const config = NODE_PRESETS[styleKey] || NODE_PRESETS['glass_disc'];

  // Life Cycle State Handling
  const lifecycle = (node as any).lifecycle_state || 'active';
  const isWarning = lifecycle === 'warning' || lifecycle === 'critical';

  // Floating animation
  const floatY = Math.sin(frame * 0.05 + hashString(node.id)) * 5;
  const rotationBase = config.rotation ? frame * 0.4 : 0;
  const rotate = rotationBase + Math.cos(frame * 0.03 + hashString(node.id)) * 2;

  // Pulse animation for active nodes
  const pulse = 1;

  const opacity = active ? (progress * config.opacity) : (0.4 * progress * config.opacity);
  const scale = node.scale || 1.0;
  const radius = interpolate(node.importance, [1, 5], [40, 80]) * scale * progress * pulse;

  const mood = MOOD_REGISTRY[cinematic_mood || 'documentary'] || MOOD_REGISTRY['documentary'];
  let color = active ? mood.colors.primary : "rgba(255,255,255,0.4)";
  if (isWarning) color = mood.colors.accent || "#ef4444";

  const renderShape = () => {
      switch (config.shape) {
          case 'glass_disc':
              return (
                  <g>
                    <circle r={radius} fill="rgba(255, 255, 255, 0.08)" stroke={color} strokeWidth={2} style={{ backdropFilter: 'blur(8px)' }} />
                    <circle r={radius * 0.85} fill="none" stroke={color} strokeWidth={1} strokeDasharray="5 10" opacity={0.6} />
                    <circle r={radius * 0.4} fill="rgba(255, 255, 255, 0.03)" stroke={color} strokeWidth={1.5} />
                    {[0, 90, 180, 270].map((angle) => {
                        const rad = (angle * Math.PI) / 180;
                        return (
                            <line
                                key={angle}
                                x1={Math.cos(rad) * (radius - 8)}
                                y1={Math.sin(rad) * (radius - 8)}
                                x2={Math.cos(rad) * radius}
                                y2={Math.sin(rad) * radius}
                                stroke={color}
                                strokeWidth={1.5}
                            />
                        );
                    })}
                  </g>
              );
          case 'orbital_rings':
              return (
                  <g>
                    <circle r={radius * 0.5} fill="none" stroke={color} strokeWidth={3} />
                    <circle r={radius * 0.8} fill="none" stroke={color} strokeWidth={1} strokeDasharray="10 15" />
                    <circle r={radius} fill="none" stroke={color} strokeWidth={0.5} strokeDasharray="4 4" />
                    <circle cx={Math.cos(frame * 0.05) * radius * 0.8} cy={Math.sin(frame * 0.05) * radius * 0.8} r={6} fill={color} />
                    <circle cx={Math.cos(frame * -0.03 + Math.PI) * radius} cy={Math.sin(frame * -0.03 + Math.PI) * radius} r={4} fill={color} />
                  </g>
              );
          case 'core_pulse':
              const waveProgress = (frame % 30) / 30;
              return (
                  <g>
                    <circle r={radius * 0.3} fill={color} />
                    <circle r={radius * 0.3 + waveProgress * radius * 0.7} fill="none" stroke={color} strokeWidth={2 * (1 - waveProgress)} opacity={1 - waveProgress} />
                    <circle r={radius * 0.3 + ((waveProgress + 0.5) % 1) * radius * 0.7} fill="none" stroke={color} strokeWidth={2 * (1 - ((waveProgress + 0.5) % 1))} opacity={1 - ((waveProgress + 0.5) % 1)} />
                  </g>
              );
          case 'conceptual_symbol':
              return (
                  <g transform={`rotate(${frame * 0.5})`}>
                    <rect x={-radius * 0.6} y={-radius * 0.6} width={radius * 1.2} height={radius * 1.2} fill="none" stroke={color} strokeWidth={2.5} transform="rotate(45)" />
                    <rect x={-radius * 0.4} y={-radius * 0.4} width={radius * 0.8} height={radius * 0.8} fill="none" stroke={color} strokeWidth={1} transform="rotate(15)" />
                    <rect x={-radius * 0.2} y={-radius * 0.2} width={radius * 0.4} height={radius * 0.4} fill={color} opacity={0.3} transform="rotate(45)" />
                    {[0, 90, 180, 270].map((angle) => {
                        const rad = (angle * Math.PI) / 180;
                        return (
                            <circle key={angle} cx={Math.cos(rad) * radius * 0.85} cy={Math.sin(rad) * radius * 0.85} r={3} fill={color} />
                        );
                    })}
                  </g>
              );
          case 'neon_hexagon':
              return (
                <path
                    d={`M ${radius} 0 L ${radius/2} ${radius*0.86} L ${-radius/2} ${radius*0.86} L ${-radius} 0 L ${-radius/2} ${-radius*0.86} L ${radius/2} ${-radius*0.86} Z`}
                    fill="rgba(2, 2, 2, 0.8)"
                    stroke={color}
                    strokeWidth={active ? 4 : 2}
                />
              );
          case 'tactical_triangle':
              return (
                  <path
                    d={`M 0 ${-radius} L ${radius} ${radius} L ${-radius} ${radius} Z`}
                    fill="rgba(5, 5, 5, 0.9)"
                    stroke={color}
                    strokeWidth={2}
                  />
              );
          case 'circuit_chip':
              return (
                  <g>
                    <rect x={-radius} y={-radius} width={radius*2} height={radius*2} fill="#111" stroke={color} strokeWidth={2} rx={4} />
                    <line x1={-radius-10} y1={-radius/2} x2={-radius} y2={-radius/2} stroke={color} strokeWidth={2} />
                    <line x1={radius} y1={-radius/2} x2={radius+10} y2={-radius/2} stroke={color} strokeWidth={2} />
                    <circle r={radius*0.3} fill={color} opacity={0.2} />
                  </g>
              );
          case 'floating_cube':
              return (
                  <path
                    d={`M 0 ${-radius} L ${radius*0.8} ${-radius*0.5} L ${radius*0.8} ${radius*0.5} L 0 ${radius} L ${-radius*0.8} ${radius*0.5} L ${-radius*0.8} ${-radius*0.5} Z`}
                    fill="rgba(5, 5, 5, 0.9)"
                    stroke={color}
                    strokeWidth={2}
                  />
              );
          case 'organic_blob':
              return (
                  <path
                    d={`M ${radius} 0 C ${radius} ${radius} ${-radius} ${radius} ${-radius} 0 C ${-radius} ${-radius} ${radius} ${-radius} ${radius} 0`}
                    fill="rgba(20, 40, 20, 0.6)"
                    stroke={color}
                    strokeWidth={2}
                    style={{ filter: 'blur(2px)' }}
                  />
              );
          case 'satellite_marker':
              return (
                  <g>
                    <circle r={radius} fill="none" stroke={color} strokeWidth={1} />
                    <rect x={-radius*1.2} y={-2} width={radius*2.4} height={4} fill={color} />
                    <rect x={-2} y={-radius*1.2} width={4} height={radius*2.4} fill={color} />
                  </g>
              );
          case 'dna_helix':
              return (
                  <g>
                      <path d={`M ${-radius/2} ${-radius} Q 0 0 ${-radius/2} ${radius}`} fill="none" stroke={color} strokeWidth={4} />
                      <path d={`M ${radius/2} ${-radius} Q 0 0 ${radius/2} ${radius}`} fill="none" stroke={color} strokeWidth={4} />
                      {[-0.6, -0.2, 0.2, 0.6].map(offset => (
                          <line key={offset} x1={-radius/2-2} y1={radius*offset} x2={radius/2+2} y2={radius*offset} stroke={color} strokeWidth={2} />
                      ))}
                  </g>
              );
          case 'neural_synapse':
              return (
                  <g>
                      <circle r={radius*0.4} fill={color} opacity={0.3} />
                      {Array.from({length: 8}).map((_, i) => (
                          <line
                            key={i}
                            x1={0} y1={0}
                            x2={Math.cos(i * Math.PI/4) * radius}
                            y2={Math.sin(i * Math.PI/4) * radius}
                            stroke={color} strokeWidth={2}
                            strokeDasharray="4 4"
                          />
                      ))}
                  </g>
              );
          case 'holographic_sphere':
              return (
                  <g>
                      <circle r={radius} fill="none" stroke={color} strokeWidth={1} />
                      <ellipse cx="0" cy="0" rx={radius} ry={radius*0.3} fill="none" stroke={color} strokeWidth={0.5} />
                      <ellipse cx="0" cy="0" rx={radius*0.3} ry={radius} fill="none" stroke={color} strokeWidth={0.5} />
                      <circle r={radius*0.1} fill={color} />
                  </g>
              );
          case 'glass_pyramid':
              return (
                  <path
                    d={`M 0 ${-radius} L ${radius} ${radius*0.5} L 0 ${radius} L ${-radius} ${radius*0.5} Z M 0 ${-radius} L 0 ${radius}`}
                    fill="rgba(255,255,255,0.1)"
                    stroke={color}
                    strokeWidth={2}
                  />
              );
          case 'cyber_eye':
              return (
                  <g>
                      <path d={`M ${-radius} 0 Q 0 ${-radius*0.8} ${radius} 0 Q 0 ${radius*0.8} ${-radius} 0`} fill="none" stroke={color} strokeWidth={2} />
                      <circle r={radius*0.3} fill="none" stroke={color} strokeWidth={2} />
                      <circle r={radius*0.1} fill={color} />
                  </g>
              );
          default:
              return (
                <circle
                    r={radius}
                    fill="rgba(10, 10, 10, 0.9)"
                    stroke={color}
                    strokeWidth={active ? 3 : 1}
                />
              );
      }
  };

  // Lifecycle Entrance
  const entrance = spring({
      frame: frame, // Single entrance scale at start of scene, no repeating blinking loops
      fps: 30,
      config: { damping: 15 }
  });

  return (
    <g id={node.id} transform={`translate(${x}, ${y + floatY}) rotate(${rotate}) scale(${entrance})`} opacity={opacity}>
      <defs>
        <filter id={`node-glow-${node.id}`} x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation={active ? "15" : "5"} result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      <g style={{ filter: config.glow && active ? `url(#node-glow-${node.id})` : 'none' }}>
        {renderShape()}
      </g>

      {/* HUD Rings */}
      {Array.from({ length: config.rings }).map((_, i) => (
          <circle
            key={i}
            r={radius + 8 + (i * 6)}
            fill="none"
            stroke={color}
            strokeWidth={0.5}
            strokeDasharray={`${10 + i*5} ${20 + i*2}`}
            transform={`rotate(${frame * (0.5 * (i+1))})`}
            opacity={0.4 / (i + 1)}
          />
      ))}

      {/* Label */}
      <text
        fill="white"
        textAnchor="middle"
        dy={radius + 35}
        style={{
            fontSize: active ? '28px' : '22px', // INCREASED SIZE
            fontWeight: 900,
            fontFamily: font || 'Inter, sans-serif',
            letterSpacing: '2px',
            textTransform: 'uppercase',
            paintOrder: 'stroke',
            stroke: 'black',
            strokeWidth: 4
        }}
      >
        {node.label}
      </text>
    </g>
  );
};

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  return hash;
}
