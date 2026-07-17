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
  index: number; // For staggered entry offsets
}

export const CRVENode: React.FC<CRVENodeProps> = ({ node, x, y, progress, active, font, cinematic_mood, index }) => {
  const frame = useCurrentFrame();

  // Slow, beautiful organic drift/breathing animation (perfectly horizontal, no rotation)
  const floatY = Math.sin(frame * 0.035 + hashString(node.id)) * 5;
  const floatX = Math.cos(frame * 0.025 + hashString(node.id)) * 3;

  // Staggered entry: each node starts its transition 15 frames after the previous one
  const staggerOffset = index * 15;
  const entryFrame = Math.max(0, frame - staggerOffset);

  // Single clean typographic entrance animation with a spring transition (damping for smooth settlement)
  const entryScale = spring({
      frame: entryFrame,
      fps: 30,
      config: { damping: 16, stiffness: 60 }
  });

  // Staggered fade-in corresponding to the entrance scale
  const nodeOpacity = interpolate(entryScale, [0, 1], [0, active ? 1 : 0.4]);
  const finalOpacity = nodeOpacity * progress;

  const mood = MOOD_REGISTRY[cinematic_mood || 'documentary'] || MOOD_REGISTRY['documentary'];
  const glowColor = active ? mood.colors.primary : "rgba(255, 255, 255, 0.4)";

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

      {/* Modern, High-End Typographic Node Presentation */}
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
