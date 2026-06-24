import React, { useMemo, useState } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { LayeredSvg } from './LayeredSvg';
import { AnimationType, SvgProvider, SvgStyle, Importance, GlowConfig, GradientConfig, LayerType } from '../types';
import { GlassPanel } from './GlassPanel';
import { getEntranceProgress } from '../lib/animationUtils';

// Import CSS once in the composition root or here for individual components
// but standardizing on a single stylesheet helps performance.
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

export const AnimatedSvg: React.FC<AnimatedSvgProps> = ({
  query,
  provider,
  animation = 'fade',
  startFrame = 0,
  durationInFrames = 150,
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

  // 1. OPTIMIZATION: Conditional Spring vs Interpolation
  // High importance or center hub objects get smooth springs
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
      default:
        return { opacity: spr * baseOpacity, transform: `scale(${baseScale})` };
    }
  }, [animation, relativeFrame, spr, baseScale, baseOpacity]);

  // 2. HARDENING: Use inline styles for variables only, shared CSS for rules
  const variableStyles = useMemo(() => {
    return {
        '--draw-progress': spr,
        '--path-length': pathLength,
        '--glow-pulse': 0.5 + Math.sin(relativeFrame / 15) * 0.5,
        '--glow-color': color
    } as React.CSSProperties;
  }, [spr, pathLength, relativeFrame, color]);

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
        ...variableStyles
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
                setPathLength(Math.max(...lengths));
            }
        }}
      />
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
