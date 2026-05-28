import React from 'react';
import { useCurrentFrame, AbsoluteFill, useVideoConfig, interpolate, spring, Easing } from 'remotion';

export const ShapesEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const x = overlay.position?.x || width / 2;
  const y = overlay.position?.y || height / 2;
  const size = overlay.size || 100;
  const color = overlay.color || "#3b82f6";

  // Unified entrance animation
  const entrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  // Smooth cyclic animations using Remotion's frame count
  let scale = entrance;
  let rotation = 0;
  let translateY = 0;
  let translateX = 0;

  if (overlay.animation === 'pulse') {
    const pulseFactor = Math.sin(frame / (20 / (overlay.speed || 1))) * 0.1;
    scale = entrance * (1 + pulseFactor);
  } else if (overlay.animation === 'float') {
    translateY = Math.sin(frame / 30) * 20;
    translateX = Math.cos(frame / 40) * 10;
  } else if (overlay.animation === 'morph') {
    rotation = frame * 2;
  }

  const renderShape = () => {
    switch (overlay.shape_type) {
      case 'circle':
        return (
          <circle
            cx={x}
            cy={y}
            r={size}
            fill="none"
            stroke={color}
            strokeWidth="4"
            className="drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]"
          />
        );
      case 'rect':
        const rSize = size;
        return (
          <rect
            x={x - rSize}
            y={y - rSize}
            width={rSize * 2}
            height={rSize * 2}
            fill="none"
            stroke={color}
            strokeWidth="4"
            rx={overlay.radius || 20}
            className="drop-shadow-[0_0_15px_rgba(255,255,255,0.3)]"
          />
        );
      case 'line':
        return (
          <line
            x1={x - size}
            y1={y}
            x2={x + size}
            y2={y}
            stroke={color}
            strokeWidth="4"
            strokeDasharray="10 5"
          />
        );
      default:
        return null;
    }
  };

  return (
    <AbsoluteFill className="pointer-events-none" style={{ zIndex: overlay.zIndex ?? 10 }}>
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        <g
          style={{
            transformOrigin: `${x}px ${y}px`,
            transform: `translate(${translateX}px, ${translateY}px) scale(${scale}) rotate(${rotation}deg)`,
            opacity: entrance
          }}
        >
          {renderShape()}

          {/* Secondary decorative elements */}
          {overlay.decorated && (
             <g opacity="0.4">
                <circle cx={x} cy={y} r={size + 30} fill="none" stroke={color} strokeWidth="1" strokeDasharray="8 8" />
                <circle cx={x} cy={y} r={size + 60} fill="none" stroke={color} strokeWidth="0.5" />
             </g>
          )}
        </g>
      </svg>
    </AbsoluteFill>
  );
};
