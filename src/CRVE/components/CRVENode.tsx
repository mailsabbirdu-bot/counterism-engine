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

export const CRVENode: React.FC<CRVENodeProps> = ({ node, x, y, progress, active, font, cinematic_mood }) => {
  const frame = useCurrentFrame();

  // Gentle, non-rotating floating/drift animation (very slow and elegant)
  const floatY = Math.sin(frame * 0.04 + hashString(node.id)) * 4;

  const opacity = active ? progress : 0.4 * progress;

  const mood = MOOD_REGISTRY[cinematic_mood || 'documentary'] || MOOD_REGISTRY['documentary'];
  const color = active ? mood.colors.primary : "rgba(255,255,255,0.6)";

  // Single clean entrance animation at the start of the scene (no looping)
  const entrance = spring({
      frame: frame,
      fps: 30,
      config: { damping: 15 }
  });

  return (
    <g id={node.id} transform={`translate(${x}, ${y + floatY}) scale(${entrance})`} opacity={opacity}>
      {/* Dynamic glow effect to draw focus to active semantic elements */}
      {active && (
        <defs>
          <filter id={`text-glow-${node.id}`} x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="12" result="blur" />
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
