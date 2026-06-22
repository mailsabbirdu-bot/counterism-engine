import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from 'remotion';
import { safeNumber } from '../lib/safeNumber';

const cinematicEase = Easing.bezier(0.65, 0, 0.35, 1);

export const TextEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width, height, fps } = useVideoConfig();

  const start = safeNumber(overlay.start, 0);
  const duration = safeNumber(overlay.duration, 120);
  const relativeFrame = frame - start;

  if (frame < start || frame > start + duration) {
    return null;
  }

  const text = (overlay.text || overlay.content || '').trim();
  const items = text.split(/\s+/);

  const heroConfig = overlay.hero_config;
  const heroWord = heroConfig?.word?.replace(/[.।]/g, '');

  const baseFontSize = typeof overlay.fontSize === 'number' ? `${overlay.fontSize}px` : (overlay.fontSize || "120px");
  const x = safeNumber(overlay.position?.x, width / 2);
  const y = safeNumber(overlay.position?.y, height / 2);

  if (frame % 30 === 0) {
    console.log(`[TextEngine] Scene: ${overlay.scene_id} Overlay: ${overlay.id} Visible: ${frame >= start && frame <= start + duration} Text: "${text.substring(0, 20)}..." Pos: (${x}, ${y}) Font: ${overlay.font} Size: ${baseFontSize} Hero: ${heroWord}`);
  }

  return (
    <div
      className="absolute pointer-events-none"
      style={{
        position: 'absolute',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: overlay.font || 'Inter, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
        fontSize: baseFontSize,
        zIndex: overlay.zIndex || 1000, // Ultra-high zIndex for text
        left: `${x}px`,
        top: `${y}px`,
        transform: 'translate(-50%, -50%)',
        // SCREEN SAFETY: Limit width and ensure wrapping
        width: '1800px', // Wider canvas for flexible centering
        maxWidth: '1800px',
        height: 'auto',
        textShadow: '0 4px 30px rgba(0,0,0,1), 0 0 120px rgba(0,0,0,0.6)', // Maximum contrast shadows
        color: overlay.color || 'white',
        WebkitTextStroke: '2px rgba(0,0,0,0.5)', // Visible readability stroke
        whiteSpace: 'normal', // Allow wrapping
        lineHeight: 1.2,
        overflow: 'visible',
        opacity: 1, // Force base opacity
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
          const itemDelay = i * (Number(overlay.stagger) || 3); // stagger in frames
          const itemFrame = relativeFrame - itemDelay;

          const entrance = spring({
            frame: isNaN(itemFrame) ? 0 : itemFrame,
            fps,
            config: { damping: 15, stiffness: 100 },
          });

          const exitFrame = duration - 15 - (items.length - i) * (Number(overlay.stagger) || 1);
          const exit = interpolate(
            isNaN(relativeFrame) ? 0 : relativeFrame,
            [exitFrame, exitFrame + 15],
            [1, 0],
            { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
          );

          const progress = entrance * exit;

          // Hero Word Logic
          const isHero = item.replace(/[.।]/g, '') === heroWord;
          const heroStart = heroConfig?.start ?? 0;
          const heroActive = !!(heroConfig && frame >= heroStart);
          const heroFrame = heroConfig ? Math.max(0, frame - heroStart) : 0;

          const heroEntrance = spring({
             frame: isNaN(heroFrame) ? 0 : heroFrame,
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
             const anim = heroConfig.animation;
             if (anim === 'glow_pulse') {
                 const pulse = Math.sin(heroFrame * 0.15) * 0.5 + 0.5;
                 style.color = 'transparent';
                 // High-end Offset Neon Stroke Design
                 style.textShadow = `
                    2px 2px 0px ${heroConfig.color},
                    -1px -1px 0px white,
                    0 0 15px ${heroConfig.color}88,
                    0 0 ${30 + pulse * 20}px ${heroConfig.color}44
                 `;
                 style.WebkitTextStroke = `1.5px rgba(255,255,255,0.8)`;
                 style.transform = `scale(${1 + heroEntrance * 0.12 + pulse * 0.03}) rotate(${pulse * 1.5}deg)`;
                 style.zIndex = 100;
             } else if (anim === 'isolate_zoom') {
                 style.transform = `scale(${1 + heroEntrance * 0.35})`;
                 style.zIndex = 100;
             } else if (anim === 'bounce_pop') {
                 const jump = Math.sin(heroEntrance * Math.PI) * -25;
                 style.transform = `translateY(${jump}px) scale(${1 + heroEntrance * 0.1})`;
             } else if (anim === 'neon_flicker') {
                 const flicker = Math.sin(heroFrame * 0.5) > 0 ? 1 : 0.9;
                 style.opacity = progress * flicker;
                 style.textShadow = `0 0 15px ${heroConfig.color}, 0 0 5px white`;
             } else if (anim === 'shake_alert') {
                 const shake = Math.sin(heroFrame * 3) * 5;
                 style.transform = `translateX(${shake}px) scale(1.1)`;
             } else if (anim === 'rainbow_flow') {
                 style.filter = `hue-rotate(${heroFrame * 10}deg)`;
             } else if (anim === 'ghost_trail') {
                 style.textShadow = `10px 0 10px ${heroConfig.color}44, -10px 0 10px ${heroConfig.color}44`;
             } else if (anim === 'glitch_pop') {
                 const offset = Math.random() > 0.8 ? (Math.random() - 0.5) * 20 : 0;
                 style.transform = `translate(${offset}px, ${offset}px) skew(${offset/2}deg)`;
             } else if (anim === 'wave_float') {
                 style.transform = `translateY(${Math.sin(heroFrame * 0.2) * 10}px)`;
             } else if (anim === 'expand_contract') {
                 style.transform = `scale(${1 + Math.sin(heroFrame * 0.3) * 0.1})`;
             } else if (anim === 'blur_reveal') {
                 style.filter = `blur(${Math.max(0, 10 - heroFrame)}px)`;
             } else if (anim === 'color_shift') {
                 style.filter = `invert(${Math.sin(heroFrame * 0.1) * 0.5 + 0.5})`;
             } else if (anim === 'rotation_swing') {
                 style.transform = `rotate(${Math.sin(heroFrame * 0.1) * 10}deg)`;
             } else if (anim === 'shadow_pulse') {
                 style.boxShadow = `0 0 ${20 + Math.sin(heroFrame * 0.2) * 10}px ${heroConfig.color}`;
             } else if (anim === 'letter_jump') {
                 style.transform = `translateY(${heroFrame < 10 ? -20 : 0}px)`;
             } else if (anim === 'skew_slide') {
                 style.transform = `skewX(${Math.sin(heroFrame * 0.1) * 20}deg)`;
             } else if (anim === 'tilt_pan') {
                 style.transform = `perspective(500px) rotateY(${Math.sin(heroFrame * 0.1) * 30}deg)`;
             } else if (anim === 'bounce_gravity') {
                 const b = Math.abs(Math.sin(heroFrame * 0.15)) * -40;
                 style.transform = `translateY(${b}px)`;
             } else if (anim === 'border_glow') {
                 style.border = `2px solid ${heroConfig.color}`;
                 style.padding = '4px 12px';
                 style.borderRadius = '12px';
             } else if (anim === 'glass_shimmer') {
                 style.background = `linear-gradient(90deg, transparent, white, transparent)`;
                 style.backgroundSize = '200% 100%';
                 style.backgroundPosition = `${heroFrame * 5}% 0`;
                 style.WebkitBackgroundClip = 'text';
                 style.WebkitTextFillColor = 'transparent';
             } else if (anim === 'heartbeat') {
                 const beat = 1 + Math.pow(Math.sin(heroFrame * 0.2), 4) * 0.2;
                 style.transform = `scale(${beat})`;
             } else if (anim === 'strobe_flash') {
                 style.opacity = progress * (heroFrame % 4 < 2 ? 1 : 0.2);
                 style.textShadow = `0 0 20px white`;
             } else if (anim === 'threed_flip') {
                 style.transform = `perspective(1000px) rotateX(${heroFrame * 10}deg)`;
             } else if (anim === 'magnetic_pull') {
                 style.letterSpacing = `${Math.max(-10, 20 - heroFrame)}px`;
             } else if (anim === 'fire_glow') {
                 style.textShadow = `0 0 10px #ff4500, 0 0 20px #ff8c00, 0 0 30px #ffd700`;
                 style.color = '#fff';
             } else if (anim === 'pixel_scatter') {
                 style.filter = `contrast(200%) brightness(150%)`;
                 style.letterSpacing = `${heroFrame % 2 === 0 ? 2 : -2}px`;
             } else if (anim === 'swing_pivot') {
                 style.transformOrigin = 'top center';
                 style.transform = `rotate(${Math.sin(heroFrame * 0.15) * 15}deg)`;
             } else if (anim === 'depth_shadow') {
                 style.textShadow = `${heroFrame/2}px ${heroFrame/2}px 0px ${heroConfig.color}88`;
             } else if (anim === 'energy_beam') {
                 style.boxShadow = `inset 0 0 50px ${heroConfig.color}, 0 0 20px ${heroConfig.color}`;
                 style.background = `${heroConfig.color}22`;
                 style.borderRadius = '8px';
             } else if (anim === 'spiral_in') {
                 style.transform = `rotate(${heroFrame * 20}deg) scale(${Math.min(1, heroFrame/10)})`;
             } else if (anim === 'fly_in_z') {
                 style.transform = `perspective(1000px) translateZ(${Math.max(0, 500 - heroFrame * 20)}px)`;
             } else if (anim === 'typewriter_flicker') {
                 style.borderRight = heroFrame % 10 < 5 ? `4px solid ${heroConfig.color}` : 'none';
             } else if (anim === 'vibrate_intense') {
                 style.transform = `translate(${(Math.random()-0.5)*10}px, ${(Math.random()-0.5)*10}px)`;
             } else if (anim === 'float_orbit') {
                 style.transform = `translate(${Math.cos(heroFrame*0.1)*20}px, ${Math.sin(heroFrame*0.1)*20}px)`;
             } else if (anim === 'mirror_split') {
                 style.filter = `drop-shadow(20px 0 0 ${heroConfig.color}66) drop-shadow(-20px 0 0 ${heroConfig.color}66)`;
             } else if (anim === 'zoom_blur_pop') {
                 style.transform = `scale(${1 + Math.max(0, 2 - heroFrame/10)})`;
                 style.filter = `blur(${Math.max(0, 10 - heroFrame)}px)`;
             } else if (anim === 'liquid_waver') {
                 style.transform = `skewX(${Math.sin(heroFrame * 0.05) * 30}deg) skewY(${Math.cos(heroFrame * 0.05) * 10}deg)`;
             } else {
                 // Default Sleek Highlight
                 style.textShadow = `0 0 10px ${heroConfig.color}`;
                 style.transform = `scale(1.1)`;
             }
             // Add robust horizontal buffer for scaling elements to prevent word overlap
             // Using a slightly larger buffer and ensuring it applies to both sides
             style.margin = `0 ${heroEntrance * 30}px`;
             style.zIndex = 1001;
          } else if (heroActive && (heroConfig.animation === 'isolate_zoom' || heroConfig.animation === 'blur_reveal')) {
             // Less aggressive dimming for non-hero words
             style.opacity = progress * (1 - heroEntrance * 0.3);
             style.filter = `blur(${heroEntrance * 3}px)`;
          }

          if (overlay.animation === 'cinematicGlow') {
            const blur = interpolate(isNaN(progress) ? 0 : progress, [0, 1], [20, 0]);
            const brightness = interpolate(isNaN(progress) ? 0 : progress, [0, 1], [3, 1]);
            const scale = interpolate(isNaN(progress) ? 0 : progress, [0, 1], [0.9, 1]);
            const yOffset = interpolate(isNaN(progress) ? 0 : progress, [0, 1], [20, 0]);
            style.filter = progress < 1 ? `blur(${blur}px) brightness(${brightness})` : (style.filter || 'none');
            style.transform = (style.transform || '') + ` translateY(${yOffset}px) scale(${scale})`;
          } else if (overlay.animation === 'slideUp') {
            const yOffset = interpolate(isNaN(progress) ? 0 : progress, [0, 1], [150, 0]);
            style.transform = (style.transform || '') + ` translateY(${yOffset}px)`;
          } else if (overlay.animation === 'wordByWord') {
            const scale = interpolate(isNaN(progress) ? 0 : progress, [0, 1], [0.5, 1]);
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
