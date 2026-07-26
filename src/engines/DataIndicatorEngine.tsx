import React from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';
import { safeNumber, isNumericValue, formatWithLocaleAndBangla } from '../lib/safeNumber';
import { ArrowUp, ArrowDown, Timer, Calendar, Flag, Activity, Zap, Shield, Cpu, Cloud, Globe, Database, Target, Trophy, Info } from 'lucide-react';

export const DataIndicatorEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();
  const start = safeNumber(overlay.start, 0);
  const duration = safeNumber(overlay.duration, 120);
  const relativeFrame = frame - start;

  if (frame < start || frame > start + duration) {
    return null;
  }

  const entrance = spring({
    frame: isNaN(relativeFrame) ? 0 : relativeFrame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const exitFrame = duration - 15;
  const exit = interpolate(
    isNaN(relativeFrame) ? 0 : relativeFrame,
    [exitFrame, exitFrame + 15],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const progress = entrance * exit;

  const renderIndicator = () => {
    switch (overlay.indicator_type) {
      case 'kpi':
      case 'counter':
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
      case 'statGrid':
        return <StatGrid overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'techMetric':
        return <TechMetric overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'dataWave':
        return <DataWave overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'scoreCard':
        return <ScoreCard overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'batteryLevel':
        return <BatteryLevel overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'pulseRadar':
        return <PulseRadar overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'multiProgress':
        return <MultiProgress overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'speedometer':
        return <Speedometer overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'ringChart':
        return <RingChart overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'statusBadge':
        return <StatusBadge overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'metricRing':
        return <MetricRing overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'floatingTag':
        return <FloatingTag overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      case 'stepIndicator':
        return <StepIndicator overlay={overlay} relativeFrame={relativeFrame} fps={fps} />;
      default:
        return null;
    }
  };

  const x = safeNumber(overlay.position?.x, videoWidth / 2);
  const y = safeNumber(overlay.position?.y, videoHeight / 2);

  return (
    <div
      className="absolute flex items-center justify-center pointer-events-none"
      style={{
        left: `${x}px`,
        top: `${y}px`,
        transform: 'translate(-50%, -50%)',
        zIndex: safeNumber(overlay.zIndex, 50),
      }}
    >
      <div style={{
        opacity: progress,
        transform: `scale(${(0.8 + progress * 0.2) * 1.35}) translateY(${(1 - exit) * -50}px)`,
        filter: `blur(${(1 - exit) * 10}px)`
      }}>
        {renderIndicator()}
      </div>
    </div>
  );
};

// --- NEW SLEEK INDICATORS ---

const StatGrid = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="grid grid-cols-2 gap-4 bg-zinc-900/60 backdrop-blur-2xl p-6 rounded-[2rem] border border-white/10 shadow-2xl" style={fontStyle}>
      {(overlay.stats || []).map((stat: any, i: number) => {
        const reveal = spring({ frame: safeFrame - i * 10, fps, config: { damping: 12 } });
        const targetValue = safeNumber(stat.value, 0);
        const val = interpolate(safeFrame - 20 - i * 10, [0, 50], [0, targetValue], { extrapolateRight: 'clamp' });

        return (
          <div key={i} className="p-4 bg-white/5 rounded-2xl border border-white/5" style={{ opacity: reveal, transform: `translateY(${(1-reveal)*20}px)` }}>
            <p className="text-white/40 text-[10px] font-bold uppercase tracking-widest">{stat.label}</p>
            <p className="text-white text-2xl font-black tabular-nums">
                {!isNumericValue(stat.value) ? stat.value : formatWithLocaleAndBangla(val, stat.value)}{stat.suffix}
            </p>
          </div>
        );
      })}
    </div>
  );
};

const TechMetric = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  const pulse = Math.sin(safeFrame * 0.1) * 0.1 + 0.9;
  const targetValue = safeNumber(overlay.value, 85);
  const val = interpolate(safeFrame, [10, 60], [0, targetValue], { extrapolateRight: 'clamp' });

  return (
    <div className="flex items-center gap-6 bg-blue-950/40 backdrop-blur-3xl p-8 rounded-full border-2 border-blue-500/30 shadow-[0_0_50px_rgba(59,130,246,0.2)]" style={fontStyle}>
       <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center shadow-lg animate-pulse" style={{ transform: `scale(${pulse})` }}>
          <Zap size={32} color="white" fill="white" />
       </div>
       <div className="flex flex-col">
          <span className="text-blue-400 text-xs font-black uppercase tracking-widest leading-none mb-1">{overlay.label || 'SYSTEM LOAD'}</span>
          <div className="text-white text-6xl font-black tabular-nums leading-none tracking-tighter">
            {!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(val, overlay.value)}%
          </div>
       </div>
    </div>
  );
};

