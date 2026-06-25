import React, { useMemo } from 'react';
import { ProcessElement, SvgProvider } from '../types';
import { AnimatedSvg } from './AnimatedSvg';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';
import { ENGINE_CONSTANTS } from '../lib/constants';

export const ProcessDiagram: React.FC<{ element: ProcessElement, sceneIconTheme?: SvgProvider }> = ({ element, sceneIconTheme }) => {
  const { x, y, steps, startFrame = 0 } = element;
  const { frame, fps } = useAnimation();

  // HARDENING: Guard empty steps (BUG-3)
  if (!steps || steps.length === 0) return null;

  const spacing = ENGINE_CONSTANTS.DEFAULT_SPACING;

  const nodePositions = useMemo(() => {
    return steps.map((_, i) => ({
      x: x + (i - (steps.length - 1) / 2) * spacing,
      y: y
    }));
  }, [x, y, steps, spacing]);

  return (
    <>
      {/* 1. Progress Line Background */}
      <div style={{
          position: 'absolute',
          left: nodePositions[0].x,
          top: y,
          width: nodePositions[steps.length - 1].x - nodePositions[0].x,
          height: 4,
          backgroundColor: 'rgba(255,255,255,0.1)',
          transform: 'translateY(-50%)',
          borderRadius: 2
      }} />

      {/* 2. Animated Progress Line */}
      {steps.map((_, i) => {
          if (i === 0) return null;
          const prevX = nodePositions[i - 1].x;
          const nextX = nodePositions[i].x;
          const start = startFrame + 45 + (i * ENGINE_CONSTANTS.STAGGER_INTERVAL * 3);
          const progress = getEntranceProgress(frame, fps, start, false);

          return (
            <div key={`progress_${i}`} style={{
                position: 'absolute',
                left: prevX,
                top: y,
                width: (nextX - prevX) * progress,
                height: 4,
                backgroundColor: '#00F5FF',
                transform: 'translateY(-50%)',
                boxShadow: '0 0 10px #00F5FF',
                borderRadius: 2,
                zIndex: 1
            }} />
          );
      })}

      {/* 3. Steps */}
      {steps.map((query, i) => {
        const stepStart = startFrame + (i * ENGINE_CONSTANTS.STAGGER_INTERVAL * 3);
        const spr = getEntranceProgress(frame, fps, stepStart, true);

        return (
            <div key={`step_${i}`} style={{ position: 'absolute', left: nodePositions[i].x, top: nodePositions[i].y, transform: 'translate(-50%, -50%)' }}>
                {/* Number Bubble */}
                <div style={{
                    position: 'absolute',
                    top: -100,
                    left: '50%',
                    transform: 'translateX(-50%)',
                    width: 50,
                    height: 50,
                    borderRadius: '50%',
                    border: '3px solid #00D1FF',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: 'white',
                    fontSize: 24,
                    fontWeight: 'bold',
                    backgroundColor: 'rgba(0, 209, 255, 0.1)',
                    opacity: spr
                }}>
                    {i + 1}
                </div>

                <AnimatedSvg
                    id={`${element.id}_node_${i}`}
                    query={query}
                    provider={sceneIconTheme || 'lucide'}
                    x={0}
                    y={0}
                    width={140}
                    height={140}
                    animation="scale"
                    startFrame={stepStart + 15}
                    durationInFrames={120}
                    style="tech"
                    importance="primary"
                />
            </div>
        );
      })}
    </>
  );
};
