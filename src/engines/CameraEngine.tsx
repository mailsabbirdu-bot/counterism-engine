import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { getPresetKeyframes } from '../lib/cameraPresets';
import { CameraConfig, CameraKeyframe, CameraPreset } from '../types/camera';

// Professional Ease-In-Out Quintic for cinematic feel
const cinematicEase = Easing.bezier(0.65, 0, 0.35, 1);

// Improved noise for handheld shake
const seedNoise = (f: number, seed: number) => {
  return Math.sin(f * 0.1 * seed) * 0.5 + Math.sin(f * 0.23 * seed + 1) * 0.3 + Math.sin(f * 0.47 * seed + 2) * 0.2;
};

const parseEasing = (easing: string | any) => {
  if (!easing) return cinematicEase;
  if (typeof easing === 'string') {
    switch (easing) {
      case 'ease': return Easing.ease;
      case 'in': return Easing.in(Easing.ease);
      case 'out': return Easing.out(Easing.ease);
      case 'in-out': return cinematicEase;
      case 'linear': return Easing.linear;
      case 'bezier': return Easing.bezier(0.25, 0.1, 0.25, 1);
      default: return cinematicEase;
    }
  }
  return cinematicEase;
};

const resolveTarget = (lookAt: string | { x: number, y: number } | undefined, overlays: any[], width: number, height: number) => {
  const cx = width / 2;
  const cy = height / 2;

  if (!lookAt) return { x: cx, y: cy };

  if (typeof lookAt === 'string') {
    const target = (overlays || []).find(o => o.id === lookAt);
    if (target && target.position) {
      return { x: target.position.x, y: target.position.y };
    }
    return { x: cx, y: cy };
  }

  return { x: lookAt.x, y: lookAt.y };
};

const getCameraState = (frame: number, keyframes: CameraKeyframe[], overlays: any[], width: number, height: number) => {
  const cx = width / 2;
  const cy = height / 2;

  if (!keyframes || keyframes.length === 0) {
    return { x: 0, y: 0, z: 0, zoom: 1, rotationX: 0, rotationY: 0, rotationZ: 0, tx: cx, ty: cy };
  }

  const sorted = [...keyframes].sort((a, b) => a.frame - b.frame);

  let i = 0;
  while (i < sorted.length - 1 && sorted[i + 1].frame <= frame) {
    i++;
  }

  const k1 = sorted[i];
  const k2 = sorted[Math.min(i + 1, sorted.length - 1)];

  const getTarget = (k: CameraKeyframe) => {
    if (k.lookAt) return resolveTarget(k.lookAt, overlays, width, height);
    return {
      x: k.x !== undefined ? cx + k.x : (k.lookAt ? cx : cx), // fallback to center if no x and no lookAt
      y: k.y !== undefined ? cy + k.y : (k.lookAt ? cy : cy)
    };
  };

  const t1 = getTarget(k1);
  const t2 = getTarget(k2);

  if (k1 === k2 || frame <= k1.frame) {
      return {
        ...k1,
        tx: t1.x,
        ty: t1.y,
        z: k1.z || 0,
        zoom: k1.zoom || 1,
        rotationX: k1.rotationX || 0,
        rotationY: k1.rotationY || 0,
        rotationZ: k1.rotationZ || 0,
      };
  }

  const tRaw = (frame - k1.frame) / (k2.frame - k1.frame);
  const easingFn = parseEasing(k1.easing);
  const t = easingFn(tRaw);

  const interp = (v1: number, v2: number) => interpolate(t, [0, 1], [v1, v2]);

  return {
    tx: interp(t1.x, t2.x),
    ty: interp(t1.y, t2.y),
    z: interp(k1.z || 0, k2.z || 0),
    zoom: interp(k1.zoom || 1, k2.zoom || 1),
    rotationX: interp(k1.rotationX || 0, k2.rotationX || 0),
    rotationY: interp(k1.rotationY || 0, k2.rotationY || 0),
    rotationZ: interp(k1.rotationZ || 0, k2.rotationZ || 0),
  };
};

