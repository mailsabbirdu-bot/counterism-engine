import React, { useMemo } from 'react';
import { HubNetworkElement, SvgProvider } from '../types';
import { AnimatedSvg } from './AnimatedSvg';
import { ConnectionLine, OrbitRing, GlowNode } from './InfographicElements';

export const HubNetwork: React.FC<{ element: HubNetworkElement, sceneIconTheme?: SvgProvider }> = ({ element, sceneIconTheme }) => {
  const { x, y, radius, nodes, centerSvg, provider, connectionStyle = 'arrow', animation = 'pop', startFrame = 0 } = element;

  const nodePositions = useMemo(() => {
    return nodes.map((_, i) => {
      const angle = (i / nodes.length) * Math.PI * 2;
      return {
        x: x + Math.cos(angle) * radius,
        y: y + Math.sin(angle) * radius
      };
    });
  }, [x, y, radius, nodes]);

  return (
    <>
      {/* 1. Orbit Ring */}
      <OrbitRing x={x} y={y} radius={radius} startFrame={startFrame} color="rgba(255,255,255,0.05)" />

      {/* 2. Connection Lines */}
      {nodePositions.map((pos, i) => (
        <ConnectionLine
          key={`${element.id}_line_${i}`}
          start={{ x, y }}
          end={pos}
          startFrame={startFrame + 15 + (i * 5)}
          duration={60}
          type={connectionStyle as any}
        />
      ))}

      {/* 3. Outer Nodes */}
      {nodes.map((query, i) => (
        <AnimatedSvg
          key={`${element.id}_node_${i}`}
          id={`${element.id}_node_${i}`}
          query={query}
          provider={provider || sceneIconTheme || 'lucide'}
          x={nodePositions[i].x}
          y={nodePositions[i].y}
          width={100}
          height={100}
          animation={animation}
          startFrame={startFrame + 30 + (i * 10)}
          durationInFrames={120}
          importance="secondary"
        />
      ))}

      {/* 4. Center Node */}
      <AnimatedSvg
        id={`${element.id}_center`}
        query={centerSvg}
        provider={provider || sceneIconTheme || 'lucide'}
        x={x}
        y={y}
        width={180}
        height={180}
        animation="trace"
        style="tech"
        importance="primary"
        glow={true}
        container="glass_panel"
        startFrame={startFrame}
        durationInFrames={150}
      />

      {/* 5. Node Pulsars */}
      {nodePositions.map((pos, i) => (
        <GlowNode
            key={`${element.id}_glow_${i}`}
            x={pos.x}
            y={pos.y}
            startFrame={startFrame + 45 + (i * 10)}
            type="pulse"
            color="rgba(255,255,255,0.2)"
        />
      ))}
    </>
  );
};
