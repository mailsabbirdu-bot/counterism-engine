import React, { useMemo } from 'react';
import { AbsoluteFill, useCurrentFrame, useVideoConfig } from 'remotion';
import { CameraConfig, CameraState } from '../lib/cameraTypes';
import { buildPresetCamera } from '../lib/cameraPresets';
import { getInterpolatedCamera } from '../lib/cameraInterpolation';

interface CameraRigProps {
  config?: CameraConfig;
  durationInFrames: number;
  children: (cameraState: CameraState) => React.ReactNode;
}

export const CameraRig: React.FC<CameraRigProps> = ({ config, durationInFrames, children }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const keyframes = useMemo(() => {
    if (!config?.enabled) return [];

    let baseKeyframes = config.keyframes || [];

    if (config.preset) {
      const presetKeyframes = buildPresetCamera(config.preset, durationInFrames, width, height);
      // Merge strategy: if user provided keyframes, they override/augment preset?
      // For simplicity, if preset exists, use it as base.
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

  const transform = `
    translate3d(${cameraState.x}px, ${cameraState.y}px, 0)
    scale(${cameraState.zoom})
    rotate(${cameraState.rotation}deg)
  `;

  return (
    <AbsoluteFill
      style={{
        transform,
        // Optional: transformOrigin can be center or customizable
        transformOrigin: 'center center'
      }}
    >
      {children(cameraState)}
    </AbsoluteFill>
  );
};
