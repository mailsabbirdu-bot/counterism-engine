import React from 'react';
import { AbsoluteFill } from 'remotion';

export const ParallaxLayer: React.FC<{
  depth?: number;
  zIndex?: number;
  children: React.ReactNode;
}> = ({ depth = 0, zIndex, children }) => {
  return (
    <AbsoluteFill
      style={{
        transformStyle: 'preserve-3d',
        transform: depth !== 0 ? `translateZ(${depth}px)` : undefined,
        zIndex,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
