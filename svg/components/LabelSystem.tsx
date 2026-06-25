import React from 'react';
import { LabelElement } from '../types';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';

export const LabelSystem: React.FC<{ element: LabelElement, targetPos?: { x: number, y: number } }> = ({ element, targetPos }) => {
  const { text, position = 'bottom', fontSize = 72, color = 'white', animation = 'slideUp', startFrame = 0 } = element;
  const { frame, fps } = useAnimation();

  if (!targetPos) return null;

  const spr = getEntranceProgress(frame, fps, startFrame, false);

  const offsets = {
    top: { x: 0, y: -200 },
    bottom: { x: 0, y: 200 },
    left: { x: -300, y: 0 },
    right: { x: 300, y: 0 },
    center: { x: 0, y: 0 }
  };

  const offset = offsets[position];
  const x = targetPos.x + offset.x;
  const y = targetPos.y + offset.y;

  const animationStyles = () => {
    switch (animation) {
      case 'fade': return { opacity: spr };
      case 'slideUp': return { opacity: spr, transform: `translateY(${(1-spr)*20}px)` };
      case 'slideDown': return { opacity: spr, transform: `translateY(${(spr-1)*20}px)` };
      case 'reveal': return { clipPath: `inset(0 ${100-spr*100}% 0 0)` };
      case 'typewriter': return { opacity: spr }; // Fallback
      default: return { opacity: spr };
    }
  };

  return (
    <div style={{
      position: 'absolute',
      left: x,
      top: y,
      transform: 'translate(-50%, -50%)',
      color,
      fontSize,
      fontWeight: '900',
      textTransform: 'uppercase',
      letterSpacing: '1px',
      whiteSpace: 'pre-wrap',
      textAlign: 'center',
      textShadow: '0 8px 30px rgba(0,0,0,0.8)',
      lineHeight: '1.1',
      ...animationStyles()
    }}>
      {text}
    </div>
  );
};
