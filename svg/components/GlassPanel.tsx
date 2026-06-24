import React from 'react';
import { spring, useCurrentFrame, useVideoConfig } from 'remotion';

interface GlassPanelProps {
  children: React.ReactNode;
  width: number;
  height: number;
  startFrame: number;
}

export const GlassPanel: React.FC<GlassPanelProps> = ({ children, width, height, startFrame }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const spr = spring({
    frame: frame - startFrame,
    fps,
    config: { damping: 12 },
  });

  if (frame < startFrame) return null;

  return (
    <div style={{
      width,
      height,
      backgroundColor: 'rgba(255, 255, 255, 0.05)',
      backdropFilter: 'blur(20px)',
      border: '1px solid rgba(255, 255, 255, 0.1)',
      borderRadius: '24px',
      boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37), inset 0 0 0 1px rgba(255, 255, 255, 0.1)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      opacity: spr,
      transform: `scale(${0.8 + spr * 0.2})`,
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Subtle sheen reflection */}
      <div style={{
        position: 'absolute',
        top: '-50%',
        left: '-50%',
        width: '200%',
        height: '200%',
        background: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 40%, rgba(255,255,255,0) 60%, rgba(255,255,255,0.1) 100%)',
        transform: `rotate(${spr * 20}deg)`,
        pointerEvents: 'none'
      }} />

      {children}
    </div>
  );
};
