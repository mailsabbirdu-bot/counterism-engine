import React from 'react';
import { ParallaxLayer } from './components/ParallaxLayer';
import { TextEngine } from './engines/TextEngine';
import { UISystem } from './engines/UISystem';
import { ShapesEngine } from './engines/ShapesEngine';
import { ChartsEngine } from './engines/ChartsEngine';
import { GraphsEngine } from './engines/GraphsEngine';
import { MediaEngine } from './engines/MediaEngine';
import { DataIndicatorEngine } from './engines/DataIndicatorEngine';
import { ShadcnEngine } from './engines/ShadcnEngine';

interface OverlayManagerProps {
  overlays: any[];
}

export const OverlayManager: React.FC<OverlayManagerProps> = ({ overlays }) => {
  if (overlays.length > 0) {
      console.log(`[OverlayManager] Detected ${overlays.length} overlays: ${overlays.map(o => `(${o.id}: ${o.type})`).join(', ')}`);
  }
  return (
    <>
      {overlays.map((overlay) => {
        if (!overlay.id) {
            console.error(`[OverlayManager] CRITICAL: Overlay missing ID!`, overlay);
        }
        const renderOverlay = () => {
          switch (overlay.type) {
            case 'text':
              return <TextEngine overlay={overlay} />;
            case 'ui_panel':
              return <UISystem overlay={overlay} />;
            case 'shape':
              return <ShapesEngine overlay={overlay} />;
            case 'chart':
              return <ChartsEngine overlay={overlay} />;
            case 'indicator':
            case 'data_indicator':
              return <DataIndicatorEngine overlay={overlay} />;
            case 'graph':
              return <GraphsEngine overlay={overlay} />;
            case 'video':
            case 'image':
              return <MediaEngine overlay={overlay} />;
            case 'shadcn_chart':
            case 'shadcn_indicator':
              return <ShadcnEngine overlay={overlay} />;
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
