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
    const flicker = Math.sin(safeFrame * 1.5) > 0 ? 1 : 0.85;
    const entrance = spring({ frame: safeFrame, fps, config: { damping: 12, stiffness: 120 } });
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    const color = overlay.color || '#00F5FF';

    return (
        <div className="absolute" style={{
            left: `${overlay.position?.x ?? 960}px`,
            top: `${overlay.position?.y ?? 540}px`,
            transform: 'translate(-50%, -50%)',
            zIndex: 100
        }}>
            <div style={{
                ...fontStyle,
                width: '650px',
                padding: '50px',
                background: 'linear-gradient(135deg, rgba(10,10,10,0.95) 0%, rgba(30,30,30,0.9) 100%)',
                backdropFilter: 'blur(40px)',
                borderRadius: '4px 80px 4px 80px',
                border: `4px solid ${color}`,
                boxShadow: `0 0 60px ${color}33, inset 0 0 30px ${color}11, 0 0 100px rgba(0,0,0,0.5)`,
                opacity: flicker * entrance,
                color: 'white',
                position: 'relative',
                overflow: 'hidden',
                transform: `perspective(1000px) rotateX(${(1-entrance) * 20}deg)`
            }}>
                {/* Modern Scanline Effect */}
                <div className="absolute inset-0 pointer-events-none opacity-10" style={{
                     background: 'repeating-linear-gradient(0deg, transparent, transparent 2px, white 3px)'
                }} />

                <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-white to-transparent opacity-40" />
                <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '30px' }}>
                    <div style={{ width: '12px', height: '12px', backgroundColor: color, borderRadius: '50%', boxShadow: `0 0 10px ${color}` }} />
                    <h3 className="text-3xl font-black uppercase tracking-[0.25em]" style={{ ...fontStyle, color, textShadow: `0 0 10px ${color}88` }}>{overlay.title || 'ALERT'}</h3>
                </div>

                <p className="text-5xl font-black leading-[1.1] tracking-tight" style={{ ...fontStyle, textShadow: '0 4px 20px rgba(0,0,0,0.5)' }}>{overlay.content}</p>

                <div className="mt-10 flex items-center justify-between border-t border-white/10 pt-6">
                    <div className="flex flex-col">
                        <span className="text-[10px] font-mono opacity-40 uppercase">System Status</span>
                        <span className="text-xs font-mono font-bold text-emerald-400">FLICKER_STABLE_V4</span>
                    </div>
                    <div className="flex flex-col items-end">
                        <span className="text-[10px] font-mono opacity-40 uppercase">Node ID</span>
                        <span className="text-xs font-mono font-bold opacity-80">{overlay.nodeId || 'PRIM-01'}</span>
                    </div>
                </div>
            </div>
        </div>
    );
};
