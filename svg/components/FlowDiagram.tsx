import React, { useMemo } from 'react';
import { FlowDiagramElement, SvgProvider } from '../types';
import { AnimatedSvg } from './AnimatedSvg';
import { ConnectionLine } from './InfographicElements';

export const FlowDiagram: React.FC<{ element: FlowDiagramElement, sceneIconTheme?: SvgProvider }> = ({ element, sceneIconTheme }) => {
  const { x, y, steps, layout = 'horizontal', arrowStyle = 'arrow', spacing = 250, startFrame = 0 } = element;

  const nodePositions = useMemo(() => {
    return steps.map((_, i) => {
      const offset = (i - (steps.length - 1) / 2) * spacing;
      return {
        x: layout === 'horizontal' ? x + offset : x,
        y: layout === 'vertical' ? y + offset : y
      };
    });
  }, [x, y, steps, layout, spacing]);

  return (
    <>
      {/* 1. Connection Arrows */}
      {nodePositions.map((pos, i) => {
        if (i === 0) return null;
        const prevPos = nodePositions[i - 1];
        return (
          <ConnectionLine
            key={`${element.id}_flow_${i}`}
            start={prevPos}
            end={pos}
            startFrame={startFrame + 15 + (i * 20)}
            duration={45}
            type={arrowStyle === 'glow' ? 'solid' : arrowStyle as any}
            color={arrowStyle === 'glow' ? '#00F5FF' : undefined}
          />
        );
      })}

      {/* 2. Nodes */}
      {steps.map((query, i) => (
        <AnimatedSvg
          key={`${element.id}_step_${i}`}
          id={`${element.id}_step_${i}`}
          query={query}
          provider={sceneIconTheme || 'lucide'}
          x={nodePositions[i].x}
          y={nodePositions[i].y}
          width={120}
          height={120}
          animation="pop"
          startFrame={startFrame + (i * 20)}
          durationInFrames={120}
          style="infographic"
          importance={i === 0 || i === steps.length - 1 ? 'primary' : 'secondary'}
        />
      ))}
    </>
  );
};
