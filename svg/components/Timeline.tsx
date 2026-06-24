import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { TimelineElement } from '../types';
import { getEntranceProgress } from '../lib/animationUtils';

export const Timeline: React.FC<{ element: TimelineElement }> = ({ element }) => {
  const { events, x, y, startFrame = 0 } = element;
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const totalWidth = 1200;
  const stepX = totalWidth / (events.length - 1);

  const overallProgress = getEntranceProgress(frame, fps, startFrame, false);

  return (
    <div style={{ position: 'absolute', left: x, top: y, transform: 'translate(-50%, -50%)' }}>
      {/* 1. Base Line */}
      <div style={{
          position: 'absolute',
          left: -totalWidth / 2,
          top: 0,
          width: totalWidth * overallProgress,
          height: 2,
          backgroundColor: 'rgba(255,255,255,0.2)',
          borderRadius: 1
      }} />

      {/* 2. Events */}
      {events.map((ev, i) => {
          const eventX = (-totalWidth / 2) + (i * stepX);
          const eventStart = startFrame + 15 + (i * 30);
          const spr = getEntranceProgress(frame, fps, eventStart, true);

          if (frame < eventStart) return null;

          return (
            <div key={`event_${i}`} style={{ position: 'absolute', left: eventX, top: 0 }}>
                {/* Node */}
                <div style={{
                    width: 16,
                    height: 16,
                    borderRadius: '50%',
                    backgroundColor: '#00F5FF',
                    border: '4px solid #000',
                    transform: `translate(-50%, -50%) scale(${spr})`,
                    boxShadow: '0 0 15px #00F5FF'
                }} />

                {/* Label */}
                <div style={{
                    position: 'absolute',
                    top: i % 2 === 0 ? 40 : -100,
                    left: 0,
                    transform: `translateX(-50%) translateY(${(1-spr)*10}px)`,
                    opacity: spr,
                    textAlign: 'center',
                    width: 200
                }}>
                    <span style={{ color: '#00F5FF', fontSize: '18px', fontWeight: '900', display: 'block' }}>{ev.year}</span>
                    <span style={{ color: 'white', fontSize: '14px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px' }}>{ev.label}</span>
                </div>

                {/* Connector vertical */}
                <div style={{
                    position: 'absolute',
                    left: 0,
                    top: i % 2 === 0 ? 0 : -40,
                    width: 1,
                    height: 40 * spr,
                    backgroundColor: 'rgba(0, 245, 255, 0.4)'
                }} />
            </div>
          );
      })}
    </div>
  );
};
