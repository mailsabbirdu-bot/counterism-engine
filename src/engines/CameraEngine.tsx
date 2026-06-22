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
  height: number
) => {
  const cx = width / 2;
  const cy = height / 2;

  if (!lookAt) return { x: cx, y: cy, zoom: null, offset: { x: 0, y: 0 } };

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

  const start = Number((config as any).start) || 0;
  const duration = Number((config as any).duration) || durationInFrames;

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

            // Resolve target's cameraFocus zoom if available
            const target = overlays.find(o => o.id === shot.targetId);
            const defaultZoom = target?.cameraFocus?.zoom || 1.5;
            const zoom = shot.zoom || defaultZoom;

            // Movement start
            keys.push({
                frame: shot.startFrame,
                easing: 'in-out'
            });

            // Shot Style Logic
            let startZoom = 1.0;
            let endZoom = zoom;
            let currentEasing = shot.easing || 'in-out';

            let rotationX = 0, rotationY = 0, rotationZ = 0, zOffset = 0;

            if (shot.style === 'push_in' || shot.style === 'slow_push') {
                startZoom = zoom * 0.85;
                endZoom = zoom;
            } else if (shot.style === 'pull_out' || shot.style === 'slow_pull') {
                startZoom = zoom * 1.15;
                endZoom = zoom;
            } else if (shot.style === 'whip_pan') {
                currentEasing = { type: 'bezier', bezier: [1, 0, 0, 1] } as any;
            } else if (shot.style === 'dramatic_reveal') {
                startZoom = zoom * 1.5;
                endZoom = zoom;
                currentEasing = { type: 'bezier', bezier: [0.16, 1, 0.3, 1] } as any;
                rotationX = 25; rotationY = -15; zOffset = -200;
            } else if (shot.style === 'cinematic_drift') {
                rotationZ = 2; rotationX = 3;
            } else if (shot.style === 'dynamic_orbit') {
                rotationY = 15; rotationX = 5;
            } else if (shot.style === 'vertical_sweep') {
                rotationX = -20;
            } else if (shot.style === 'spiral_vortex') {
                rotationZ = 45; startZoom = zoom * 0.5;
            } else if (shot.style === 'glitch_snap') {
                currentEasing = { type: 'bezier', bezier: [0.1, 0.9, 0.2, 1] } as any;
                rotationZ = -5;
            } else if (shot.style === 'low_angle_hero') {
                rotationX = -35; zOffset = 100;
            } else if (shot.style === 'side_strafe_left') {
                rotationY = -20;
            } else if (shot.style === 'side_strafe_right') {
                rotationY = 20;
            } else if (shot.style === 'aerial_top_down') {
                rotationX = 70; startZoom = zoom * 0.7;
            } else if (shot.style === 'shaky_handheld') {
                rotationZ = 3; rotationX = 2; rotationY = 2;
            } else if (shot.style === 'zoom_blur_reveal') {
                startZoom = 0.1; currentEasing = { type: 'bezier', bezier: [0.4, 0, 0.2, 1] } as any;
            } else if (shot.style === 'tilt_shift_focus') {
                rotationX = 15; rotationY = 15;
            } else if (shot.style === 'power_zoom') {
                startZoom = zoom * 0.4; currentEasing = { type: 'bezier', bezier: [0.85, 0, 0.15, 1] } as any;
            } else if (shot.style === 'smooth_glide') {
                rotationZ = -1; rotationY = -5;
            } else if (shot.style === 'epic_scaling') {
                startZoom = 0.5; endZoom = zoom * 1.2;
            } else if (shot.style === 'warp_speed') {
                zOffset = -1000; startZoom = 0.5;
            } else if (shot.style === 'rolling_horizon') {
                rotationZ = -90; currentEasing = { type: 'bezier', bezier: [0.6, -0.28, 0.735, 0.045] } as any;
            } else if (shot.style === 'fisheye_distort') {
                startZoom = 1.8; endZoom = zoom; rotationX = 10;
            } else if (shot.style === 'dolly_zoom') {
                startZoom = zoom * 2; endZoom = zoom; zOffset = 500;
            } else if (shot.style === 'parallax_slide') {
                rotationY = 40; zOffset = -300;
            } else if (shot.style === 'staccato_jump') {
                currentEasing = { type: 'bezier', bezier: [0, 1, 0, 1] } as any;
            } else if (shot.style === 'oblique_view') {
                rotationX = 20; rotationY = 20; rotationZ = 10;
            } else if (shot.style === 'macro_focus') {
                startZoom = zoom * 1.4; endZoom = zoom;
            } else if (shot.style === 'uprising_reveal') {
                rotationX = -60; zOffset = -500;
            } else if (shot.style === 'descending_gaze') {
                rotationX = 60; zOffset = 500;
            } else if (shot.style === 'infinity_loop') {
                rotationZ = 360; rotationY = 30;
            } else if (shot.style === 'kaleidoscope') {
                rotationZ = 180; rotationX = 20; rotationY = 20;
            } else if (shot.style === 'cyber_scan') {
                rotationY = -45; rotationX = 10;
            } else if (shot.style === 'extreme_closeup') {
                startZoom = zoom * 3; endZoom = zoom;
            } else if (shot.style === 'wide_panorama') {
                startZoom = zoom * 0.3; endZoom = zoom;
            } else if (shot.style === 'pendulum_swing') {
                rotationZ = -30; rotationY = 15;
            } else if (shot.style === 'drunken_stumble') {
                rotationZ = 10; rotationX = 10; rotationY = 10;
            } else if (shot.style === 'floating_weightless') {
                rotationX = 5; rotationY = 5; rotationZ = 5;
            } else if (shot.style === 'rapid_fire') {
                currentEasing = Easing.bounce as any;
            } else if (shot.style === 'gentle_breeze') {
                rotationZ = 0.5; rotationY = 1;
            } else if (shot.style === 'the_matrix') {
                rotationY = 90; startZoom = zoom * 0.5;
            } else if (shot.style === 'heartbeat_zoom') {
                currentEasing = Easing.elastic(1) as any;
            }

            // Reach target: start movement transition
            keys.push({
                frame: shot.startFrame + inDur,
                lookAt: shot.targetId,
                zoom: startZoom,
                rotationX,
                rotationY,
                rotationZ,
                z: zOffset,
                easing: 'linear'
            });

            // End hold: finish cinematic drift/animation within shot
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

  const cameraState = useMemo(() => getCameraState(isNaN(frame) ? 0 : frame, mergedKeyframes, overlays, width, height), [frame, mergedKeyframes, overlays, width, height]);
  const nextFrameState = useMemo(() => getCameraState(isNaN(frame) ? 0.5 : frame + 0.5, mergedKeyframes, overlays, width, height), [frame, mergedKeyframes, overlays, width, height]);

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

  if (frame % 30 === 0) {
    console.log(`[CameraEngine] Frame ${frame}: tx=${tx.toFixed(1)}, ty=${ty.toFixed(1)}, zoom=${zoom.toFixed(2)}`);
  }

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
        perspective: `${config.perspective || 2000}px`,
        backgroundColor: '#000'
      }}
    >
      {/* Cinematic Camera Pivot System */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width, height,
          zIndex: 1,
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
        {/* Fixed Background Layer inside the same 3D container for absolute layering */}
        {backgroundLayer && (
            <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                width,
                height,
                // Even further in the distance. scale(12) compensates for perspective shrinkage at -10000px
                transform: `translate3d(0, 0, -10000px) scale(12)`,
                zIndex: -100, // Absolute bottom
                pointerEvents: 'none'
            }}>
                {backgroundLayer}
            </div>
        )}

        {/* Global Dark Overlay for Readability, placed between BG and Overlays in 3D space */}
        <div style={{
            position: 'absolute',
            top: 0, left: 0, width, height,
            backgroundColor: 'rgba(0,0,0,0.4)',
            transform: `translate3d(0, 0, -5000px) scale(6)`,
            zIndex: -50,
            pointerEvents: 'none'
        }} />

        <div style={{ position: 'absolute', top: 0, left: 0, width, height, zIndex: 1, transformStyle: 'preserve-3d' }}>
            {children}
        </div>
      </div>
    </div>
  );
};
