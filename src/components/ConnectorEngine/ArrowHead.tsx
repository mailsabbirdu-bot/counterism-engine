import React from 'react';

interface ArrowHeadProps {
  point: { x: number; y: number };
  angle: number;
  color: string;
  size?: number;
  opacity?: number;
}

export const ArrowHead: React.FC<ArrowHeadProps> = ({
  point,
  angle,
  color,
  size = 12,
  opacity = 1
}) => {
  return (
    <path
      d={`M 0 0 L ${size} ${size / 2} L 0 ${size} L ${size / 4} ${size / 2} Z`}
      fill={color}
      style={{
        opacity,
        transform: `translate(${point.x}px, ${point.y}px) rotate(${angle}deg) translate(-${size / 2}px, -${size / 2}px)`,
        filter: `drop-shadow(0 0 5px ${color})`
      }}
    />
  );
};
