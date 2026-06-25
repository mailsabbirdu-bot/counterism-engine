import React, { useMemo, useState, useEffect } from 'react';
import { LayeredSvg } from './LayeredSvg';
import { AnimationType, SvgProvider, SvgStyle, Importance, GlowConfig, GradientConfig, LayerType } from '../types';
import { GlassPanel } from './GlassPanel';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';
import { ENGINE_CONSTANTS } from '../lib/constants';
import { getAnimationStyles } from '../lib/animationRegistry';
import { getTheme } from '../lib/themes';

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
  const theme = getTheme(); // In a real system, we'd get this from a ThemeContext

  const [pathLength, setPathLength] = useState<number>(ENGINE_CONSTANTS.MAX_SVG_PATH_LENGTH);

  const relativeFrame = frame - startFrame;

  // 1. OPTIMIZATION: Conditional Spring vs Interpolation
  const isHighImportance = importance === 'primary' || container === 'glass_panel';
  const spr = getEntranceProgress(frame, fps, startFrame, isHighImportance);

  // Automatic importance-based scaling and opacity
  const baseScale = importance === 'primary' ? 1.2 : importance === 'decorative' ? 0.7 : 1;
  const baseOpacity = importance === 'decorative' ? 0.4 : 1;

  // Theme-aware coloring
  const finalColor = color === 'white' ? theme.primaryColor : color;
  const importanceGlow = importance === 'primary' && !glow ? { color: finalColor, intensity: 0.4, radius: 30 } : glow;

  const animationStyles = useMemo(() => {
    if (relativeFrame < 0) return { opacity: 0 };
    return getAnimationStyles(animation, { relativeFrame, spr, baseScale, baseOpacity });
  }, [animation, relativeFrame, spr, baseScale, baseOpacity]);

  const variableStyles = useMemo(() => {
    const dashOffset = pathLength * (1 - spr);

    return {
        '--draw-progress': spr,
        '--dash-offset': `${dashOffset}px`,
        '--path-length': `${pathLength}px`,
        '--glow-pulse': 0.5 + Math.sin(relativeFrame / 15) * 0.5,
        '--glow-color': finalColor,
        '--glass-blur': `${ENGINE_CONSTANTS.GLASS_PANEL_BLUR}px`
    } as React.CSSProperties;
  }, [spr, pathLength, relativeFrame, finalColor]);

  const svgLayer = (
    <LayeredSvg
      query={query}
      provider={provider}
      color={finalColor}
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
