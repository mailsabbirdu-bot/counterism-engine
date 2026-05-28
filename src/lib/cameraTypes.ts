export interface CameraKeyframe {
  frame: number;
  x: number;
  y: number;
  zoom: number;
  rotation?: number;
}

export interface CameraConfig {
  enabled?: boolean;
  preset?: 'slowPushIn' | 'slowZoomOut' | 'panLeft' | 'panRight' | 'cinematicFloat';
  keyframes?: CameraKeyframe[];
}

export interface CameraState {
  x: number;
  y: number;
  zoom: number;
  rotation: number;
}
