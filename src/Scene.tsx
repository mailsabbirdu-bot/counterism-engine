import React from 'react';
import { AbsoluteFill, Video, staticFile } from 'remotion';
import { OverlayManager } from './OverlayManager';
import { ProceduralBackground } from './engines/ProceduralBackground';

export const Scene: React.FC<{ sceneData: any }> = ({ sceneData }) => {
  if (!sceneData) {
    return <AbsoluteFill className="bg-black" />;
  }

  const renderBackground = () => {
    switch (sceneData.background_type) {
      case 'video':
        if (!sceneData.video_path) return null;
        return (
          <>
            <Video
              src={staticFile(sceneData.video_path)}
              className="w-full h-full object-cover"
              playRemoteVideo={true}
              muted
              loop
            />
            {/* Dark overlay for readability */}
            <AbsoluteFill className="bg-black/40" />
          </>
        );
      case 'procedural':
        return <ProceduralBackground config={sceneData.procedural_config || {}} />;
      case 'none':
        return null;
      default:
        // Fallback to video if video_path is present, otherwise none
        if (sceneData.video_path) {
          return (
            <>
              <Video
                src={staticFile(sceneData.video_path)}
                className="w-full h-full object-cover"
                playRemoteVideo={true}
                muted
                loop
              />
              <AbsoluteFill className="bg-black/40" />
            </>
          );
        }
        return null;
    }
  };

  return (
    <AbsoluteFill className="bg-black">
      {/* STEP 1 — Load Background */}
      {renderBackground()}

      {/* STEP 2-4 — Composite Layers */}
      <OverlayManager overlays={sceneData.overlays || []} />
    </AbsoluteFill>
  );
};
