import React, { useMemo, useState } from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';
import { LayeredSvg } from './LayeredSvg';
import { AnimationType, SvgProvider, SvgStyle, Importance, GlowConfig, GradientConfig } from '../types';
import { GlassPanel } from './GlassPanel';

interface AnimatedSvgProps {
  query: string;
  provider: SvgProvider;
  animation: AnimationType;
  startFrame: number;
  durationInFrames: number;
  width: number;
  height: number;
  x: number;
  y: number;
  color?: string;
  strokeWidth?: number;

  // Professional Styling
  style?: SvgStyle;
  importance?: Importance;
  glow?: boolean | GlowConfig;
  depth?: boolean;
  container?: 'glass_panel';
  gradient?: GradientConfig;
  id?: string;

  // Grouping/Composition support
  groupOffset?: { x: number, y: number };
}

export const AnimatedSvg: React.FC<AnimatedSvgProps> = ({
  query,
  provider,
  animation,
  startFrame,
  durationInFrames,
  width,
  height,
  x,
  y,
  color = 'white',
  strokeWidth = 2,
  style = 'fill',
  importance = 'secondary',
  glow,
  depth,
  container,
  gradient,
  id = 'svg',
  groupOffset = { x: 0, y: 0 }
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [pathLength, setPathLength] = useState<number>(5000);

  const relativeFrame = frame - startFrame;

  // Automatic importance-based scaling and opacity
  const baseScale = importance === 'primary' ? 1.2 : importance === 'decorative' ? 0.7 : 1;
  const baseOpacity = importance === 'decorative' ? 0.4 : 1;
  const importanceGlow = importance === 'primary' && !glow ? { color, intensity: 0.4, radius: 30 } : glow;

  // Base entrance spring
  const spr = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 12 },
  });

  const animationStyles = useMemo(() => {
    if (relativeFrame < 0) return { opacity: 0 };

    const progress = Math.min(1, Math.max(0, relativeFrame / durationInFrames));

    switch (animation) {
      case 'fade':
        return { opacity: spr * baseOpacity };
      case 'scale':
        return { opacity: spr * baseOpacity, transform: `scale(${spr * baseScale})` };
      case 'pop':
        return { opacity: spr * baseOpacity, transform: `scale(${spr * 1.1 * baseScale})` };
      case 'rotate':
        return { opacity: spr * baseOpacity, transform: `rotate(${spr * 360}deg) scale(${spr * baseScale})` };
      case 'bounce':
        const bounce = spring({ frame: relativeFrame, fps, config: { mass: 0.5, damping: 5 } });
        return { opacity: baseOpacity, transform: `scale(${bounce * baseScale})` };
      case 'slideUp':
        return { opacity: spr * baseOpacity, transform: `translateY(${(1 - spr) * 100}px) scale(${baseScale})` };
      case 'slideDown':
        return { opacity: spr * baseOpacity, transform: `translateY(${(spr - 1) * 100}px) scale(${baseScale})` };
      case 'pulse':
        const pulse = 1 + Math.sin(relativeFrame / 10) * 0.05;
        return { opacity: baseOpacity, transform: `scale(${spr * baseScale * pulse})` };
      case 'float':
        const floatY = Math.sin(relativeFrame / 20) * 20;
        return { opacity: spr * baseOpacity, transform: `translateY(${floatY}px) scale(${spr * baseScale})` };
      case 'orbit':
        const orbitX = Math.cos(relativeFrame / 30) * 50;
        const orbitY = Math.sin(relativeFrame / 30) * 50;
        return { opacity: spr * baseOpacity, transform: `translate(${orbitX}px, ${orbitY}px) scale(${spr * baseScale})` };
      case 'reveal':
        return { opacity: 1, clipPath: `inset(0 ${100 - spr * 100}% 0 0)`, transform: `scale(${baseScale})` };
      case 'draw':
      case 'trace':
        return { opacity: 1, transform: `scale(${baseScale})` };
      case 'glowPulse':
        return { opacity: 1, transform: `scale(${baseScale})` };
      default:
        return { opacity: baseOpacity, transform: `scale(${baseScale})` };
    }
  }, [animation, relativeFrame, spr, baseScale, baseOpacity, durationInFrames, fps]);

  const customAnimStyles = useMemo(() => {
    if (animation !== 'draw' && animation !== 'trace' && animation !== 'glowPulse') return {};

    return {
        '--draw-progress': spr,
        '--path-length': pathLength,
        '--glow-pulse': 0.5 + Math.sin(relativeFrame / 15) * 0.5,
    };
  }, [animation, spr, pathLength, relativeFrame]);

  const content = (
    <div
      style={{
        position: 'absolute',
        left: x + groupOffset.x,
        top: y + groupOffset.y,
        width,
        height,
        transform: 'translate(-50%, -50%)',
        ...animationStyles,
        ...customAnimStyles as any
      }}
      className={`svg-motion-container ${animation}`}
    >
      <LayeredSvg
        query={query}
        provider={provider}
        color={color}
        strokeWidth={strokeWidth}
        style={style}
        gradient={gradient}
        glow={animation === 'glowPulse' ? true : importanceGlow}
        depth={depth}
        width={width}
        height={height}
        id={id}
        onLoad={(_, lengths) => {
            if (lengths.length > 0) {
                // We use the max length of all paths for the CSS animation
                setPathLength(Math.max(...lengths));
            }
        }}
      />

      <style dangerouslySetInnerHTML={{ __html: `
        .svg-motion-container.draw svg path,
        .svg-motion-container.trace svg path {
          stroke-dasharray: var(--path-length, 5000);
          stroke-dashoffset: calc(var(--path-length, 5000) * (1 - var(--draw-progress, 1)));
          transition: stroke-dashoffset 0.1s linear;
        }
        .svg-motion-container.trace svg path {
          stroke-width: 4px;
          filter: drop-shadow(0 0 10px currentColor);
        }
        .svg-motion-container.glowPulse > div {
           filter: drop-shadow(0 0 calc(var(--glow-pulse) * 30px) ${color});
           opacity: calc(0.6 + var(--glow-pulse) * 0.4);
        }
      `}} />
    </div>
  );

  if (container === 'glass_panel') {
      return (
        <div style={{ position: 'absolute', left: x + groupOffset.x, top: y + groupOffset.y, transform: 'translate(-50%, -50%)' }}>
            <GlassPanel width={width * 1.5} height={height * 1.5} startFrame={startFrame}>
                <div style={{ transform: 'scale(0.8)' }}>
                    <LayeredSvg
                        query={query}
                        provider={provider}
                        color={color}
                        strokeWidth={strokeWidth}
                        style={style}
                        gradient={gradient}
                        glow={importanceGlow}
                        depth={depth}
                        width={width}
                        height={height}
                        id={id}
                    />
                </div>
            </GlassPanel>
        </div>
      );
  }

  return content;
};
