import React from 'react';
import { AbsoluteFill, useVideoConfig } from 'remotion';
import { CameraState } from '../lib/cameraTypes';

interface CameraDebugOverlayProps {
  cameraState: CameraState;
  enabled?: boolean;
}

export const CameraDebugOverlay: React.FC<CameraDebugOverlayProps> = ({ cameraState, enabled }) => {
  const { width, height } = useVideoConfig();

  if (!enabled) return null;

  return (
    <AbsoluteFill className="pointer-events-none z-[9999]">
      {/* Viewport Bounds */}
      <div
        className="absolute border-4 border-red-500/50"
        style={{ width, height, left: 0, top: 0 }}
      />

      {/* World Indicator (Conceptual) */}
      <div className="absolute top-10 left-10 bg-black/80 text-white p-4 font-mono text-sm rounded-xl border border-white/20 backdrop-blur-md">
        <h3 className="text-red-400 font-bold mb-2">DEBUG: CAMERA SYSTEM</h3>
        <p>X: <span className="text-emerald-400">{cameraState.x.toFixed(2)}</span></p>
        <p>Y: <span className="text-emerald-400">{cameraState.y.toFixed(2)}</span></p>
        <p>Zoom: <span className="text-emerald-400">{cameraState.zoom.toFixed(3)}</span></p>
        <p>Rotation: <span className="text-emerald-400">{cameraState.rotation.toFixed(2)}°</span></p>
      </div>

      {/* World Bounds Center Crosshair */}
      <div className="absolute top-1/2 left-1/2 w-10 h-1 border-t border-white/30 -translate-x-1/2" />
      <div className="absolute top-1/2 left-1/2 w-1 h-10 border-l border-white/30 -translate-y-1/2" />
    </AbsoluteFill>
  );
};