const DataWave = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="flex flex-col items-center bg-black/40 backdrop-blur-md p-10 rounded-[3rem] border border-white/10" style={fontStyle}>
       <div className="flex gap-1 h-20 items-end mb-4">
          {[...Array(12)].map((_, i) => {
            const h = interpolate(Math.sin(safeFrame * 0.2 + i * 0.5), [-1, 1], [10, 60]);
            return <div key={i} className="w-3 bg-blue-500 rounded-full opacity-60" style={{ height: `${h}px` }} />;
          })}
       </div>
       <span className="text-white text-4xl font-black tabular-nums">{overlay.value}{overlay.suffix}</span>
       <span className="text-white/30 text-xs font-bold uppercase tracking-widest mt-1">{overlay.label}</span>
    </div>
  );
};

const BatteryLevel = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const targetValue = safeNumber(overlay.value, 100);
    const progress = interpolate(safeFrame, [0, 80], [0, targetValue], { extrapolateRight: 'clamp' });
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="flex flex-col items-center gap-4 bg-zinc-900/80 p-8 rounded-3xl border border-white/10" style={fontStyle}>
            <div className="w-24 h-40 border-4 border-white/20 rounded-xl relative p-1">
                <div className="absolute -top-4 left-1/2 -translate-x-1/2 w-8 h-4 bg-white/20 rounded-t-lg" />
                <div className="w-full bg-emerald-500 rounded-lg shadow-[0_0_30px_rgba(16,185,129,0.5)] transition-all" style={{ height: `${progress}%`, marginTop: `${100 - progress}%` }} />
            </div>
            <div className="text-center">
                <p className="text-white text-3xl font-black tabular-nums">{formatWithLocaleAndBangla(progress, overlay.value)}%</p>
                <p className="text-white/40 text-[10px] font-bold uppercase tracking-widest">{overlay.label || 'POWER'}</p>
            </div>
        </div>
    );
};

const ScoreCard = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  const targetValue = safeNumber(overlay.value, 10);
  const val = interpolate(safeFrame, [20, 70], [0, targetValue], { extrapolateRight: 'clamp' });
  return (
    <div className="bg-gradient-to-br from-indigo-600 to-purple-700 p-1 rounded-3xl shadow-2xl">
       <div className="bg-zinc-900/90 backdrop-blur-xl p-10 rounded-[1.4rem] flex flex-col items-center min-w-[280px]" style={fontStyle}>
          <Trophy size={48} className="text-yellow-400 mb-4" />
          <span className="text-white/40 text-xs font-bold uppercase tracking-widest mb-1">{overlay.label}</span>
          <span className="text-white text-8xl font-black tabular-nums tracking-tighter">{formatWithLocaleAndBangla(val, overlay.value, 1)}</span>
          <div className="h-1 w-20 bg-indigo-500 rounded-full mt-4" />
       </div>
    </div>
  );
};

const PulseRadar = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="relative w-64 h-64 flex items-center justify-center" style={fontStyle}>
            <div className="absolute inset-0 border-2 border-white/10 rounded-full" />
            <div className="absolute inset-8 border border-white/10 rounded-full" />
            <div className="absolute inset-16 border border-white/10 rounded-full" />
            <div className="absolute w-1 h-32 bg-gradient-to-t from-emerald-500 to-transparent origin-bottom" style={{ transform: `rotate(${safeFrame * 4}deg)` }} />
            <div className="z-10 bg-emerald-500/20 backdrop-blur-md p-4 rounded-2xl border border-emerald-500/40 text-center">
                <span className="text-emerald-400 text-xs font-black block mb-1 uppercase">Detected</span>
                <span className="text-white text-3xl font-black tabular-nums">{overlay.value || '124'}</span>
            </div>
        </div>
    );
};

