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

  const opacity = interpolate(relativeFrame, [0, 15], [0, 1], { extrapolateRight: 'clamp' });

  // Dynamic progress value simulation
  const progressValue = interpolate(
    relativeFrame,
    [10, 80],
    [overlay.initialProgress || 0, overlay.targetProgress || 100],
    { extrapolateRight: 'clamp' }
  );

  const getIcon = (type: string) => {
    switch (type) {
      case 'terminal': return <Terminal className="text-blue-400 w-5 h-5" />;
      case 'security': return <ShieldCheck className="text-emerald-400 w-5 h-5" />;
      case 'activity': return <Activity className="text-rose-400 w-5 h-5" />;
      case 'cpu': return <Cpu className="text-amber-400 w-5 h-5" />;
      default: return <Box className="text-indigo-400 w-5 h-5" />;
    }
  };

  return (
    <div
      className="absolute p-8"
      style={{
        left: overlay.position?.x ?? 100,
        top: overlay.position?.y ?? 100,
        opacity,
        transform: `perspective(1000px) rotateY(${(1 - entrance) * 20}deg) scale(${0.9 + entrance * 0.1})`
      }}
    >
      <Card className={`
        w-[450px] overflow-hidden border-0 shadow-2xl
        ${overlay.variant === 'glass'
          ? 'bg-white/5 backdrop-blur-2xl ring-1 ring-white/20'
          : 'bg-zinc-950/80 ring-1 ring-zinc-800'}
      `}>
        {/* Glow effect */}
        <div className="absolute -top-24 -left-24 w-48 h-48 bg-blue-500/20 blur-[100px] pointer-events-none" />

        <CardHeader className="flex flex-row items-center gap-4 space-y-0 p-6 border-b border-white/5 bg-white/5">
          <div className="p-2.5 bg-white/5 rounded-xl ring-1 ring-white/10 shadow-inner">
            {getIcon(overlay.iconType)}
          </div>
          <div className="flex flex-col">
            <CardTitle className="text-lg font-bold text-white tracking-tight leading-none mb-1">
              {overlay.title}
            </CardTitle>
            <span className="text-[10px] text-white/40 font-mono uppercase tracking-[0.2em]">
              Node: {overlay.nodeId || 'PRIMARY-V4'}
            </span>
          </div>
        </CardHeader>

        <CardContent className="p-6">
          <p className="text-zinc-400 text-sm leading-relaxed mb-8 font-medium">
            {overlay.description}
          </p>

          <div className="space-y-4">
            <div className="flex justify-between items-end">
              <div className="flex flex-col gap-1">
                <span className="text-[9px] text-zinc-500 font-bold uppercase tracking-widest">Efficiency</span>
                <span className="text-xl font-mono text-white tabular-nums">
                  {progressValue.toFixed(1)}%
                </span>
              </div>
              <div className="flex gap-2">
                {[...Array(3)].map((_, i) => (
                  <div
                    key={i}
                    className="w-1.5 h-1.5 rounded-full bg-blue-500/40 animate-pulse"
                    style={{ animationDelay: `${i * 0.2}s` }}
                  />
                ))}
              </div>
            </div>
            <Progress value={progressValue} className="h-1.5 bg-white/5" />

            <div className="pt-2 grid grid-cols-2 gap-4">
              <div className="bg-white/5 rounded-lg p-3 ring-1 ring-white/5">
                <span className="block text-[8px] text-zinc-500 uppercase mb-1">Latency</span>
                <span className="text-xs font-mono text-emerald-400">12ms</span>
              </div>
              <div className="bg-white/5 rounded-lg p-3 ring-1 ring-white/5">
                <span className="block text-[8px] text-zinc-500 uppercase mb-1">Load</span>
                <span className="text-xs font-mono text-amber-400">0.82</span>
              </div>
            </div>
          </div>
        </CardContent>

        {/* Scanning line effect */}
        <div
          className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-500/5 to-transparent h-20 w-full -translate-y-full animate-[scan_4s_linear_infinite]"
          style={{ animationDuration: '4s' }}
        />
      </Card>
    </div>
  );
};
