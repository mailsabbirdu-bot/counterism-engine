import React from 'react';
import { AbsoluteFill } from 'remotion';
import { ConnectionLine, GlowNode, OrbitRing } from './InfographicElements';
import { InfographicBackground } from './InfographicBackgrounds';
import { AnimatedSvg } from './AnimatedSvg';

interface InfographicComposerProps {
  sceneData: any;
}

export const InfographicComposer: React.FC<InfographicComposerProps> = ({ sceneData }) => {
  if (!sceneData) return null;

  const elements = sceneData.elements || [];
  const lines = sceneData.infographic_lines || [];
  const nodes = sceneData.infographic_nodes || [];
  const background = sceneData.background;

  return (
    <AbsoluteFill className="pointer-events-none">
      {/* 1. Background System */}
      <InfographicBackground type={background} />

      {/* 2. Orbit Rings (Behind elements) */}
      {nodes.filter((n: any) => n.radius).map((node: any, i: number) => (
        <OrbitRing
          key={`orbit-${i}`}
          x={node.x}
          y={node.y}
          radius={node.radius}
          startFrame={node.start || 0}
          color={node.color}
        />
      ))}

      {/* 3. Connection Lines */}
      {lines.map((line: any, i: number) => (
        <ConnectionLine
          key={`line-${i}`}
          start={line.start_pos}
          end={line.end_pos}
          startFrame={line.start || 0}
          duration={line.duration || 60}
          color={line.color}
          type={line.type}
        />
      ))}

      {/* 4. Glow Nodes & Primitives */}
      {nodes.filter((n: any) => !n.radius).map((node: any, i: number) => (
        <GlowNode
          key={`node-${i}`}
          x={node.x}
          y={node.y}
          startFrame={node.start || 0}
          color={node.color}
          type={node.type}
        />
      ))}

      {/* 5. Main SVG Elements */}
      {elements.filter((el: any) => el.type === 'svg').map((el: any) => (
        <AnimatedSvg
          key={el.id}
          {...el}
        />
      ))}
    </AbsoluteFill>
  );
};
