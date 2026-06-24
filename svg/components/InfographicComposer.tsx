import React, { useMemo } from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { ConnectionLine, GlowNode, OrbitRing } from './InfographicElements';
import { InfographicBackground } from './InfographicBackgrounds';
import { AnimatedSvg } from './AnimatedSvg';
import { HubNetwork } from './HubNetwork';
import { FlowDiagram } from './FlowDiagram';
import { ProcessDiagram } from './ProcessDiagram';
import { LabelSystem } from './LabelSystem';
import { CalloutSystem } from './CalloutSystem';
import { KpiCard } from './KpiCard';
import { Timeline } from './Timeline';
import { CompositionEngine } from './CompositionEngine';
import { SvgGroup, StorytellingElement, LayerType } from '../types';

interface InfographicComposerProps {
  sceneData: any;
}

const LAYER_ORDER: LayerType[] = ['background', 'decorative', 'secondary', 'primary', 'foreground', 'overlay'];

export const InfographicComposer: React.FC<InfographicComposerProps> = ({ sceneData }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!sceneData) return null;

  const elements: StorytellingElement[] = sceneData.elements || [];
  const groups: SvgGroup[] = sceneData.groups || [];
  const lines = sceneData.infographic_lines || [];
  const nodes = sceneData.infographic_nodes || [];
  const background = sceneData.background;
  const sceneIconTheme = sceneData.sceneIconTheme;

  // 1. Resolve element positions (including group-based layouts)
  const resolvedElements = useMemo(() => {
      const result = elements.map(el => ({ ...el }));

      groups.forEach(group => {
          const children = result.filter((el: any) => el.groupId === group.id);
          const groupX = group.x ?? 960;
          const groupY = group.y ?? 540;
          const spacing = group.spacing ?? 200;

          children.forEach((child: any, index) => {
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
              } else if (group.layout === 'radial') {
                  const angle = (index / children.length) * Math.PI * 2;
                  child.x = groupX + Math.cos(angle) * spacing;
                  child.y = groupY + Math.sin(angle) * spacing;
              }
          });
      });

      return result;
  }, [elements, groups]);

  // 2. Map ID to resolved position for lines and relative components
  const positionMap = useMemo(() => {
      const map: Record<string, { x: number, y: number }> = {};
      resolvedElements.forEach((el: any) => {
          if (el.id) map[el.id] = { x: el.x, y: el.y };
      });
      return map;
  }, [resolvedElements]);

  // 3. Sorting by Layer
  const sortedElements = useMemo(() => {
      return [...resolvedElements].sort((a: any, b: any) => {
          const idxA = LAYER_ORDER.indexOf(a.layer || 'primary');
          const idxB = LAYER_ORDER.indexOf(b.layer || 'primary');
          return idxA - idxB;
      });
  }, [resolvedElements]);

  return (
    <AbsoluteFill className="pointer-events-none">
      {/* 1. Background System */}
      <InfographicBackground type={background} />

      {/* 2. Orbit Rings */}
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

      {/* 3. Group background rings */}
      {groups.filter(g => g.backgroundRing).map((group, i) => (
          <OrbitRing
            key={`group-ring-${i}`}
            x={group.x ?? 960}
            y={group.y ?? 540}
            radius={group.spacing ?? 200}
            startFrame={0}
            color="rgba(255,255,255,0.05)"
          />
      ))}

      {/* 4. Connection Lines (Resolved by ID) */}
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

      {/* 5. Components Rendering */}
      {sortedElements.map((el: any) => {
          const commonProps = { key: el.id, sceneIconTheme };

          switch(el.type) {
              case 'svg':
                  const group = groups.find(g => g.id === el.groupId);
                  let groupOffset = { x: 0, y: 0 };
                  if (group && group.enterAnimation) {
                      const spr = spring({ frame: frame - (el.startFrame || 0), fps, config: { damping: 15 } });
                      if (group.enterAnimation === 'slideUp') groupOffset.y = (1 - spr) * 50;
                  }
                  return <AnimatedSvg {...el} {...commonProps} groupOffset={groupOffset} provider={el.provider || sceneIconTheme || 'lucide'} />;

              case 'hub_network': return <HubNetwork element={el} {...commonProps} />;
              case 'flow_diagram': return <FlowDiagram element={el} {...commonProps} />;
              case 'process': return <ProcessDiagram element={el} {...commonProps} />;
              case 'label': return <LabelSystem element={el} targetPos={positionMap[el.target]} key={el.id} />;
              case 'callout': return <CalloutSystem element={el} targetPos={positionMap[el.target]} key={el.id} />;
              case 'kpi': return <KpiCard element={el} {...commonProps} />;
              case 'timeline': return <Timeline element={el} key={el.id} />;
              case 'composition': return <CompositionEngine element={el} {...commonProps} />;
              default: return null;
          }
      })}

      {/* 6. Simple Nodes */}
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
    </AbsoluteFill>
  );
};
