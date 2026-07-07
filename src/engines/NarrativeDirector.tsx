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

export const NarrativeDirector: React.FC<{ role: string; children: React.ReactNode }> = ({ role, children }) => {
    const frame = useCurrentFrame();
    const { width, height } = useVideoConfig();

    const language = useMemo(() => NARRATIVE_LANGUAGES[role] || NARRATIVE_LANGUAGES.trend, [role]);

    // Narrative Color Shift
    const colorIntensity = interpolate(frame % 120, [0, 60, 120], [0.1, 0.2, 0.1]);

    return (
        <div className="w-full h-full relative overflow-hidden">
            {/* Global Narrative Atmosphere */}
            <div
                className="absolute inset-0 pointer-events-none transition-colors duration-1000"
                style={{
                    backgroundColor: `${language.color}11`,
                    boxShadow: `inset 0 0 100px ${language.color}${Math.floor(colorIntensity * 255).toString(16).padStart(2, '0')}`
                }}
            />

            {/* Language-Specific UI Overlays */}
            {language.uiOverlay === 'chromatic' && (
                <div className="absolute inset-0 pointer-events-none opacity-20 mix-blend-screen bg-gradient-to-r from-red-500/20 via-transparent to-blue-500/20" />
            )}

            {children}
        </div>
    );
};
