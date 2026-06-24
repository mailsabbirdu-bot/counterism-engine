import React from 'react';
import { AbsoluteFill } from 'remotion';
import { ConnectionLine, GlowNode } from './InfographicElements';

interface InfographicComposerProps {
  sceneData: any;
}

export const InfographicComposer: React.FC<InfographicComposerProps> = ({ sceneData }) => {
  if (!sceneData) return null;

  const lines = sceneData.infographic_lines || [];
  const nodes = sceneData.infographic_nodes || [];

  return (
    <AbsoluteFill className="pointer-events-none">
      {/* 1. Background Connection Lines */}
      {lines.map((line: any, i: number) => (
        <ConnectionLine
          key={`line-${i}`}
          start={line.start_pos}
          end={line.end_pos}
          startFrame={line.start || 0}
          duration={line.duration || 60}
          color={line.color}
        />
      ))}

      {/* 2. Glow Nodes */}
      {nodes.map((node: any, i: number) => (
        <GlowNode
          key={`node-${i}`}
          x={node.x}
          y={node.y}
          startFrame={node.start || 0}
          color={node.color}
        />
      ))}
    </AbsoluteFill>
  );
};
