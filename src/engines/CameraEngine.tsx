import React, { useMemo } from 'react';
import { useCurrentFrame, interpolate, Easing } from 'remotion';

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
  keyframes: CameraKeyframe[];
}

export const CameraEngine: React.FC<{
  config?: CameraConfig;
  children: React.ReactNode;
}> = ({ config, children }) => {
  const frame = useCurrentFrame();

  if (!config || !config.enabled || !config.keyframes || config.keyframes.length === 0) {
    return <>{children}</>;
  }

  const { sortedKeyframes, frames } = useMemo(() => {
    const sorted = [...config.keyframes].sort((a, b) => a.frame - b.frame);
    return {
      sortedKeyframes: sorted,
      frames: sorted.map((k) => k.frame),
    };
  }, [config.keyframes]);

  const cameraState = useMemo(() => {
    const getVal = (prop: keyof CameraKeyframe, defaultValue: number) => {
      const values = sortedKeyframes.map((k) => (k[prop] as number) ?? defaultValue);
      if (frames.length === 1) return values[0];

      // Map easing names to Easing functions
      const easing = sortedKeyframes[0].easing === 'bezier'
        ? Easing.bezier(0.33, 1, 0.68, 1) // easeOutCubic
        : sortedKeyframes[0].easing === 'ease'
          ? Easing.inOut(Easing.ease)
          : Easing.linear;

      return interpolate(frame, frames, values, {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
        easing: easing
      });
    };

    return {
      x: getVal('x', 0),
      y: getVal('y', 0),
      z: getVal('z', 0),
      zoom: getVal('zoom', 1),
      rotationX: getVal('rotationX', 0),
      rotationY: getVal('rotationY', 0),
      rotationZ: getVal('rotationZ', 0),
    };
  }, [frame, frames, sortedKeyframes]);

  const perspective = config.perspective || 1000;

  const containerStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    perspective: `${perspective}px`,
    perspectiveOrigin: '50% 50%',
    overflow: 'hidden',
  };

  // Improved scene style with hardware acceleration hints
  const sceneStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    transformStyle: 'preserve-3d',
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    transform: `
      translate3d(${-cameraState.x}px, ${-cameraState.y}px, ${-cameraState.z}px)
      scale3d(${cameraState.zoom}, ${cameraState.zoom}, 1)
      rotateX(${cameraState.rotationX}deg)
      rotateY(${cameraState.rotationY}deg)
      rotateZ(${cameraState.rotationZ}deg)
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
