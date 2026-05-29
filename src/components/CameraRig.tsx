import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { CameraConfig, CameraState } from '../lib/cameraTypes';
import { buildPresetCamera } from '../lib/cameraPresets';
import { getInterpolatedCamera } from '../lib/cameraInterpolation';
import { CameraDebugOverlay } from './CameraDebugOverlay';

interface CameraRigProps {
  config?: CameraConfig;
  debug?: boolean;
  durationInFrames: number;
  children: (cameraState: CameraState) => React.ReactNode;
}

export const CameraRig: React.FC<CameraRigProps> = ({ config, debug, durationInFrames, children }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const keyframes = useMemo(() => {
    if (!config?.enabled) return [];

    let baseKeyframes = config.keyframes || [];

    if (config.preset) {
      const presetKeyframes = buildPresetCamera(config.preset, durationInFrames, width, height);
      if (baseKeyframes.length === 0) {
        baseKeyframes = presetKeyframes;
      }
    }

    return baseKeyframes;
  }, [config, durationInFrames, width, height]);

  const cameraState: CameraState = useMemo(() => {
    if (!config?.enabled || keyframes.length === 0) {
      return { x: 0, y: 0, zoom: 1, rotation: 0 };
    }
    return getInterpolatedCamera(frame, keyframes);
  }, [frame, keyframes, config?.enabled]);

  // VITAL: Force a single-line string with explicit units
  const transform = `translate3d(${cameraState.x}px, ${cameraState.y}px, 0) scale(${cameraState.zoom}) rotate(${cameraState.rotation}deg)`;

  if (frame % 30 === 0) {
    console.log(`[CameraRig] Frame: ${frame} Transform: ${transform}`);
  }

  return (
    <>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          transform,
          transformOrigin: 'center center',
          willChange: 'transform',
          backfaceVisibility: 'hidden'
        }}
      >
        {children(cameraState)}
      </div>
      <CameraDebugOverlay cameraState={cameraState} enabled={debug} />
    </>
  );
};
