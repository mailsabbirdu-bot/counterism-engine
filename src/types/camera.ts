import { EasingFunction } from 'remotion';

export interface CameraKeyframe {
	frame: number;
	x?: number;
	y?: number;
	z?: number;
	zoom?: number;
	rotationX?: number;
	rotationY?: number;
	rotationZ?: number;
	easing?: string | { type: 'bezier'; bezier: [number, number, number, number] };
	lookAt?: string | {
		x: number;
		y: number;
	};
}

export interface CinematicShot {
	targetId: string;
	startFrame: number;
	duration: number;
	zoom?: number;
	inDuration?: number;
	outDuration?: number;
	easing?: string | { type: 'bezier'; bezier: [number, number, number, number] };
}

export type CameraPreset = 'slow_push' | 'slow_pull' | 'ken_burns' | 'dramatic_reveal' | 'handheld_static' | 'whip_pan_right' | 'whip_pan_left';

export interface CameraShakeConfig {
	enabled: boolean;
	intensity?: number;
	speed?: number;
	rotationIntensity?: number;
}

export interface MotionBlurConfig {
	enabled: boolean;
	intensity?: number;
}

export interface CameraConfig {
	enabled: boolean;
	perspective?: number;
	preset?: CameraPreset;
	keyframes?: CameraKeyframe[];
	shots?: CinematicShot[];
	shake?: CameraShakeConfig;
	motionBlur?: MotionBlurConfig;
}
