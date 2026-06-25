import React, { useMemo } from 'react';
import { AbsoluteFill, interpolate, useCurrentFrame } from 'remotion';

export const ProceduralBackground: React.FC<{ config: any }> = ({ config }) => {
  const frame = useCurrentFrame();
  const variant = config.variant || 'neon_grid';
  const primaryColor = config.primaryColor || '#050505';
  const secondaryColor = config.secondaryColor || '#0A0A0B';
  const accentColor = config.accentColor || '#00F5FF';

  const renderVariant = () => {
    switch (variant) {
      case 'tech_grid':
        return (
          <AbsoluteFill className="overflow-hidden" style={{ backgroundColor: primaryColor }}>
            <div
              className="absolute inset-0 opacity-[0.1]"
              style={{
                backgroundImage: `linear-gradient(${accentColor} 1px, transparent 1px), linear-gradient(90deg, ${accentColor} 1px, transparent 1px)`,
                backgroundSize: '100px 100px',
                backgroundPosition: `${frame * 0.5}px ${frame * 0.5}px`
              }}
            />
          </AbsoluteFill>
        );

      case 'mesh_gradient':
        return (
          <AbsoluteFill className="overflow-hidden" style={{ backgroundColor: primaryColor }}>
            <div style={{
                position: 'absolute',
                inset: '-50%',
                background: `radial-gradient(circle at ${50 + Math.sin(frame / 120) * 30}% ${50 + Math.cos(frame / 150) * 30}%, ${accentColor}15 0%, transparent 50%),
                             radial-gradient(circle at ${20 + Math.cos(frame / 180) * 20}% ${80 + Math.sin(frame / 200) * 20}%, #FFD70010 0%, transparent 50%)`,
                filter: 'blur(80px)',
                transform: `rotate(${frame * 0.05}deg)`
            }} />
          </AbsoluteFill>
        );

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
        return (
          <AbsoluteFill className="overflow-hidden" style={{ backgroundColor: primaryColor }}>
             {/* 3D Perspective Grid - Endless Scrolling */}
             <div style={{
                 position: 'absolute',
                 inset: 0,
                 transform: 'perspective(1000px) rotateX(60deg) scale(2.5)',
                 transformOrigin: 'center bottom',
                 opacity: 0.35
             }}>
                 <div style={{
                     position: 'absolute',
                     inset: 0,
                     backgroundImage: `linear-gradient(to right, ${accentColor} 1px, transparent 1px), linear-gradient(to bottom, ${accentColor} 1px, transparent 1px)`,
                     backgroundSize: '100px 100px',
                     backgroundPosition: `0px ${frame * 2}px`, // Endless vertical scroll
                     maskImage: 'linear-gradient(to bottom, transparent 20%, black 80%)'
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
