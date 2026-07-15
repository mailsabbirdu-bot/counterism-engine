import React from 'react';
import { useCurrentFrame, interpolate, spring } from 'remotion';
import { CRVENodeData } from '../lib/types';

interface CRVENodeProps {
  node: CRVENodeData;
  x: number;
  y: number;
  progress: number;
  active: boolean;
  font?: string;
}

import { NODE_PRESETS, CRVENodeStyle } from '../lib/nodeStyles';

export const CRVENode: React.FC<CRVENodeProps> = ({ node, x, y, progress, active, font }) => {
  const frame = useCurrentFrame();

  // Custom Preset Assignment (AI/Orchestrator driven, or deterministic)
  const styleKey: CRVENodeStyle = (node as any).style_preset || 'glass_disc';
  const config = NODE_PRESETS[styleKey] || NODE_PRESETS['glass_disc'];

  // Floating animation
  const floatY = Math.sin(frame * 0.05 + hashString(node.id)) * 5;
  const rotationBase = config.rotation ? frame * 0.4 : 0;
  const rotate = rotationBase + Math.cos(frame * 0.03 + hashString(node.id)) * 2;

  // Pulse animation for active nodes
  const pulse = active ? 1 + Math.sin(frame * 0.15) * 0.05 : 1;

  const opacity = active ? (progress * config.opacity) : (0.4 * progress * config.opacity);
  const scale = node.scale || 1.0;
  const radius = interpolate(node.importance, [1, 5], [40, 80]) * scale * progress * pulse;

  const color = active ? "#00F5FF" : "rgba(255,255,255,0.4)";

  const renderShape = () => {
      switch (config.shape) {
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

  return (
    <g transform={`translate(${x}, ${y + floatY}) rotate(${rotate})`} opacity={opacity}>
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
