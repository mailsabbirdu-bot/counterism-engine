import React, { useMemo, useEffect } from 'react';
import { SvgProvider, SvgStyle, GradientConfig } from '../types';
import { SvgRegistry } from '../lib/svgRegistry';
import { ENGINE_CONSTANTS } from '../lib/constants';

interface RemoteSvgProps {
  query: string;
  provider: SvgProvider;
  color?: string;
  strokeWidth?: number;
  style?: SvgStyle;
  gradient?: GradientConfig;
  id?: string;
  onLoad?: (pathLength: number) => void;
}

export const RemoteSvg: React.FC<RemoteSvgProps> = ({
  query,
  provider,
  color = 'white',
  strokeWidth = ENGINE_CONSTANTS.DEFAULT_STROKE_WIDTH,
  style = 'fill',
  gradient,
  id = 'svg',
  onLoad
}) => {
  // HARDENING: Render from registry ONLY. No runtime fetching or DOM parsing.
  const asset = SvgRegistry.get(query, provider);

  const gradientId = useMemo(() => {
    // HARDENING (BUG-5): Use hashed IDs to prevent oversized IDs from long query strings
    let hash = 0;
    const str = `${query}-${id}`;
    for (let i = 0; i < str.length; i++) {
        hash = ((hash << 5) - hash) + str.charCodeAt(i);
        hash |= 0;
    }
    return `grad-${Math.abs(hash).toString(16)}`;
  }, [query, id]);

  const processedMarkup = useMemo(() => {
      if (!asset) return null;

      let markup = asset.markup;
      const finalColor = gradient ? `url(#${gradientId})` : color;

      // Robust attribute injection via simple string replacement for performance
      // since markup was already sanitized/processed in preloader.

      // 1. Force Scaling
      markup = markup.replace(/<svg/, `<svg width="100%" height="100%" preserveAspectRatio="xMidYMid meet"`);

      // 2. Inject Gradient if needed
      if (gradient) {
          const gradDef = `
            <defs>
                <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" style="stop-color:${gradient.start};stop-opacity:1" />
                    <stop offset="100%" style="stop-color:${gradient.end};stop-opacity:1" />
                </linearGradient>
            </defs>
          `;
          markup = markup.replace(/>/, `>${gradDef}`);
      }

      // 3. Apply Style (Deterministic string replacement)
      // Note: In a real production system, we might use a more sophisticated
      // pre-serialized JSON structure for paths, but for this refactor
      // we maintain the current string-based injection for compatibility.

      if (style === 'outline') {
          markup = markup.replace(/fill="[^"]*"/g, 'fill="none"');
          markup = markup.replace(/stroke="[^"]*"/g, `stroke="${finalColor}"`);
          markup = markup.replace(/stroke-width="[^"]*"/g, `stroke-width="${strokeWidth}"`);
      } else {
          markup = markup.replace(/fill="[^"]*"/g, `fill="${finalColor}"`);
          if (style === 'tech' || style === 'corporate') {
              markup = markup.replace(/stroke="[^"]*"/g, `stroke="${finalColor}"`);
              markup = markup.replace(/stroke-width="[^"]*"/g, `stroke-width="${strokeWidth * 0.5}"`);
          }
      }

      return markup;
  }, [asset, color, strokeWidth, style, gradient, gradientId]);

  // Notify parent of path length for animations
  useEffect(() => {
      if (asset && onLoad) {
          onLoad(asset.pathLength);
      }
  }, [asset, onLoad]);

  if (!asset) {
    return (
        <div className="bg-red-500/10 p-2 rounded text-[10px] text-red-500 border border-red-500/20 text-center">
            SVG Missing: {query} (Run Preloader)
        </div>
    );
  }

  return (
    <div
      className="w-full h-full flex items-center justify-center"
      dangerouslySetInnerHTML={{ __html: processedMarkup || '' }}
    />
  );
};
