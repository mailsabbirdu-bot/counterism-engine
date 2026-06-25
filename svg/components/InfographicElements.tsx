import React, { useMemo } from 'react';
import { ConnectionLineProps } from '../types';
import { generateSvgId } from '../lib/svgUtils';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';

export const ConnectionLine: React.FC<ConnectionLineProps & { start: {x:number, y:number}, end: {x:number, y:number} }> = ({
  start,
  end,
  startFrame = 0,
  duration = 60,
  color = 'rgba(255,255,255,0.2)',
  type = 'dotted'
}) => {
  const { frame, fps } = useAnimation();

  // OPTIMIZATION: Use interpolation for lines
  const progress = getEntranceProgress(frame, fps, startFrame, false);

  // HARDENING: Unique Marker IDs to prevent collisions
  const markerId = useMemo(() => generateSvgId('arrowhead', `${start.x}-${start.y}-${end.x}-${end.y}`), [start, end]);

  if (frame < startFrame) return null;

  const currentX = start.x + (end.x - start.x) * progress;
  const currentY = start.y + (end.y - start.y) * progress;

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
      <defs>
        <marker id={markerId} markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill={color} />
        </marker>
      </defs>
      <line
        x1={start.x}
        y1={start.y}
        x2={currentX}
        y2={currentY}
        stroke={color}
        strokeWidth="2"
        strokeDasharray={type === 'dotted' ? "4 4" : "0"}
        markerEnd={type === 'arrow' ? `url(#${markerId})` : ""}
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
    x, y, radius, startFrame = 0, color = 'rgba(255,255,255,0.1)', orbitSpeed = 1
}) => {
    const { frame } = useAnimation();
    const relativeFrame = frame - startFrame;
    if (frame < startFrame) return null;

    // HARDENING: Clamp rotation
    const rotation = (relativeFrame * orbitSpeed) % 360;

    return (
        <div style={{
            position: 'absolute',
            left: x,
            top: y,
            width: radius * 2,
            height: radius * 2,
            border: `1px solid ${color}`,
            borderRadius: '50%',
            transform: `translate(-50%, -50%) rotate(${rotation}deg)`,
            zIndex: 1
        }}>
            <div style={{
                position: 'absolute',
                top: -4,
                left: '50%',
                width: 8,
                height: 8,
                backgroundColor: color,
                borderRadius: '50%',
                boxShadow: `0 0 10px ${color}`
            }} />
        </div>
    );
};
