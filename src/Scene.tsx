import React, { useEffect, useState } from 'react';
import { AbsoluteFill, useVideoConfig, OffthreadVideo } from 'remotion';
import { OverlayManager } from './OverlayManager';
import { ProceduralBackground } from './engines/ProceduralBackground';
import { CameraEngine } from './engines/CameraEngine';
import { resolveAsset } from './lib/resolveAsset';
import { AudioEngine } from './engines/AudioEngine';
import { AnimationProvider } from '../svg/components/AnimationContext';
import { InfographicComposer } from '../svg/components/InfographicComposer';
import { loadAnalysis } from './services/AnalysisLoader';
import { VisualEyeDebug } from './engines/VisualEyeDebug';

export const Scene: React.FC<{ sceneData: any }> = ({ sceneData }) => {
  const { durationInFrames } = useVideoConfig();
  const [analysis, setAnalysis] = useState<any>(null);

  useEffect(() => {
    const videoPath = sceneData.background?.video_path || sceneData.video_path;
    if (videoPath) {
      loadAnalysis(videoPath).then(setAnalysis);
    }
  }, [sceneData.background?.video_path, sceneData.video_path, sceneData.background?.background_type, sceneData.background_type]);

  if (!sceneData) {
    return <AbsoluteFill className="bg-black" />;
  }

  const renderBackground = () => {
    const bgType = sceneData.background?.background_type || sceneData.background_type || 'video';
    const videoPath = sceneData.background?.video_path || sceneData.video_path;
    const audioEnabled = sceneData.background?.audio_enabled ?? sceneData.audio_enabled;
    const procConfig = sceneData.background?.procedural_config || sceneData.procedural_config || {};

    switch (bgType) {
      case 'video':
        if (!videoPath) return null;
        const bgUrl = resolveAsset(videoPath);
        return (
          <OffthreadVideo
            src={bgUrl}
            className="w-full h-full object-cover"
            muted={audioEnabled !== true}
          />
        );
      case 'procedural':
        return <ProceduralBackground config={procConfig} />;
      case 'none':
        return null;
      default:
        if (videoPath) {
          const fallbackUrl = resolveAsset(videoPath);
          return (
            <OffthreadVideo
              src={fallbackUrl}
              className="w-full h-full object-cover"
              muted={audioEnabled !== true}
            />
          );
        }
        return null;
    }
  };

  return (
    <AbsoluteFill className="bg-black">
      <AnimationProvider>
        <AudioEngine sceneId={sceneData.scene_id} />
        <CameraEngine
          config={sceneData.camera}
          overlays={sceneData.overlays || []}
          backgroundLayer={renderBackground()}
        >
          <InfographicComposer sceneData={sceneData} />
          <OverlayManager overlays={sceneData.overlays || []} analysis={analysis} />
          {sceneData.visual_eye_debug && <VisualEyeDebug analysis={analysis} />}
        </CameraEngine>
      </AnimationProvider>
    </AbsoluteFill>
  );
};
