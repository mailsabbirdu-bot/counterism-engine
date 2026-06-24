import React, { useMemo } from 'react';
import { CompositionElement, SvgElement, SvgProvider } from '../types';
import { COMPOSITIONS } from '../lib/compositionLibrary';
import { AnimatedSvg } from './AnimatedSvg';
import { ConnectionLine } from './InfographicElements';

export const CompositionEngine: React.FC<{
  element: CompositionElement,
  sceneIconTheme?: SvgProvider
}> = ({ element, sceneIconTheme }) => {
  const definition = COMPOSITIONS[element.compositionType];

  if (!definition) {
    return null;
  }

  const { x: baseX, y: baseY, scale = 1, enterAnimation = 'scale', startFrame = 0 } = element;

  // 1. Expand elements with base coordinates
  const expandedElements = useMemo(() => {
    return definition.elements.map((el: any) => ({
      ...el,
      id: `${element.id}_${el.id}`,
      x: baseX + (el.offsetX * scale),
      y: baseY + (el.offsetY * scale),
      width: el.width * scale,
      height: el.height * scale,
      animation: el.animation || enterAnimation,
      provider: el.provider || sceneIconTheme || 'lucide',
      startFrame: startFrame + (el.startFrame || 0),
      durationInFrames: el.durationInFrames || 150
    })) as SvgElement[];
  }, [definition, baseX, baseY, scale, enterAnimation, sceneIconTheme, element.id, startFrame]);

  // 2. Map for line resolution
  const posMap = useMemo(() => {
    const map: Record<string, { x: number, y: number }> = {};
    expandedElements.forEach(el => {
      map[el.id.replace(`${element.id}_`, '')] = { x: el.x, y: el.y };
    });
    return map;
  }, [expandedElements, element.id]);

  return (
    <>
      {/* Render Lines */}
      {definition.lines?.map((line, i) => {
        const start = posMap[line.from];
        const end = posMap[line.to];
        if (!start || !end) return null;

        return (
          <ConnectionLine
            key={`${element.id}_line_${i}`}
            start={start}
            end={end}
            startFrame={startFrame + 30} // Staggered start
            duration={60}
            type={line.type as any}
          />
        );
      })}

      {/* Render SVGs */}
      {expandedElements.map(el => (
        <AnimatedSvg
          key={el.id}
          {...el}
          provider={el.provider as SvgProvider}
          animation={el.animation || 'fade'}
          startFrame={el.startFrame || 0}
          durationInFrames={el.durationInFrames || 150}
        />
      ))}
    </>
  );
};
