import React, { useEffect, useRef } from 'react';
import { useCurrentFrame, AbsoluteFill } from 'remotion';
import { gsap } from 'gsap';

export const ShapesEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const circleRef = useRef<SVGCircleElement>(null);
  const relativeFrame = frame - overlay.start;

  useEffect(() => {
    if (circleRef.current && overlay.animation === 'pulse') {
      gsap.to(circleRef.current, {
        attr: { r: 100 },
        opacity: 0.2,
        duration: 1,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut"
      });
    }
  }, [overlay.animation]);

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  return (
    <AbsoluteFill className="pointer-events-none flex items-center justify-center">
      <svg width="100%" height="100%" viewBox="0 0 1920 1080">
        <circle
          ref={circleRef}
          cx="960"
          cy="540"
          r="50"
          fill="none"
          stroke={overlay.color}
          strokeWidth="4"
          opacity="0.5"
        />
      </svg>
    </AbsoluteFill>
  );
};
