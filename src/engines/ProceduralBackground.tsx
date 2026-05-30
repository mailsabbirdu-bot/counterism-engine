import React from 'react';
import { useCurrentFrame, useVideoConfig } from 'remotion';

export const ProceduralBackground: React.FC<{ config: any }> = ({ config }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  // Animated gradient using template colors
  const primaryColor = config.primaryColor || '#000033';
  const secondaryColor = config.secondaryColor || '#000066';

  // Subtle hue shifting for "cinematic" feel if requested
  const speed = config.speed || 1;
  const isSolid = !!config.color;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        background: isSolid ? config.color : `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        overflow: 'hidden',
      }}
    >
      {/* Moving particle grid for depth perception - disabled in solid mode */}
      {!isSolid && (
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.3) 1px, transparent 1px)',
            backgroundSize: '100px 100px',
            transform: `translate(${frame * 0.5}px, ${frame * 0.2}px) scale(2)`,
          }}
        />
      )}

      {/* Animated glow overlay */}
      <div
        className="absolute inset-0"
        style={{
          background: isSolid ? 'none' : 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.4) 100%)',
          pointerEvents: 'none',
        }}
      />
    </div>
  );
};
