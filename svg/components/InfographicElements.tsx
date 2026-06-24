import React from 'react';
import { spring, useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

interface ConnectionLineProps {
  start: { x: number; y: number };
  end: { x: number; y: number };
  startFrame: number;
  duration: number;
  color?: string;
}

export const ConnectionLine: React.FC<ConnectionLineProps> = ({
  start,
  end,
  startFrame,
  duration,
  color = 'rgba(255,255,255,0.2)'
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
      <line
        x1={start.x}
        y1={start.y}
        x2={currentX}
        y2={currentY}
        stroke={color}
        strokeWidth="2"
        strokeDasharray="4 4"
      />
    </svg>
  );
};

export const GlowNode: React.FC<{ x: number, y: number, startFrame: number, color?: string }> = ({
  x, y, startFrame, color = '#3b82f6'
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 10, stiffness: 100 },
  });

  if (frame < startFrame) return null;

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
        transform: `translate(-50%, -50%) scale(${progress})`,
        boxShadow: `0 0 20px ${color}`,
        zIndex: 2
      }}
    />
  );
};
