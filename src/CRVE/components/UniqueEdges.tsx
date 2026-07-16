import React from 'react';
import { useCurrentFrame, interpolate } from 'remotion';
import { Point } from '../lib/pathUtils';

interface EdgeProps {
  path: string;
  color: string;
  progress: number;
  active: boolean;
}

export const DNAEdge: React.FC<EdgeProps> = ({ path, color, progress, active }) => {
    const frame = useCurrentFrame();
    // DNA Helix style: Two intertwined lines with rungs
    return (
        <g opacity={active ? progress : 0.2}>
            <path d={path} fill="none" stroke={color} strokeWidth={1} strokeOpacity={0.3} />
            {/* We would need complex path sampling for a true helix,
                for now let's use a dual-dash approach */}
            <path
                d={path} fill="none" stroke={color} strokeWidth={2}
                strokeDasharray="5 15" strokeDashoffset={frame}
            />
            <path
                d={path} fill="none" stroke={color} strokeWidth={2}
                strokeDasharray="5 15" strokeDashoffset={-frame}
            />
        </g>
    );
};

export const CircuitEdge: React.FC<EdgeProps> = ({ path, color, progress, active }) => {
    const frame = useCurrentFrame();
    return (
        <g opacity={active ? progress : 0.2}>
            <path d={path} fill="none" stroke={color} strokeWidth={1} strokeDasharray="10 5" />
            <circle r={3} fill={color}>
                <animateMotion path={path} dur="3s" repeatCount="indefinite" />
            </circle>
            {/* Square data packets */}
            <rect width={6} height={6} fill={color} opacity={0.6}>
                <animateMotion path={path} dur="2s" repeatCount="indefinite" />
            </rect>
        </g>
    );
};

export const NeuralEdge: React.FC<EdgeProps> = ({ path, color, progress, active }) => {
    const frame = useCurrentFrame();
    const flash = Math.sin(frame * 0.2) > 0.8;
    return (
        <g opacity={active ? progress : 0.1}>
            <path d={path} fill="none" stroke={color} strokeWidth={flash ? 3 : 1} strokeOpacity={flash ? 0.8 : 0.3} />
            <path d={path} fill="none" stroke="white" strokeWidth={0.5} strokeDasharray="1 20" strokeDashoffset={-frame * 5} />
        </g>
    );
};
