import React, { useMemo } from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { ConnectionLine, GlowNode, OrbitRing } from './InfographicElements';
import { InfographicBackground } from './InfographicBackgrounds';
import { AnimatedSvg } from './AnimatedSvg';
import { SvgGroup, SvgElement } from '../types';

interface InfographicComposerProps {
  sceneData: any;
}

export const InfographicComposer: React.FC<InfographicComposerProps> = ({ sceneData }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!sceneData) return null;

  const elements = sceneData.elements || [];
  const groups: SvgGroup[] = sceneData.groups || [];
  const lines = sceneData.infographic_lines || [];
  const nodes = sceneData.infographic_nodes || [];
  const background = sceneData.background;

  // 1. Resolve element positions (including group-based layouts)
  const resolvedElements = useMemo(() => {
      // Create a deep copy to avoid mutating original data
      const result = elements.map((el: any) => ({ ...el }));

      groups.forEach(group => {
          const children = result.filter(el => el.groupId === group.id);
          const groupX = group.x ?? 960;
          const groupY = group.y ?? 540;
          const spacing = group.spacing ?? 200;

          children.forEach((child, index) => {
              if (group.layout === 'horizontal') {
                  const offset = (index - (children.length - 1) / 2) * spacing;
                  child.x = groupX + offset;
                  child.y = groupY;
              } else if (group.layout === 'vertical') {
                  const offset = (index - (children.length - 1) / 2) * spacing;
                  child.x = groupX;
                  child.y = groupY + offset;
              } else if (group.layout === 'orbit') {
                  const angle = (index / children.length) * Math.PI * 2;
                  child.x = groupX + Math.cos(angle) * spacing;
                  child.y = groupY + Math.sin(angle) * spacing;
              } else if (group.layout === 'grid') {
                  const cols = Math.ceil(Math.sqrt(children.length));
                  const row = Math.floor(index / cols);
                  const col = index % cols;
                  child.x = groupX + (col - (cols - 1) / 2) * spacing;
                  child.y = groupY + (row - (Math.ceil(children.length / cols) - 1) / 2) * spacing;
              }
          });
      });

      return result;
  }, [elements, groups]);

  // 2. Map ID to resolved position for lines
  const positionMap = useMemo(() => {
      const map: Record<string, { x: number, y: number }> = {};
      resolvedElements.forEach(el => {
          if (el.id) map[el.id] = { x: el.x, y: el.y };
      });
      return map;
  }, [resolvedElements]);

  return (
    <AbsoluteFill className="pointer-events-none">
      {/* Background System */}
      <InfographicBackground type={background} />

      {/* Orbit Rings (Behind elements) */}
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

      {/* Connection Lines (Resolved by ID) */}
      {lines.map((line: any, i: number) => {
          const start = line.from ? positionMap[line.from] : line.start_pos;
          const end = line.to ? positionMap[line.to] : line.end_pos;

          if (!start || !end) return null;

          return (
            <ConnectionLine
              key={`line-${i}`}
              start={start}
              end={end}
              startFrame={line.start || 0}
              duration={line.duration || 60}
              color={line.color}
              type={line.type}
            />
          );
      })}

      {/* Glow Nodes & Primitives */}
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

      {/* Group Animations & Elements */}
      {resolvedElements.filter((el: any) => el.type === 'svg').map((el: any) => {
          const group = groups.find(g => g.id === el.groupId);

          // Group-level animation logic (staggered entrance offset)
          let groupOffset = { x: 0, y: 0 };
          if (group && group.animation) {
              const spr = spring({
                  frame: frame - (el.startFrame || 0),
                  fps,
                  config: { damping: 15 }
              });

              if (group.animation === 'slideUp') groupOffset.y = (1 - spr) * 50;
              if (group.animation === 'scale') {
                  // Handled via groupOffset doesn't make sense for scale,
                  // but we could support group-level properties in the future
              }
          }

          return (
            <AnimatedSvg
              key={el.id}
              {...el}
              groupOffset={groupOffset}
            />
          );
      })}
    </AbsoluteFill>
  );
};
