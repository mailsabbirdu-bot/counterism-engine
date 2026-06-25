import React, { useMemo } from 'react';
import { AbsoluteFill, spring, useVideoConfig } from 'remotion';
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
import { NarrativeTemplate } from './NarrativeTemplates';
import { useAnimation } from './AnimationContext';
import { SvgGroup, StorytellingElement, LayerType, SvgProvider } from '../types';
import { ENGINE_CONSTANTS } from '../lib/constants';
import { calculateRadialPosition, calculateLinearPosition, calculateGridPosition } from '../lib/layoutUtils';

interface InfographicComposerProps {
  sceneData: any;
}

const LAYER_ORDER: LayerType[] = ['background', 'decorative', 'secondary', 'primary', 'foreground', 'overlay'];

/**
 * Infographic Composer
 * Renders complex multi-layered visual storytelling compositions from JSON.
 */
export const InfographicComposer: React.FC<InfographicComposerProps> = React.memo(({ sceneData }) => {
  const { frame, fps } = useAnimation();

  if (!sceneData) return null;

  const elements: StorytellingElement[] = sceneData.elements || [];
  const groups: SvgGroup[] = sceneData.groups || [];
  const lines = sceneData.infographic_lines || [];
  const nodes = sceneData.infographic_nodes || [];
  const background = sceneData.background;
  const sceneIconTheme: SvgProvider | undefined = sceneData.sceneIconTheme;

  // 1. Resolve element positions (including group-based layouts)
  const resolvedElements = useMemo(() => {
      const result = elements.map(el => ({ ...el }));

      groups.forEach(group => {
          const children = result.filter((el: any) => el.groupId === group.id);
          const groupX = group.x ?? ENGINE_CONSTANTS.CENTER_X;
          const groupY = group.y ?? ENGINE_CONSTANTS.CENTER_Y;
          const spacing = group.spacing ?? ENGINE_CONSTANTS.DEFAULT_SPACING;

          children.forEach((child: any, index) => {
              // HARDENING (P2-5): Use centralized layout utilities
              let pos = { x: child.x, y: child.y };

              if (group.layout === 'horizontal' || group.layout === 'vertical') {
                  pos = calculateLinearPosition(index, children.length, groupX, groupY, spacing, group.layout);
              } else if (group.layout === 'orbit' || group.layout === 'radial') {
                  pos = calculateRadialPosition(index, children.length, groupX, groupY, spacing);
              } else if (group.layout === 'grid') {
                  pos = calculateGridPosition(index, children.length, groupX, groupY, spacing);
              }

              child.x = pos.x;
              child.y = pos.y;
          });
      });

      return result;
  }, [elements, groups]);

  // 2. Map ID to resolved position for lines and relative components
  const positionMap = useMemo(() => {
      const map: Record<string, { x: number, y: number }> = {};
      resolvedElements.forEach((el: any) => {
          if (el.id) map[el.id] = { x: el.x, y: el.y };

          // Special handling for sub-components (HubNetwork ids)
          if (el.type === 'hub_network') {
              map[`${el.id}_center`] = { x: el.x, y: el.y };
          }
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
      {/* Narrative Templates */}
      <NarrativeTemplate
        story={sceneData.story}
        startFrame={sceneData.startFrame || 0}
        sceneIconTheme={sceneIconTheme}
        positionMap={positionMap}
      />

      {/* Background System */}
      {background && (
          <InfographicBackground type={background} />
      )}

      {/* Orbit Rings */}
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

      {/* Group background rings */}
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

      {/* Components Rendering */}
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

      {/* Simple Nodes */}
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
});
