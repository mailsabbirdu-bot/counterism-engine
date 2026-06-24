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

        // Inject color and stroke-width if needed into the raw SVG string
        let processed = content;

        // Basic injection (Real production system would use a parser,
        // but this keeps architecture simple as requested)
        processed = processed.replace(/stroke="[^"]*"/g, `stroke="${color}"`);
        processed = processed.replace(/fill="[^"]*"/g, `fill="${color}"`);
        processed = processed.replace(/stroke-width="[^"]*"/g, `stroke-width="${strokeWidth}"`);

        // If the SVG doesn't have these attributes, prepend them to paths
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
    return <div style={{ color: 'red', fontSize: '12px' }}>Icon Error: {error}</div>;
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
