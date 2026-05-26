import React from 'react';
import { useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';
import { motion, AnimatePresence } from 'framer-motion';

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

  return (
    <div
      className={`absolute inset-0 flex items-center justify-center pointer-events-none p-20 ${overlay.style}`}
      style={{ fontFamily: overlay.font }}
    >
      <div className="flex flex-wrap justify-center gap-x-2">
        {items.map((item: string, i: number) => {
          const delay = i * (overlay.stagger || 0.05);

          const progress = spring({
            frame: relativeFrame,
            fps,
            config: { damping: 12 },
            delay: delay * fps,
          });

          let initial = {};
          let animate = {};
          let transition = {
            duration: 0.8,
            ease: [0.16, 1, 0.3, 1], // easeOutExpo
            delay: delay,
          };

          if (overlay.animation === 'cinematicGlow') {
            initial = { opacity: 0, filter: 'blur(10px) brightness(2)', y: 10 };
            animate = { opacity: 1, filter: 'blur(0px) brightness(1)', y: 0 };
          } else if (overlay.animation === 'slideUp') {
            initial = { opacity: 0, y: 100 };
            animate = { opacity: 1, y: 0 };
          } else if (overlay.animation === 'wordByWord') {
            initial = { opacity: 0, scale: 0.8 };
            animate = { opacity: 1, scale: 1 };
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
                textShadow: overlay.animation === 'cinematicGlow' ? '0 0 15px rgba(255,255,255,0.3)' : 'none'
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
