import { interpolate, Easing } from 'remotion';
import { CameraKeyframe, CameraState } from './cameraTypes';

export const normalizeCameraKeyframes = (keyframes: CameraKeyframe[]): CameraKeyframe[] => {
  if (keyframes.length === 0) {
    return [{ frame: 0, x: 0, y: 0, zoom: 1, rotation: 0 }];
  }

  return keyframes.sort((a, b) => a.frame - b.frame);
};

export const getInterpolatedCamera = (
  frame: number,
  keyframes: CameraKeyframe[]
): CameraState => {
  const sortedKeyframes = normalizeCameraKeyframes(keyframes);

  if (sortedKeyframes.length === 1) {
    return {
      x: sortedKeyframes[0].x,
      y: sortedKeyframes[0].y,
      zoom: sortedKeyframes[0].zoom,
      rotation: sortedKeyframes[0].rotation || 0,
    };
  }

  const frames = sortedKeyframes.map(k => k.frame);

  const x = interpolate(frame, frames, sortedKeyframes.map(k => k.x), {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const y = interpolate(frame, frames, sortedKeyframes.map(k => k.y), {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const zoom = interpolate(frame, frames, sortedKeyframes.map(k => k.zoom), {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const rotation = interpolate(frame, frames, sortedKeyframes.map(k => k.rotation || 0), {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  return { x, y, zoom, rotation };
};
