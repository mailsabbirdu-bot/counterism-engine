import React, { useEffect, useState, useMemo } from 'react';
import { SvgProvider } from '../types';
import { SvgProviderService } from '../services/SvgProviderService';

interface RemoteSvgProps {
  query: string;
  provider: SvgProvider;
  color?: string;
  strokeWidth?: number;
  onLoad?: (svgData: string) => void;
}

export const RemoteSvg: React.FC<RemoteSvgProps> = ({
  query,
  provider,
  color = 'white',
  strokeWidth = 2,
  onLoad
}) => {
  const [svgContent, setSvgContent] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    SvgProviderService.fetchSvg(query, provider)
      .then(content => {
        if (!isMounted) return;

        // 1. SCALING FIX: Strip hardcoded width/height and force 100%
        let processed = content;
        processed = processed.replace(/width="[^"]*"/, 'width="100%"');
        processed = processed.replace(/height="[^"]*"/, 'height="100%"');

        // 2. STYLING FIX: Inject color and stroke-width
        processed = processed.replace(/stroke="[^"]*"/g, `stroke="${color}"`);
        processed = processed.replace(/fill="[^"]*"/g, `fill="${color}"`);
        processed = processed.replace(/stroke-width="[^"]*"/g, `stroke-width="${strokeWidth}"`);

        // Ensure stroke and stroke-width exist for outlines
        if (!processed.includes('stroke=')) {
          processed = processed.replace(/<path/g, `<path stroke="${color}" stroke-width="${strokeWidth}" fill="none"`);
        }

        setSvgContent(processed);
        if (onLoad) onLoad(processed);
      })
      .catch(err => {
        if (isMounted) setError(err.message);
      });

    return () => { isMounted = false; };
  }, [query, provider, color, strokeWidth]);

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
