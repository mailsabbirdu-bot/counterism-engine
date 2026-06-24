import React, { useMemo, useState } from 'react';
import { LayeredSvg } from './LayeredSvg';
import { AnimationType, SvgProvider, SvgStyle, Importance, GlowConfig, GradientConfig, LayerType } from '../types';
import { GlassPanel } from './GlassPanel';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';
import { ENGINE_CONSTANTS } from '../lib/constants';

// Import CSS once in the composition root
import '../styles/svgAnimations.css';

export interface AnimatedSvgProps {
  query: string;
  provider: SvgProvider;
  animation?: AnimationType;
  startFrame?: number;
  durationInFrames?: number;
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
  layer?: LayerType;

  // Grouping/Composition support
  groupOffset?: { x: number, y: number };
}

/**
 * Professional Animated SVG Component
 * HARDENING: Wrapper architecture for GlassPanel (P1-3).
 */
export const AnimatedSvg: React.FC<AnimatedSvgProps> = ({
  query,
  provider,
  animation = 'fade',
  startFrame = 0,
  durationInFrames = ENGINE_CONSTANTS.DEFAULT_ANIMATION_DURATION,
  width,
  height,
  x,
  y,
  color = 'white',
  strokeWidth = ENGINE_CONSTANTS.DEFAULT_STROKE_WIDTH,
  style = 'fill',
  importance = 'secondary',
  glow,
  depth,
  container,
  gradient,
  id = 'svg',
  groupOffset = { x: 0, y: 0 }
}) => {
  const { frame, fps } = useAnimation();
  const [pathLength, setPathLength] = useState<number>(ENGINE_CONSTANTS.MAX_SVG_PATH_LENGTH);

  const relativeFrame = frame - startFrame;

  // 1. OPTIMIZATION: Conditional Spring vs Interpolation
  const isHighImportance = importance === 'primary' || container === 'glass_panel';
  const spr = getEntranceProgress(frame, fps, startFrame, isHighImportance);

  // Automatic importance-based scaling and opacity
  const baseScale = importance === 'primary' ? 1.2 : importance === 'decorative' ? 0.7 : 1;
  const baseOpacity = importance === 'decorative' ? 0.4 : 1;
  const importanceGlow = importance === 'primary' && !glow ? { color, intensity: 0.4, radius: 30 } : glow;

  const animationStyles = useMemo(() => {
    if (relativeFrame < 0) return { opacity: 0 };

    switch (animation) {
      case 'fade':
        return { opacity: spr * baseOpacity };
      case 'scale':
        return { opacity: spr * baseOpacity, transform: `scale(${spr * baseScale})` };
      case 'pop':
        return { opacity: spr * baseOpacity, transform: `scale(${spr * 1.1 * baseScale})` };
      case 'rotate':
        return { opacity: spr * baseOpacity, transform: `rotate(${(spr * 360) % 360}deg) scale(${spr * baseScale})` };
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
      default:
        return { opacity: spr * baseOpacity, transform: `scale(${baseScale})` };
    }
  }, [animation, relativeFrame, spr, baseScale, baseOpacity]);

  const variableStyles = useMemo(() => {
    const dashOffset = pathLength * (1 - spr);

    return {
        '--draw-progress': spr,
        '--dash-offset': `${dashOffset}px`,
        '--path-length': `${pathLength}px`,
        '--glow-pulse': 0.5 + Math.sin(relativeFrame / 15) * 0.5,
        '--glow-color': color
    } as React.CSSProperties;
  }, [spr, pathLength, relativeFrame, color]);

  const svgLayer = (
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
      onLoad={(length) => {
          setPathLength(length);
      }}
    />
  );

  const innerContent = (
    <div
      style={{
        width,
        height,
        transform: container === 'glass_panel' ? 'scale(0.8)' : 'none',
        ...animationStyles,
        ...variableStyles
      }}
      className={`svg-motion-container ${animation}`}
    >
      {svgLayer}
    </div>
  );

  return (
    <div style={{
        position: 'absolute',
        left: x + groupOffset.x,
        top: y + groupOffset.y,
        transform: 'translate(-50%, -50%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
    }}>
        {container === 'glass_panel' ? (
            <GlassPanel width={width * 1.5} height={height * 1.5} startFrame={startFrame}>
                {innerContent}
            </GlassPanel>
        ) : innerContent}
    </div>
  );
};
