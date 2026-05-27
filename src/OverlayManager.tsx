import React from 'react';
import { TextEngine } from './engines/TextEngine';
import { UISystem } from './engines/UISystem';
import { ShapesEngine } from './engines/ShapesEngine';
import { ChartsEngine } from './engines/ChartsEngine';
import { GraphsEngine } from './engines/GraphsEngine';
import { MediaEngine } from './engines/MediaEngine';

export const OverlayManager: React.FC<{ overlays: any[] }> = ({ overlays }) => {
  return (
    <>
      {overlays.map((overlay) => {
        switch (overlay.type) {
          case 'text':
            return <TextEngine key={overlay.id} overlay={overlay} />;
          case 'ui_panel':
            return <UISystem key={overlay.id} overlay={overlay} />;
          case 'shape':
            return <ShapesEngine key={overlay.id} overlay={overlay} />;
          case 'chart':
            return <ChartsEngine key={overlay.id} overlay={overlay} />;
          case 'graph':
            return <GraphsEngine key={overlay.id} overlay={overlay} />;
          case 'video':
          case 'image':
            return <MediaEngine key={overlay.id} overlay={overlay} />;
          default:
            return null;
        }
      })}
    </>
  );
};
