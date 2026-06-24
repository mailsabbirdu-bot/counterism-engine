import React from 'react';
import { AbsoluteFill } from 'remotion';
import { AnimatedSvg } from './AnimatedSvg';
import { SvgScene } from '../types';

interface JsonSceneRendererProps {
  sceneData: SvgScene;
}

export const JsonSceneRenderer: React.FC<JsonSceneRendererProps> = ({ sceneData }) => {
  if (!sceneData || !sceneData.elements) return null;

  return (
    <AbsoluteFill>
      {sceneData.elements.map((el) => {
        if (el.type !== 'svg') return null;

        return (
          <AnimatedSvg
            key={el.id}
            query={el.query}
            provider={el.provider}
            animation={el.animation}
            startFrame={el.startFrame}
            durationInFrames={el.durationInFrames}
            width={el.width}
            height={el.height}
            x={el.x}
            y={el.y}
            color={el.color}
            strokeWidth={el.strokeWidth}
          />
        );
      })}
    </AbsoluteFill>
  );
};
