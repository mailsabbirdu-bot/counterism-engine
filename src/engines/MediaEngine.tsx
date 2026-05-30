import React from 'react';
import { useCurrentFrame, interpolate, OffthreadVideo, Img, useVideoConfig, Sequence, AbsoluteFill } from 'remotion';
import { resolveAsset } from '../lib/resolveAsset';

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
  const { width: videoWidth, height: videoHeight } = useVideoConfig();

  const fadeDuration = Math.min(15, Math.floor(overlay.duration / 2));

  const opacity = interpolate(
    frame,
    [0, fadeDuration, overlay.duration - fadeDuration, overlay.duration],
    [0, 1, 1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const scale = interpolate(
    frame,
    [0, overlay.duration],
    [1, 1.05],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const x = overlay.position?.x ?? videoWidth / 2;
  const y = overlay.position?.y ?? videoHeight / 2;

  const containerStyle: React.CSSProperties = {
    position: 'absolute',
    left: `${x}px`,
    top: `${y}px`,
    zIndex: overlay.zIndex,
    width: overlay.width ? `${overlay.width}px` : 'auto',
    height: overlay.height ? `${overlay.height}px` : 'auto',
    opacity,
    transform: `translate(-50%, -50%) scale(${scale})`,
    borderRadius: `${overlay.borderRadius ?? 0}px`,
    overflow: 'hidden',
    boxShadow: overlay.shadow ? '0 20px 50px rgba(0,0,0,0.5)' : 'none',
    border: overlay.border ? `${overlay.border.width}px solid ${overlay.border.color}` : 'none',
  };

  const mediaStyle: React.CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'cover',
  };

  const mediaUrl = resolveAsset(overlay.src);

  return (
    <AbsoluteFill className="pointer-events-none">
      <div style={containerStyle}>
        {overlay.type === 'video' ? (
          <OffthreadVideo
            src={mediaUrl}
            style={mediaStyle}
            startFrom={overlay.startFrom || 0}
            muted={overlay.audio_enabled !== true}
          />
        ) : (
          <Img
            src={mediaUrl}
            style={mediaStyle}
          />
        )}
      </div>
    </AbsoluteFill>
  );
};
