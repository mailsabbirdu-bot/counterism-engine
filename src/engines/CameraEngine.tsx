import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate, Easing, useVideoConfig, AbsoluteFill } from 'remotion';

export interface CameraEasing {
  type: 'ease' | 'linear' | 'bezier' | 'step';
  bezier?: [number, number, number, number];
}

export interface CameraKeyframe {
  frame: number;
  x?: number;
  y?: number;
  z?: number;
  zoom?: number;
  rotationX?: number;
  rotationY?: number;
  rotationZ?: number;
  easing?: 'ease' | 'linear' | 'bezier' | 'step' | CameraEasing;
  lookAt?: {
    x: number;
    y: number;
    z: number;
  };
}

export interface CameraConfig {
  enabled: boolean;
  perspective?: number;
  pathSmoothing?: boolean;
  motionBlur?: {
    enabled: boolean;
    intensity?: number;
  };
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

  // Calculate the maximum possible pan and zoom to determine a safe "Cover" scale for background
  const coverScale = useMemo(() => {
    if (!config?.keyframes || config.keyframes.length === 0) return 1.1;

    const perspective = config.perspective || 1000;

    // We calculate the required scale for EVERY keyframe and take the maximum
    // This is much safer than combining global maximums.
    const requiredScales = config.keyframes.map(k => {
      const zoom = k.zoom ?? 1;
      const z = k.z ?? 0;

      // Effective scale due to zoom and Z-depth
      const zScale = perspective / (perspective + z);
      const effectiveScale = zoom * zScale;

      // 1. Base scale to counter zooming OUT
      const zoomFactor = 1 / Math.max(0.1, effectiveScale);

      // 2. Panning factor (requires overscan)
      const panFactorX = 1 + (Math.abs(k.x ?? 0) * 2) / width;
      const panFactorY = 1 + (Math.abs(k.y ?? 0) * 2) / height;
      const panFactor = Math.max(panFactorX, panFactorY);

      // 3. Rotation factor (sin(45) ~ 1.41)
      const rot = Math.max(Math.abs(k.rotationX ?? 0), Math.abs(k.rotationY ?? 0), Math.abs(k.rotationZ ?? 0));
      const rotationFactor = 1 + (rot / 45) * 0.42;

      return zoomFactor * panFactor * rotationFactor;
    });

    const maxScale = Math.max(...requiredScales);

    // Optimization: Cap at 5x to avoid massive texture memory usage, plus 10% safety margin
    return Math.min(5, maxScale * 1.1);
  }, [config?.keyframes, config?.perspective, width, height]);

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

    const getEasingFunc = (easingInput?: string | CameraEasing) => {
      if (typeof easingInput === 'object') {
        if (easingInput.type === 'bezier' && easingInput.bezier) {
          return Easing.bezier(easingInput.bezier[0], easingInput.bezier[1], easingInput.bezier[2], easingInput.bezier[3]);
        }
        if (easingInput.type === 'step') {
          return (t: number) => (t < 0.5 ? 0 : 1);
        }
        return getEasingFunc(easingInput.type);
      }

      switch (easingInput) {
        case 'bezier':
          return Easing.bezier(0.33, 1, 0.68, 1); // easeOutCubic
        case 'ease':
          return Easing.inOut(Easing.ease);
        case 'step':
          return (t: number) => (t < 0.5 ? 0 : 1);
        case 'linear':
        default:
          return Easing.linear;
      }
    };

    const easing = getEasingFunc(startK.easing);

    const getCatmullRom = (t: number, p0: number, p1: number, p2: number, p3: number) => {
      const v0 = (p2 - p0) * 0.5;
      const v1 = (p3 - p1) * 0.5;
      const t2 = t * t;
      const t3 = t * t2;
      return (2 * p1 - 2 * p2 + v0 + v1) * t3 + (-3 * p1 + 3 * p2 - 2 * v0 - v1) * t2 + v0 * t + p1;
    };

