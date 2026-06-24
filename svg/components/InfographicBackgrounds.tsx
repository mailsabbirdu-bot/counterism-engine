import React from 'react';
import { AbsoluteFill } from 'remotion';
import { BackgroundType } from '../types';

interface InfographicBackgroundProps {
  type?: BackgroundType;
}

export const InfographicBackground: React.FC<InfographicBackgroundProps> = ({ type }) => {
  if (!type) return null;

  return (
    <AbsoluteFill className="pointer-events-none overflow-hidden" style={{ zIndex: 0 }}>
      {type === 'tech_grid' && (
        <div
          className="absolute inset-0 opacity-[0.1]"
          style={{
            backgroundImage: `linear-gradient(#ffffff 1px, transparent 1px), linear-gradient(90deg, #ffffff 1px, transparent 1px)`,
            backgroundSize: '100px 100px'
          }}
        />
      )}

      {type === 'blueprint_grid' && (
        <div
          className="absolute inset-0 opacity-[0.15]"
          style={{
            backgroundColor: '#001a33',
            backgroundImage: `linear-gradient(rgba(255,255,255,0.1) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.1) 2px, transparent 2px), linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)`,
            backgroundSize: '100px 100px, 100px 100px, 20px 20px, 20px 20px'
          }}
        />
      )}

      {type === 'dotted_pattern' && (
        <div
          className="absolute inset-0 opacity-[0.1]"
          style={{
            backgroundImage: `radial-gradient(circle, #ffffff 2px, transparent 0)`,
            backgroundSize: '50px 50px'
          }}
        />
      )}

      {type === 'network_pattern' && (
        <svg className="absolute inset-0 w-full h-full opacity-[0.1]">
          <pattern id="network" x="0" y="0" width="200" height="200" patternUnits="userSpaceOnUse">
            <circle cx="20" cy="20" r="3" fill="white" />
            <circle cx="150" cy="40" r="3" fill="white" />
            <circle cx="80" cy="120" r="3" fill="white" />
            <circle cx="180" cy="160" r="3" fill="white" />
            <line x1="20" y1="20" x2="150" y2="40" stroke="white" strokeWidth="1" />
            <line x1="20" y1="20" x2="80" y2="120" stroke="white" strokeWidth="1" />
            <line x1="150" y1="40" x2="180" y2="160" stroke="white" strokeWidth="1" />
            <line x1="80" y1="120" x2="180" y2="160" stroke="white" strokeWidth="1" />
          </pattern>
          <rect width="100%" height="100%" fill="url(#network)" />
        </svg>
      )}

      {type === 'radial_glow' && (
        <div
          className="absolute inset-0 opacity-[0.15]"
          style={{
            background: 'radial-gradient(circle at center, rgba(59, 130, 246, 0.4) 0%, rgba(0, 0, 0, 0) 70%)'
          }}
        />
      )}
    </AbsoluteFill>
  );
};
