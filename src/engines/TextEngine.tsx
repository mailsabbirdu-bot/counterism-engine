import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { motion } from 'framer-motion';

export const TextEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const items = overlay.splitMode === 'char'
    ? overlay.content.split('')
    : overlay.content.split(' ');

  // Base font size
  const baseFontSize = overlay.fontSize || "120px";

  // Center coordinate mapping
  const x = overlay.position?.x ?? 0;
  const y = overlay.position?.y ?? 0;

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: overlay.font || 'Inter',
        fontSize: baseFontSize,
        zIndex: overlay.zIndex,
        // Positioning logic: Top-Left Absolute (x,y is center of text)
        left: `${x}px`,
        top: `${y}px`,
        transform: 'translate(-50%, -50%)',
        width: 'auto',
        height: 'auto',
        textShadow: '0 4px 30px rgba(0,0,0,0.5), 0 0 100px rgba(0,0,0,0.2)',
        color: 'white',
        whiteSpace: 'nowrap'
      }}
    >
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '24px',
        justifyContent: 'center',
        textAlign: 'center'
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
                fontWeight: 900,
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
