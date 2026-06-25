import React, { useMemo } from 'react';
import { RemoteSvg } from './RemoteSvg';
import { SvgProvider, SvgStyle, GradientConfig, GlowConfig } from '../types';
import { generateSvgId } from '../lib/svgUtils';

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
  onLoad?: (pathLength: number) => void;
}

/**
 * Layered SVG Rendering
 * HARDENING: Use SVG Filters (drop-shadow, blur) to reduce DOM node duplication (P1-2).
 */
export const LayeredSvg: React.FC<LayeredSvgProps> = ({
  query,
  provider,
  color = 'white',
  strokeWidth = 2,
  style = 'fill',
  gradient,
  glow,
  depth,
  id = 'layer',
  width,
  height,
  onLoad
}) => {
  const glowConfig: GlowConfig | null = typeof glow === 'object' ? glow : glow ? { color: color, intensity: 0.6, radius: 20 } : null;
  const filterId = useMemo(() => generateSvgId('filter', `${query}-${id}`), [query, id]);

  const filter = useMemo(() => {
      const filters = [];
      if (depth) {
          filters.push(`drop-shadow(15px 15px 15px rgba(0,0,0,0.5))`);
      }
      if (glowConfig) {
          // Multi-pass glow for realism
          filters.push(`drop-shadow(0 0 ${glowConfig.radius || 10}px ${glowConfig.color || color})`);
          filters.push(`drop-shadow(0 0 ${(glowConfig.radius || 10) * 2}px ${glowConfig.color || color}80)`);
      }
      return filters.join(' ');
  }, [depth, glowConfig, color]);

  return (
    <div style={{
        width, height,
        position: 'relative',
        filter: filter, // Multi-pass high-fidelity filters
    }}>
      {/* 3. MAIN LAYER (Now handles styles/gradients) */}
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

      {/* 4. HIGHLIGHT LAYER (Tech Overlay) */}
      {style === 'tech' && (
        <div style={{
          position: 'absolute',
          inset: 0,
          opacity: 0.4,
          background: 'linear-gradient(135deg, rgba(255,255,255,0.4) 0%, rgba(255,255,255,0) 50%)',
          mixBlendMode: 'overlay',
          pointerEvents: 'none',
          borderRadius: 'inherit',
          // Mask the highlight with the main SVG for depth?
          // Browser support for mask on div is complex, so we stick to simple overlay pass.
        }} />
      )}
    </div>
  );
};
