import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from 'remotion';

const cinematicEase = Easing.bezier(0.65, 0, 0.35, 1);

export const TextEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const text = overlay.text || overlay.content || '';
  const items = text.split(' ');

  const heroConfig = overlay.hero_config;
  const heroWord = heroConfig?.word?.replace(/[.।]/g, '');

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

          // Hero Word Logic
          const isHero = item.replace(/[.।]/g, '') === heroWord;
          const heroActive = heroConfig && frame >= heroConfig.start;
          const heroFrame = frame - heroConfig?.start;

          const heroEntrance = spring({
             frame: heroFrame,
             fps,
             config: { damping: 12, stiffness: 100 }
          });

          let style: React.CSSProperties = {
            display: 'inline-block',
            whiteSpace: item === ' ' ? 'pre' : 'normal',
            fontWeight: 900,
            opacity: progress,
          };

          const activeColor = isHero && heroActive ? heroConfig.color : (overlay.color || 'white');
          style.color = activeColor;

          if (isHero && heroActive) {
             if (heroConfig.animation === 'glow_pulse') {
                 const glow = interpolate(heroEntrance, [0, 1], [0, 40]);
                 style.textShadow = `0 0 ${glow}px ${heroConfig.color}`;
                 style.transform = `scale(${1 + heroEntrance * 0.2})`;
             } else if (heroConfig.animation === 'isolate_zoom') {
                 style.transform = `scale(${1 + heroEntrance * 0.5})`;
                 style.zIndex = 100;
             } else if (heroConfig.animation === 'bounce_pop') {
                 const jump = Math.sin(heroEntrance * Math.PI) * -30;
                 style.transform = `translateY(${jump}px) scale(${1 + heroEntrance * 0.1})`;
             }
          } else if (heroActive && heroConfig.animation === 'isolate_zoom') {
             style.opacity = progress * (1 - heroEntrance * 0.8);
             style.filter = `blur(${heroEntrance * 10}px)`;
          }

          if (overlay.animation === 'cinematicGlow') {
            const blur = interpolate(progress, [0, 1], [20, 0]);
            const brightness = interpolate(progress, [0, 1], [3, 1]);
            const scale = interpolate(progress, [0, 1], [0.9, 1]);
            const yOffset = interpolate(progress, [0, 1], [20, 0]);
            style.filter = progress < 1 ? `blur(${blur}px) brightness(${brightness})` : (style.filter || 'none');
            style.transform = (style.transform || '') + ` translateY(${yOffset}px) scale(${scale})`;
          } else if (overlay.animation === 'slideUp') {
            const yOffset = interpolate(progress, [0, 1], [150, 0]);
            style.transform = (style.transform || '') + ` translateY(${yOffset}px)`;
          } else if (overlay.animation === 'wordByWord') {
            const scale = interpolate(progress, [0, 1], [0.5, 1]);
            style.transform = (style.transform || '') + ` scale(${scale})`;
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
