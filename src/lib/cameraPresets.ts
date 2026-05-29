export interface CameraKeyframe {
  frame: number;
  x?: number;
  y?: number;
  z?: number;
  zoom?: number;
  rotationX?: number;
  rotationY?: number;
  rotationZ?: number;
  easing?: string;
}

export type CameraPreset = 'slow_push' | 'slow_pull' | 'ken_burns' | 'dramatic_reveal' | 'handheld_static' | 'whip_pan_right' | 'whip_pan_left';

export const getPresetKeyframes = (preset: CameraPreset, duration: number): CameraKeyframe[] => {
  switch (preset) {
    case 'slow_push':
      return [
        { frame: 0, zoom: 1, x: 0, y: 0 },
        { frame: duration, zoom: 1.2, x: 0, y: 0 }
      ];
    case 'slow_pull':
      return [
        { frame: 0, zoom: 1.2, x: 0, y: 0 },
        { frame: duration, zoom: 1, x: 0, y: 0 }
      ];
    case 'ken_burns':
      return [
        { frame: 0, zoom: 1.1, x: -50, y: -30 },
        { frame: duration, zoom: 1.3, x: 50, y: 30 }
      ];
    case 'dramatic_reveal':
      return [
        { frame: 0, zoom: 2, rotationX: 20, rotationY: -15, rotationZ: 5, y: 100 },
        { frame: duration, zoom: 1, rotationX: 0, rotationY: 0, rotationZ: 0, y: 0 }
      ];
    case 'handheld_static':
      // This is mostly handled by the shake logic, but we can add a slow drift
      return [
        { frame: 0, x: -10, y: -5, rotationZ: -0.5 },
        { frame: duration / 2, x: 10, y: 5, rotationZ: 0.5 },
        { frame: duration, x: -10, y: -5, rotationZ: -0.5 }
      ];
    case 'whip_pan_right':
      return [
        { frame: 0, x: -1000, rotationZ: -5, zoom: 1.1 },
        { frame: Math.min(15, duration), x: 0, rotationZ: 0, zoom: 1 }
      ];
    case 'whip_pan_left':
      return [
        { frame: 0, x: 1000, rotationZ: 5, zoom: 1.1 },
        { frame: Math.min(15, duration), x: 0, rotationZ: 0, zoom: 1 }
      ];
    default:
      return [];
  }
};
