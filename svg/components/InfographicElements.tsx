import React from 'react';
import { spring, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

interface ConnectionLineProps {
  start: { x: number; y: number };
  end: { x: number; y: number };
  startFrame: number;
  duration: number;
  color?: string;
  type?: 'solid' | 'dotted' | 'arrow';
}

export const ConnectionLine: React.FC<ConnectionLineProps> = ({
  start,
  end,
  startFrame,
  duration,
  color = 'rgba(255,255,255,0.2)',
  type = 'dotted'
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 20 },
  });

  if (frame < startFrame) return null;

  const currentX = interpolate(progress, [0, 1], [start.x, end.x]);
  const currentY = interpolate(progress, [0, 1], [start.y, end.y]);

  return (
    <svg className="absolute inset-0 w-full h-full pointer-events-none" style={{ zIndex: 1 }}>
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
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
        markerEnd={type === 'arrow' ? "url(#arrowhead)" : ""}
      />
    </svg>
  );
};

export const GlowNode: React.FC<{ x: number, y: number, startFrame: number, color?: string, type?: 'glow' | 'pulse' | 'signal' }> = ({
  x, y, startFrame, color = '#3b82f6', type = 'glow'
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const relativeFrame = frame - startFrame;
  const progress = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 10, stiffness: 100 },
  });

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
          opacity: interpolate(relativeFrame % 30, [0, 30], [0.6, 0]),
          transform: `scale(${interpolate(relativeFrame % 30, [0, 30], [0.5, 2])})`
        }} />
      )}
    </div>
  );
};

export const OrbitRing: React.FC<{ x: number, y: number, radius: number, startFrame: number, color?: string }> = ({
    x, y, radius, startFrame, color = 'rgba(255,255,255,0.1)'
}) => {
    const frame = useCurrentFrame();
    const relativeFrame = frame - startFrame;
    if (frame < startFrame) return null;

    return (
        <div style={{
            position: 'absolute',
            left: x,
            top: y,
            width: radius * 2,
            height: radius * 2,
            border: `1px solid ${color}`,
            borderRadius: '50%',
            transform: `translate(-50%, -50%) rotate(${relativeFrame}deg)`,
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
