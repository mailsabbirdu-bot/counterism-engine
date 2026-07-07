import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, Easing } from 'remotion';
import { safeNumber } from '../lib/safeNumber';
import { getPresetKeyframes } from '../lib/cameraPresets';
import { SHOT_PRESETS } from '../lib/shotPresets';
import { CameraConfig, CameraKeyframe, CameraPreset } from '../types/camera';
import { useFocus } from '../context/FocusContext';

// Professional Ease-In-Out Quintic for cinematic feel
const cinematicEase = Easing.bezier(0.65, 0, 0.35, 1);
const narrativeEase = Easing.bezier(0.33, 1, 0.68, 1); // Fast start, gentle finish

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
      case 'narrative': return narrativeEase;
      case 'linear': return Easing.linear;
      case 'bezier': return Easing.bezier(0.25, 0.1, 0.25, 1);
      case 'bounce': return Easing.bounce;
      case 'elastic': return Easing.elastic(1);
      default: return cinematicEase;
    }
  }
  // Handle complex easing object (e.g. from Shot Styles)
  if (typeof easing === 'object' && easing.type === 'bezier' && easing.bezier) {
    const [x1, y1, x2, y2] = easing.bezier;
    return Easing.bezier(x1, y1, x2, y2);
  }
  return cinematicEase;
};

const resolveTarget = (
  lookAt: string | { x: number, y: number } | undefined,
  overlays: any[],
  width: number,
  height: number,
  focalTargets: Record<string, any> = {}
) => {
  const cx = width / 2;
  const cy = height / 2;

  if (!lookAt) return { x: cx, y: cy, zoom: null, offset: { x: 0, y: 0 } };

  // v4.0: First priority: Check FocusProvider for semantic targets
  if (typeof lookAt === 'string' && focalTargets[lookAt]) {
      const target = focalTargets[lookAt];
      return { x: target.x, y: target.y, zoom: target.zoom || null, offset: { x: 0, y: 0 } };
  }

  // EXTREME: Support "ACTIVE_NODE" and "ACTIVE_FOCUS" tracking
  if (lookAt === 'ACTIVE_NODE' || lookAt === 'ACTIVE_FOCUS') {
      const trackerId = lookAt === 'ACTIVE_NODE' ? 'active-node-pos' : 'active-focus-pos';
      const tracker = typeof document !== 'undefined' ? document.getElementById(trackerId) : null;
      if (tracker) {
          const x = Number(tracker.getAttribute('data-x'));
          const y = Number(tracker.getAttribute('data-y'));
          if (!isNaN(x) && !isNaN(y)) return { x, y, zoom: null, offset: { x: 0, y: 0 } };
      }
  }

  if (typeof lookAt === 'string') {
    const target = (overlays || []).find(o => o.id === lookAt);
    if (target && target.position) {
      const focus = target.cameraFocus || {};
      return {
        x: target.position.x + (focus.offsetX || 0),
        y: target.position.y + (focus.offsetY || 0),
        zoom: focus.zoom || null,
        offset: { x: focus.offsetX || 0, y: focus.offsetY || 0 }
      };
    }
    return { x: cx, y: cy, zoom: null, offset: { x: 0, y: 0 } };
  }

  return { x: lookAt.x, y: lookAt.y, zoom: null, offset: { x: 0, y: 0 } };
};

