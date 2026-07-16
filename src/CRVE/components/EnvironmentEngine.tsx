import React from 'react';
import { useCurrentFrame, AbsoluteFill, useVideoConfig, interpolate } from 'remotion';

interface EnvironmentEngineProps {
    fx: string;
    lighting: string;
    color: string;
}

export const EnvironmentEngine: React.FC<EnvironmentEngineProps> = ({ fx, lighting, color }) => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();

    return (
        <AbsoluteFill className="pointer-events-none">
            {/* 1. Background Layers */}
            {fx === 'grid' && (
                <div style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    backgroundImage: `linear-gradient(to right, ${color}33 1px, transparent 1px), linear-gradient(to bottom, ${color}33 1px, transparent 1px)`,
                    backgroundSize: '80px 80px',
                    opacity: 0.2
                }} />
            )}

            {fx === 'stars' && (
                <svg width="100%" height="100%">
                    {Array.from({ length: 100 }).map((_, i) => (
                        <circle
                            key={i}
                            cx={Math.random() * width}
                            cy={Math.random() * height}
                            r={Math.random() * 2}
                            fill="white"
                            opacity={Math.sin(frame * 0.05 + i) * 0.5 + 0.5}
                        />
                    ))}
                </svg>
            )}

            {fx === 'radar' && (
                <div style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    border: `1px solid ${color}44`,
                    borderRadius: '50%',
                    transform: 'scale(1.2)',
                    opacity: 0.1
                }}>
                    <div style={{
                        position: 'absolute',
                        top: '50%',
                        left: '50%',
                        width: '100%',
                        height: '2px',
                        background: `linear-gradient(to right, transparent, ${color})`,
                        transformOrigin: 'left',
                        transform: `rotate(${frame * 2}deg)`
                    }} />
                </div>
            )}

            {/* 2. Lighting System */}
            {lighting === 'spotlight' && (
                <div style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    background: `radial-gradient(circle at 50% 50%, transparent, rgba(0,0,0,0.8))`,
                    opacity: 0.7
                }} />
            )}

            {lighting === 'volumetric' && (
                 <div style={{
                    position: 'absolute',
                    width: '100%',
                    height: '100%',
                    background: `linear-gradient(45deg, ${color}11, transparent)`,
                    filter: 'blur(100px)',
                    opacity: 0.3
                }} />
            )}

            {/* 3. Noise/Texture Overlay */}
            <div style={{
                position: 'absolute',
                width: '100%',
                height: '100%',
                backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)'/%3E%3C/svg%3E")`,
                opacity: 0.03,
                mixBlendMode: 'overlay'
            }} />
        </AbsoluteFill>
    );
};
