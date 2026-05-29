import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { motion } from 'framer-motion';
import { cn } from '../lib/utils';

export const TextEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const items = overlay.splitMode === 'char'
    ? overlay.content.split('')
    : overlay.content.split(' ');

  // Base font size - if not provided, use a large default
  const baseFontSize = overlay.fontSize || "120px";

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        display: 'flex',
        alignItems: overlay.position ? 'flex-start' : 'center',
        justifyContent: overlay.position ? 'flex-start' : 'center',
        padding: overlay.position ? '0' : '80px',
        fontFamily: overlay.font || 'Inter',
        fontSize: baseFontSize,
        zIndex: overlay.zIndex,
        left: overlay.position ? `${overlay.position.x}px` : '0',
        top: overlay.position ? `${overlay.position.y}px` : '0',
        width: overlay.position ? 'auto' : '100%',
        height: overlay.position ? 'auto' : '100%',
        textShadow: '0 4px 30px rgba(0,0,0,0.5), 0 0 100px rgba(0,0,0,0.2)',
        color: 'white'
      }}
    >
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '24px',
        justifyContent: overlay.position ? 'flex-start' : 'center',
        textAlign: overlay.position ? 'left' : 'center',
        maxWidth: overlay.position ? '100%' : '80%'
      }}>
        {items.map((item: string, i: number) => {
          const delay = i * (overlay.stagger || 0.1);

          let initial = {};
          let animate = {};
          let transition = {
            duration: 1.2,
            ease: [0.16, 1, 0.3, 1], // easeOutExpo
            delay: delay,
          };

          if (overlay.animation === 'cinematicGlow') {
            initial = { opacity: 0, filter: 'blur(20px) brightness(3)', y: 20, scale: 0.9 };
            animate = { opacity: 1, filter: 'blur(0px) brightness(1)', y: 0, scale: 1 };
          } else if (overlay.animation === 'slideUp') {
            initial = { opacity: 0, y: 150 };
            animate = { opacity: 1, y: 0 };
          } else if (overlay.animation === 'wordByWord') {
            initial = { opacity: 0, scale: 0.5 };
            animate = { opacity: 1, scale: 1 };
          } else {
             // Default fade in
             initial = { opacity: 0 };
             animate = { opacity: 1 };
          }

          return (
            <motion.span
              key={i}
              initial={initial}
              animate={animate}
              transition={transition}
              style={{
                display: 'inline-block',
                whiteSpace: item === ' ' ? 'pre' : 'normal',
                fontWeight: 900, // Force extra bold for cinematic impact
              }}
            >
              {item}
            </motion.span>
          );
        })}
      </div>
    </div>
  );
};
