import React, { useMemo } from 'react';
import { CalloutElement } from '../types';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';
import { ENGINE_CONSTANTS } from '../lib/constants';

export const CalloutSystem: React.FC<{ element: CalloutElement, targetPos?: { x: number, y: number } }> = ({ element, targetPos }) => {
  const { title, body, direction = 'right', startFrame = 0 } = element;
  const { frame, fps } = useAnimation();

  if (!targetPos) return null;

  const spr = getEntranceProgress(frame, fps, startFrame, true);

  const lineLength = ENGINE_CONSTANTS.CALLOUT_LINE_LENGTH;
  const boxWidth = ENGINE_CONSTANTS.CALLOUT_BOX_WIDTH;

  const offsets = {
    right: { lx: 30, ly: 0, ex: lineLength, ey: 0, bx: lineLength, by: 0, align: 'left' },
    left: { lx: -30, ly: 0, ex: -lineLength, ey: 0, bx: -lineLength - boxWidth, by: 0, align: 'right' },
    top: { lx: 0, ly: -30, ex: 0, ey: -lineLength, bx: -boxWidth/2, by: -lineLength - 100, align: 'center' },
    bottom: { lx: 0, ly: 30, ex: 0, ey: lineLength, bx: -boxWidth/2, by: lineLength, align: 'center' }
  };

  const off = offsets[direction];

  return (
    <div style={{ position: 'absolute', left: targetPos.x, top: targetPos.y }}>
      {/* 1. Leader Line */}
      <svg style={{ position: 'absolute', overflow: 'visible', pointerEvents: 'none' }}>
        <line
          x1={off.lx} y1={off.ly}
          x2={off.lx + (off.ex - off.lx) * spr}
          y2={off.ly + (off.ey - off.ly) * spr}
          stroke="white" strokeWidth="2" strokeDasharray="4 4"
        />
        <circle cx={off.lx} cy={off.ly} r="4" fill="white" opacity={spr} />
      </svg>

      {/* 2. Callout Box */}
      <div style={{
        position: 'absolute',
        left: off.bx,
        top: off.by,
        width: boxWidth,
        padding: '20px',
        backgroundColor: 'rgba(0,0,0,0.6)',
        backdropFilter: 'blur(10px)',
        border: '1px solid rgba(255,255,255,0.2)',
        borderRadius: '12px',
        opacity: spr,
        transform: `translateY(${(1-spr)*20}px)`,
        textAlign: off.align as 'left' | 'right' | 'center'
      }}>
        <h4 style={{ color: '#00F5FF', fontSize: '18px', fontWeight: 'bold', margin: '0 0 5px 0', textTransform: 'uppercase' }}>{title}</h4>
        <p style={{ color: 'white', fontSize: '14px', margin: 0, opacity: 0.8, lineHeight: '1.4' }}>{body}</p>
      </div>
    </div>
  );
};
