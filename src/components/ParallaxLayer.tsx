import React from 'react';
import { AbsoluteFill, useVideoConfig } from 'remotion';

export const ParallaxLayer: React.FC<{
  depth?: number;
  zIndex?: number;
  children: React.ReactNode;
  blur?: number;
}> = ({ depth = 0, zIndex, children, blur }) => {
  const { width, height } = useVideoConfig();

  // Cinematic Depth Logic
  // Objects further away (negative depth) get automatic blur
  const zBlur = blur ?? (depth < 0 ? Math.abs(depth) / 10 : 0);
  const scale = 1 + (depth / 1000);

  return (
    <AbsoluteFill
      style={{
        transformStyle: 'preserve-3d',
        transform: `translate3d(0, 0, ${depth}px) scale(${scale})`,
        filter: zBlur > 0 ? `blur(${zBlur}px)` : undefined,
        zIndex,
        width,
        height,
        pointerEvents: 'none'
      }}
    >
      {children}
    </AbsoluteFill>
  );
};
