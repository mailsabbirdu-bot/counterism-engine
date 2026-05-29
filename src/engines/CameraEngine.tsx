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
  easing?: 'linear' | 'ease' | 'bezier' | 'in' | 'out';
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

  const { sortedKeyframes } = useMemo(() => {
    const sorted = [...config.keyframes].sort((a, b) => a.frame - b.frame);
    return { sortedKeyframes: sorted };
  }, [config.keyframes]);

  const cameraState = useMemo(() => {
    // Find the current segment
    let startIdx = 0;
    for (let i = 0; i < sortedKeyframes.length - 1; i++) {
      if (frame >= sortedKeyframes[i].frame) {
        startIdx = i;
      }
    }

    const endIdx = Math.min(startIdx + 1, sortedKeyframes.length - 1);
    const startKey = sortedKeyframes[startIdx];
    const endKey = sortedKeyframes[endIdx];

    const getInterpolated = (prop: keyof CameraKeyframe, defaultValue: number) => {
      const startVal = (startKey[prop] as number) ?? defaultValue;
      const endVal = (endKey[prop] as number) ?? defaultValue;

      if (startIdx === endIdx) return startVal;

      const easingType = startKey.easing || 'ease';
      let easingFn = Easing.linear;

      if (easingType === 'ease') easingFn = Easing.inOut(Easing.ease);
      else if (easingType === 'in') easingFn = Easing.in(Easing.ease);
      else if (easingType === 'out') easingFn = Easing.out(Easing.ease);
      else if (easingType === 'bezier') easingFn = Easing.bezier(0.33, 1, 0.68, 1);

      return interpolate(frame, [startKey.frame, endKey.frame], [startVal, endVal], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
        easing: easingFn,
      });
    };

    return {
      x: getInterpolated('x', 0),
      y: getInterpolated('y', 0),
      z: getInterpolated('z', 0),
      zoom: getInterpolated('zoom', 1),
      rotationX: getInterpolated('rotationX', 0),
      rotationY: getInterpolated('rotationY', 0),
      rotationZ: getInterpolated('rotationZ', 0),
    };
  }, [frame, sortedKeyframes]);

  const perspective = config.perspective || 1000;

  const containerStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    perspective: `${perspective}px`,
    perspectiveOrigin: '50% 50%',
    overflow: 'hidden',
  };

  // Professional transform order: Translation first, then rotation
  const sceneStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    transformStyle: 'preserve-3d',
    willChange: 'transform',
    backfaceVisibility: 'hidden',
    transform: `
      perspective(${perspective}px)
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
