import { CameraKeyframe, CameraConfig } from './cameraTypes';

export const buildPresetCamera = (
  preset: string,
  durationInFrames: number,
  width: number,
  height: number
): CameraKeyframe[] => {
  switch (preset) {
    case 'slowPushIn':
      return [
        { frame: 0, x: 0, y: 0, zoom: 1 },
        { frame: durationInFrames, x: 0, y: 0, zoom: 1.15 }
      ];
    case 'slowZoomOut':
      return [
        { frame: 0, x: 0, y: 0, zoom: 1.15 },
        { frame: durationInFrames, x: 0, y: 0, zoom: 1 }
      ];
    case 'panLeft':
      // Camera moves left -> World moves right
      return [
        { frame: 0, x: -200, y: 0, zoom: 1.1 },
        { frame: durationInFrames, x: 200, y: 0, zoom: 1.1 }
      ];
    case 'panRight':
      // Camera moves right -> World moves left
      return [
        { frame: 0, x: 200, y: 0, zoom: 1.1 },
        { frame: durationInFrames, x: -200, y: 0, zoom: 1.1 }
      ];
    case 'cinematicFloat':
      return [
        { frame: 0, x: -50, y: -30, zoom: 1.02, rotation: -0.5 },
        { frame: Math.floor(durationInFrames / 2), x: 50, y: 30, zoom: 1.05, rotation: 0.5 },
        { frame: durationInFrames, x: -50, y: -30, zoom: 1.02, rotation: -0.5 }
      ];
    default:
      return [];
  }
};
