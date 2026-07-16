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

export const ElectricDischarge: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    const frame = useCurrentFrame();
    return (
        <g style={{ filter: 'blur(1px)' }}>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width}
                strokeOpacity={active ? progress : 0.2}
            />
            {active && [1, 2, 3].map(i => (
                <path
                    key={i}
                    d={path}
                    fill="none"
                    stroke="white"
                    strokeWidth={1}
                    strokeDasharray={`${Math.random() * 20} ${Math.random() * 50}`}
                    strokeDashoffset={frame * (5 + i)}
                    opacity={0.8}
                />
            ))}
        </g>
    );
};

export const EnergyRibbon: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    return (
        <g opacity={active ? progress : 0.2}>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width * 4}
                strokeOpacity={0.1}
            />
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width}
                strokeOpacity={0.6}
            />
        </g>
    );
};

export const BreakingLine: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    const frame = useCurrentFrame();
    const isBroken = (frame % 60) > 30;
    return (
        <g opacity={progress}>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={2}
                strokeDasharray={isBroken ? "10 5" : "none"}
                strokeOpacity={active ? 1 : 0.3}
            />
        </g>
    );
};

export const LaserSweep: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    const frame = useCurrentFrame();
    const sweepProgress = (frame * 0.05 * grammar.speed) % 1;

    return (
        <g>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={0.5}
                strokeOpacity={0.2 * progress}
            />
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width}
                strokeDasharray="100 1000"
                strokeDashoffset={-sweepProgress * 1000}
                strokeOpacity={active ? progress : 0.1}
                style={{ filter: 'blur(1px)' }}
            />
            {/* The "head" of the laser */}
            <circle r={4} fill="white" style={{ filter: 'blur(2px)' }}>
                <animateMotion path={path} dur={`${2/grammar.speed}s`} repeatCount="indefinite" />
            </circle>
        </g>
    );
};

export const SankeyLink: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    return (
        <g opacity={active ? 0.6 * progress : 0.1}>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width * 5}
                strokeOpacity={0.3}
            />
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={1}
                strokeDasharray="5 5"
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
        </g>
    );
};

export const ElectricArc: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    const frame = useCurrentFrame();

    // Create "jagged" effect using noise
    const noise = Math.sin(frame * 0.5) * 5;

    return (
        <g style={{ filter: 'url(#electricGlow)' }}>
             <defs>
                <filter id="electricGlow">
                    <feGaussianBlur stdDeviation="4" result="blur" />
                    <feComposite in="SourceGraphic" in2="blur" operator="over" />
                </filter>
            </defs>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width}
                strokeOpacity={0.8 * progress}
            />
            <path
                d={path}
                fill="none"
                stroke="white"
                strokeWidth={grammar.width * 0.5}
                strokeDasharray="10 30"
                strokeDashoffset={-frame * 20}
                strokeOpacity={active ? progress : 0.1}
            />
        </g>
    );
};

export const LiquidFlow: React.FC<ParticleStreamProps> = ({ path, grammar, progress, active }) => {
    const frame = useCurrentFrame();
    return (
        <g>
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width}
                strokeOpacity={0.2 * progress}
                strokeLinecap="round"
            />
            <path
                d={path}
                fill="none"
                stroke={grammar.color}
                strokeWidth={grammar.width * 0.7}
                strokeDasharray="40 100"
                strokeDashoffset={-frame * 5}
                strokeOpacity={active ? 0.6 * progress : 0.1}
                strokeLinecap="round"
                style={{ filter: 'blur(2px)' }}
            />
        </g>
    );
};
