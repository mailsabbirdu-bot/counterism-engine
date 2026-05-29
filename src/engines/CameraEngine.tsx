import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate } from 'remotion';

export interface CameraKeyframe {
  frame: number;
  x?: number;
  y?: number;
  z?: number;
  zoom?: number;
  rotationX?: number;
  rotationY?: number;
  rotationZ?: number;
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
  const { width, height } = useVideoConfig();

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

  const getInterpolated = (prop: keyof CameraKeyframe, defaultValue: number) => {
    const values = sortedKeyframes.map((k) => (k[prop] as number) ?? defaultValue);
    if (frames.length === 1) return values[0];

    return interpolate(frame, frames, values, {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
  };

  const x = getInterpolated('x', 0);
  const y = getInterpolated('y', 0);
  const z = getInterpolated('z', 0);
  const zoom = getInterpolated('zoom', 1);
  const rotationX = getInterpolated('rotationX', 0);
  const rotationY = getInterpolated('rotationY', 0);
  const rotationZ = getInterpolated('rotationZ', 0);

  const perspective = config.perspective || 1000;

  // To simulate a camera moving, we move the scene in the opposite direction.
  // However, zoom is better handled as a positive scale on the container.

  const containerStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    perspective: `${perspective}px`,
    perspectiveOrigin: '50% 50%',
    overflow: 'hidden',
  };

  const sceneStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    transformStyle: 'preserve-3d',
    transform: `
      translateZ(${-perspective * (1 - zoom)}px)
      translateX(${-x}px)
      translateY(${-y}px)
      translateZ(${-z}px)
      rotateX(${rotationX}deg)
      rotateY(${rotationY}deg)
      rotateZ(${rotationZ}deg)
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
