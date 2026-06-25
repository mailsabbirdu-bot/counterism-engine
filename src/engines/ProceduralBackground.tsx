import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

export const ProceduralBackground: React.FC<{ config: any }> = ({ config }) => {
  const frame = useCurrentFrame();
  const variant = config.variant || 'neon_grid';
  const primaryColor = config.primaryColor || '#0F172A';
  const secondaryColor = config.secondaryColor || '#1E293B';
  const accentColor = config.accentColor || '#00F5FF';

  const renderVariant = () => {
    switch (variant) {
      case 'dark_particles':
        return (
          <AbsoluteFill className="overflow-hidden" style={{ backgroundColor: primaryColor }}>
            {/* Morphing Background Gradient */}
            <div style={{
                position: 'absolute',
                inset: '-50%',
                background: `radial-gradient(circle at ${50 + Math.sin(frame / 60) * 20}% ${50 + Math.cos(frame / 80) * 20}%, ${secondaryColor} 0%, ${primaryColor} 70%)`,
                transform: `rotate(${frame * 0.1}deg)`,
                opacity: 0.8
            }} />

            {/* Animated Particles */}
            {[...Array(20)].map((_, i) => {
              const x = (i * 7.7) % 100;
              const y = (i * 13.3) % 100;
              const size = 2 + (i % 4);
              const op = 0.1 + (i % 3) * 0.1;
              return (
                <div key={i} style={{
                    position: 'absolute',
                    left: `${x}%`,
                    top: `${y}%`,
                    width: size,
                    height: size,
                    backgroundColor: accentColor,
                    borderRadius: '50%',
                    opacity: op,
                    boxShadow: `0 0 10px ${accentColor}`,
                    transform: `translate3d(${Math.sin((frame + i * 10) / 40) * 50}px, ${Math.cos((frame + i * 15) / 50) * 50}px, 0)`
                }} />
              );
            })}
          </AbsoluteFill>
        );

      case 'liquid_gradient':
        return (
          <AbsoluteFill className="overflow-hidden" style={{ backgroundColor: primaryColor }}>
            <div style={{
                position: 'absolute',
                inset: 0,
                background: `linear-gradient(${135 + frame * 0.2}deg, ${primaryColor}, ${secondaryColor})`,
                filter: 'hue-rotate(' + Math.sin(frame / 100) * 30 + 'deg)'
            }} />
            <div style={{
                position: 'absolute',
                inset: 0,
                background: `radial-gradient(circle at ${50 + Math.sin(frame / 50) * 30}% ${50 + Math.cos(frame / 70) * 30}%, ${accentColor}20 0%, transparent 50%)`,
                mixBlendMode: 'screen'
            }} />
          </AbsoluteFill>
        );

      case 'neon_grid':
      default:
        const gridOp = interpolate(Math.sin(frame / 30), [-1, 1], [0.03, 0.08]);
        return (
          <AbsoluteFill className="overflow-hidden" style={{ backgroundColor: primaryColor }}>
             {/* 3D Perspective Grid */}
             <div style={{
                 position: 'absolute',
                 inset: 0,
                 transform: 'perspective(1000px) rotateX(60deg) scale(2)',
                 transformOrigin: 'center bottom',
                 opacity: 0.4
             }}>
                 <div style={{
                     position: 'absolute',
                     inset: 0,
                     backgroundImage: `linear-gradient(to right, ${accentColor} 1px, transparent 1px), linear-gradient(to bottom, ${accentColor} 1px, transparent 1px)`,
                     backgroundSize: '100px 100px',
                     transform: `translateY(${(frame * 2) % 100}px)`,
                     maskImage: 'linear-gradient(to bottom, transparent, black)'
                 }} />
             </div>

             {/* Scanning Line */}
             <div style={{
                 position: 'absolute',
                 left: 0,
                 right: 0,
                 top: (frame * 5) % 1080,
                 height: '2px',
                 background: `linear-gradient(to right, transparent, ${accentColor}, transparent)`,
                 opacity: 0.3,
                 boxShadow: `0 0 20px ${accentColor}`
             }} />

             {/* Vignette */}
             <div style={{
                 position: 'absolute',
                 inset: 0,
                 background: 'radial-gradient(circle at center, transparent 0%, rgba(0,0,0,0.6) 100%)'
             }} />
          </AbsoluteFill>
        );
    }
  };

  return renderVariant();
};
