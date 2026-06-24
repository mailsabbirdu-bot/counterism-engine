import React, { useMemo } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring } from 'remotion';
import { ProcessElement } from '../types';
import { AnimatedSvg } from './AnimatedSvg';

export const ProcessDiagram: React.FC<{ element: ProcessElement, sceneIconTheme?: any }> = ({ element, sceneIconTheme }) => {
  const { x, y, steps } = element;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const spacing = 350;

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
          const start = 60 + (i * 30);
          const progress = spring({ frame: frame - start, fps, config: { damping: 20 } });

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
      {steps.map((query, i) => (
        <div key={`step_${i}`} style={{ position: 'absolute', left: nodePositions[i].x, top: nodePositions[i].y, transform: 'translate(-50%, -50%)' }}>
            {/* Number Bubble */}
            <div style={{
                position: 'absolute',
                top: -80,
                left: '50%',
                transform: 'translateX(-50%)',
                width: 40,
                height: 40,
                borderRadius: '50%',
                border: '2px solid #00F5FF',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: 'white',
                fontSize: 18,
                fontWeight: 'bold',
                backgroundColor: 'rgba(0, 245, 255, 0.1)',
                opacity: spring({ frame: frame - (15 + i * 30), fps })
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
                startFrame={30 + (i * 30)}
                durationInFrames={120}
                style="tech"
                importance="primary"
            />
        </div>
      ))}
    </>
  );
};
