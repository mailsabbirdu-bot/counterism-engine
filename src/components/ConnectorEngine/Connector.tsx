import React, { useMemo, useRef, useEffect, useState } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring, AbsoluteFill } from 'remotion';
import { ConnectorProps } from './types';
import { ConnectorPresets } from './ConnectorPresets';
import { AnchorResolver, Point } from './AnchorResolver';
import { PathGenerator } from './PathGenerator';
import { ParticleFlow } from './ParticleFlow';
import { ArrowHead } from './ArrowHead';

export const Connector: React.FC<ConnectorProps & { start?: number; duration?: number; id?: string }> = ({
  source,
  target,
  preset = 'smooth_curve',
  overlays = [],
  animation: userAnimation = {},
  style: userStyle = {},
  sourceAnchor = 'center',
  targetAnchor = 'center',
  start = 0,
  duration: userDuration = 120,
  id = 'connector'
}) => {
  const frame = useCurrentFrame();
  const { fps, width: videoWidth, height: videoHeight } = useVideoConfig();
  const pathRef = useRef<SVGPathElement>(null);
  const [pathLength, setPathLength] = useState(0);

  const config = useMemo(() => ConnectorPresets[preset] || ConnectorPresets.smooth_curve, [preset]);

  const startPoint = useMemo(() => AnchorResolver.resolve(source, overlays, sourceAnchor), [source, overlays, sourceAnchor]);
  const endPoint = useMemo(() => AnchorResolver.resolve(target, overlays, targetAnchor), [target, overlays, targetAnchor]);

  const path = useMemo(() => {
    switch (config.pathType) {
      case 'arc': return PathGenerator.generateArcPath(startPoint, endPoint);
      case 'sCurve': return PathGenerator.generateSPath(startPoint, endPoint);
      case 'zigzag': return PathGenerator.generateZigzagPath(startPoint, endPoint);
      case 'branch': return PathGenerator.generateBranchPath(startPoint, endPoint);
      case 'straight': return PathGenerator.generateStraightPath(startPoint, endPoint);
      case 'smoothCurve':
      default: return PathGenerator.generateSmoothCurve(startPoint, endPoint);
    }
  }, [startPoint, endPoint, config.pathType]);

  useEffect(() => {
    if (pathRef.current) {
      setPathLength(pathRef.current.getTotalLength());
    }
  }, [path, overlays]);

  const relativeFrame = frame - start;
  if (frame < start || frame > start + userDuration) return null;

  const drawProgress = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 12, stiffness: 100 },
  });

  const opacity = interpolate(relativeFrame, [0, 15, userDuration - 15, userDuration], [0, 1, 1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp'
  });

  const finalStyle = { ...config.style, ...userStyle };
  const finalAnimation = { ...config.animation, ...userAnimation };

  return (
    <AbsoluteFill className="pointer-events-none">
      <svg width={videoWidth} height={videoHeight} viewBox={`0 0 ${videoWidth} ${videoHeight}`} style={{ opacity }}>
        <defs>
            <filter id={`glow-${id}`} x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="6" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
            </filter>
        </defs>

        {/* Shadow/Glow path */}
        {finalStyle.glow && (
            <path
                d={path}
                fill="none"
                stroke={finalStyle.color}
                strokeWidth={finalStyle.width * 2}
                strokeOpacity={0.3}
                filter={`url(#glow-${id})`}
                strokeDasharray={pathLength}
                strokeDashoffset={pathLength * (1 - drawProgress)}
            />
        )}

        {/* Main path */}
        <path
          ref={pathRef}
          id={id}
          d={path}
          fill="none"
          stroke={finalStyle.color}
          strokeWidth={finalStyle.width}
          strokeDasharray={finalStyle.dashArray || pathLength}
          strokeDashoffset={pathLength * (1 - drawProgress)}
          strokeLinecap="round"
          strokeLinejoin="round"
        />

        {/* Arrow Head at the end */}
        {drawProgress > 0.95 && (
            <ArrowHead
                point={endPoint}
                angle={Math.atan2(endPoint.y - startPoint.y, endPoint.x - startPoint.x) * 180 / Math.PI}
                color={finalStyle.color || '#fff'}
                opacity={interpolate(drawProgress, [0.95, 1], [0, 1])}
            />
        )}

        {/* Particles */}
        {finalAnimation.particle && drawProgress > 0.1 && (
            <ParticleFlow
                path={path}
                color={finalStyle.color || '#fff'}
                count={finalAnimation.particleCount || 1}
                duration={finalAnimation.duration || 60}
            />
        )}
      </svg>
    </AbsoluteFill>
  );
};
