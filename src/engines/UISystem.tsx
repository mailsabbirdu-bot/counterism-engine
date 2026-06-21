import React from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';
import { Terminal, ShieldCheck, Activity, Cpu, Box } from 'lucide-react';

export const UISystem: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();
  const start = Number(overlay.start) || 0;
  const duration = Number(overlay.duration) || 120;
  const relativeFrame = frame - start;

  if (frame < start || frame > start + duration) {
    return null;
  }

  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;

  if (overlay.indicator_type === 'flickerTextBox') {
      return <FlickerTextBox overlay={overlay} safeFrame={safeFrame} fps={fps} />;
  }

  const entrance = spring({
    frame: safeFrame,
    fps,
    config: { damping: 15, stiffness: 100 }
  });

  const opacity = interpolate(safeFrame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  const progressValue = interpolate(
    safeFrame,
    [30, 120],
    [overlay.initialProgress || 0, overlay.targetProgress || 100],
    { extrapolateRight: 'clamp' }
  );

  const getIcon = (type: string) => {
    switch (type) {
      case 'terminal': return <Terminal className="text-blue-400 w-8 h-8" />;
      case 'security': return <ShieldCheck className="text-emerald-400 w-8 h-8" />;
      case 'activity': return <Activity className="text-rose-400 w-8 h-8" />;
      case 'cpu': return <Cpu className="text-amber-400 w-8 h-8" />;
      default: return <Box className="text-indigo-400 w-8 h-8" />;
    }
  };

  const x = overlay.position?.x ?? width / 2;
  const y = overlay.position?.y ?? height / 2;

  return (
    <div
      className="absolute"
      style={{
        left: `${x}px`,
        top: `${y}px`,
        opacity,
        zIndex: overlay.zIndex ?? 40,
        transform: `translate(-50%, -50%) perspective(2000px) rotateY(${(1 - entrance) * 30}deg) scale(${0.85 + entrance * 0.15})`,
        filter: `blur(${(1 - opacity) * 10}px)`,
        color: 'white'
      }}
    >
      <div style={{
        width: '550px',
        backgroundColor: 'rgba(20, 20, 20, 0.9)',
        borderRadius: '24px',
        border: '1px solid rgba(255, 255, 255, 0.2)',
        padding: '32px',
        boxShadow: '0 50px 100px rgba(0,0,0,0.6)',
        overflow: 'hidden',
        position: 'relative'
      }}>
        {/* Glow effect */}
        <div className="absolute -top-32 -left-32 w-64 h-64 bg-blue-500/30 blur-[120px] pointer-events-none" />

        <div style={{ display: 'flex', alignItems: 'center', gap: '24px', marginBottom: '24px' }}>
           <div style={{ padding: '16px', background: 'rgba(255,255,255,0.1)', borderRadius: '16px' }}>
              {getIcon(overlay.iconType)}
           </div>
           <div>
              <h2 style={{ fontSize: '24px', fontWeight: 'bold', margin: 0 }}>{overlay.title}</h2>
              <p style={{ opacity: 0.5, fontSize: '12px', margin: 0 }}>Node: {overlay.nodeId || 'PRIMARY-V4'}</p>
           </div>
        </div>

        <p style={{ fontSize: '18px', marginBottom: '24px', fontWeight: 'bold' }}>{overlay.description}</p>

        <div style={{ background: 'rgba(255,255,255,0.1)', height: '12px', borderRadius: '6px', width: '100%', marginBottom: '12px' }}>
           <div style={{ background: '#3b82f6', height: '100%', borderRadius: '6px', width: `${progressValue}%` }} />
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
           <div style={{ background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '12px', width: '45%' }}>
              <span style={{ fontSize: '12px', opacity: 0.5 }}>LATENCY</span>
              <div style={{ color: '#10b981', fontWeight: 'bold' }}>12ms</div>
           </div>
           <div style={{ background: 'rgba(255,255,255,0.05)', padding: '16px', borderRadius: '12px', width: '45%' }}>
              <span style={{ fontSize: '12px', opacity: 0.5 }}>LOAD</span>
              <div style={{ color: '#f59e0b', fontWeight: 'bold' }}>0.82</div>
           </div>
        </div>
      </div>
    </div>
  );
};

const FlickerTextBox = ({ overlay, safeFrame, fps }: any) => {
    const flicker = Math.sin(safeFrame * 0.8) > 0 ? 1 : 0.7;
    const entrance = spring({ frame: safeFrame, fps, config: { damping: 12 } });
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    const color = overlay.color || '#3b82f6';

    return (
        <div className="absolute" style={{
            left: `${overlay.position?.x ?? 960}px`,
            top: `${overlay.position?.y ?? 540}px`,
            transform: 'translate(-50%, -50%)',
            zIndex: 100
        }}>
            <div style={{
                ...fontStyle,
                width: '600px',
                padding: '40px',
                backgroundColor: 'rgba(0,0,0,0.85)',
                backdropFilter: 'blur(20px)',
                borderRadius: '12px 60px 12px 60px',
                border: `3px solid ${color}`,
                boxShadow: `0 0 40px ${color}44, inset 0 0 20px ${color}22`,
                opacity: flicker * entrance,
                color: 'white',
                position: 'relative',
                overflow: 'hidden'
            }}>
                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white to-transparent opacity-30 animate-pulse" />
                <h3 className="text-2xl font-black uppercase tracking-widest mb-4" style={{ ...fontStyle, color }}>{overlay.title}</h3>
                <p className="text-4xl font-bold leading-tight" style={fontStyle}>{overlay.content}</p>
                <div className="mt-6 flex items-center justify-between opacity-50">
                    <span className="text-xs font-mono">STATUS: FLICKER_ACTIVE</span>
                    <span className="text-xs font-mono">CORE_V4</span>
                </div>
            </div>
        </div>
    );
};
