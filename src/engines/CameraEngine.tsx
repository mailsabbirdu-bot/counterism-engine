import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { getPresetKeyframes, CameraPreset, CameraKeyframe } from '../lib/cameraPresets';

export interface CameraConfig {
  enabled: boolean;
  perspective?: number;
  preset?: CameraPreset;
  keyframes?: CameraKeyframe[];
  shake?: {
    enabled: boolean;
    intensity?: number;
    speed?: number;
    rotationIntensity?: number;
  };
  motionBlur?: {
    enabled: boolean;
    intensity?: number;
  };
}

// Catmull-Rom Spline Interpolation for smooth spatial paths
const catmullRom = (p0: number, p1: number, p2: number, p3: number, t: number) => {
  const v0 = (p2 - p0) * 0.5;
  const v1 = (p3 - p1) * 0.5;
  const t2 = t * t;
  const t3 = t * t2;
  return (2 * p1 - 2 * p2 + v0 + v1) * t3 + (-3 * p1 + 3 * p2 - 2 * v0 - v1) * t2 + v0 * t + p1;
};

const parseEasing = (easing: string | any) => {
  if (!easing) return Easing.linear;
  if (typeof easing === 'string') {
    switch (easing) {
      case 'ease': return Easing.ease;
      case 'in': return Easing.in(Easing.ease);
      case 'out': return Easing.out(Easing.ease);
      case 'in-out': return Easing.inOut(Easing.ease);
      case 'bezier': return Easing.bezier(0.25, 0.1, 0.25, 1);
      case 'step': return (t: number) => (t < 0.5 ? 0 : 1);
      default: return Easing.linear;
    }
  }
  if (easing.type === 'bezier' && easing.bezier) {
    return Easing.bezier(easing.bezier[0], easing.bezier[1], easing.bezier[2], easing.bezier[3]);
  }
  return Easing.linear;
};

