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
  index: number;
}

export const CRVENode: React.FC<CRVENodeProps> = ({ node, x, y, progress, active, font, cinematic_mood, index }) => {
  const frame = useCurrentFrame();

  const isHeader = (node as any).isHeaderNode;

  // Slow, beautiful organic drift/breathing animation (perfectly horizontal, no rotation)
  // Header titles drift even slower and more majestically
  const floatY = Math.sin(frame * (isHeader ? 0.02 : 0.035) + hashString(node.id)) * (isHeader ? 3 : 5);
  const floatX = Math.cos(frame * (isHeader ? 0.015 : 0.025) + hashString(node.id)) * (isHeader ? 2 : 3);

  // Staggered entry
  const staggerOffset = index * 15;
  const entryFrame = Math.max(0, frame - staggerOffset);

  const entryScale = spring({
      frame: entryFrame,
      fps: 30,
      config: { damping: 16, stiffness: 60 }
  });

  const nodeOpacity = interpolate(entryScale, [0, 1], [0, active ? 1 : 0.4]);
  const finalOpacity = nodeOpacity * progress;

  const mood = MOOD_REGISTRY[cinematic_mood || 'documentary'] || MOOD_REGISTRY['documentary'];
  const glowColor = active ? mood.colors.primary : "rgba(255, 255, 255, 0.4)";

  if (isHeader) {
    // Beautiful, cinematic Header Title styling with an accent line below it
    return (
      <g id={node.id} transform={`translate(${x + floatX}, ${y + floatY}) scale(${entryScale})`} opacity={finalOpacity}>
        <defs>
          <filter id={`header-glow-${node.id}`} x="-30%" y="-30%" width="160%" height="160%">
            <feGaussianBlur stdDeviation="20" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>

        {/* Soft, wide ambient glow behind the title */}
        <text
          fill={mood.colors.primary}
          textAnchor="middle"
          dy="0"
          style={{
              fontSize: '44px',
              fontWeight: 900,
              fontFamily: font || 'Inter, sans-serif',
              letterSpacing: '8px',
              textTransform: 'uppercase',
              opacity: 0.15,
              filter: `url(#header-glow-${node.id})`
          }}
        >
          {node.label}
        </text>

        {/* Main sharp Title text */}
        <text
          fill="white"
          textAnchor="middle"
          dy="0"
          style={{
              fontSize: '40px',
              fontWeight: 900,
              fontFamily: font || 'Inter, sans-serif',
              letterSpacing: '8px',
              textTransform: 'uppercase',
              paintOrder: 'stroke',
              stroke: 'rgba(0,0,0,0.95)',
              strokeWidth: 8
          }}
        >
          {node.label}
        </text>

        {/* Cinematic thin horizontal separator below the title */}
        <line
          x1="-150"
          y1="25"
          x2="150"
          y2="25"
          stroke={mood.colors.primary}
          strokeWidth="1.5"
          opacity={0.6 * entryScale}
          strokeDasharray="10 15"
        />
        {/* Central glowing beacon */}
        <circle
          cx="0"
          cy="25"
          r="4"
          fill={mood.colors.primary}
          style={{ filter: `drop-shadow(0 0 5px ${mood.colors.primary})` }}
          opacity={entryScale}
        />
      </g>
    );
  }

  return (
    <g id={node.id} transform={`translate(${x + floatX}, ${y + floatY}) scale(${entryScale})`} opacity={finalOpacity}>
      {/* Cinematic typography glowing background for active nodes */}
      {active && (
        <defs>
          <filter id={`text-glow-${node.id}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="15" result="blur" />
            <feMerge>
              <feMergeNode in="blur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
      )}

      {/* Modern, High-End Typographic Node Representation */}
      <text
        fill="white"
        textAnchor="middle"
        dy="10"
        style={{
            fontSize: active ? '34px' : '26px',
            fontWeight: 900,
            fontFamily: font || 'Inter, sans-serif',
            letterSpacing: '3px',
            textTransform: 'uppercase',
            paintOrder: 'stroke',
            stroke: 'rgba(0, 0, 0, 0.95)',
            strokeWidth: 6,
            filter: active ? `url(#text-glow-${node.id})` : 'none',
            transition: 'all 0.3s ease-in-out'
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
