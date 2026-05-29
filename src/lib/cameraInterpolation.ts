import { interpolate, Easing } from 'remotion';
import { CameraKeyframe, CameraState } from './cameraTypes';

export const normalizeCameraKeyframes = (keyframes: CameraKeyframe[]): CameraKeyframe[] => {
  if (!keyframes || keyframes.length === 0) {
    return [{ frame: 0, x: 0, y: 0, zoom: 1, rotation: 0 }];
  }

  // Sort and remove duplicates at the same frame
  const sorted = [...keyframes].sort((a, b) => a.frame - b.frame);
  const unique: CameraKeyframe[] = [];

  sorted.forEach(kf => {
    if (unique.length === 0 || unique[unique.length - 1].frame !== kf.frame) {
      unique.push(kf);
    }
  });

  return unique;
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

  const inputFrames = sortedKeyframes.map(k => k.frame);
  const options = {
    extrapolateLeft: 'clamp' as const,
    extrapolateRight: 'clamp' as const,
  };

  const x = interpolate(frame, inputFrames, sortedKeyframes.map(k => k.x), options);
  const y = interpolate(frame, inputFrames, sortedKeyframes.map(k => k.y), options);
  const zoom = interpolate(frame, inputFrames, sortedKeyframes.map(k => k.zoom), options);
  const rotation = interpolate(frame, inputFrames, sortedKeyframes.map(k => k.rotation || 0), options);

  return { x, y, zoom, rotation };
};
