import React from 'react';
import { useCurrentFrame } from 'remotion';
import { motion, AnimatePresence } from 'framer-motion';

export const TextEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const words = overlay.content.split(' ');
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  return (
    <div
      className={`absolute inset-0 flex items-center justify-center pointer-events-none p-20 ${overlay.style}`}
      style={{ fontFamily: overlay.font }}
    >
      <div className="flex flex-wrap justify-center gap-x-4">
        {words.map((word: string, i: number) => {
          const delay = (i * 0.1);

          let initial = {};
          let animate = {};

          if (overlay.animation === 'wordByWord') {
            initial = { opacity: 0, y: 20 };
            animate = { opacity: 1, y: 0 };
          } else if (overlay.animation === 'slideUp') {
            initial = { opacity: 0, y: 50 };
            animate = { opacity: 1, y: 0 };
          } else if (overlay.animation === 'fadeIn') {
            initial = { opacity: 0, scale: 0.95 };
            animate = { opacity: 1, scale: 1 };
          }

          return (
            <motion.span
              key={i}
              initial={initial}
              animate={animate}
              transition={{
                delay: delay,
                duration: 0.5,
                ease: "easeOut"
              }}
              style={{
                display: 'inline-block',
                textShadow: '0 0 20px rgba(255,255,255,0.5)'
              }}
            >
              {word}
            </motion.span>
          );
        })}
      </div>
    </div>
  );
};
