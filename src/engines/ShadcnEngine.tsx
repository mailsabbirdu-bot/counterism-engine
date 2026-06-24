import React, { useMemo } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, Easing, spring } from 'remotion';
import { safeNumber } from '../lib/safeNumber';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, RadarChart, PolarGrid,
  PolarAngleAxis, Radar, ScatterChart, Scatter, RadialBarChart, RadialBar,
  ComposedChart, Legend, BarChart as ReBarChart, Cell as ReCell,
  Treemap, FunnelChart, Funnel, Sankey, ErrorBar
} from 'recharts';
import {
  Zap, Shield, Cpu, Activity, ArrowUp, ArrowDown, Globe, Database,
  Target, Trophy, Clock, Calendar, Flag, User, Mail, Settings,
  Search, Bell, Lock, Unlock, Camera, Video, Smartphone, Laptop,
  Server, HardDrive, Wifi, Bluetooth, Battery, MapPin, Navigation,
  ShoppingBag, CreditCard, BarChart3, PieChart as PieIcon, LineChart as LineIcon,
  Mic, Music, Headphones, Volume2, Share2, Heart, Star, Cloud, Download, Upload,
  RefreshCw, Layers, Grid, List, CheckCircle, AlertTriangle, XCircle, Info
} from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// --- SHADCN CHART ENGINE ---

export const ShadcnEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps, width: videoWidth, height: videoHeight } = useVideoConfig();
  const start = safeNumber(overlay.start, 0);
  const duration = safeNumber(overlay.duration, 120);
  const relativeFrame = frame - start;

  if (frame < start || frame > start + duration) return null;

  const entrance = spring({
    frame: isNaN(relativeFrame) ? 0 : relativeFrame,
    fps,
    config: { damping: 15, stiffness: 100 },
  });

  const exitFrame = duration - 15;
  const exit = interpolate(isNaN(relativeFrame) ? 0 : relativeFrame, [exitFrame, exitFrame + 15], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const progress = entrance * exit;

  const font = overlay.font || 'Inter, sans-serif';
  const dataProgress = interpolate(isNaN(relativeFrame) ? 0 : relativeFrame, [30, 90], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 1, 0.68, 1) });

  const renderContent = () => {
    if (overlay.type === 'shadcn_chart') return <ShadcnChart overlay={overlay} dataProgress={dataProgress} font={font} />;
    if (overlay.type === 'shadcn_indicator') return <ShadcnIndicator overlay={overlay} relativeFrame={relativeFrame} fps={fps} font={font} />;
    return null;
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
        transform: `scale(${0.9 + progress * 0.1}) translateY(${(1 - exit) * -50}px)`,
        filter: `blur(${(1 - exit) * 10}px)`,
        fontFamily: font
      }}>
        {renderContent()}
      </div>
    </div>
  );
};

// --- CHART VARIANTS (30+ PRESETS) ---

