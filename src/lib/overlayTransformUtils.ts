import React from 'react';

/**
 * Lightweight utility to calculate parallax transform
 * finalX = cameraX * depth
 */
export const getParallaxStyle = (cameraX: number, cameraY: number, depth: number = 1): React.CSSProperties => {
  if (depth === 1) return {};

  // The camera rig already moves the parent container by cameraX/cameraY.
  // To achieve parallax, we need to counter-move or extra-move the child based on depth.
  // If depth is 1, the item moves 1:1 with camera (static in world).
  // If depth is 0.5 (far), it should move SLOWER in the viewport, meaning it moves
  // with the camera but less.

  // Since parent moves by cameraX, moving child by -cameraX * (1 - depth)
  // results in net movement: cameraX + (-cameraX + cameraX * depth) = cameraX * depth.

  const offsetX = -cameraX * (1 - depth);
  const offsetY = -cameraY * (1 - depth);

  return {
    transform: `translate3d(${offsetX}px, ${offsetY}px, 0)`,
  };
};
