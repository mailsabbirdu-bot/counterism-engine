import React from 'react';
import { AbsoluteFill, OffthreadVideo, staticFile } from 'remotion';
import { OverlayManager } from './OverlayManager';
import { ProceduralBackground } from './engines/ProceduralBackground';

export const Scene: React.FC<{ sceneData: any }> = ({ sceneData }) => {
  const renderBackground = () => {
    switch (sceneData.background_type) {
      case 'video':
        return (
          <OffthreadVideo
            src={staticFile(sceneData.video_path)}
            className="w-full h-full object-cover"
          />
        );
      case 'procedural':
        return <ProceduralBackground config={sceneData.procedural_config || {}} />;
      case 'none':
      default:
        return <AbsoluteFill className="bg-zinc-950" />;
    }
  };

  return (
    <AbsoluteFill className="bg-black">
      {/* Background Layer */}
      {renderBackground()}

      {/* Overlay Layers */}
      <OverlayManager overlays={sceneData.overlays} />
    </AbsoluteFill>
  );
};
