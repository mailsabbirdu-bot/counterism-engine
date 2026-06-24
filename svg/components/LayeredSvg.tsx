import React from 'react';
import { RemoteSvg } from './RemoteSvg';
import { SvgProvider, SvgStyle, GradientConfig, GlowConfig } from '../types';

interface LayeredSvgProps {
  query: string;
  provider: SvgProvider;
  color?: string;
  strokeWidth?: number;
  style?: SvgStyle;
  gradient?: GradientConfig;
  glow?: boolean | GlowConfig;
  depth?: boolean;
  id?: string;
  width: number;
  height: number;
  onLoad?: (svgData: string, pathLengths: number[]) => void;
}

export const LayeredSvg: React.FC<LayeredSvgProps> = ({
  query,
  provider,
  color = 'white',
  strokeWidth = 2,
  style = 'fill',
  gradient,
  glow,
  depth,
  id,
  width,
  height,
  onLoad
}) => {
  const glowConfig: GlowConfig | null = typeof glow === 'object' ? glow : glow ? { color: color, intensity: 0.6, radius: 20 } : null;

  return (
    <div style={{ width, height, position: 'relative' }}>
      {/* 1. DEPTH LAYER (Shadow) */}
      {depth && (
        <div style={{ position: 'absolute', inset: 0, transform: 'translate(10px, 10px)', filter: 'blur(10px)', opacity: 0.3 }}>
          <RemoteSvg
            query={query}
            provider={provider}
            color="black"
            style={style}
          />
        </div>
      )}

      {/* 2. GLOW LAYER */}
      {glowConfig && (
        <div style={{
          position: 'absolute',
          inset: 0,
          filter: `blur(${glowConfig.radius || 20}px)`,
          opacity: glowConfig.intensity || 0.6,
          transform: 'scale(1.05)'
        }}>
          <RemoteSvg
            query={query}
            provider={provider}
            color={glowConfig.color || color}
            style={style === 'outline' ? 'outline' : 'fill'}
            strokeWidth={strokeWidth + 2}
          />
        </div>
      )}

      {/* 3. MAIN LAYER */}
      <div style={{ position: 'absolute', inset: 0 }}>
        <RemoteSvg
          query={query}
          provider={provider}
          color={color}
          style={style}
          strokeWidth={strokeWidth}
          gradient={gradient}
          id={id}
          onLoad={onLoad}
        />
      </div>

      {/* 4. HIGHLIGHT LAYER */}
      {style === 'tech' && (
        <div style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.4,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 50%)',
          mixBlendMode: 'overlay',
          pointerEvents: 'none',
          borderRadius: 'inherit'
        }} />
      )}
    </div>
  );
};
