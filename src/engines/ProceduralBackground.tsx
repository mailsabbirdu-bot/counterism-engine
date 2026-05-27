import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';

export const ProceduralBackground: React.FC<{ config: any }> = ({ config }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const particles = useMemo(() => {
    return Array.from({ length: config.particles || 50 }, (_, i) => ({
      id: i,
      x: Math.random() * width,
      y: Math.random() * height,
      size: Math.random() * 3 + 1,
      speed: Math.random() * 1 + 0.5,
      opacity: Math.random() * 0.5 + 0.1
    }));
  }, [width, height, config.particles]);

  const primaryColor = config.primaryColor || '#09090b';
  const secondaryColor = config.secondaryColor || '#1e1b4b';

  return (
    <AbsoluteFill style={{ backgroundColor: primaryColor }}>
      {/* Animated Gradient */}
      <div
        className="absolute inset-0 opacity-40"
        style={{
          background: `radial-gradient(circle at ${50 + Math.sin(frame/100)*20}% ${50 + Math.cos(frame/100)*20}%, ${secondaryColor} 0%, transparent 70%)`
        }}
      />

      {/* Floating Particles */}
      <svg width={width} height={height} className="absolute inset-0">
        {particles.map((p) => (
          <circle
            key={p.id}
            cx={p.x}
            cy={(p.y - frame * p.speed) % height}
            r={p.size}
            fill="white"
            opacity={p.opacity}
          />
        ))}
      </svg>

      {/* Grid Overlay */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)`,
          backgroundSize: '100px 100px'
        }}
      />
    </AbsoluteFill>
  );
};
