import React, { useMemo } from 'react';
import { interpolate } from 'remotion';
import { KpiElement, SvgProvider } from '../types';
import { RemoteSvg } from './RemoteSvg';
import { getEntranceProgress } from '../lib/animationUtils';
import { useAnimation } from './AnimationContext';
import { ENGINE_CONSTANTS } from '../lib/constants';

export const KpiCard: React.FC<{ element: KpiElement, sceneIconTheme?: SvgProvider }> = ({ element, sceneIconTheme }) => {
  const { title, value, trend, subtitle, icon, x, y, startFrame = 0 } = element;
  const { frame, fps } = useAnimation();

  const spr = getEntranceProgress(frame, fps, startFrame, true);

  // Value animation (numeric only)
  const displayValue = useMemo(() => {
    const rel = frame - (startFrame + 15);
    if (rel < 0) return typeof value === 'number' ? '0' : value;

    if (typeof value === 'number') {
        const count = interpolate(rel, [0, 60], [0, value], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        return Math.round(count).toLocaleString();
    }
    // Handle strings like "170M"
    const match = String(value).match(/^([\d.]+)([A-Z%]+)?$/);
    if (match) {
        const num = parseFloat(match[1]);
        const suffix = match[2] || '';
        const count = interpolate(rel, [0, 60], [0, num], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
        return `${count.toFixed(match[1].includes('.') ? 1 : 0)}${suffix}`;
    }
    return value;
  }, [value, frame, startFrame]);

  return (
    <div style={{
        position: 'absolute',
        left: x,
        top: y,
        transform: `translate(-50%, -50%) scale(${0.8 + spr * 0.2})`,
        opacity: spr,
        width: ENGINE_CONSTANTS.KPI_CARD_WIDTH,
        padding: '24px',
        backgroundColor: 'rgba(255,255,255,0.03)',
        backdropFilter: 'blur(30px)',
        border: '1px solid rgba(255,255,255,0.1)',
        borderRadius: '32px',
        boxShadow: '0 20px 50px rgba(0,0,0,0.3)',
        display: 'flex',
        flexDirection: 'column',
        gap: '12px'
    }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ color: 'rgba(255,255,255,0.4)', fontSize: '10px', fontWeight: '900', textTransform: 'uppercase', letterSpacing: '2px' }}>{title}</span>
                <h2 style={{ color: 'white', fontSize: '48px', fontWeight: '900', margin: '4px 0 0 0', letterSpacing: '-2px' }}>{displayValue}</h2>
            </div>
            {icon && (
                <div style={{ width: 48, height: 48, backgroundColor: 'rgba(0, 245, 255, 0.1)', borderRadius: '12px', padding: '8px' }}>
                    <RemoteSvg query={icon} provider={sceneIconTheme || 'lucide'} color="#00F5FF" />
                </div>
            )}
        </div>

        {(trend || subtitle) && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                {trend && (
                    <span style={{
                        color: trend.startsWith('+') ? '#10b981' : '#ef4444',
                        fontSize: '12px',
                        fontWeight: 'bold',
                        backgroundColor: trend.startsWith('+') ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                        padding: '4px 8px',
                        borderRadius: '8px'
                    }}>
                        {trend}
                    </span>
                )}
                {subtitle && <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: '12px', fontWeight: 'medium' }}>{subtitle}</span>}
            </div>
        )}
    </div>
  );
};