const MultiProgress = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="flex flex-col gap-6 bg-black/40 backdrop-blur-xl p-10 rounded-[3rem] border border-white/10 w-96" style={fontStyle}>
            {(overlay.items || []).map((item: any, i: number) => {
                const targetValue = safeNumber(item.value, 0);
                const progress = interpolate(safeFrame - i * 15, [0, 60], [0, targetValue], { extrapolateRight: 'clamp' });
                return (
                    <div key={i} className="flex flex-col gap-2">
                        <div className="flex justify-between text-[10px] font-black uppercase text-white/40 tracking-widest">
                            <span>{item.label}</span>
                            <span>{formatWithLocaleAndBangla(progress, item.value)}%</span>
                        </div>
                        <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-blue-500 rounded-full" style={{ width: `${progress}%`, backgroundColor: item.color || '#3b82f6' }} />
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

const Speedometer = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const targetValue = safeNumber(overlay.value, 120);
    const val = interpolate(safeFrame, [10, 80], [0, targetValue], { extrapolateRight: 'clamp' });
    const rotation = (val / (overlay.max || 200)) * 240 - 120;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="relative w-80 h-80 flex flex-col items-center justify-center bg-zinc-900 rounded-full border-8 border-white/5 shadow-2xl overflow-hidden" style={fontStyle}>
            <div className="absolute inset-4 rounded-full border-2 border-white/5 border-dashed animate-spin" style={{ animationDuration: '20s' }} />
            <div className="text-white text-7xl font-black leading-none">{formatWithLocaleAndBangla(val, overlay.value)}</div>
            <div className="text-white/30 text-xs font-bold uppercase tracking-[0.3em] mt-2">{overlay.label || 'SPEED'}</div>
            <div className="absolute bottom-10 w-1 h-32 bg-rose-500 origin-top rounded-full shadow-[0_0_15px_rgba(244,63,94,0.8)]" style={{ transform: `rotate(${rotation}deg)` }} />
        </div>
    );
};

const RingChart = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="relative w-80 h-80 flex items-center justify-center" style={fontStyle}>
            {(overlay.rings || []).map((ring: any, i: number) => {
                const targetValue = safeNumber(ring.value, 0);
                const progress = interpolate(safeFrame - i * 20, [0, 80], [0, targetValue], { extrapolateRight: 'clamp' });
                const size = 280 - i * 45;
                return (
                    <div key={i} className="absolute rounded-full border-[12px] border-white/5" style={{
                        width: `${size}px`, height: `${size}px`,
                        background: `conic-gradient(${ring.color || '#3b82f6'} ${progress}%, transparent 0)`,
                        maskImage: 'radial-gradient(transparent 62%, black 64%)',
                        WebkitMaskImage: 'radial-gradient(transparent 62%, black 64%)',
                    }} />
                );
            })}
            <div className="flex flex-col items-center z-10">
                <span className="text-white text-5xl font-black tabular-nums">{overlay.value}</span>
                <span className="text-white/40 text-[10px] font-bold uppercase tracking-widest">{overlay.label}</span>
            </div>
        </div>
    );
};

const StatusBadge = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="bg-emerald-500/10 backdrop-blur-2xl px-10 py-6 rounded-full border-2 border-emerald-500/30 flex items-center gap-4 shadow-xl" style={fontStyle}>
            <div className="w-4 h-4 bg-emerald-500 rounded-full animate-ping" />
            <span className="text-emerald-400 font-black text-2xl uppercase tracking-tighter">{overlay.status || 'SYSTEM ONLINE'}</span>
        </div>
    );
};

const MetricRing = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    const progress = interpolate(safeFrame, [0, 60], [0, 360]);
    return (
        <div className="w-64 h-64 relative flex items-center justify-center" style={fontStyle}>
            <svg className="w-full h-full -rotate-90">
                <circle cx="128" cy="128" r="100" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="20" />
                <circle cx="128" cy="128" r="100" fill="none" stroke={overlay.color || "#3b82f6"} strokeWidth="20" strokeDasharray="628" strokeDashoffset={628 - (628 * (overlay.value || 75) / 100)} strokeLinecap="round" style={{ transition: 'stroke-dashoffset 1s ease' }} />
            </svg>
            <div className="absolute flex flex-col items-center">
                <span className="text-white text-6xl font-black">{overlay.value}%</span>
                <span className="text-white/30 text-[10px] font-bold uppercase">{overlay.label}</span>
            </div>
        </div>
    );
};

const FloatingTag = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const y = Math.sin(safeFrame * 0.05) * 15;
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="bg-white/10 backdrop-blur-lg px-8 py-4 rounded-2xl border border-white/20 flex items-center gap-3 shadow-2xl" style={{ ...fontStyle, transform: `translateY(${y}px)` }}>
            <Info size={24} className="text-blue-400" />
            <span className="text-white font-bold text-xl">{overlay.content || 'REAL-TIME DATA'}</span>
        </div>
    );
};

