import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';

interface ParticleFlowProps {
  path: string;
  color: string;
  count?: number;
  duration?: number;
  size?: number;
}

export const ParticleFlow: React.FC<ParticleFlowProps> = ({
  path,
  color,
  count = 1,
  duration = 60,
  size = 6
}) => {
  const frame = useCurrentFrame();

  return (
    <>
      {[...Array(count)].map((_, i) => {
        const delay = i * (duration / count);
        const progress = (frame + delay) % duration / duration;

        return (
          <circle key={i} r={size} fill={color} style={{
            offsetPath: `path("${path}")`,
            offsetDistance: `${progress * 100}%`,
            filter: `drop-shadow(0 0 10px ${color})`,
            opacity: interpolate(progress, [0, 0.1, 0.9, 1], [0, 1, 1, 0])
          }} />
        );
      })}
    </>
  );
};
