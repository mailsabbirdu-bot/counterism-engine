import React, { useMemo } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';

interface DirectorLanguage {
    color: string;
    atmosphere: 'nasa' | 'bloomberg' | 'cyberpunk' | 'historical' | 'none';
    cameraEffect: 'push' | 'shake' | 'drift' | 'none';
    uiOverlay?: 'scanlines' | 'ticker' | 'chromatic' | 'none';
    sfx?: string;
}

const NARRATIVE_LANGUAGES: Record<string, DirectorLanguage> = {
    trend: {
        color: '#00F5FF',
        atmosphere: 'nasa',
        cameraEffect: 'push',
        uiOverlay: 'scanlines'
    },
    conflict: {
        color: '#FF3E6C',
        atmosphere: 'cyberpunk',
        cameraEffect: 'shake',
        uiOverlay: 'chromatic'
    },
    comparison: {
        color: '#10b981',
        atmosphere: 'bloomberg',
        cameraEffect: 'drift',
        uiOverlay: 'ticker'
    },
    historical: {
        color: '#F5F5DC',
        atmosphere: 'historical',
        cameraEffect: 'drift',
        uiOverlay: 'none'
    }
};

const NarrativeParticles: React.FC<{ role: string; color: string; frame: number }> = ({ role, color, frame }) => {
    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden opacity-30">
            {[...Array(15)].map((_, i) => {
                const speed = 0.5 + (i % 5) * 0.2;
                const offset = (frame * speed + i * 50) % 1200;
                return (
                    <div
                        key={i}
                        className="absolute rounded-full"
                        style={{
                            width: role === 'trend' ? '2px' : '4px',
                            height: role === 'trend' ? '10px' : '4px',
                            backgroundColor: color,
                            left: `${(i * 7) % 100}%`,
                            top: role === 'trend' ? `${100 - (offset/12)}%` : `${(offset/12)}%`,
                            boxShadow: `0 0 10px ${color}`,
                            opacity: 1 - (offset/1200)
                        }}
                    />
                );
            })}
        </div>
    );
};

export const NarrativeDirector: React.FC<{ role: string; children: React.ReactNode }> = ({ role, children }) => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();

    const language = useMemo(() => NARRATIVE_LANGUAGES[role] || NARRATIVE_LANGUAGES.trend, [role]);

    // Narrative Color Shift
    const colorIntensity = interpolate(frame % 120, [0, 60, 120], [0.1, 0.2, 0.1]);

    // Global Mood Lighting
    const lightingOpacity = role === 'conflict' ? interpolate(Math.sin(frame * 0.1), [-1, 1], [0.05, 0.15]) : 0.1;

    return (
        <div className="w-full h-full relative overflow-hidden bg-black">
            {/* 1. Narrative Particles */}
            <NarrativeParticles role={role} color={language.color} frame={frame} />

            {/* 2. Global Narrative Atmosphere (Vignette & Lighting) */}
            <div
                className="absolute inset-0 pointer-events-none transition-colors duration-1000 z-10"
                style={{
                    background: `radial-gradient(circle, transparent 30%, ${language.color}05 100%)`,
                    backgroundColor: `${language.color}${Math.floor(lightingOpacity * 255).toString(16).padStart(2, '0')}`,
                    boxShadow: `inset 0 0 150px ${language.color}${Math.floor(colorIntensity * 180).toString(16).padStart(2, '0')}`
                }}
            />

            {/* 3. Language-Specific UI Overlays */}
            {language.uiOverlay === 'chromatic' && (
                <div className="absolute inset-0 pointer-events-none opacity-10 mix-blend-screen bg-gradient-to-r from-red-500/40 via-transparent to-blue-500/40 z-20" />
            )}

            {language.uiOverlay === 'scanlines' && (
                <div className="absolute inset-0 pointer-events-none opacity-20 z-20" style={{
                    backgroundImage: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
                    backgroundSize: '100% 3px, 3px 100%'
                }} />
            )}

            {/* 4. Motion Jitter for Conflict */}
            <div style={{
                width: '100%', height: '100%',
                transform: role === 'conflict' ? `translate(${Math.random() * 2 - 1}px, ${Math.random() * 2 - 1}px)` : 'none'
            }}>
                {children}
            </div>
        </div>
    );
};
