import { interpolate, spring, SpringConfig, Easing } from 'remotion';

export const DEFAULT_SPRING_CONFIG: SpringConfig = {
  damping: 12,
  stiffness: 100,
  mass: 1,
  overshootClamping: false,
};

/**
 * Centered Animation Logic
 * Reduces spring overhead by using interpolation for secondary elements.
 */
export const getEntranceProgress = (
  frame: number,
  fps: number,
  startFrame: number = 0,
  useSpring: boolean = false,
  config: SpringConfig = DEFAULT_SPRING_CONFIG
) => {
  const relativeFrame = frame - startFrame;
  if (relativeFrame < 0) return 0;

  if (useSpring) {
    return spring({
      frame: relativeFrame,
      fps,
      config,
    });
  }

  // Quintic Out Easing for ultra-sleek movement
  return interpolate(relativeFrame, [0, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.bezier(0.23, 1, 0.32, 1)
  });
};

export const getScaleProgress = (
  frame: number,
  fps: number,
  startFrame: number = 0,
  useSpring: boolean = true
) => {
    const progress = getEntranceProgress(frame, fps, startFrame, useSpring);
    return 0.8 + progress * 0.2;
};

export const getRevealProgress = (
    frame: number,
    fps: number,
    startFrame: number = 0
) => {
    return interpolate(frame - startFrame, [0, 30], [0, 100], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp'
    });
};