const getCameraState = (frame: number, keyframes: CameraKeyframe[], overlays: any[], width: number, height: number, focalTargets: Record<string, any> = {}) => {
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
    if (k.lookAt) return resolveTarget(k.lookAt, overlays, width, height, focalTargets);
    return {
      x: k.x !== undefined ? cx + k.x : cx,
      y: k.y !== undefined ? cy + k.y : cy,
      zoom: null,
      offset: { x: 0, y: 0 }
    };
  };

  const t1 = getTarget(k1);
  const t2 = getTarget(k2);

  const z1 = k1.zoom ?? t1.zoom ?? 1;
  const z2 = k2.zoom ?? t2.zoom ?? 1;

  if (k1 === k2 || frame <= k1.frame) {
      return {
        ...k1,
        tx: t1.x,
        ty: t1.y,
        z: k1.z || 0,
        zoom: z1,
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
    zoom: interp(z1, z2),
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
  const { targets: focalTargets } = useFocus();

  const start = Number((config as any)?.start) || 0;
  const duration = Number((config as any)?.duration) || durationInFrames;

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
            const target = overlays.find(o => o.id === shot.targetId);
            const defaultZoom = target?.cameraFocus?.zoom || 1.5;
            const zoom = shot.zoom || defaultZoom;

            const preset = shot.style ? SHOT_PRESETS[shot.style] : null;

            // Start zoom calculation
            const startZoom = preset?.startZoom ? (preset.startZoom > 5 ? preset.startZoom : zoom * preset.startZoom) : zoom;
            const endZoom = preset?.endZoomOffset ? zoom * preset.endZoomOffset : zoom;
            const currentEasing = shot.easing || preset?.easing || 'in-out';

            keys.push({ frame: shot.startFrame, easing: 'in-out' });

            keys.push({
                frame: shot.startFrame + inDur,
                lookAt: shot.targetId,
                zoom: startZoom,
                rotationX: preset?.rotationX || 0,
                rotationY: preset?.rotationY || 0,
                rotationZ: preset?.rotationZ || 0,
                z: preset?.zOffset || 0,
                easing: 'linear'
            });

            keys.push({
                frame: shot.startFrame + shot.duration,
                lookAt: shot.targetId,
                zoom: endZoom,
                rotationX: 0,
                rotationY: 0,
                rotationZ: 0,
                z: 0,
                easing: currentEasing
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

  const cameraState = useMemo(() => getCameraState(isNaN(frame) ? 0 : frame, mergedKeyframes, overlays, width, height, focalTargets), [frame, mergedKeyframes, overlays, width, height, focalTargets]);
  const nextFrameState = useMemo(() => getCameraState(isNaN(frame) ? 0.5 : frame + 0.5, mergedKeyframes, overlays, width, height, focalTargets), [frame, mergedKeyframes, overlays, width, height, focalTargets]);

  if (!config?.enabled) {
    return <div style={{ width, height, position: 'relative' }}>{backgroundLayer}{children}</div>;
  }

  const cx = width / 2;
  const cy = height / 2;

  // Cinematic Handheld Shake - Disabled by default
  let shakeX = 0, shakeY = 0, shakeRotZ = 0;
  if (config?.shake?.enabled === true) {
    const intensity = config.shake.intensity || 1.5;
    const speed = config.shake.speed || 1.0;
    const f = frame * speed;
    shakeX = seedNoise(f, 1) * 10 * intensity;
    shakeY = seedNoise(f, 2) * 10 * intensity;
    shakeRotZ = seedNoise(f, 3) * 0.5 * intensity;
  }

  const tx = safeNumber(cameraState.tx + shakeX, cx);
  const ty = safeNumber(cameraState.ty + shakeY, cy);
  const zoom = safeNumber(cameraState.zoom, 1);
  const rotZ = safeNumber(cameraState.rotationZ + shakeRotZ, 0);

  if (frame % 30 === 0) {
    console.log(`[CameraEngine] Frame ${frame}: tx=${tx.toFixed(1)}, ty=${ty.toFixed(1)}, zoom=${zoom.toFixed(2)} rotZ=${rotZ}`);
  }

  // Motion Blur (Sub-frame delta)
  const dx = (nextFrameState.tx - cameraState.tx) * zoom;
  const dy = (nextFrameState.ty - cameraState.ty) * zoom;
  const speed = Math.sqrt(dx * dx + dy * dy);
  const blur = config.motionBlur?.enabled ? Math.min(speed * (config.motionBlur.intensity || 0.5), 10) : 0;

  // Global Atmosphere System (NASA/Bloomberg/Cyberpunk styles)
  const stylePreset = (config as any)?.style_preset || 'none';
  const showVignette = stylePreset !== 'none';
  const showHUD = ['nasa', 'bloomberg', 'cyberpunk'].includes(stylePreset);

  return (
    <div
      style={{
        width, height,
        position: 'relative',
        overflow: 'hidden',
        perspective: `${config.perspective || 2000}px`,
        backgroundColor: '#000'
      }}
    >
      {/* STATIC BACKGROUND SYSTEM: Unaffected by Camera Movements */}
      {backgroundLayer && (
          <div style={{
              position: 'absolute',
              top: 0, left: 0, width, height,
              zIndex: 0,
              pointerEvents: 'none'
          }}>
              {backgroundLayer}
          </div>
      )}

      {/* Global Dark Overlay for Readability - Static */}
      <div style={{
          position: 'absolute',
          top: 0, left: 0, width, height,
          backgroundColor: 'rgba(0,0,0,0.4)',
          zIndex: 5,
          pointerEvents: 'none'
      }} />

      {/* Cinematic Atmosphere Layer (Vignette, Grain, Scanlines) */}
      {showVignette && (
        <div style={{
          position: 'absolute', top: 0, left: 0, width, height, zIndex: 6,
          background: 'radial-gradient(circle, transparent 40%, rgba(0,0,0,0.8) 120%)',
          pointerEvents: 'none'
        }} />
      )}

      {showHUD && (
        <div style={{
            position: 'absolute', top: 0, left: 0, width, height, zIndex: 7,
            opacity: 0.1, pointerEvents: 'none',
            background: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
            backgroundSize: '100% 2px, 3px 100%'
        }} />
      )}

      {/* Cinematic Camera Pivot System - Transforms Overlays only */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width, height,
          zIndex: 10,
          transformStyle: 'preserve-3d',
          // 1. Move the pivot point (target) to the screen center
          // 2. Scale and Rotate around that pivot
          transformOrigin: `${tx}px ${ty}px`,
          transform: `
            translate3d(${cx - tx}px, ${cy - ty}px, 0)
            scale3d(${zoom}, ${zoom}, 1)
            rotateZ(${rotZ}deg)
            rotateX(${cameraState.rotationX || 0}deg)
            rotateY(${cameraState.rotationY || 0}deg)
            translate3d(0, 0, ${-(cameraState.z || 0)}px)
          `,
          filter: blur > 1 ? `blur(${blur}px)` : 'none',
          willChange: 'transform',
          backfaceVisibility: 'hidden',
        }}
      >
        <div style={{ position: 'absolute', top: 0, left: 0, width, height, zIndex: 1000, transformStyle: 'preserve-3d' }}>
            {children}
        </div>
      </div>
    </div>
  );
};
