import React, { useEffect, useState, useMemo, useRef } from 'react';
import { SvgProvider, SvgStyle, GradientConfig } from '../types';
import { SvgCacheService } from '../services/SvgCacheService';
import { random } from 'remotion';

interface RemoteSvgProps {
  query: string;
  provider: SvgProvider;
  color?: string;
  strokeWidth?: number;
  style?: SvgStyle;
  gradient?: GradientConfig;
  id?: string;
  onLoad?: (svgData: string, pathLengths: number[]) => void;
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
  const containerRef = useRef<HTMLDivElement>(null);

  const gradientId = useMemo(() => `grad-${query.replace(/[^a-z0-9]/gi, '')}-${Math.floor(random(id) * 10000)}`, [query, id]);

  useEffect(() => {
    let isMounted = true;

    SvgCacheService.getSvg(query, provider)
      .then(content => {
        if (!isMounted) return;

        const parser = new DOMParser();
        const doc = parser.parseFromString(content, 'image/svg+xml');
        const svgElement = doc.querySelector('svg');

        if (!svgElement) {
            throw new Error('Invalid SVG: No root element');
        }

        svgElement.setAttribute('width', '100%');
        svgElement.setAttribute('height', '100%');
        svgElement.setAttribute('preserveAspectRatio', 'xMidYMid meet');

        const finalColor = gradient ? `url(#${gradientId})` : color;

        // TARGET ALL STYLABLE ELEMENTS
        const elements = svgElement.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon');

        elements.forEach(el => {
            // Remove ANY hardcoded styles or attributes that might override our theme
            el.removeAttribute('style');
            el.removeAttribute('fill');
            el.removeAttribute('stroke');
            el.removeAttribute('stroke-width');

            if (style === 'outline') {
                el.setAttribute('fill', 'none');
                el.setAttribute('stroke', finalColor);
                el.setAttribute('stroke-width', strokeWidth.toString());
            } else {
                // Determine if element should be stroke-only or fill-based
                // Most icons use fill for the main shape.
                // We default to fill, but allow stroke if specifically requested or if it's a line-based shape
                const isLineType = ['line', 'polyline'].includes(el.tagName.toLowerCase());

                if (isLineType) {
                    el.setAttribute('fill', 'none');
                    el.setAttribute('stroke', finalColor);
                    el.setAttribute('stroke-width', strokeWidth.toString());
                } else {
                    el.setAttribute('fill', finalColor);
                    // Add subtle stroke even to filled shapes for 'tech' style crispness
                    if (style === 'tech' || style === 'corporate') {
                        el.setAttribute('stroke', finalColor);
                        el.setAttribute('stroke-width', (strokeWidth * 0.5).toString());
                    }
                }
            }
        });

        if (gradient) {
            const defs = doc.createElementNS('http://www.w3.org/2000/svg', 'defs');
            const linearGrad = doc.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
            linearGrad.setAttribute('id', gradientId);
            linearGrad.setAttribute('x1', '0%');
            linearGrad.setAttribute('y1', '0%');
            linearGrad.setAttribute('x2', '100%');
            linearGrad.setAttribute('y2', '100%');

            const stop1 = doc.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop1.setAttribute('offset', '0%');
            stop1.setAttribute('stop-color', gradient.start);

            const stop2 = doc.createElementNS('http://www.w3.org/2000/svg', 'stop');
            stop2.setAttribute('offset', '100%');
            stop2.setAttribute('stop-color', gradient.end);

            linearGrad.appendChild(stop1);
            linearGrad.appendChild(stop2);
            defs.appendChild(linearGrad);
            svgElement.insertBefore(defs, svgElement.firstChild);
        }

        const serialized = new XMLSerializer().serializeToString(doc);
        setSvgContent(serialized);
      })
      .catch(err => {
        if (isMounted) setError(err.message);
      });

    return () => { isMounted = false; };
  }, [query, provider, color, strokeWidth, style, gradient, gradientId]);

  useEffect(() => {
      if (svgContent && containerRef.current && onLoad) {
          const paths = containerRef.current.querySelectorAll('path, rect, circle, ellipse, line, polyline, polygon');
          const lengths: number[] = [];
          paths.forEach((p: any) => {
              try {
                  // For non-paths, we can approximate or use special methods if available
                  if (p.getTotalLength) {
                      lengths.push(p.getTotalLength());
                  } else {
                      // Bounding box approximation for simple shapes
                      const bbox = p.getBBox();
                      lengths.push((bbox.width + bbox.height) * 2);
                  }
              } catch(e) {
                  lengths.push(5000);
              }
          });
          onLoad(svgContent, lengths);
      }
  }, [svgContent, onLoad]);

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
      ref={containerRef}
      className="w-full h-full flex items-center justify-center"
      dangerouslySetInnerHTML={{ __html: svgContent }}
    />
  );
};
