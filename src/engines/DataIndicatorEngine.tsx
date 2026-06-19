import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { ArrowUp, ArrowDown, Timer, Calendar, Flag, Activity } from 'lucide-react';

export const DataIndicatorEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  // Remotion-based timing for sync with camera
  const entrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const exitFrame = overlay.duration - 15;
  const exit = interpolate(
    relativeFrame,
    [exitFrame, exitFrame + 15],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const progress = entrance * exit;

  const renderIndicator = () => {
    switch (overlay.indicator_type) {
      case 'kpi':
      case 'kpiNumber':
        return <KPINumber overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'percentageCounter':
        return <PercentageCounter overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'comparisonKPI':
        return <ComparisonKPI overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'deltaIndicator':
        return <DeltaIndicator overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'timer':
      case 'countdown':
        return <Countdown overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'progressBar':
        return <ProgressBar overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'circularProgress':
        return <CircularProgress overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'semiGauge':
        return <SemiGauge overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'milestoneTracker':
        return <MilestoneTracker overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'dashboardCard':
        return <DashboardCard overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'timeline':
        return <EventTimeline overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'milestoneTimeline':
        return <MilestoneTimeline overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      default:
        return null;
    }
  };

  const x = overlay.position?.x ?? videoWidth / 2;
  const y = overlay.position?.y ?? videoHeight / 2;

  return (
    <div
      className="absolute flex items-center justify-center pointer-events-none"
      style={{
        left: `${x}px`,
        top: `${y}px`,
        transform: 'translate(-50%, -50%)',
        zIndex: overlay.zIndex ?? 50,
      }}
    >
      <div style={{
        opacity: progress,
        transform: `scale(${0.8 + progress * 0.2}) translateY(${(1 - exit) * -50}px)`,
        filter: `blur(${(1 - exit) * 10}px)`
      }}>
        {renderIndicator()}
      </div>
    </div>
  );
};

const DashboardCard = ({ overlay, relativeFrame, fps }: any) => {
  const value = interpolate(relativeFrame, [20, 80], [0, overlay.value || 0], { extrapolateRight: 'clamp' });
  return (
    <div className="bg-zinc-900/80 backdrop-blur-xl p-8 rounded-3xl border border-white/20 w-80 shadow-2xl overflow-hidden relative">
      <div className="absolute top-0 right-0 p-4 opacity-10">
         <Activity size={80} />
      </div>
      <h4 className="text-white/40 text-sm font-bold uppercase tracking-widest mb-2">{overlay.label}</h4>
      <div className="text-white text-5xl font-black mb-4 tabular-nums">
        {overlay.prefix}{Math.round(value).toLocaleString()}{overlay.suffix}
      </div>
      <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold">
         <ArrowUp size={16} />
         <span>{overlay.trend || '+12.5%'}</span>
         <span className="text-white/20">from last month</span>
      </div>
    </div>
  );
};

