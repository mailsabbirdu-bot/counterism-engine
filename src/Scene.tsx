import React from 'react';
import { AbsoluteFill, OffthreadVideo, staticFile } from 'remotion';
import { OverlayManager } from './OverlayManager';

export const Scene: React.FC<{ sceneData: any }> = ({ sceneData }) => {
  return (
    <AbsoluteFill className="bg-black">
      {/* STEP 1 — Load Scene Video */}
      <OffthreadVideo
        src={staticFile(sceneData.video_path)}
        className="w-full h-full object-cover"
      />

      {/* STEP 2-4 — Composite Layers */}
      <OverlayManager overlays={sceneData.overlays} />
    </AbsoluteFill>
  );
};