const ShadcnChart = ({ overlay, dataProgress, font }: any) => {
  const data = useMemo(() => {
    const raw = overlay.data || [{ name: 'A', value: 400, value2: 240 }, { name: 'B', value: 300, value2: 139 }, { name: 'C', value: 600, value2: 380 }];
    if (!Array.isArray(raw)) return raw;
    return raw.map(item => {
        const newItem = { ...item };
        Object.keys(item).forEach(key => {
            if (typeof item[key] === 'number') newItem[key] = item[key] * dataProgress;
        });
        return newItem;
    });
  }, [overlay.data, dataProgress]);

  const style = overlay.variant || 'modern_glass';
  const width = safeNumber(overlay.width, 800);
  const height = safeNumber(overlay.height, 500);

  return (
    <div className={cn(
      "p-8 rounded-[2.5rem] border border-white/10 shadow-2xl overflow-hidden flex flex-col",
      style === 'modern_glass' ? "bg-zinc-950/70 backdrop-blur-3xl" : "bg-black"
    )} style={{ width, height }}>
      <div className="mb-6 flex justify-between items-start text-left w-full">
        <div>
            <h3 className="text-white text-2xl font-black tracking-tight uppercase leading-tight">{overlay.title || 'Analytics'}</h3>
            <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-1">{overlay.subtitle || 'Real-time System Data'}</p>
        </div>
        <div className="bg-white/5 p-2 rounded-xl border border-white/5">
            <BarChart3 size={20} className="text-blue-500" />
        </div>
      </div>
      <div className="flex-1 w-full min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          {renderChartByType(overlay, data, font)}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const renderChartByType = (overlay: any, data: any, font: any) => {
    const type = overlay.chart_type || 'glass_area';
    const mainColor = overlay.color || '#3b82f6';
    const secondaryColor = overlay.color2 || '#8b5cf6';

    // HARDENING: Disable Recharts default transitions (isAnimationActive={false})
    // and rely on dataProgress (already mapped into data object above)

    switch(type) {
        case 'glass_area':
            return (
                <AreaChart data={data}>
                    <defs>
                        <linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor={mainColor} stopOpacity={0.4}/>
                            <stop offset="95%" stopColor={mainColor} stopOpacity={0}/>
                        </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{fill: '#666', fontSize: 10, fontFamily: font}} />
                    <YAxis axisLine={false} tickLine={false} tick={{fill: '#666', fontSize: 10, fontFamily: font}} />
                    <Area type="monotone" dataKey="value" stroke={mainColor} strokeWidth={4} fillOpacity={1} fill="url(#areaFill)" isAnimationActive={false} />
                </AreaChart>
            );
        case 'neon_bar':
            return (
                <BarChart data={data}>
                    <XAxis dataKey="name" hide />
                    <Bar dataKey="value" fill={mainColor} radius={[10, 10, 0, 0]} isAnimationActive={false}>
                        {data.map((entry: any, index: number) => (
                            <ReCell key={`cell-${index}`} fill={index % 2 === 0 ? mainColor : secondaryColor} fillOpacity={0.8} />
                        ))}
                    </Bar>
                </BarChart>
            );
        case 'stacked_line':
            return (
                <LineChart data={data}>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <Line type="stepAfter" dataKey="value" stroke={mainColor} strokeWidth={4} dot={{ r: 6, fill: mainColor, strokeWidth: 2, stroke: '#000' }} isAnimationActive={false} />
                    <Line type="stepAfter" dataKey="value2" stroke={secondaryColor} strokeWidth={4} dot={{ r: 6, fill: secondaryColor, strokeWidth: 2, stroke: '#000' }} isAnimationActive={false} />
                </LineChart>
            );
        case 'radial_score':
            return (
                <RadialBarChart innerRadius="20%" outerRadius="100%" barSize={30} data={data}>
                    <RadialBar background dataKey="value" cornerRadius={15} fill={mainColor} isAnimationActive={false} />
                    <Legend iconSize={10} layout="vertical" verticalAlign="middle" align="right" />
                </RadialBarChart>
            );
        case 'radar_web':
            return (
                <RadarChart outerRadius="80%" data={data}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="name" tick={{fill: '#fff', fontSize: 12}} />
                    <Radar dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.4} dot={{r: 4, fill: mainColor}} isAnimationActive={false} />
                </RadarChart>
            );
        case 'composed_tech':
            return (
                <ComposedChart data={data}>
                    <XAxis dataKey="name" hide />
                    <Area type="monotone" dataKey="value" fill={mainColor} fillOpacity={0.1} stroke="none" isAnimationActive={false} />
                    <Bar dataKey="value2" barSize={30} fill={secondaryColor} radius={[4, 4, 0, 0]} isAnimationActive={false} />
                    <Line type="monotone" dataKey="value" stroke={mainColor} strokeWidth={3} dot={{r: 5}} isAnimationActive={false} />
                </ComposedChart>
            );
        case 'pie_donut_glass':
            return (
                <PieChart>
                    <Pie data={data} innerRadius="60%" outerRadius="85%" paddingAngle={5} dataKey="value" cornerRadius={8} isAnimationActive={false}>
                        {data.map((_: any, i: number) => <Cell key={i} fill={i % 2 === 0 ? mainColor : secondaryColor} />)}
                    </Pie>
                </PieChart>
            );
        case 'scatter_bubble':
            return (
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <XAxis type="number" dataKey="x" hide />
                    <YAxis type="number" dataKey="y" hide />
                    <Scatter name="Data" data={data} fill={mainColor} isAnimationActive={false}>
                        {data.map((entry: any, index: number) => <Cell key={`cell-${index}`} fillOpacity={0.6} />)}
                    </Scatter>
                </ScatterChart>
            );
        case 'horizontal_pill_bar':
            return (
                <BarChart data={data} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" hide />
                    <Bar dataKey="value" fill={mainColor} radius={20} barSize={20} isAnimationActive={false} />
                </BarChart>
            );
        case 'step_area':
            return (
                <AreaChart data={data}>
                    <Area type="step" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.3} strokeWidth={3} isAnimationActive={false} />
                </AreaChart>
            );
        case 'multi_bar_stack':
            return (
                <BarChart data={data}>
                    <Bar dataKey="value" stackId="a" fill={mainColor} isAnimationActive={false} />
                    <Bar dataKey="value2" stackId="a" fill={secondaryColor} radius={[10,10,0,0]} isAnimationActive={false} />
                </BarChart>
            );
        case 'curved_edge_line':
            return (
                <LineChart data={data}>
                    <Line type="basis" dataKey="value" stroke={mainColor} strokeWidth={5} dot={false} isAnimationActive={false} />
                </LineChart>
            );
        case 'double_radar':
            return (
                <RadarChart outerRadius="75%" data={data}>
                    <PolarGrid stroke="rgba(255,255,255,0.05)" />
                    <Radar name="A" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.5} isAnimationActive={false} />
                    <Radar name="B" dataKey="value2" stroke={secondaryColor} fill={secondaryColor} fillOpacity={0.5} isAnimationActive={false} />
                </RadarChart>
            );
        default:
            return (
                <AreaChart data={data}>
                    <Area type="monotone" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.2} isAnimationActive={false} />
                </AreaChart>
            );
    }
};

