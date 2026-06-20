import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from 'remotion';

export const TextEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const text = overlay.text || overlay.content || '';
  const items = overlay.splitMode === 'char'
    ? text.split('')
    : text.split(' ');

  const baseFontSize = overlay.fontSize || "120px";
  const x = overlay.position?.x ?? width / 2;
  const y = overlay.position?.y ?? height / 2;

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        position: 'absolute',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: overlay.font || 'Inter',
        fontSize: baseFontSize,
        zIndex: overlay.zIndex,
        left: `${x}px`,
        top: `${y}px`,
        transform: 'translate(-50%, -50%)',
        // SCREEN SAFETY: Limit width and ensure wrapping
        width: 'auto',
        maxWidth: '1600px',
        height: 'auto',
        textShadow: '0 4px 30px rgba(0,0,0,0.5), 0 0 100px rgba(0,0,0,0.2)',
        color: overlay.color || 'white',
        whiteSpace: 'normal', // Allow wrapping
        lineHeight: 1.2
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
          const itemDelay = i * (overlay.stagger || 3); // stagger in frames
          const itemFrame = relativeFrame - itemDelay;

          const entrance = spring({
            frame: itemFrame,
            fps,
            config: { damping: 15, stiffness: 100 },
          });

          const exitFrame = overlay.duration - 15 - (items.length - i) * (overlay.stagger || 1);
          const exit = interpolate(
            relativeFrame,
            [exitFrame, exitFrame + 15],
            [1, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );

          const progress = entrance * exit;

          let style: React.CSSProperties = {
            display: 'inline-block',
            whiteSpace: item === ' ' ? 'pre' : 'normal',
            fontWeight: 900,
            opacity: progress,
          };

          if (overlay.animation === 'cinematicGlow') {
            const blur = interpolate(progress, [0, 1], [20, 0]);
            const brightness = interpolate(progress, [0, 1], [3, 1]);
            const scale = interpolate(progress, [0, 1], [0.9, 1]);
            const yOffset = interpolate(progress, [0, 1], [20, 0]);
            style.filter = progress < 1 ? `blur(${blur}px) brightness(${brightness})` : 'none';
            style.transform = `translateY(${yOffset}px) scale(${scale})`;
          } else if (overlay.animation === 'slideUp') {
            const yOffset = interpolate(progress, [0, 1], [150, 0]);
            style.transform = `translateY(${yOffset}px)`;
          } else if (overlay.animation === 'wordByWord') {
            const scale = interpolate(progress, [0, 1], [0.5, 1]);
            style.transform = `scale(${scale})`;
          }

          return (
            <span key={i} style={style}>
              {item}
            </span>
          );
        })}
      </div>
    </div>
  );
};
