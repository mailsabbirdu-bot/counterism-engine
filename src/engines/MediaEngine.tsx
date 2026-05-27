import React from 'react';
import { useCurrentFrame, interpolate, staticFile, OffthreadVideo, Img, useVideoConfig, Sequence } from 'remotion';

export const MediaEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  if (!overlay.src) {
    return null;
  }

  return (
    <Sequence from={overlay.start} durationInFrames={overlay.duration}>
      <MediaContent overlay={overlay} />
    </Sequence>
  );
};

const MediaContent: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const opacity = interpolate(
    frame,
    [0, 15, overlay.duration - 15, overlay.duration],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const scale = interpolate(
    frame,
    [0, overlay.duration],
    [1, 1.05],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const style: React.CSSProperties = {
    position: 'absolute',
    left: overlay.position?.x ?? 0,
    top: overlay.position?.y ?? 0,
    width: overlay.width ?? 'auto',
    height: overlay.height ?? 'auto',
    opacity,
    transform: `scale(${scale})`,
    borderRadius: overlay.borderRadius ?? 0,
    overflow: 'hidden',
    boxShadow: overlay.shadow ? '0 20px 50px rgba(0,0,0,0.5)' : 'none',
    border: overlay.border ? `${overlay.border.width}px solid ${overlay.border.color}` : 'none',
  };

  return (
    <div style={style}>
      {overlay.type === 'video' ? (
        <OffthreadVideo
          src={staticFile(overlay.src)}
          className="w-full h-full object-cover"
          startFrom={overlay.startFrom || 0}
          muted={overlay.muted !== false}
        />
      ) : (
        <Img
          src={staticFile(overlay.src)}
          className="w-full h-full object-cover"
        />
      )}
    </div>
  );
};
