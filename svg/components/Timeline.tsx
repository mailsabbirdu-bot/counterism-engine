import React from 'react';
import { TimelineElement } from '../types';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';
import { ENGINE_CONSTANTS } from '../lib/constants';

export const Timeline: React.FC<{ element: TimelineElement }> = ({ element }) => {
  const { events, x, y, startFrame = 0 } = element;
  const { frame, fps } = useAnimation();

  // HARDENING: Guard divide-by-zero (BUG-2)
  const totalEvents = events.length;
  if (totalEvents === 0) return null;

  const totalWidth = ENGINE_CONSTANTS.TIMELINE_WIDTH;
  const stepX = totalEvents > 1 ? totalWidth / Math.max(totalEvents - 1, 1) : 0;

  const overallProgress = getEntranceProgress(frame, fps, startFrame, false);

  return (
    <div style={{ position: 'absolute', left: x, top: y, transform: 'translate(-50%, -50%)' }}>
      {/* 1. Base Line */}
      <div style={{
          position: 'absolute',
          left: -totalWidth / 2,
          top: 0,
          width: totalWidth * overallProgress,
          height: 4,
          backgroundColor: 'rgba(255,255,255,0.2)',
          borderRadius: 2
      }} />

      {/* 2. Events */}
      {events.map((ev, i) => {
          const eventX = (-totalWidth / 2) + (i * stepX);
          const eventStart = startFrame + 15 + (i * ENGINE_CONSTANTS.STAGGER_INTERVAL * 3);
          const spr = getEntranceProgress(frame, fps, eventStart, true);

          if (frame < eventStart) return null;

          return (
            <div key={`event_${i}`} style={{ position: 'absolute', left: eventX, top: 0 }}>
                {/* Node */}
                <div style={{
                    width: 24,
                    height: 24,
                    borderRadius: '50%',
                    backgroundColor: '#00D1FF',
                    border: '6px solid #000',
                    transform: `translate(-50%, -50%) scale(${spr})`,
                    boxShadow: '0 0 20px #00D1FF'
                }} />

                {/* Label */}
                <div style={{
                    position: 'absolute',
                    top: i % 2 === 0 ? 50 : -130,
                    left: 0,
                    transform: `translateX(-50%) translateY(${(1-spr)*15}px)`,
                    opacity: spr,
                    textAlign: 'center',
                    width: 300
                }}>
                    <span style={{ color: '#00D1FF', fontSize: '28px', fontWeight: '900', display: 'block' }}>{ev.year}</span>
                    <span style={{ color: 'white', fontSize: '20px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px' }}>{ev.label}</span>
                </div>

                {/* Connector vertical */}
                <div style={{
                    position: 'absolute',
                    left: 0,
                    top: i % 2 === 0 ? 0 : -50,
                    width: 2,
                    height: 50 * spr,
                    backgroundColor: 'rgba(0, 209, 255, 0.4)'
                }} />
            </div>
          );
      })}
    </div>
  );
};
