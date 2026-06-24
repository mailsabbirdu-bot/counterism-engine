import React, { useEffect, useState, useMemo } from 'react';
import { SvgProvider, SvgStyle, GradientConfig } from '../types';
import { SvgProviderService } from '../services/SvgProviderService';
import { random } from 'remotion';

interface RemoteSvgProps {
  query: string;
  provider: SvgProvider;
  color?: string;
  strokeWidth?: number;
  style?: SvgStyle;
  gradient?: GradientConfig;
  id?: string;
  onLoad?: (svgData: string) => void;
}

export const RemoteSvg: React.FC<RemoteSvgProps> = ({
  query,
  provider,
  color = 'white',
  strokeWidth = 2,
  style = 'fill',
  gradient,
  id = 'svg',
  onLoad
}) => {
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const gradientId = useMemo(() => `grad-${query.replace(/[^a-z0-9]/gi, '')}-${Math.floor(random(id) * 10000)}`, [query, id]);

  useEffect(() => {
    let isMounted = true;

    SvgProviderService.fetchSvg(query, provider)
      .then(content => {
        if (!isMounted) return;

        // 1. SCALING FIX: Strip hardcoded width/height and force 100%
        let processed = content;
        processed = processed.replace(/width="[^"]*"/, 'width="100%"');
        processed = processed.replace(/height="[^"]*"/, 'height="100%"');

        const finalColor = gradient ? `url(#${gradientId})` : color;

        // 2. STYLING SYSTEM
        if (style === 'outline') {
            // Force outline mode: kill all fills, force strokes
            processed = processed.replace(/fill="[^"]*"/g, 'fill="none"');
            processed = processed.replace(/stroke="[^"]*"/g, `stroke="${finalColor}"`);
            processed = processed.replace(/stroke-width="[^"]*"/g, `stroke-width="${strokeWidth}"`);

            if (!processed.includes('stroke=')) {
                processed = processed.replace(/<(path|rect|circle|ellipse|line|polyline|polygon)/g, `<$1 stroke="${finalColor}" stroke-width="${strokeWidth}" fill="none"`);
            }
        } else {
            // Fill or other styles
            processed = processed.replace(/fill="[^"]*"/g, `fill="${finalColor}"`);
            processed = processed.replace(/stroke="[^"]*"/g, `stroke="${finalColor}"`);
            processed = processed.replace(/stroke-width="[^"]*"/g, `stroke-width="${strokeWidth}"`);
        }

        // 3. GRADIENT INJECTION
        if (gradient) {
            const gradDef = `
                <defs>
                    <linearGradient id="${gradientId}" x1="0%" y1="0%" x2="100%" y2="100%">
                        <stop offset="0%" style="stop-color:${gradient.start};stop-opacity:1" />
                        <stop offset="100%" style="stop-color:${gradient.end};stop-opacity:1" />
                    </linearGradient>
                </defs>
            `;
            // Insert defs at the beginning of SVG
            processed = processed.replace(/<svg([^>]*)>/, `<svg$1>${gradDef}`);
        }

        setSvgContent(processed);
        if (onLoad) onLoad(processed);
      })
      .catch(err => {
        if (isMounted) setError(err.message);
      });

    return () => { isMounted = false; };
  }, [query, provider, color, strokeWidth, style, gradient, gradientId]);

  if (error) {
    return (
        <div className="bg-red-500/10 p-2 rounded text-[10px] text-red-500 border border-red-500/20 text-center">
            SVG Missing: {query}
        </div>
    );
  }

  if (!svgContent) {
    return <div className="animate-pulse bg-white/10 rounded-full w-full h-full" />;
  }

  return (
    <div
      className="w-full h-full flex items-center justify-center"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
};