const EventTimeline = ({ overlay, relativeFrame, fps }: any) => {
  return (
    <div className="flex flex-col gap-8 w-[800px]">
      {overlay.events.map((event: any, i: number) => {
        const itemFrame = relativeFrame - i * 20;
        const reveal = spring({ frame: itemFrame, fps, config: { damping: 15 } });
        if (itemFrame < 0) return null;

        return (
          <div
            key={i}
            className="flex items-start gap-6"
            style={{ opacity: reveal, transform: `translateX(${(1-reveal) * -30}px)` }}
          >
            <div className="flex flex-col items-center">
               <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg border-2 border-white/20">
                  <Calendar color="white" size={32} />
               </div>
               {i < overlay.events.length - 1 && <div className="w-1 h-20 bg-white/10 my-2 rounded-full" />}
            </div>
            <div className="flex-1 bg-white/5 backdrop-blur-sm p-6 rounded-3xl border border-white/10">
               <span className="text-blue-400 font-mono text-sm font-bold uppercase tracking-widest">{event.date}</span>
               <h3 className="text-white text-2xl font-black mt-1">{event.title}</h3>
               <p className="text-white/60 text-lg mt-2 leading-relaxed">{event.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const MilestoneTimeline = ({ overlay, relativeFrame, fps }: any) => {
  return (
    <div className="flex items-center justify-between w-[1200px] relative">
      <div className="absolute top-1/2 left-0 w-full h-1 bg-white/10 -translate-y-1/2 rounded-full" />
      {overlay.milestones.map((m: any, i: number) => {
        const itemFrame = relativeFrame - i * 30;
        const reveal = spring({ frame: itemFrame, fps, config: { damping: 12 } });
        if (itemFrame < 0) return null;

        return (
          <div key={i} className="relative z-10 flex flex-col items-center" style={{ opacity: reveal, transform: `scale(${reveal})` }}>
            <div className="w-10 h-10 bg-indigo-600 rounded-full border-4 border-white/20 shadow-xl flex items-center justify-center">
               <Flag size={20} color="white" />
            </div>
            <div className="absolute top-12 flex flex-col items-center text-center w-48">
               <span className="text-indigo-400 font-black text-xs uppercase tracking-widest mb-1">{m.date}</span>
               <h4 className="text-white font-bold text-sm leading-tight">{m.title}</h4>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const ProgressBar = ({ overlay, relativeFrame, fps }: any) => {
  const progress = interpolate(relativeFrame, [10, 70], [0, overlay.value || 100], { extrapolateRight: 'clamp' });
  return (
    <div className="bg-zinc-900/90 backdrop-blur-xl p-10 rounded-3xl border border-white/10 w-[600px]">
      <div className="flex justify-between items-end mb-4">
        <span className="text-white text-2xl font-black uppercase tracking-widest">{overlay.label}</span>
        <span className="text-blue-400 text-4xl font-mono font-black">{Math.round(progress)}%</span>
      </div>
      <div className="h-6 w-full bg-white/10 rounded-full overflow-hidden border-2 border-white/5">
        <div
          className="h-full bg-gradient-to-r from-blue-600 to-indigo-400 shadow-[0_0_20px_rgba(37,99,235,0.6)]"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
};

const CircularProgress = ({ overlay, relativeFrame, fps }: any) => {
  const progress = interpolate(relativeFrame, [0, 80], [0, overlay.value || 100], { extrapolateRight: 'clamp' });
  return (
    <div className="relative flex items-center justify-center w-80 h-80">
      <div
        className="absolute inset-0 rounded-full border-[20px] border-white/5"
      />
      <div
        className="absolute inset-0 rounded-full border-[20px] border-transparent"
        style={{
          background: `conic-gradient(#3b82f6 ${progress}%, transparent 0)`,
          maskImage: 'radial-gradient(transparent 58%, black 60%)',
          WebkitMaskImage: 'radial-gradient(transparent 58%, black 60%)',
          filter: 'drop-shadow(0 0 15px rgba(59,130,246,0.5))'
        }}
      />
      <div className="flex flex-col items-center justify-center z-10">
         <span className="text-white text-7xl font-black tabular-nums">{Math.round(progress)}%</span>
         <span className="text-white/40 text-xs font-bold uppercase tracking-[0.2em]">{overlay.label}</span>
      </div>
    </div>
  );
};

const SemiGauge = ({ overlay, relativeFrame, fps }: any) => {
  const progress = interpolate(relativeFrame, [0, 90], [0, overlay.value || 100], { extrapolateRight: 'clamp' });
  const rotation = (progress / 100) * 180 - 90;

  return (
    <div className="relative w-[500px] h-[250px] overflow-hidden flex items-end justify-center">
      <div
        className="absolute top-0 w-[500px] h-[500px] rounded-full border-[40px] border-white/5"
      />
      <div
        className="absolute top-0 w-[500px] h-[500px] rounded-full border-[40px] border-transparent"
        style={{
          background: `conic-gradient(from 270deg, #ef4444, #eab308, #22c55e)`,
          maskImage: 'radial-gradient(transparent 58%, black 60%)',
          WebkitMaskImage: 'radial-gradient(transparent 58%, black 60%)',
          clipPath: 'polygon(0 0, 100% 0, 100% 50%, 0 50%)'
        }}
      />
      {/* Needle */}
      <div
        className="absolute bottom-0 w-2 h-48 bg-white origin-bottom rounded-full shadow-2xl z-20"
        style={{ transform: `rotate(${rotation}deg)` }}
      />
      <div className="absolute bottom-4 flex flex-col items-center">
         <div className="text-white text-5xl font-black">{overlay.value}{overlay.suffix}</div>
         <div className="text-white/40 text-sm font-bold uppercase">{overlay.label}</div>
      </div>
    </div>
  );
};

const MilestoneTracker = ({ overlay, relativeFrame, fps }: any) => {
  const activeIndex = Math.min(
    overlay.milestones.length - 1,
    Math.floor(interpolate(relativeFrame, [0, 100], [0, overlay.milestones.length], { extrapolateRight: 'clamp' }))
  );

  return (
    <div className="flex gap-4 items-center bg-black/40 backdrop-blur-md p-6 rounded-2xl border border-white/10">
      {overlay.milestones.map((m: any, i: number) => {
        const isActive = i <= activeIndex;
        const isCurrent = i === activeIndex;
        return (
          <React.Fragment key={i}>
            <div className="flex flex-col items-center gap-2">
              <div
                className={`w-12 h-12 rounded-full border-4 flex items-center justify-center transition-colors duration-300 ${
                  isActive ? 'bg-blue-600 border-white/40' : 'bg-zinc-800 border-white/10'
                } ${isCurrent ? 'scale-125 shadow-[0_0_20px_rgba(37,99,235,0.8)]' : ''}`}
              >
                <span className="text-white font-black text-sm">{i + 1}</span>
              </div>
              <span className={`text-[10px] font-bold uppercase whitespace-nowrap ${isActive ? 'text-white' : 'text-white/20'}`}>
                {m.label}
              </span>
            </div>
            {i < overlay.milestones.length - 1 && (
              <div className={`w-16 h-1 rounded-full ${i < activeIndex ? 'bg-blue-600' : 'bg-white/10'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const KPINumber = ({ overlay, relativeFrame, fps }: any) => {
  const value = interpolate(relativeFrame, [0, 45], [0, overlay.value || 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div className="flex flex-col items-center justify-center bg-zinc-900/80 backdrop-blur-xl p-12 rounded-[2.5rem] border border-white/20 shadow-2xl min-w-[400px]">
      <span className="text-white/50 text-xl font-mono uppercase tracking-[0.3em] mb-4 font-bold">{overlay.label}</span>
      <div className="text-white text-8xl font-black tracking-tighter tabular-nums">
        {Math.round(value).toLocaleString()}
        {overlay.suffix}
      </div>
    </div>
  );
};

const PercentageCounter = ({ overlay, relativeFrame, fps }: any) => {
  const value = interpolate(relativeFrame, [0, 60], [0, overlay.value || 0], {
    extrapolateRight: 'clamp',
  });

  return (
    <div className="flex items-center justify-center bg-blue-600 p-16 rounded-full shadow-[0_0_80px_rgba(37,99,235,0.4)] border-4 border-white/30">
       <div className="text-white text-9xl font-black tabular-nums">
         {Math.round(value)}%
       </div>
    </div>
  );
};

const ComparisonKPI = ({ overlay, relativeFrame, fps }: any) => {
  const v1 = interpolate(relativeFrame, [10, 50], [0, overlay.value1 || 0], { extrapolateRight: 'clamp' });
  const v2 = interpolate(relativeFrame, [20, 60], [0, overlay.value2 || 0], { extrapolateRight: 'clamp' });

  return (
    <div className="flex gap-12 bg-black/60 backdrop-blur-2xl p-10 rounded-3xl border border-white/10">
      <div className="flex flex-col items-center">
        <span className="text-white/40 text-sm font-bold uppercase mb-2">{overlay.label1}</span>
        <div className="text-white text-6xl font-black tabular-nums">{Math.round(v1).toLocaleString()}</div>
      </div>
      <div className="w-[2px] bg-white/10 self-stretch" />
      <div className="flex flex-col items-center">
        <span className="text-white/40 text-sm font-bold uppercase mb-2">{overlay.label2}</span>
        <div className="text-blue-400 text-6xl font-black tabular-nums">{Math.round(v2).toLocaleString()}</div>
      </div>
    </div>
  );
};

const DeltaIndicator = ({ overlay, relativeFrame, fps }: any) => {
  const progress = spring({ frame: relativeFrame, fps, config: { damping: 12 } });
  const isPositive = (overlay.value || 0) >= 0;

  return (
    <div className="flex items-center gap-6 bg-zinc-900 p-8 rounded-2xl border border-white/20">
      <div className={`${isPositive ? 'bg-emerald-500' : 'bg-rose-500'} p-4 rounded-xl`}>
        {isPositive ? <ArrowUp color="white" size={48} strokeWidth={3} /> : <ArrowDown color="white" size={48} strokeWidth={3} />}
      </div>
      <div className="flex flex-col">
        <span className="text-white/40 text-xs font-bold uppercase tracking-widest">{overlay.label || 'Change'}</span>
        <div className={`text-6xl font-black tabular-nums ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`} style={{ opacity: progress, transform: `translateX(${(1-progress) * -20}px)` }}>
          {isPositive ? '+' : ''}{overlay.value}%
        </div>
      </div>
    </div>
  );
};

const Countdown = ({ overlay, relativeFrame, fps }: any) => {
  const totalSeconds = overlay.seconds || 10;
  const currentSeconds = Math.max(0, totalSeconds - Math.floor(relativeFrame / fps));

  return (
    <div className="bg-rose-600 p-12 rounded-[3rem] shadow-[0_0_100px_rgba(225,29,72,0.5)] border-8 border-white/20 flex items-center gap-8">
      <Timer size={80} color="white" strokeWidth={2.5} className="animate-pulse" />
      <div className="flex flex-col">
        <span className="text-white/60 font-black text-2xl uppercase tracking-tighter">Time Remaining</span>
        <div className="text-white text-9xl font-black tabular-nums leading-none">
          {currentSeconds}s
        </div>
      </div>
    </div>
  );
};
