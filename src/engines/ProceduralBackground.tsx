import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export const ProceduralBackground: React.FC<{ config: any }> = ({ config }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Simple animated gradient for now
  const hue = (frame * (config.speed || 1)) % 360;
  const color1 = `hsl(${hue}, 70%, 20%)`;
  const color2 = `hsl(${(hue + 60) % 360}, 70%, 10%)`;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: `linear-gradient(135deg, ${color1}, ${color2})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Add some moving particles or subtle patterns if needed */}
      <div
        className="absolute inset-0 opacity-20"
        style={{
          backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '50px 50px',
          transform: `translate(${frame * 0.5}px, ${frame * 0.2}px)`,
        }}
      />
    </div>
  );
};
