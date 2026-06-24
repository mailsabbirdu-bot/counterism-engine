import React, { useMemo, useState } from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';
import { RemoteSvg } from './RemoteSvg';
import { AnimationType, SvgProvider } from '../types';

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
  color,
  strokeWidth = 2
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const [hasPaths, setHasPaths] = useState(false);

  const relativeFrame = frame - startFrame;

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
        return { opacity: spr };
      case 'scale':
        return { opacity: spr, transform: `scale(${spr})` };
      case 'pop':
        return { opacity: spr, transform: `scale(${spr * 1.1})` };
      case 'rotate':
        return { opacity: spr, transform: `rotate(${spr * 360}deg) scale(${spr})` };
      case 'bounce':
        const bounce = spring({ frame: relativeFrame, fps, config: { mass: 0.5, damping: 5 } });
        return { opacity: 1, transform: `scale(${bounce})` };
      case 'slideUp':
        return { opacity: spr, transform: `translateY(${(1 - spr) * 100}px)` };
      case 'slideDown':
        return { opacity: spr, transform: `translateY(${(spr - 1) * 100}px)` };
      case 'slideLeft':
        return { opacity: spr, transform: `translateX(${(1 - spr) * 100}px)` };
      case 'slideRight':
        return { opacity: spr, transform: `translateX(${(spr - 1) * 100}px)` };
      case 'draw':
        // Handle in standard switch for outer container, but logic is inside RemoteSvg via CSS
        return { opacity: 1 };
      default:
        return { opacity: 1 };
    }
  }, [animation, relativeFrame, spr, durationInFrames, fps]);

  // CSS for Draw animation
  const drawStyles = useMemo(() => {
    if (animation !== 'draw') return {};

    // Fallback if no paths (fill-only icon)
    if (!hasPaths) {
        return { opacity: spr, transform: `scale(${spr})` };
    }

    // Path tracing logic via CSS
    // We target all paths inside the injected HTML
    return {
        '--draw-progress': spr,
    };
  }, [animation, hasPaths, spr]);

  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width,
        height,
        transform: 'translate(-50%, -50%)',
        ...animationStyles,
        ...drawStyles as any
      }}
      className={animation === 'draw' ? 'svg-draw-container' : ''}
    >
      <RemoteSvg
        query={query}
        provider={provider}
        color={color}
        strokeWidth={strokeWidth}
        onLoad={(content) => {
            if (content.includes('<path')) setHasPaths(true);
        }}
      />

      {/* Global CSS for Draw Animation */}
      <style dangerouslySetInnerHTML={{ __html: `
        .svg-draw-container svg path {
          stroke-dasharray: 1000;
          stroke-dashoffset: calc(1000 * (1 - var(--draw-progress, 1)));
          transition: stroke-dashoffset 0.1s linear;
        }
      `}} />
    </div>
  );
};
