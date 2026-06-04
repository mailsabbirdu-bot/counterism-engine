import React from 'react';
import { ParallaxLayer } from './components/ParallaxLayer';
import { TextEngine } from './engines/TextEngine';
import { UISystem } from './engines/UISystem';
import { ShapesEngine } from './engines/ShapesEngine';
import { ChartsEngine } from './engines/ChartsEngine';
import { GraphsEngine } from './engines/GraphsEngine';
import { MediaEngine } from './engines/MediaEngine';
import { DataIndicatorEngine } from './engines/DataIndicatorEngine';
import { MapEngine } from './engines/MapEngine';

interface OverlayManagerProps {
  overlays: any[];
}

export const OverlayManager: React.FC<OverlayManagerProps> = ({ overlays }) => {
  return (
    <>
      {overlays.map((overlay) => {
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
            case 'data_indicator':
              return <DataIndicatorEngine overlay={overlay} />;
            case 'graph':
              return <GraphsEngine overlay={overlay} />;
            case 'video':
            case 'image':
              return <MediaEngine overlay={overlay} />;
            case 'map':
              return <MapEngine overlay={overlay} />;
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
