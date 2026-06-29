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
    if (sceneData.background_type === 'video' && sceneData.video_path) {
      loadAnalysis(sceneData.video_path).then(setAnalysis);
    }
  }, [sceneData.video_path, sceneData.background_type]);

  if (!sceneData) {
    return <AbsoluteFill className="bg-black" />;
  }

  const renderBackground = () => {
    switch (sceneData.config?.background?.type || sceneData.background_type) {
      case 'video':
        if (!sceneData.video_path) return null;
        const bgUrl = resolveAsset(sceneData.video_path);
        return (
          <OffthreadVideo
            src={bgUrl}
            className="w-full h-full object-cover"
            muted={sceneData.audio_enabled !== true}
          />
        );
      case 'procedural':
        return <ProceduralBackground config={sceneData.config?.background?.config || sceneData.procedural_config || {}} />;
      case 'none':
        return null;
      default:
        if (sceneData.video_path) {
          const fallbackUrl = resolveAsset(sceneData.video_path);
          return (
            <OffthreadVideo
              src={fallbackUrl}
              className="w-full h-full object-cover"
              muted={sceneData.audio_enabled !== true}
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
