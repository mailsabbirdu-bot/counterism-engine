import React from 'react';
import { useCurrentFrame } from 'remotion';
import { ParallaxLayer } from './components/ParallaxLayer';
import { TextEngine } from './engines/TextEngine';
import { UISystem } from './engines/UISystem';
import { ShapesEngine } from './engines/ShapesEngine';
import { ChartsEngine } from './engines/ChartsEngine';
import { GraphsEngine } from './engines/GraphsEngine';
import { MediaEngine } from './engines/MediaEngine';
import { DataIndicatorEngine } from './engines/DataIndicatorEngine';
import { ShadcnEngine } from './engines/ShadcnEngine';
import { AnimatedSvg } from '../svg/components/AnimatedSvg';
import { resolvePosition } from './services/SmartPositionResolver';

interface OverlayManagerProps {
  overlays: any[];
  analysis?: any;
}

export const OverlayManager: React.FC<OverlayManagerProps> = ({ overlays, analysis }) => {
  const frame = useCurrentFrame();

  if (overlays.length > 0 && frame === 0) {
      console.log(`[OverlayManager] Detected ${overlays.length} overlays: ${overlays.map(o => `(${o.id}: ${o.type})`).join(', ')}`);
  }
  return (
    <>
      {overlays.map((overlay) => {
        if (!overlay.id) {
            console.error(`[OverlayManager] CRITICAL: Overlay missing ID!`, overlay);
        }

        // Apply Smart Position Resolution
        const resolvedPosition = resolvePosition(overlay, analysis, frame);
        const positionalOverlay = {
            ...overlay,
            position: resolvedPosition
        };

        const renderOverlay = () => {
          switch (overlay.type) {
            case 'text':
              return <TextEngine overlay={positionalOverlay} />;
            case 'ui_panel':
              return <UISystem overlay={positionalOverlay} />;
            case 'shape':
              return <ShapesEngine overlay={positionalOverlay} />;
            case 'chart':
              return <ChartsEngine overlay={positionalOverlay} />;
            case 'indicator':
            case 'data_indicator':
              return <DataIndicatorEngine overlay={positionalOverlay} />;
            case 'graph':
              return <GraphsEngine overlay={positionalOverlay} />;
            case 'video':
            case 'image':
              return <MediaEngine overlay={positionalOverlay} />;
            case 'shadcn_chart':
            case 'shadcn_indicator':
              return <ShadcnEngine overlay={positionalOverlay} />;
            case 'svg':
              return (
                <AnimatedSvg
                  {...positionalOverlay}
                  query={overlay.query || overlay.content || 'house'}
                  provider={overlay.provider || 'iconify'}
                  animation={overlay.animation || 'draw'}
                  startFrame={overlay.start || 0}
                  durationInFrames={overlay.duration || 90}
                  width={overlay.width || 300}
                  height={overlay.height || 300}
                  x={positionalOverlay.position?.x || 960}
                  y={positionalOverlay.position?.y || 540}
                />
              );
            default:
              return null;
          }
        };

        const content = renderOverlay();
        if (!content) return null;

        return (
          <ParallaxLayer key={overlay.id} depth={overlay.depth} zIndex={overlay.zIndex}>
            {content}
          </ParallaxLayer>
        );
      })}
    </>
  );
};
