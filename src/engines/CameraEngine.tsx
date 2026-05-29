import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate, Easing, useVideoConfig } from 'remotion';

export interface CameraKeyframe {
  frame: number;
  x?: number;
  y?: number;
  z?: number;
  zoom?: number;
  rotationX?: number;
  rotationY?: number;
  rotationZ?: number;
  easing?: 'ease' | 'linear' | 'bezier';
}

export interface CameraConfig {
  enabled: boolean;
  perspective?: number;
  shake?: {
    enabled: boolean;
    intensity?: number;
    speed?: number;
    rotationIntensity?: number;
  };
  keyframes: CameraKeyframe[];
}

export const CameraEngine: React.FC<{
  config?: CameraConfig;
  children: React.ReactNode;
}> = ({ config, children }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const sortedKeyframes = useMemo(() => {
    if (!config?.keyframes) return [];
    return [...config.keyframes].sort((a, b) => a.frame - b.frame);
  }, [config?.keyframes]);

  const cameraState = useMemo(() => {
    if (sortedKeyframes.length === 0) {
      return { x: 0, y: 0, z: 0, zoom: 1, rotationX: 0, rotationY: 0, rotationZ: 0 };
    }

    if (sortedKeyframes.length === 1) {
      const k = sortedKeyframes[0];
      return {
        x: k.x ?? 0,
        y: k.y ?? 0,
        z: k.z ?? 0,
        zoom: k.zoom ?? 1,
        rotationX: k.rotationX ?? 0,
        rotationY: k.rotationY ?? 0,
        rotationZ: k.rotationZ ?? 0,
      };
    }

    // Find the current segment
    let startIdx = 0;
    for (let i = 0; i < sortedKeyframes.length - 1; i++) {
      if (frame >= sortedKeyframes[i].frame && frame <= sortedKeyframes[i + 1].frame) {
        startIdx = i;
        break;
      }
      if (frame > sortedKeyframes[i + 1].frame) {
        startIdx = i;
      }
    }

    const startK = sortedKeyframes[startIdx];
    const endK = sortedKeyframes[startIdx + 1] || startK;

    const getEasingFunc = (type?: string) => {
      switch (type) {
        case 'bezier':
          return Easing.bezier(0.33, 1, 0.68, 1); // easeOutCubic
        case 'ease':
          return Easing.inOut(Easing.ease);
        case 'linear':
        default:
          return Easing.linear;
      }
    };

    const easing = getEasingFunc(startK.easing);

    const interpolateProp = (prop: keyof CameraKeyframe, defaultValue: number) => {
      if (startK.frame === endK.frame) return (startK[prop] as number) ?? defaultValue;
      return interpolate(
        frame,
        [startK.frame, endK.frame],
        [(startK[prop] as number) ?? defaultValue, (endK[prop] as number) ?? defaultValue],
        {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
          easing,
        }
      );
    };

    return {
      x: interpolateProp('x', 0),
      y: interpolateProp('y', 0),
      z: interpolateProp('z', 0),
      zoom: interpolateProp('zoom', 1),
      rotationX: interpolateProp('rotationX', 0),
      rotationY: interpolateProp('rotationY', 0),
      rotationZ: interpolateProp('rotationZ', 0),
    };
  }, [frame, sortedKeyframes]);

  // Handle subtle camera shake if enabled
  const shakeOffset = useMemo(() => {
    if (!config?.shake?.enabled) return { x: 0, y: 0, rz: 0 };

    const intensity = config.shake.intensity ?? 2;
    const speed = config.shake.speed ?? 1;
    const rIntensity = config.shake.rotationIntensity ?? 0.2;

    // Smooth multi-frequency sine waves for handheld feel
    const x = Math.sin(frame * 0.15 * speed) * intensity + Math.sin(frame * 0.07 * speed) * (intensity * 0.4);
    const y = Math.cos(frame * 0.12 * speed) * intensity + Math.cos(frame * 0.05 * speed) * (intensity * 0.4);
    const rz = Math.sin(frame * 0.1 * speed) * rIntensity;

    return { x, y, rz };
  }, [frame, config?.shake]);

  if (!config || !config.enabled) {
    return <>{children}</>;
  }

  const perspective = config.perspective || 1000;
  const cx = width / 2;
  const cy = height / 2;

  const containerStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    perspective: `${perspective}px`,
    perspectiveOrigin: '50% 50%',
    overflow: 'hidden',
  };

  // Professional Camera Transform Matrix
  // We use a specific order:
  // 1. Move to center (cx, cy)
  // 2. Apply Zoom (Scale)
  // 3. Apply Camera Rotations (including subtle shake rotation)
  // 4. Move by Camera Offset (x, y, z) + Shake Offset
  // 5. Move back from center (-cx, -cy)
  // This ensures zoom and rotations happen relative to the camera's viewport center
  const sceneStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    transformStyle: 'preserve-3d',
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    transform: `
      translate3d(${cx}px, ${cy}px, 0)
      scale3d(${cameraState.zoom}, ${cameraState.zoom}, 1)
      rotateX(${cameraState.rotationX}deg)
      rotateY(${cameraState.rotationY}deg)
      rotateZ(${cameraState.rotationZ + (shakeOffset.rz || 0)}deg)
      translate3d(${-cameraState.x + shakeOffset.x}px, ${-cameraState.y + shakeOffset.y}px, ${-cameraState.z}px)
      translate3d(${-cx}px, ${-cy}px, 0)
    `,
  };

  return (
    <div style={containerStyle}>
      <div style={sceneStyle}>
        {children}
      </div>
    </div>
  );
};
