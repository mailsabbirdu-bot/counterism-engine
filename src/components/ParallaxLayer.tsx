import React from 'react';
import { AbsoluteFill, useVideoConfig } from 'remotion';

export const ParallaxLayer: React.FC<{
  depth?: number;
  zIndex?: number;
  children: React.ReactNode;
}> = ({ depth = 0, zIndex, children }) => {
  const { width, height } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        transformStyle: 'preserve-3d',
        transform: depth !== 0 ? `translate3d(0, 0, ${depth}px)` : undefined,
        zIndex,
        width,
        height,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
