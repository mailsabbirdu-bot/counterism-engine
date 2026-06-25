import React, { useMemo } from 'react';
import { ConnectionLineProps } from '../types';
import { generateSvgId } from '../lib/svgUtils';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';

export const ConnectionLine: React.FC<ConnectionLineProps & {
    start: {x:number, y:number},
    end: {x:number, y:number},
    paddingStart?: number,
    paddingEnd?: number
}> = ({
  start,
  end,
  startFrame = 0,
  duration = 60,
  color = 'rgba(255,255,255,0.2)',
  type = 'dotted',
  paddingStart = 0,
  paddingEnd = 0
}) => {
  const { frame, fps } = useAnimation();

  // OPTIMIZATION: Use interpolation for lines
  const progress = getEntranceProgress(frame, fps, startFrame, false);

  // Calculate direction vector and distance
  const dx = end.x - start.x;
  const dy = end.y - start.y;
  const dist = Math.sqrt(dx * dx + dy * dy);

  // Calculate padded points to prevent icon overlap
  const unitX = dx / dist;
  const unitY = dy / dist;

  const paddedStart = {
      x: start.x + unitX * paddingStart,
      y: start.y + unitY * paddingStart
  };

  const paddedEnd = {
      x: end.x - unitX * paddingEnd,
      y: end.y - unitY * paddingEnd
  };

  // HARDENING: Unique Marker IDs to prevent collisions
  const markerId = useMemo(() => generateSvgId('arrowhead', `${start.x}-${start.y}-${end.x}-${end.y}`), [start, end]);

  if (frame < startFrame) return null;

  const currentX = paddedStart.x + (paddedEnd.x - paddedStart.x) * progress;
  const currentY = paddedStart.y + (paddedEnd.y - paddedStart.y) * progress;

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
      <defs>
        <marker id={markerId} markerWidth="14" markerHeight="12" refX="12" refY="6" orient="auto">
          <polygon points="0 0, 14 6, 0 12" fill={color} />
        </marker>
      </defs>
      <line
        x1={paddedStart.x}
        y1={paddedStart.y}
        x2={currentX}
        y2={currentY}
        stroke={color}
        strokeWidth="6" // Thick, bold lines (Vox Style)
        strokeDasharray={type === 'dotted' ? "12 12" : "0"}
        markerEnd={type === 'arrow' ? `url(#${markerId})` : ""}
        strokeLinecap="round"
      />
    </svg>
  );
};

export const GlowNode: React.FC<{ x: number, y: number, startFrame?: number, color?: string, type?: 'glow' | 'pulse' | 'signal' }> = ({
  x, y, startFrame = 0, color = '#3b82f6', type = 'glow'
}) => {
  const { frame, fps } = useAnimation();

  const relativeFrame = frame - startFrame;
  const progress = getEntranceProgress(frame, fps, startFrame, false);

  if (frame < startFrame) return null;

  const pulse = type === 'pulse' ? Math.sin(relativeFrame / 10) * 0.2 + 1 : 1;

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: 12,
        height: 12,
        backgroundColor: color,
        borderRadius: '50%',
        transform: `translate(-50%, -50%) scale(${progress * pulse})`,
        boxShadow: `0 0 ${20 * pulse}px ${color}`,
        zIndex: 2
      }}
    >
      {type === 'signal' && (
        <div style={{
          position: 'absolute',
          inset: -20,
          border: `2px solid ${color}`,
          borderRadius: '50%',
          opacity: (1 - (relativeFrame % 30) / 30) * 0.6,
          transform: `scale(${0.5 + ((relativeFrame % 30) / 30) * 1.5})`
        }} />
      )}
    </div>
  );
};

export const OrbitRing: React.FC<{ x: number, y: number, radius: number, startFrame?: number, color?: string, orbitSpeed?: number }> = ({
    x, y, radius, startFrame = 0, color = 'rgba(255,255,255,0.1)', orbitSpeed = 0.5 // Slower, more subtle
}) => {
    const { frame } = useAnimation();
    const relativeFrame = frame - startFrame;
    if (frame < startFrame) return null;

    // rotation is slower and more cinematic
    const rotation = (relativeFrame * orbitSpeed) % 360;

    return (
        <div style={{
            position: 'absolute',
            left: x,
            top: y,
            width: radius * 2,
            height: radius * 2,
            border: `2px solid ${color}`, // Thicker ring
            borderRadius: '50%',
            transform: `translate(-50%, -50%)`, // Removed rotation if confusing
            zIndex: 1
        }} />
    );
};
