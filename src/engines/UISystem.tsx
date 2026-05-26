import React from 'react';
import { interpolate, useCurrentFrame, spring, useVideoConfig } from 'remotion';
import { Terminal, ShieldCheck } from 'lucide-react';
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
    config: { damping: 12 }
  });

  const opacity = interpolate(relativeFrame, [0, 10], [0, 1]);
  const progressValue = interpolate(relativeFrame, [0, 60], [0, 100], { extrapolateRight: 'clamp' });

  return (
    <div
      className="absolute p-8"
      style={{
        left: overlay.position?.x ?? 50,
        top: overlay.position?.y ?? 50,
        opacity,
        transform: `scale(${entrance}) translateX(${(1 - entrance) * -50}px)`
      }}
    >
      <Card className={`
        w-[400px] backdrop-blur-xl bg-white/5 border-white/20 shadow-2xl
        ${overlay.variant === 'dark' ? 'bg-black/60' : ''}
      `}>
        <CardHeader className="flex flex-row items-center gap-3 space-y-0 p-6">
          <div className="p-2 bg-blue-500/20 rounded-lg">
            <Terminal className="text-blue-400 w-5 h-5" />
          </div>
          <CardTitle className="text-xl font-bold text-white tracking-tight">
            {overlay.title}
          </CardTitle>
        </CardHeader>

        <CardContent className="p-6 pt-0">
          <p className="text-white/70 text-sm leading-relaxed mb-6">
            {overlay.description}
          </p>

          <div className="space-y-3">
            <div className="flex justify-between items-center text-[10px] text-white/40 font-mono uppercase tracking-widest">
              <span>Core Status</span>
              <span className="text-green-400 flex items-center gap-1">
                 <ShieldCheck className="w-3 h-3" /> Encrypted
              </span>
            </div>
            <Progress value={progressValue} className="h-1 bg-white/10" />
          </div>
        </CardContent>
      </Card>
    </div>
  );
};
