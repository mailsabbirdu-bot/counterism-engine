import React from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';
import { Terminal, ShieldCheck, Activity, Cpu, Box } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { Progress } from '../components/ui/progress';

export const UISystem: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const entrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 15, stiffness: 100 }
  });

  const opacity = interpolate(relativeFrame, [0, 20], [0, 1], { extrapolateRight: 'clamp' });

  // Dynamic progress value simulation
  const progressValue = interpolate(
    relativeFrame,
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

  return (
    <div
      className="absolute p-8"
      style={{
        left: overlay.position?.x ?? 100,
        top: overlay.position?.y ?? 100,
        opacity,
        zIndex: overlay.zIndex,
        transform: `perspective(2000px) rotateY(${(1 - entrance) * 30}deg) scale(${0.85 + entrance * 0.15})`,
        filter: `blur(${(1 - opacity) * 10}px)`
      }}
    >
      <Card className={`
        w-[550px] overflow-hidden border-0 shadow-[0_50px_100px_rgba(0,0,0,0.6)]
        ${overlay.variant === 'glass'
          ? 'bg-zinc-900/60 backdrop-blur-3xl ring-1 ring-white/30'
          : 'bg-zinc-950/90 ring-1 ring-zinc-700 shadow-2xl'}
      `}>
        {/* Glow effect */}
        <div className="absolute -top-32 -left-32 w-64 h-64 bg-blue-500/30 blur-[120px] pointer-events-none" />

        <CardHeader className="flex flex-row items-center gap-6 space-y-0 p-8 border-b border-white/10 bg-white/5">
          <div className="p-4 bg-white/10 rounded-2xl ring-1 ring-white/20 shadow-inner">
            {getIcon(overlay.iconType)}
          </div>
          <div className="flex flex-col">
            <CardTitle className="text-2xl font-black text-white tracking-tight leading-none mb-2">
              {overlay.title}
            </CardTitle>
            <span className="text-xs text-white/50 font-mono uppercase tracking-[0.3em]">
              Node: {overlay.nodeId || 'PRIMARY-V4'}
            </span>
          </div>
        </CardHeader>

        <CardContent className="p-8">
          <p className="text-zinc-300 text-lg leading-relaxed mb-10 font-bold">
            {overlay.description}
          </p>

          <div className="space-y-6">
            <div className="flex justify-between items-end">
              <div className="flex flex-col gap-2">
                <span className="text-xs text-zinc-500 font-black uppercase tracking-widest">Efficiency</span>
                <span className="text-3xl font-mono text-white tabular-nums font-black">
                  {progressValue.toFixed(1)}%
                </span>
              </div>
              <div className="flex gap-3 mb-2">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="w-2.5 h-2.5 rounded-full bg-blue-500/50 animate-pulse"
                    style={{ animationDelay: `${i * 0.15}s` }}
                  />
                ))}
              </div>
            </div>
            <Progress value={progressValue} className="h-3 bg-white/10 rounded-full" />

            <div className="pt-4 grid grid-cols-2 gap-6">
              <div className="bg-white/5 rounded-xl p-4 ring-1 ring-white/10">
                <span className="block text-xs text-zinc-500 uppercase font-black mb-2">Latency</span>
                <span className="text-lg font-mono text-emerald-400 font-bold">12ms</span>
              </div>
              <div className="bg-white/5 rounded-xl p-4 ring-1 ring-white/10">
                <span className="block text-xs text-zinc-500 uppercase font-black mb-2">Load</span>
                <span className="text-lg font-mono text-amber-400 font-bold">0.82</span>
              </div>
            </div>
          </div>
        </CardContent>

        {/* Scanning line effect */}
        <div
          className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-500/10 to-transparent h-40 w-full -translate-y-full animate-[scan_6s_linear_infinite]"
          style={{ animationDuration: '6s' }}
        />
      </Card>
    </div>
  );
};