export const CameraEngine: React.FC<{
  config: CameraConfig;
  overlays: any[];
  children: React.ReactNode;
  backgroundLayer?: React.ReactNode;
}> = ({ config, overlays, children, backgroundLayer }) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames } = useVideoConfig();

  const mergedKeyframes = useMemo(() => {
    const keys: CameraKeyframe[] = [{ frame: 0, zoom: 1, x: 0, y: 0, rotationZ: 0 }];

    if (config?.keyframes) {
      keys.push(...config.keyframes);
    }

    if (config?.preset) {
      keys.push(...getPresetKeyframes(config.preset as CameraPreset, durationInFrames));
    }

    if (config?.shots && config.shots.length > 0) {
        config.shots.forEach(shot => {
            const inDur = shot.inDuration ?? 30;
            const zoom = shot.zoom || 1.5;

            // Movement start (previous state is preserved until shot.startFrame)
            keys.push({
                frame: shot.startFrame,
                // We implicitly inherit the previous target/zoom here by not defining them,
                // but we need to ensure the easing for the NEXT segment starts here.
                easing: 'in-out'
            });

            // Reach target
            keys.push({
                frame: shot.startFrame + inDur,
                lookAt: shot.targetId,
                zoom: zoom,
                easing: 'linear' // Next segment is the hold
            });

            // End hold
            keys.push({
                frame: shot.startFrame + shot.duration,
                lookAt: shot.targetId,
                zoom: zoom,
                easing: 'in-out' // Next segment is movement away
            });
        });
    }

    const uniqueKeysMap = new Map();
    keys.forEach(k => {
      const existing = uniqueKeysMap.get(k.frame);
      uniqueKeysMap.set(k.frame, { ...existing, ...k });
    });

    return Array.from(uniqueKeysMap.values()).sort((a, b) => a.frame - b.frame);
  }, [config, durationInFrames]);

  const cameraState = useMemo(() => getCameraState(frame, mergedKeyframes, overlays, width, height), [frame, mergedKeyframes, overlays, width, height]);
  const nextFrameState = useMemo(() => getCameraState(frame + 0.5, mergedKeyframes, overlays, width, height), [frame, mergedKeyframes, overlays, width, height]);

  if (!config?.enabled) {
    return <div style={{ width, height, position: 'relative' }}>{backgroundLayer}{children}</div>;
  }

  const cx = width / 2;
  const cy = height / 2;

  // Cinematic Handheld Shake
  let shakeX = 0, shakeY = 0, shakeRotZ = 0;
  if (config.shake?.enabled) {
    const intensity = config.shake.intensity || 1.5;
    const speed = config.shake.speed || 1.0;
    const f = frame * speed;
    shakeX = seedNoise(f, 1) * 10 * intensity;
    shakeY = seedNoise(f, 2) * 10 * intensity;
    shakeRotZ = seedNoise(f, 3) * 0.5 * intensity;
  }

  const tx = cameraState.tx + shakeX;
  const ty = cameraState.ty + shakeY;
  const zoom = cameraState.zoom;
  const rotZ = cameraState.rotationZ + shakeRotZ;

  // Motion Blur (Sub-frame delta)
  const dx = (nextFrameState.tx - cameraState.tx) * zoom;
  const dy = (nextFrameState.ty - cameraState.ty) * zoom;
  const speed = Math.sqrt(dx * dx + dy * dy);
  const blur = config.motionBlur?.enabled ? Math.min(speed * (config.motionBlur.intensity || 0.5), 10) : 0;

  return (
    <div
      style={{
        width, height,
        position: 'relative',
        overflow: 'hidden',
        perspective: `${config.perspective || 1000}px`,
        backgroundColor: '#000'
      }}
    >
      {backgroundLayer && (
        <div style={{
          position: 'absolute',
          inset: -100, // Overscan for shake/zoom
          zIndex: 0,
          transform: `translate3d(${(cx - tx) * 0.02}px, ${(cy - ty) * 0.02}px, -50px) scale(1.1)`,
          willChange: 'transform'
        }}>
          {backgroundLayer}
        </div>
      )}

      <div
        style={{
          position: 'absolute',
          width, height,
          zIndex: 1,
          transformStyle: 'preserve-3d',
          transformOrigin: '0 0',
          transform: `
            translate3d(${cx}px, ${cy}px, 0)
            scale3d(${zoom}, ${zoom}, 1)
            rotateZ(${rotZ}deg)
            rotateX(${cameraState.rotationX || 0}deg)
            rotateY(${cameraState.rotationY || 0}deg)
            translate3d(${-tx}px, ${-ty}px, ${-(cameraState.z || 0)}px)
          `,
          filter: blur > 1 ? `blur(${blur}px)` : 'none',
          willChange: 'transform',
          backfaceVisibility: 'hidden',
        }}
      >
        {children}
      </div>
    </div>
  );
};