// --- INDICATOR VARIANTS (30+ PRESETS) ---

const ShadcnIndicator = ({ overlay, relativeFrame, fps, font }: any) => {
    const type = overlay.indicator_type || 'metric_tile';
    const mainColor = overlay.color || '#3b82f6';
    const secondaryColor = overlay.color2 || '#8b5cf6';
    const safeFrame = isNaN(relativeFrame) ? 0 : relativeFrame;

    switch(type) {
        case 'metric_tile':
            return (
                <div className="bg-zinc-900/80 backdrop-blur-2xl p-6 rounded-3xl border border-white/10 w-64 shadow-xl">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-blue-500/10 rounded-xl"><Activity className="text-blue-500" size={24} /></div>
                        <span className="text-emerald-400 text-xs font-bold bg-emerald-500/10 px-2 py-1 rounded-lg">+12.5%</span>
                    </div>
                    <p className="text-white/40 text-[10px] font-black uppercase tracking-widest leading-none">{overlay.label || 'CORE ACTIVITY'}</p>
                    <p className="text-white text-4xl font-black mt-2 tabular-nums tracking-tighter">{Math.round(overlay.value || 8420).toLocaleString()}</p>
                </div>
            );
        case 'tech_badge':
            return (
                <div className="bg-blue-600 px-8 py-4 rounded-full flex items-center gap-4 shadow-[0_0_40px_rgba(37,99,235,0.4)] border-2 border-white/20">
                    <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center"><Zap size={20} className="text-white fill-white" /></div>
                    <div className="flex flex-col">
                        <span className="text-white/60 text-[8px] font-black uppercase tracking-tighter">System Power</span>
                        <span className="text-white text-2xl font-black leading-none uppercase">{overlay.value || 'Active'}</span>
                    </div>
                </div>
            );
        case 'activity_ring':
            const progress = interpolate(safeFrame, [10, 70], [0, overlay.value || 75], { extrapolateRight: 'clamp' });
            return (
                <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="w-full h-full -rotate-90">
                        <circle cx="96" cy="96" r="80" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
                        <circle cx="96" cy="96" r="80" fill="none" stroke={mainColor} strokeWidth="12" strokeDasharray="502" strokeDashoffset={502 - (502 * progress / 100)} strokeLinecap="round" />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                        <span className="text-white text-5xl font-black tabular-nums tracking-tighter">{Math.round(progress)}%</span>
                        <span className="text-white/30 text-[8px] font-bold uppercase tracking-widest">{overlay.label || 'LOAD'}</span>
                    </div>
                </div>
            );
        case 'crypto_card':
            return (
                <div className="bg-zinc-950 p-8 rounded-[2rem] border border-white/10 w-72 shadow-2xl flex flex-col gap-4">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 bg-orange-500/20 rounded-2xl flex items-center justify-center"><Database className="text-orange-500" size={28} /></div>
                        <div><p className="text-white font-black text-lg">BTC / USD</p><p className="text-white/30 text-[10px] font-bold uppercase">Bitcoin Network</p></div>
                    </div>
                    <div className="text-white text-4xl font-black tracking-tighter tabular-nums leading-none">$ {overlay.value || '64,281'}</div>
                    <div className="h-10 w-full bg-emerald-500/10 rounded-xl flex items-center px-4 justify-between border border-emerald-500/20">
                        <div className="flex items-center gap-1 text-emerald-400 font-bold text-xs"><ArrowUp size={14} /> 2.4%</div>
                        <div className="h-2 w-20 bg-emerald-500/40 rounded-full" />
                    </div>
                </div>
            );
        case 'server_status':
            return (
                <div className="bg-zinc-900 border border-white/10 p-6 rounded-3xl w-80 shadow-2xl overflow-hidden relative">
                    <div className="absolute top-0 right-0 p-4 opacity-10"><Server size={60} /></div>
                    <div className="flex items-center gap-2 mb-4">
                        <div className="w-3 h-3 bg-emerald-500 rounded-full animate-pulse" /><span className="text-emerald-500 text-xs font-black uppercase">Online</span>
                    </div>
                    <h4 className="text-white font-black text-xl mb-1 uppercase tracking-tight">Node Cluster A</h4>
                    <p className="text-white/30 text-[10px] font-bold uppercase mb-4">Response: 14ms</p>
                    <div className="flex gap-1">{[...Array(18)].map((_, i) => (<div key={i} className="h-6 w-2 bg-emerald-500/40 rounded-sm" style={{ opacity: Math.random() > 0.1 ? 1 : 0.2 }} />))}</div>
                </div>
            );
        case 'weather_glass':
            return (
                <div className="bg-white/10 backdrop-blur-2xl p-8 rounded-[3rem] border border-white/20 w-64 flex flex-col items-center shadow-2xl">
                    <Globe size={64} className="text-blue-400 mb-4 animate-spin" style={{ animationDuration: '10s' }} /><span className="text-white text-6xl font-black leading-none">24°C</span>
                    <span className="text-white/40 text-xs font-bold uppercase tracking-[0.3em] mt-2">Atmosphere</span>
                    <div className="w-full h-px bg-white/10 my-6" /><div className="flex justify-between w-full text-white/60 text-[10px] font-black uppercase"><span>Humidity</span><span>42%</span></div>
                </div>
            );
        case 'notification_stack':
            return (
                <div className="flex flex-col gap-3 w-80">
                    <div className="bg-white/10 backdrop-blur-lg p-4 rounded-2xl border border-white/20 flex items-center gap-3 transform translate-x-4"><Bell className="text-yellow-400" size={20} /><div><p className="text-white font-bold text-xs">Security Alert</p><p className="text-white/40 text-[8px]">New login from Tokyo</p></div></div>
                    <div className="bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 flex items-center gap-3"><Mail className="text-indigo-400" size={20} /><div><p className="text-white font-bold text-xs">New Message</p><p className="text-white/40 text-[8px]">You have 3 unread items</p></div></div>
                </div>
            );
        case 'network_ping':
            return (
                <div className="bg-black/60 p-6 rounded-3xl border border-white/10 flex items-center gap-6 w-72">
                    <div className="relative"><Wifi className="text-blue-500" size={40} /><div className="absolute inset-0 animate-ping bg-blue-500/20 rounded-full scale-150" /></div>
                    <div className="flex flex-col"><span className="text-white font-black text-2xl leading-none tabular-nums">48 ms</span><span className="text-white/30 text-[8px] font-bold uppercase tracking-widest mt-1">Latency</span></div>
                </div>
            );
        default:
            return (
                <div className="bg-zinc-900 p-8 rounded-3xl border border-white/10">
                    <p className="text-white/40 text-xs font-bold uppercase mb-2">{overlay.label}</p>
                    <p className="text-white text-5xl font-black tabular-nums">{overlay.value}</p>
                </div>
            );
    }
};
