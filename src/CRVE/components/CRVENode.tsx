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

export const CRVENode: React.FC<CRVENodeProps> = ({ node, x, y, progress, active, font }) => {
  const frame = useCurrentFrame();

  // Floating animation
  const floatY = Math.sin(frame * 0.05 + hashString(node.id)) * 5;
  const rotate = Math.cos(frame * 0.03 + hashString(node.id)) * 2;

  // Pulse animation for active nodes
  const pulse = active ? 1 + Math.sin(frame * 0.15) * 0.05 : 1;

  const opacity = active ? progress : 0.4 * progress;
  const scale = node.scale || 1.0;
  const radius = interpolate(node.importance, [1, 5], [40, 80]) * scale * progress * pulse;

  return (
    <g transform={`translate(${x}, ${y + floatY}) rotate(${rotate})`} opacity={opacity}>
      <defs>
        <filter id={`node-glow-${node.id}`} x="-100%" y="-100%" width="300%" height="300%">
          <feGaussianBlur stdDeviation={active ? "15" : "5"} result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>

      {/* Background Disc */}
      <circle
        r={radius}
        fill="rgba(10, 10, 10, 0.9)"
        stroke={active ? "#00F5FF" : "rgba(255,255,255,0.2)"}
        strokeWidth={active ? 3 : 1}
        style={{ filter: active ? `url(#node-glow-${node.id})` : 'none' }}
      />

      {/* HUD Rings */}
      <circle
        r={radius + 8}
        fill="none"
        stroke={active ? "#00F5FF" : "rgba(255,255,255,0.1)"}
        strokeWidth={0.5}
        strokeDasharray="10 20"
        transform={`rotate(${frame * 0.5})`}
      />

      {/* Label */}
      <text
        fill="white"
        textAnchor="middle"
        dy={radius + 35}
        style={{
            fontSize: active ? '18px' : '14px',
            fontWeight: 800,
            fontFamily: font || 'Inter, sans-serif',
            letterSpacing: '2px',
            textTransform: 'uppercase'
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
