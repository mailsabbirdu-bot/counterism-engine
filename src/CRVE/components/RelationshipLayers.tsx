import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate, spring } from 'remotion';
import { Point, samplePath } from '../lib/pathUtils';
import { RelationshipGrammar } from '../lib/types';

interface ParticleStreamProps {
  path: string;
  grammar: RelationshipGrammar;
  progress: number;
  active: boolean;
}

export const ParticleStream: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
  const frame = useCurrentFrame();
  const points = useMemo(() => samplePath(path, 30), [path]);

  const particleCount = 12;
  const particles = Array.from({ length: particleCount }).map((_, i) => {
    const offset = (i / particleCount + (frame * 0.02 * grammar.speed)) % 1;
    const pointIdx = Math.floor(offset * (points.length - 1));
    const p1 = points[pointIdx];
    const p2 = points[Math.min(pointIdx + 1, points.length - 1)];

    if (!p1 || !p2) return null;

    const subOffset = (offset * (points.length - 1)) % 1;
    const x = p1.x + (p2.x - p1.x) * subOffset;
    const y = p1.y + (p2.y - p1.y) * subOffset;

    const opacity = active ? interpolate(offset, [0, 0.2, 0.8, 1], [0, 1, 1, 0]) : 0.1;
    const size = interpolate(offset, [0, 0.5, 1], [2, 4, 2]);

    return (
      <circle
        key={i}
        cx={x}
        cy={y}
        r={size * progress}
        fill={grammar.color}
        opacity={opacity * progress}
      />
    );
  });

  return (
    <g>
      <path
        d={path}
        fill="none"
        stroke={grammar.color}
        strokeWidth={grammar.width * 0.5}
        strokeOpacity={0.15 * progress}
      />
      {particles}
    </g>
  );
};

export const EnergyBeam: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    const frame = useCurrentFrame();
    const dashOffset = -frame * 10 * grammar.speed;

    return (
        <g>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width}
                strokeOpacity={0.3 * progress}
                style={{ filter: 'blur(4px)' }}
            />
            <path
                d={path}
                fill="none"
                stroke="white"
                strokeWidth={grammar.width * 0.4}
                strokeDasharray="20 40"
                strokeDashoffset={dashOffset}
                strokeOpacity={active ? progress : 0.1}
            />
        </g>
    );
};

export const HUDConnector: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    return (
        <g opacity={progress}>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={1}
                strokeDasharray="4 4"
                strokeOpacity={0.4}
            />
            {/* End points markers */}
            {active && (
                <circle cx={0} cy={0} r={3} fill={grammar.color} style={{ transform: `translate(var(--sx), var(--sy))` }} />
            )}
        </g>
    );
};