const getCameraState = (frame: number, keyframes: CameraKeyframe[], width: number, height: number) => {
  if (!keyframes || keyframes.length === 0) {
    return { x: 0, y: 0, z: 0, zoom: 1, rotationX: 0, rotationY: 0, rotationZ: 0 };
  }

  const sorted = [...keyframes].sort((a, b) => a.frame - b.frame);

  // Find segment
  let i = 0;
  while (i < sorted.length - 1 && sorted[i + 1].frame <= frame) {
    i++;
  }

  const k1 = sorted[i];
  const k2 = sorted[Math.min(i + 1, sorted.length - 1)];

  if (k1 === k2) {
      const state = { ...k1 };
      if ((k1 as any).lookAt) {
          state.x = (k1 as any).lookAt.x;
          state.y = (k1 as any).lookAt.y;
          state.z = (k1 as any).lookAt.z || state.z;
      }
      return state;
  }

  const tRaw = (frame - k1.frame) / (k2.frame - k1.frame);
  const easingFn = parseEasing(k1.easing);
  const t = easingFn(tRaw);

  // For x, y, z we use Catmull-Rom if possible
  const getVal = (prop: keyof CameraKeyframe) => {
    const getP = (k: CameraKeyframe) => {
        if (prop === 'x' || prop === 'y' || prop === 'z') {
            if ((k as any).lookAt) {
                return (k as any).lookAt[prop] ?? (k[prop] || 0);
            }
        }
        return (k[prop] as number) || 0;
    };

    const p1 = getP(k1);
    const p2 = getP(k2);
    const p0 = getP(sorted[Math.max(0, i - 1)]);
    const p3 = getP(sorted[Math.min(sorted.length - 1, i + 2)]);
    return catmullRom(p0, p1, p2, p3, t);
  };

  const interp = (prop: keyof CameraKeyframe) => interpolate(t, [0, 1], [(k1[prop] as number) || 0, (k2[prop] as number) || 0]);

  const state: any = {
    x: getVal('x'),
    y: getVal('y'),
    z: getVal('z'),
    zoom: interpolate(t, [0, 1], [k1.zoom || 1, k2.zoom || 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
    rotationX: interp('rotationX'),
    rotationY: interp('rotationY'),
    rotationZ: interp('rotationZ') || (k1 as any).rotation || 0,
  };

  return state;
};

export const CameraEngine: React.FC<{
  config: CameraConfig;
  children: React.ReactNode;
  backgroundLayer?: React.ReactNode;
}> = ({ config, children, backgroundLayer }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const mergedKeyframes = useMemo(() => {
    if (!config) return [{ frame: 0, x: 0, y: 0, z: 0, zoom: 1, rotationX: 0, rotationY: 0, rotationZ: 0 }];

    let keys = [...(config.keyframes || [])];
    if (config.preset) {
      const presetKeys = getPresetKeyframes(config.preset as CameraPreset, durationInFrames);
      const manualFrames = new Set(keys.map(k => k.frame));
      presetKeys.forEach(pk => {
        if (!manualFrames.has(pk.frame)) {
          keys.push(pk);
        }
      });
      keys.sort((a, b) => a.frame - b.frame);
    }

    if (keys.length === 0) {
      keys.push({ frame: 0, x: 0, y: 0, z: 0, zoom: 1, rotationX: 0, rotationY: 0, rotationZ: 0 });
    }

    return keys;
  }, [config, durationInFrames]);

  const cameraState = useMemo(() => getCameraState(frame, mergedKeyframes, width, height), [frame, mergedKeyframes, width, height]);
  const prevCameraState = useMemo(() => getCameraState(frame - 0.5, mergedKeyframes, width, height), [frame, mergedKeyframes, width, height]);

  if (!config?.enabled) {
    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>
        {backgroundLayer}
        {children}
      </div>
    );
  }

  // Camera Shake logic
  let shakeX = 0;
  let shakeY = 0;
  let shakeRotZ = 0;
  if (config.shake?.enabled) {
    const intensity = config.shake.intensity || 2;
    const speed = config.shake.speed || 1.0;
    const rotIntensity = config.shake.rotationIntensity || 0.2;
    shakeX = (Math.sin(frame * 0.15 * speed) + Math.sin(frame * 0.4 * speed) * 0.5) * intensity;
    shakeY = (Math.sin(frame * 0.2 * speed + 1) + Math.sin(frame * 0.35 * speed + 2) * 0.5) * intensity;
    shakeRotZ = Math.sin(frame * 0.1 * speed) * rotIntensity;
  }

  const cx = width / 2;
  const cy = height / 2;

  const tx = (cameraState.x || 0) + shakeX;
  const ty = (cameraState.y || 0) + shakeY;
  const zoom = cameraState.zoom || 1;
  const rotZ = (cameraState.rotationZ || 0) + shakeRotZ;

  // Motion Blur
  const dx = (cameraState.x || 0) - (prevCameraState.x || 0);
  const dy = (cameraState.y || 0) - (prevCameraState.y || 0);
  const blurAmount = config.motionBlur?.enabled
    ? Math.min(Math.sqrt(dx * dx + dy * dy) * (config.motionBlur.intensity || 0.5) * 0.3, 4)
    : 0;

  // Background Parallax & Coverage
  const angleRad = (Math.abs(rotZ) % 90) * (Math.PI / 180);
  const rotScale = Math.cos(angleRad) + Math.sin(angleRad);
  const zoomScale = 1 / Math.min(zoom, 1);
  const coverScale = Math.max(rotScale * zoomScale, 1) * 1.1;

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        perspective: `${config.perspective || 1000}px`,
        backgroundColor: 'black'
      }}
    >
      {backgroundLayer && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            zIndex: 0,
            transform: `scale(${coverScale}) translate3d(${-(cameraState.x || 0) * 0.05}px, ${-(cameraState.y || 0) * 0.05}px, -100px)`,
            filter: blurAmount > 1 ? `blur(${Math.round(blurAmount * 0.5 * 10) / 10}px)` : 'none',
            willChange: 'transform',
          }}
        >
          {backgroundLayer}
        </div>
      )}

      <div
        style={{
          position: 'absolute',
          inset: 0,
          zIndex: 1,
          transformStyle: 'preserve-3d',
          transform: `
            translate3d(${cx}px, ${cy}px, 0)
            scale3d(${zoom}, ${zoom}, 1)
            rotateX(${cameraState.rotationX || 0}deg)
            rotateY(${cameraState.rotationY || 0}deg)
            rotateZ(${rotZ}deg)
            translate3d(${-tx}px, ${-ty}px, ${-(cameraState.z || 0)}px)
          `,
          filter: blurAmount > 1 ? `blur(${Math.round(blurAmount * 10) / 10}px)` : 'none',
          willChange: 'transform',
          backfaceVisibility: 'hidden',
        }}
      >
        {children}
      </div>
    </div>
  );
};
