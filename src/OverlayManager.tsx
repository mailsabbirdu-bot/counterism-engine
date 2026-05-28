import React from 'react';
import { TextEngine } from './engines/TextEngine';
import { UISystem } from './engines/UISystem';
import { ShapesEngine } from './engines/ShapesEngine';
import { ChartsEngine } from './engines/ChartsEngine';
import { GraphsEngine } from './engines/GraphsEngine';
import { MediaEngine } from './engines/MediaEngine';
import { getParallaxStyle } from './lib/overlayTransformUtils';

interface OverlayManagerProps {
  overlays: any[];
  cameraX?: number;
  cameraY?: number;
}

export const OverlayManager: React.FC<OverlayManagerProps> = ({
  overlays,
  cameraX = 0,
  cameraY = 0
}) => {
  return (
    <div
      className="absolute inset-0"
      style={{
        // Create the virtual overlay world (e.g., 4000x4000 centered)
        width: '4000px',
        height: '4000px',
        left: '50%',
        top: '50%',
        marginLeft: '-2000px',
        marginTop: '-2000px',
      }}
    >
      {overlays.map((overlay) => {
        const parallaxStyle = getParallaxStyle(cameraX, cameraY, overlay.depth);

        const renderEngine = () => {
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
        };

        return (
          <div key={overlay.id} style={parallaxStyle}>
            {renderEngine()}
          </div>
        );
      })}
    </div>
  );
};