const StepIndicator = ({ overlay, relativeFrame, fps }: any) => {
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
    const currentStep = Math.min((overlay.steps || []).length, Math.floor(safeFrame / 30));
    const fontStyle = { fontFamily: overlay.font || 'Inter' };
    return (
        <div className="flex flex-col gap-4 bg-zinc-900/60 p-8 rounded-3xl border border-white/10" style={fontStyle}>
            {(overlay.steps || []).map((step: any, i: number) => (
                <div key={i} className="flex items-center gap-4 opacity-40 transition-all duration-500" style={{ opacity: i <= currentStep ? 1 : 0.2 }}>
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-black text-xs ${i <= currentStep ? 'bg-indigo-600 text-white' : 'bg-white/10 text-white/30'}`}>{i+1}</div>
                    <span className="text-white font-bold uppercase tracking-widest text-sm">{step}</span>
                </div>
            ))}
        </div>
    );
};


// --- EXISTING COMPONENTS (UPDATED WITH FONTS) ---

const DashboardCard = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue = safeNumber(overlay.value, 0);
  const value = interpolate(safeFrame, [20, 80], [0, targetValue], { extrapolateRight: 'clamp' });
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="bg-zinc-900/80 backdrop-blur-xl p-8 rounded-3xl border border-white/20 w-80 shadow-2xl overflow-hidden relative" style={fontStyle}>
      <div className="absolute top-0 right-0 p-4 opacity-10">
         <Activity size={80} />
      </div>
      <h4 className="text-white/40 text-sm font-bold uppercase tracking-widest mb-2" style={fontStyle}>{overlay.label}</h4>
      <div className="text-white text-5xl font-black mb-4 tabular-nums" style={fontStyle}>
        {overlay.prefix}{!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(value, overlay.value)}{overlay.suffix}
      </div>
      <div className="flex items-center gap-2 text-emerald-400 text-sm font-bold" style={fontStyle}>
         <ArrowUp size={16} />
         <span>{overlay.trend || '+12.5%'}</span>
         <span className="text-white/20">from last month</span>
      </div>
    </div>
  );
};

const EventTimeline = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="flex flex-col gap-8 w-[800px]" style={fontStyle}>
      {(overlay.events || []).map((event: any, i: number) => {
        const itemFrame = safeFrame - i * 20;
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
            <div className="flex-1 bg-white/5 backdrop-blur-sm p-6 rounded-3xl border border-white/10" style={fontStyle}>
               <span className="text-blue-400 text-sm font-bold uppercase tracking-widest" style={fontStyle}>{event.date}</span>
               <h3 className="text-white text-2xl font-black mt-1" style={fontStyle}>{event.title}</h3>
               <p className="text-white/60 text-lg mt-2 leading-relaxed" style={fontStyle}>{event.description}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const MilestoneTimeline = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="flex items-center justify-between w-[1200px] relative" style={fontStyle}>
      <div className="absolute top-1/2 left-0 w-full h-1 bg-white/10 -translate-y-1/2 rounded-full" />
      {(overlay.milestones || []).map((m: any, i: number) => {
        const itemFrame = safeFrame - i * 30;
        const reveal = spring({ frame: itemFrame, fps, config: { damping: 12 } });
        if (itemFrame < 0) return null;

        return (
          <div key={i} className="relative z-10 flex flex-col items-center" style={{ opacity: reveal, transform: `scale(${reveal})` }}>
            <div className="w-10 h-10 bg-indigo-600 rounded-full border-4 border-white/20 shadow-xl flex items-center justify-center">
               <Flag size={20} color="white" />
            </div>
            <div className="absolute top-12 flex flex-col items-center text-center w-48" style={fontStyle}>
               <span className="text-indigo-400 font-black text-xs uppercase tracking-widest mb-1" style={fontStyle}>{m.date}</span>
               <h4 className="text-white font-bold text-sm leading-tight" style={fontStyle}>{m.title}</h4>
            </div>
          </div>
        );
      })}
    </div>
  );
};

const ProgressBar = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue = safeNumber(overlay.value, 100);
  const progress = interpolate(safeFrame, [10, 70], [0, targetValue], { extrapolateRight: 'clamp' });
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="bg-zinc-900/90 backdrop-blur-xl p-10 rounded-3xl border border-white/10 w-[600px]" style={fontStyle}>
      <div className="flex justify-between items-end mb-4">
        <span className="text-white text-2xl font-black uppercase tracking-widest" style={fontStyle}>{overlay.label}</span>
        <span className="text-blue-400 text-4xl font-black" style={fontStyle}>{!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(progress, overlay.value)}%</span>
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
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue = safeNumber(overlay.value, 100);
  const progress = interpolate(safeFrame, [0, 80], [0, targetValue], { extrapolateRight: 'clamp' });
  const fontStyle = { fontFamily: overlay.font || 'Inter' };
  return (
    <div className="relative flex items-center justify-center w-80 h-80" style={fontStyle}>
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
      <div className="flex flex-col items-center justify-center z-10" style={fontStyle}>
         <span className="text-white text-7xl font-black tabular-nums" style={fontStyle}>{!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(progress, overlay.value)}%</span>
         <span className="text-white/40 text-xs font-bold uppercase tracking-[0.2em]" style={fontStyle}>{overlay.label}</span>
      </div>
    </div>
  );
};

const SemiGauge = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue = safeNumber(overlay.value, 100);
  const progress = interpolate(safeFrame, [0, 90], [0, targetValue], { extrapolateRight: 'clamp' });
  const rotation = (progress / 100) * 180 - 90;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };

  return (
    <div className="relative w-[500px] h-[250px] overflow-hidden flex items-end justify-center" style={fontStyle}>
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
      <div
        className="absolute bottom-0 w-2 h-48 bg-white origin-bottom rounded-full shadow-2xl z-20"
        style={{ transform: `rotate(${rotation}deg)` }}
      />
      <div className="absolute bottom-4 flex flex-col items-center" style={fontStyle}>
         <div className="text-white text-5xl font-black" style={fontStyle}>
            <span style={fontStyle}>{!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(progress, overlay.value)}</span>
            <span style={fontStyle}>{overlay.suffix}</span>
         </div>
         <div className="text-white/40 text-sm font-bold uppercase" style={fontStyle}>{overlay.label}</div>
      </div>
    </div>
  );
};

const MilestoneTracker = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const activeIndex = Math.min(
    (overlay.milestones || []).length - 1,
    Math.floor(interpolate(safeFrame, [0, 100], [0, (overlay.milestones || []).length], { extrapolateRight: 'clamp' }))
  );
  const fontStyle = { fontFamily: overlay.font || 'Inter' };

  return (
    <div className="flex gap-4 items-center bg-black/40 backdrop-blur-md p-6 rounded-2xl border border-white/10" style={fontStyle}>
      {(overlay.milestones || []).map((m: any, i: number) => {
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
                <span className="text-white font-black text-sm" style={fontStyle}>{i + 1}</span>
              </div>
              <span className={`text-[10px] font-bold uppercase whitespace-nowrap ${isActive ? 'text-white' : 'text-white/20'}`} style={fontStyle}>
                {m.label}
              </span>
            </div>
            {i < (overlay.milestones || []).length - 1 && (
              <div className={`w-16 h-1 rounded-full ${i < activeIndex ? 'bg-blue-600' : 'bg-white/10'}`} />
            )}
          </React.Fragment>
        );
      })}
    </div>
  );
};

const KPINumber = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue = safeNumber(overlay.value, 0);
  const value = interpolate(safeFrame, [0, 45], [0, targetValue], {
    extrapolateRight: 'clamp',
  });

  const font = overlay.font || 'Inter';
  const fontStyle = { fontFamily: font };

  return (
    <div className="flex flex-col items-center justify-center bg-zinc-900/80 backdrop-blur-xl p-12 rounded-[3rem] border border-white/20 shadow-2xl min-w-[500px]" style={fontStyle}>
      <span className="text-white/60 text-3xl uppercase tracking-[0.4em] mb-8 font-black" style={fontStyle}>{overlay.label}</span>
      <div className="text-9xl font-black tracking-tighter tabular-nums flex items-baseline" style={{ ...fontStyle, color: overlay.color || 'white' }}>
        <span style={fontStyle}>{!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(value, overlay.value)}</span>
        {overlay.suffix && <span className="ml-4 text-6xl" style={fontStyle}>{overlay.suffix}</span>}
      </div>
    </div>
  );
};

const PercentageCounter = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue = safeNumber(overlay.value, 0);
  const value = interpolate(safeFrame, [0, 60], [0, targetValue], {
    extrapolateRight: 'clamp',
  });
  const fontStyle = { fontFamily: overlay.font || 'Inter' };

  return (
    <div className="flex items-center justify-center bg-blue-600 p-16 rounded-full shadow-[0_0_80px_rgba(37,99,235,0.4)] border-4 border-white/30" style={{ ...fontStyle, backgroundColor: overlay.color || '#2563eb' }}>
       <div className="text-white text-9xl font-black tabular-nums" style={fontStyle}>
         {!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(value, overlay.value)}%
       </div>
    </div>
  );
};

const ComparisonKPI = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const targetValue1 = safeNumber(overlay.value1, 0);
  const targetValue2 = safeNumber(overlay.value2, 0);
  const v1 = interpolate(safeFrame, [10, 50], [0, targetValue1], { extrapolateRight: 'clamp' });
  const v2 = interpolate(safeFrame, [20, 60], [0, targetValue2], { extrapolateRight: 'clamp' });
  const fontStyle = { fontFamily: overlay.font || 'Inter' };

  return (
    <div className="flex gap-12 bg-black/60 backdrop-blur-2xl p-10 rounded-3xl border border-white/10" style={fontStyle}>
      <div className="flex flex-col items-center" style={fontStyle}>
        <span className="text-white/40 text-sm font-bold uppercase mb-2" style={fontStyle}>{overlay.label1}</span>
        <div className="text-white text-6xl font-black tabular-nums" style={fontStyle}>
            {!isNumericValue(overlay.value1) ? overlay.value1 : formatWithLocaleAndBangla(v1, overlay.value1)}
        </div>
      </div>
      <div className="w-[2px] bg-white/10 self-stretch" />
      <div className="flex flex-col items-center" style={fontStyle}>
        <span className="text-white/40 text-sm font-bold uppercase mb-2" style={fontStyle}>{overlay.label2}</span>
        <div className="text-blue-400 text-6xl font-black tabular-nums" style={fontStyle}>
            {!isNumericValue(overlay.value2) ? overlay.value2 : formatWithLocaleAndBangla(v2, overlay.value2)}
        </div>
      </div>
    </div>
  );
};

const DeltaIndicator = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const progress = spring({ frame: safeFrame, fps, config: { damping: 12 } });
  const targetValue = safeNumber(overlay.value, 0);
  const isPositive = targetValue >= 0;
  const fontStyle = { fontFamily: overlay.font || 'Inter' };

  return (
    <div className="flex items-center gap-6 bg-zinc-900 p-8 rounded-2xl border border-white/20" style={fontStyle}>
      <div className={`${isPositive ? 'bg-emerald-500' : 'bg-rose-500'} p-4 rounded-xl`}>
        {isPositive ? <ArrowUp color="white" size={48} strokeWidth={3} /> : <ArrowDown color="white" size={48} strokeWidth={3} />}
      </div>
      <div className="flex flex-col" style={fontStyle}>
        <span className="text-white/40 text-xs font-bold uppercase tracking-widest" style={fontStyle}>{overlay.label || 'Change'}</span>
        <div className={`text-6xl font-black tabular-nums ${isPositive ? 'text-emerald-400' : 'text-rose-400'}`} style={{ ...fontStyle, opacity: progress, transform: `translateX(${(1-progress) * -20}px)` }}>
          {isPositive ? '+' : ''}{!isNumericValue(overlay.value) ? overlay.value : formatWithLocaleAndBangla(targetValue, overlay.value)}%
        </div>
      </div>
    </div>
  );
};

const Countdown = ({ overlay, relativeFrame, fps }: any) => {
  const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;
  const totalSeconds = overlay.seconds || 10;
  const currentSeconds = Math.max(0, totalSeconds - Math.floor(safeFrame / fps));
  const fontStyle = { fontFamily: overlay.font || 'Inter' };

  return (
    <div className="bg-rose-600 p-12 rounded-[3rem] shadow-[0_0_100px_rgba(225,29,72,0.5)] border-8 border-white/20 flex items-center gap-8" style={fontStyle}>
      <Timer size={80} color="white" strokeWidth={2.5} className="animate-pulse" />
      <div className="flex flex-col" style={fontStyle}>
        <span className="text-white/60 font-black text-2xl uppercase tracking-tighter" style={fontStyle}>Time Remaining</span>
        <div className="text-white text-9xl font-black tabular-nums leading-none" style={fontStyle}>
          {currentSeconds}s
        </div>
      </div>
    </div>
  );
};