    const interpolateProp = (prop: keyof CameraKeyframe, defaultValue: number) => {
      if (startK.frame === endK.frame) return (startK[prop] as number) ?? defaultValue;

      const t = (frame - startK.frame) / (endK.frame - startK.frame);
      const easedT = easing(t);

      if (config?.pathSmoothing && ['x', 'y', 'z'].includes(prop as string)) {
        const p0K = sortedKeyframes[Math.max(0, startIdx - 1)];
        const p1K = startK;
        const p2K = endK;
        const p3K = sortedKeyframes[Math.min(sortedKeyframes.length - 1, startIdx + 2)];

        const p0 = (p0K[prop] as number) ?? defaultValue;
        const p1 = (p1K[prop] as number) ?? defaultValue;
        const p2 = (p2K[prop] as number) ?? defaultValue;
        const p3 = (p3K[prop] as number) ?? defaultValue;

        return getCatmullRom(easedT, p0, p1, p2, p3);
      }

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

    const x = interpolateProp('x', 0);
    const y = interpolateProp('y', 0);
    const z = interpolateProp('z', 0);

    let lookAtRotation = { x: 0, y: 0 };
    if (startK.lookAt && endK.lookAt) {
      // Proper lookAt interpolation
      const targetX = interpolate(frame, [startK.frame, endK.frame], [startK.lookAt.x, endK.lookAt.x], { easing, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const targetY = interpolate(frame, [startK.frame, endK.frame], [startK.lookAt.y, endK.lookAt.y], { easing, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
      const targetZ = interpolate(frame, [startK.frame, endK.frame], [startK.lookAt.z, endK.lookAt.z], { easing, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

      // Calculate vector from camera to target
      const dx = targetX - x;
      const dy = targetY - y;
      const dz = targetZ - z;

      // Calculate rotations
      // rotationY is pan (around Y axis), rotationX is tilt (around X axis)
      // We negate them because we are transforming the SCENE, not the CAMERA
      // Using -dz because the camera default view is along -Z axis
      const yaw = -Math.atan2(dx, -dz) * (180 / Math.PI);
      const pitch = Math.atan2(dy, Math.sqrt(dx * dx + dz * dz)) * (180 / Math.PI);

      lookAtRotation = { x: pitch, y: yaw };
    }

    return {
      x,
      y,
      z,
      zoom: interpolateProp('zoom', 1),
      rotationX: startK.lookAt ? lookAtRotation.x : interpolateProp('rotationX', 0),
      rotationY: startK.lookAt ? lookAtRotation.y : interpolateProp('rotationY', 0),
      rotationZ: interpolateProp('rotationZ', 0),
    };
  }, [frame, sortedKeyframes, config?.pathSmoothing]);

  // Calculate velocity for motion blur (lightweight approach)
  const motionBlurStyle = useMemo(() => {
    if (!config?.motionBlur?.enabled || frame === 0) return {};

    const intensity = config.motionBlur.intensity ?? 0.5;

    let startIdx = 0;
    for (let i = 0; i < sortedKeyframes.length - 1; i++) {
      if (frame >= sortedKeyframes[i].frame && frame <= sortedKeyframes[i + 1].frame) {
        startIdx = i;
        break;
      }
    }

    const s = sortedKeyframes[startIdx];
    const e = sortedKeyframes[startIdx + 1];

    if (!s || !e || s.frame === e.frame) return {};

    const duration = e.frame - s.frame;
    const dx = ((e.x ?? 0) - (s.x ?? 0)) / duration;
    const dy = ((e.y ?? 0) - (s.y ?? 0)) / duration;
    const dz = ((e.z ?? 0) - (s.z ?? 0)) / duration;
    const dZoom = ((e.zoom ?? 1) - (s.zoom ?? 1)) / duration;

    const totalVelocity = Math.sqrt(dx * dx + dy * dy + dz * dz) + Math.abs(dZoom * 1000);
    const blurAmount = Math.min(8, totalVelocity * 0.01 * intensity);

    if (blurAmount < 0.2) return {};

    return {
      filter: `blur(${blurAmount.toFixed(1)}px)`,
    };
  }, [frame, sortedKeyframes, config?.motionBlur]);

  // Handle subtle camera shake if enabled
  const shakeOffset = useMemo(() => {
    if (!config?.shake?.enabled) return { x: 0, y: 0, rz: 0 };

    const intensity = config.shake.intensity ?? 2;
    const speed = config.shake.speed ?? 1;
    const rIntensity = config.shake.rotationIntensity ?? 0.2;

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

  // Overlays use the full 3D cinematic stack (including perspective, lookAt rotations, and Z translation)
  const overlayStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    transformStyle: 'preserve-3d',
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    ...motionBlurStyle,
    transform: `translate3d(${cx}px, ${cy}px, 0) scale3d(${cameraState.zoom}, ${cameraState.zoom}, 1) rotateX(${cameraState.rotationX}deg) rotateY(${cameraState.rotationY}deg) rotateZ(${cameraState.rotationZ + (shakeOffset.rz || 0)}deg) translate3d(${-cameraState.x + shakeOffset.x}px, ${-cameraState.y + shakeOffset.y}px, ${-cameraState.z}px) translate3d(${-cx}px, ${-cy}px, 0)`,
  };

  // Background uses only 2D functionalities: Panning (X, Y) and Scaling (Zoom)
  // VITAL: To maintain sync during pans, the translation offset MUST be divided by the scale
  // if we scale BEFORE translating, or adjusted if we translate then scale.
  // Using a clean matrix-like stack:
  const backgroundStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    willChange: 'transform',
    transform: `
      translate3d(${cx}px, ${cy}px, 0)
      scale3d(${cameraState.zoom * coverScale}, ${cameraState.zoom * coverScale}, 1)
      translate3d(${( -cameraState.x + shakeOffset.x ) / coverScale}px, ${( -cameraState.y + shakeOffset.y ) / coverScale}px, 0)
      translate3d(${-cx}px, ${-cy}px, 0)
    `,
  };

  const childrenArray = React.Children.toArray(children);
  const background = childrenArray[0];
  const overlays = childrenArray.slice(1);

  return (
    <div style={containerStyle}>
      {/* Background layer: 2D ONLY */}
      <AbsoluteFill style={backgroundStyle}>
        {background}
      </AbsoluteFill>

      {/* Overlay layer: FULL 3D */}
      <div style={overlayStyle}>
        {overlays}
      </div>
    </div>
  );
};
