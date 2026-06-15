import React, { useRef } from 'react';
import { AbsoluteFill, OffthreadVideo, useVideoConfig } from 'remotion';
import { OverlayManager } from './OverlayManager';
import { ProceduralBackground } from './engines/ProceduralBackground';
import { CameraEngine } from './engines/CameraEngine';
import { resolveAsset } from './lib/resolveAsset';
import { AudioEngine } from './engines/AudioEngine';

export const Scene: React.FC<{ sceneData: any }> = ({ sceneData }) => {
  const { durationInFrames } = useVideoConfig();

  if (!sceneData) {
    return <AbsoluteFill className="bg-black" />;
  }

  const renderBackground = () => {
    switch (sceneData.config?.background?.type || sceneData.background_type) {
      case 'video':
        if (!sceneData.video_path) return null;
        const bgUrl = resolveAsset(sceneData.video_path);
        console.log(`[Scene Background] Path: ${sceneData.video_path} -> Resolved URL: ${bgUrl}`);
        return (
          <>
            <OffthreadVideo
              src={bgUrl}
              className="w-full h-full object-cover"
              muted={sceneData.audio_enabled !== true}
            />
            {/* Dark overlay for readability */}
            <AbsoluteFill className="bg-black/40" />
          </>
        );
      case 'procedural':
        return <ProceduralBackground config={sceneData.config?.background?.config || sceneData.procedural_config || {}} />;
      case 'none':
        return null;
      default:
        // Fallback to video if video_path is present, otherwise none
        if (sceneData.video_path) {
          const fallbackUrl = resolveAsset(sceneData.video_path);
          return (
            <>
              <OffthreadVideo
                src={fallbackUrl}
                className="w-full h-full object-cover"
                muted={sceneData.audio_enabled !== true}
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
      <AudioEngine sceneId={sceneData.scene_id} />
      <CameraEngine
        config={sceneData.camera}
        overlays={sceneData.overlays || []}
        backgroundLayer={renderBackground()}
      >
        <OverlayManager overlays={sceneData.overlays || []} />
      </CameraEngine>
    </AbsoluteFill>
  );
};
