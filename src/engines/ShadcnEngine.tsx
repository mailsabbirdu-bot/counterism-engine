import React, { useMemo } from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, Easing, spring } from 'remotion';
import { safeNumber, isNumericValue, formatWithLocaleAndBangla } from '../lib/safeNumber';
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
        transform: `scale(${(0.9 + progress * 0.1) * 1.25}) translateY(${(1 - exit) * -50}px)`,
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
                    <Area type="monotone" dataKey="value" stroke={mainColor} strokeWidth={4} fillOpacity={1} fill="url(#areaFill)" />
                </AreaChart>
            );
        case 'neon_bar':
            return (
                <BarChart data={data}>
                    <XAxis dataKey="name" hide />
                    <Bar dataKey="value" fill={mainColor} radius={[10, 10, 0, 0]}>
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
                    <Line type="stepAfter" dataKey="value" stroke={mainColor} strokeWidth={4} dot={{ r: 6, fill: mainColor, strokeWidth: 2, stroke: '#000' }} />
                    <Line type="stepAfter" dataKey="value2" stroke={secondaryColor} strokeWidth={4} dot={{ r: 6, fill: secondaryColor, strokeWidth: 2, stroke: '#000' }} />
                </LineChart>
            );
        case 'radial_score':
            return (
                <RadialBarChart innerRadius="20%" outerRadius="100%" barSize={30} data={data}>
                    <RadialBar background dataKey="value" cornerRadius={15} fill={mainColor} />
                    <Legend iconSize={10} layout="vertical" verticalAlign="middle" align="right" />
                </RadialBarChart>
            );
        case 'radar_web':
            return (
                <RadarChart outerRadius="80%" data={data}>
                    <PolarGrid stroke="rgba(255,255,255,0.1)" />
                    <PolarAngleAxis dataKey="name" tick={{fill: '#fff', fontSize: 12}} />
                    <Radar dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.4} dot={{r: 4, fill: mainColor}} />
                </RadarChart>
            );
        case 'composed_tech':
            return (
                <ComposedChart data={data}>
                    <XAxis dataKey="name" hide />
                    <Area type="monotone" dataKey="value" fill={mainColor} fillOpacity={0.1} stroke="none" />
                    <Bar dataKey="value2" barSize={30} fill={secondaryColor} radius={[4, 4, 0, 0]} />
                    <Line type="monotone" dataKey="value" stroke={mainColor} strokeWidth={3} dot={{r: 5}} />
                </ComposedChart>
            );
        case 'pie_donut_glass':
            return (
                <PieChart>
                    <Pie data={data} innerRadius="60%" outerRadius="85%" paddingAngle={5} dataKey="value" cornerRadius={8}>
                        {data.map((_: any, i: number) => <Cell key={i} fill={i % 2 === 0 ? mainColor : secondaryColor} />)}
                    </Pie>
                </PieChart>
            );
        case 'scatter_bubble':
            return (
                <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <XAxis type="number" dataKey="x" hide />
                    <YAxis type="number" dataKey="y" hide />
                    <Scatter name="Data" data={data} fill={mainColor}>
                        {data.map((entry: any, index: number) => <Cell key={`cell-${index}`} fillOpacity={0.6} />)}
                    </Scatter>
                </ScatterChart>
            );
        case 'horizontal_pill_bar':
            return (
                <BarChart data={data} layout="vertical">
                    <XAxis type="number" hide />
                    <YAxis dataKey="name" type="category" hide />
                    <Bar dataKey="value" fill={mainColor} radius={20} barSize={20} />
                </BarChart>
            );
        case 'step_area':
            return (
                <AreaChart data={data}>
                    <Area type="step" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.3} strokeWidth={3} />
                </AreaChart>
            );
        case 'multi_bar_stack':
            return (
                <BarChart data={data}>
                    <Bar dataKey="value" stackId="a" fill={mainColor} />
                    <Bar dataKey="value2" stackId="a" fill={secondaryColor} radius={[10,10,0,0]} />
                </BarChart>
            );
        case 'curved_edge_line':
            return (
                <LineChart data={data}>
                    <Line type="basis" dataKey="value" stroke={mainColor} strokeWidth={5} dot={false} />
                </LineChart>
            );
        case 'double_radar':
            return (
                <RadarChart outerRadius="75%" data={data}>
                    <PolarGrid stroke="rgba(255,255,255,0.05)" />
                    <Radar name="A" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.5} />
                    <Radar name="B" dataKey="value2" stroke={secondaryColor} fill={secondaryColor} fillOpacity={0.5} />
                </RadarChart>
            );
        case 'funnel_glass':
            return (
                <FunnelChart>
                    <Funnel dataKey="value" data={data} isAnimationActive={false}>
                        <Legend />
                    </Funnel>
                </FunnelChart>
            );
        case 'vertical_stepper':
            return (
                <BarChart data={data}>
                    <Bar dataKey="value" fill={mainColor} radius={[5, 5, 5, 5]} barSize={10} />
                </BarChart>
            );
        case 'micro_sparkline':
            return (
                <LineChart data={data}>
                    <Line type="monotone" dataKey="value" stroke={mainColor} strokeWidth={4} dot={false} />
                </LineChart>
            );
        case 'grid_dots':
            return (
                <ScatterChart>
                    <XAxis type="category" dataKey="name" hide />
                    <YAxis type="number" dataKey="value" hide />
                    <Scatter data={data} fill={mainColor} shape="circle" />
                </ScatterChart>
            );
        case 'smooth_area_dual':
            return (
                <AreaChart data={data}>
                    <Area type="monotone" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.2} />
                    <Area type="monotone" dataKey="value2" stroke={secondaryColor} fill={secondaryColor} fillOpacity={0.2} />
                </AreaChart>
            );
        case 'bar_race_top':
            return (
                <BarChart data={data} layout="vertical">
                    <YAxis dataKey="name" type="category" hide />
                    <XAxis type="number" hide />
                    <Bar dataKey="value" fill={mainColor} radius={[0, 10, 10, 0]} />
                </BarChart>
            );
        case 'thick_line_glow':
            return (
                <LineChart data={data}>
                    <Line type="monotone" dataKey="value" stroke={mainColor} strokeWidth={8} dot={false} strokeLinecap="round" />
                </LineChart>
            );
        case 'layered_pies':
            return (
                <PieChart>
                    <Pie data={data} dataKey="value" outerRadius="40%" fill={mainColor} />
                    <Pie data={data} dataKey="value2" innerRadius="50%" outerRadius="80%" fill={secondaryColor} />
                </PieChart>
            );
        case 'range_area':
            return (
                <AreaChart data={data}>
                    <Area type="monotone" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.4} />
                </AreaChart>
            );
        case 'pixel_bars':
            return (
                <BarChart data={data}>
                    <Bar dataKey="value" fill={mainColor} barSize={4} />
                </BarChart>
            );
        case 'curved_scatter':
            return (
                <ScatterChart>
                    <Scatter data={data} fill={mainColor} line={{ stroke: mainColor, strokeWidth: 2 }} shape="diamond" />
                </ScatterChart>
            );
        case 'staircase_line':
            return (
                <LineChart data={data}>
                    <Line type="step" dataKey="value" stroke={mainColor} strokeWidth={4} />
                </LineChart>
            );
        case 'floating_bars':
            return (
                <BarChart data={data}>
                    <Bar dataKey="value" fill={mainColor} radius={10} barSize={40} />
                </BarChart>
            );
        case 'hollow_pie':
            return (
                <PieChart>
                    <Pie data={data} dataKey="value" innerRadius="80%" outerRadius="90%" fill={mainColor} stroke="none" />
                </PieChart>
            );
        case 'dual_axis_tech':
            return (
                <ComposedChart data={data}>
                    <Bar dataKey="value" fill={mainColor} opacity={0.3} />
                    <Line dataKey="value2" stroke={secondaryColor} strokeWidth={4} />
                </ComposedChart>
            );
        case 'jagged_peak':
            return (
                <AreaChart data={data}>
                    <Area type="linear" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.5} />
                </AreaChart>
            );
        case 'dot_matrix_chart':
            return (
                <ScatterChart>
                    <Scatter data={data} fill={mainColor} shape="square" />
                </ScatterChart>
            );
        default:
            return (
                <AreaChart data={data}>
                    <Area type="monotone" dataKey="value" stroke={mainColor} fill={mainColor} fillOpacity={0.2} />
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

    const renderValue = (val: any) => {
        if (val === undefined || val === null) return '8,420';
        if (typeof val === 'number') {
            return val.toLocaleString();
        }
        return String(val);
    };

    switch(type) {
        case 'metric_tile':
            return (
                <div className="bg-zinc-900/80 backdrop-blur-2xl p-6 rounded-3xl border border-white/10 w-64 shadow-xl">
                    <div className="flex justify-between items-start mb-4">
                        <div className="p-3 bg-blue-500/10 rounded-xl"><Activity className="text-blue-500" size={24} /></div>
                        <span className="text-emerald-400 text-xs font-bold bg-emerald-500/10 px-2 py-1 rounded-lg">+12.5%</span>
                    </div>
                    <p className="text-white/40 text-[10px] font-black uppercase tracking-widest leading-none">{overlay.label || 'CORE ACTIVITY'}</p>
                    <p className="text-white text-4xl font-black mt-2 tabular-nums tracking-tighter">{renderValue(overlay.value)}</p>
                </div>
            );
        case 'tech_badge':
            return (
                <div className="bg-blue-600 px-8 py-4 rounded-full flex items-center gap-4 shadow-[0_0_40px_rgba(37,99,235,0.4)] border-2 border-white/20">
                    <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center"><Zap size={20} className="text-white fill-white" /></div>
                    <div className="flex flex-col">
                        <span className="text-white/60 text-[8px] font-black uppercase tracking-tighter">{overlay.label || overlay.title || 'System Power'}</span>
                        <span className="text-white text-2xl font-black leading-none uppercase">{renderValue(overlay.value)}</span>
                    </div>
                </div>
            );
        case 'activity_ring':
            const targetVal = safeNumber(overlay.value, 75);
            const progress = interpolate(safeFrame, [10, 70], [0, targetVal], { extrapolateRight: 'clamp' });
            return (
                <div className="relative w-48 h-48 flex items-center justify-center">
                    <svg className="w-full h-full -rotate-90">
                        <circle cx="96" cy="96" r="80" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="12" />
                        <circle cx="96" cy="96" r="80" fill="none" stroke={mainColor} strokeWidth="12" strokeDasharray="502" strokeDashoffset={502 - (502 * progress / 100)} strokeLinecap="round" />
                    </svg>
                    <div className="absolute flex flex-col items-center">
                        <span className="text-white text-5xl font-black tabular-nums tracking-tighter">{formatWithLocaleAndBangla(progress, overlay.value)}%</span>
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
        case 'user_profile_stat':
            return (
                <div className="bg-white/5 backdrop-blur-md p-6 rounded-[2rem] border border-white/10 flex items-center gap-6 w-96">
                    <div className="w-20 h-20 bg-gradient-to-tr from-indigo-500 to-pink-500 rounded-full border-4 border-white/10 flex items-center justify-center"><User size={40} color="white" /></div>
                    <div className="flex flex-col">
                        <h3 className="text-white font-black text-2xl leading-none">mailsabbir</h3><p className="text-indigo-400 text-xs font-bold uppercase tracking-widest mt-1">Prime Member</p>
                        <div className="flex gap-4 mt-3">
                            <div><p className="text-white font-black text-lg leading-none">12.4K</p><p className="text-white/20 text-[8px] font-bold uppercase">Posts</p></div>
                            <div className="w-px h-6 bg-white/10" /><div><p className="text-white font-black text-lg leading-none">840</p><p className="text-white/20 text-[8px] font-bold uppercase">Following</p></div>
                        </div>
                    </div>
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
        case 'storage_pill':
            return (
                <div className="bg-zinc-950 p-6 rounded-full border border-white/10 w-96 flex items-center gap-4">
                    <div className="w-12 h-12 bg-indigo-500/20 rounded-full flex items-center justify-center"><HardDrive className="text-indigo-500" size={24} /></div>
                    <div className="flex-1">
                        <div className="flex justify-between mb-1"><span className="text-white text-[10px] font-black uppercase tracking-widest">NVMe Drive 0</span><span className="text-indigo-400 text-[10px] font-black">84%</span></div>
                        <div className="h-2 w-full bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-indigo-500 rounded-full shadow-[0_0_15px_rgba(99,102,241,0.6)]" style={{ width: '84%' }} /></div>
                    </div>
                </div>
            );
        case 'upload_cloud':
            return (
                <div className="bg-blue-600/10 border-2 border-dashed border-blue-500/40 p-8 rounded-[2.5rem] flex flex-col items-center gap-4 w-72">
                    <Cloud className="text-blue-500 animate-bounce" size={48} />
                    <div className="text-center"><p className="text-white font-black text-lg leading-tight uppercase">Uploading Assets</p><p className="text-blue-400 text-[10px] font-bold">42.5 MB / 100 MB</p></div>
                    <div className="w-full h-1 bg-white/5 rounded-full mt-2"><div className="h-full bg-blue-500 rounded-full" style={{ width: '42%' }} /></div>
                </div>
            );
        case 'score_board':
            return (
                <div className="flex items-center gap-4 bg-zinc-900/90 p-4 rounded-3xl border border-white/10 shadow-2xl">
                    <div className="bg-blue-600 p-4 rounded-2xl flex flex-col items-center min-w-[80px]"><span className="text-white text-[8px] font-black uppercase">Home</span><span className="text-white text-4xl font-black">2</span></div>
                    <span className="text-white/20 font-black text-2xl">:</span>
                    <div className="bg-rose-600 p-4 rounded-2xl flex flex-col items-center min-w-[80px]"><span className="text-white text-[8px] font-black uppercase">Away</span><span className="text-white text-4xl font-black">1</span></div>
                    <div className="px-4"><div className="w-2 h-2 bg-rose-500 rounded-full animate-ping mb-1" /><span className="text-white/40 text-[8px] font-black uppercase tracking-widest">LIVE</span></div>
                </div>
            );
        case 'notification_stack':
            return (
                <div className="flex flex-col gap-3 w-80">
                    <div className="bg-white/10 backdrop-blur-lg p-4 rounded-2xl border border-white/20 flex items-center gap-3 transform translate-x-4"><Bell className="text-yellow-400" size={20} /><div><p className="text-white font-bold text-xs">Security Alert</p><p className="text-white/40 text-[8px]">New login from Tokyo</p></div></div>
                    <div className="bg-white/5 backdrop-blur-md p-4 rounded-2xl border border-white/10 flex items-center gap-3"><Mail className="text-indigo-400" size={20} /><div><p className="text-white font-bold text-xs">New Message</p><p className="text-white/40 text-[8px]">You have 3 unread items</p></div></div>
                </div>
            );
        case 'data_ticker':
            return (
                <div className="bg-zinc-900 border-l-4 border-indigo-500 px-8 py-4 rounded-r-2xl shadow-xl w-64 flex flex-col">
                    <span className="text-indigo-400 text-[8px] font-black uppercase tracking-widest mb-1">Stock Ticker</span>
                    <div className="flex items-baseline gap-2"><span className="text-white text-3xl font-black tabular-nums">AAPL</span><span className="text-emerald-400 text-xs font-bold">+1.8%</span></div>
                </div>
            );
        case 'network_ping':
            return (
                <div className="bg-black/60 p-6 rounded-3xl border border-white/10 flex items-center gap-6 w-72">
                    <div className="relative"><Wifi className="text-blue-500" size={40} /><div className="absolute inset-0 animate-ping bg-blue-500/20 rounded-full scale-150" /></div>
                    <div className="flex flex-col"><span className="text-white font-black text-2xl leading-none tabular-nums">48 ms</span><span className="text-white/30 text-[8px] font-bold uppercase tracking-widest mt-1">Latency</span></div>
                </div>
            );
        case 'step_indicator_glass':
            return (
                <div className="flex items-center gap-4 bg-white/5 p-4 rounded-2xl border border-white/5">
                    {[1,2,3,4].map(i => (<div key={i} className={cn("w-10 h-10 rounded-xl flex items-center justify-center font-black text-sm", i <= safeNumber(overlay.value, 2) ? "bg-indigo-600 text-white shadow-lg" : "bg-white/5 text-white/20")}>{i}</div>))}
                </div>
            );
        case 'battery_pack':
            const batteryProgress = interpolate(safeFrame, [0, 80], [0, safeNumber(overlay.value, 100)], { extrapolateRight: 'clamp' });
            return (
                <div className="bg-zinc-900 p-6 rounded-3xl border border-white/10 flex items-center gap-6 w-64">
                    <div className="relative w-12 h-20 border-2 border-white/20 rounded-lg p-1">
                        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-6 h-3 bg-white/20 rounded-t-sm"/>
                        <div className="w-full bg-emerald-500 rounded-sm" style={{ height: `${batteryProgress}%`, marginTop: `${100 - batteryProgress}%` }}/>
                    </div>
                    <div className="flex flex-col">
                        <span className="text-white text-3xl font-black leading-none">{formatWithLocaleAndBangla(batteryProgress, overlay.value)}%</span>
                        <span className="text-white/20 text-[8px] font-bold uppercase mt-1">Power Cell</span>
                    </div>
                </div>
            );
        case 'media_controls':
            return (
                <div className="bg-white/5 backdrop-blur-xl p-4 rounded-full border border-white/10 flex items-center gap-6 shadow-2xl px-8">
                    <Music size={20} className="text-indigo-400" /><div className="flex gap-4 items-center"><Mic size={18} className="text-white/40"/><RefreshCw size={18} className="text-white/40"/><Volume2 size={20} className="text-white"/></div>
                </div>
            );
        case 'social_stats':
            return (
                <div className="bg-zinc-950 p-6 rounded-[2.5rem] border border-white/10 flex flex-col gap-4 w-64">
                    <div className="flex justify-between items-center"><Heart className="text-rose-500 fill-rose-500" size={24}/><Star className="text-yellow-400 fill-yellow-400" size={24}/><Share2 className="text-blue-400" size={24}/></div>
                    <div className="flex justify-between text-white font-black text-xl tabular-nums"><span>12.4K</span><span>842</span><span>2.1K</span></div>
                </div>
            );
        case 'tech_folder':
            return (
                <div className="bg-indigo-600/10 border-l-8 border-indigo-600 p-6 rounded-r-3xl w-80 shadow-xl flex items-center gap-6">
                    <Layers size={40} className="text-indigo-500" />
                    <div className="flex flex-col"><h4 className="text-white font-black text-lg uppercase tracking-tight">Asset Library</h4><p className="text-indigo-400 text-[10px] font-bold uppercase">124 Elements Loaded</p></div>
                </div>
            );
        case 'system_cpu':
            return (
                <div className="bg-zinc-900 p-8 rounded-[2rem] border border-white/10 flex flex-col items-center w-64">
                    <Cpu size={48} className="text-blue-500 mb-4 animate-pulse" />
                    <span className="text-white text-5xl font-black tabular-nums">3.4</span><span className="text-blue-400 text-[10px] font-bold uppercase tracking-widest mt-1">GHz CLOCK</span>
                </div>
            );
        case 'location_tag':
            return (
                <div className="bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/20 flex items-center gap-3 w-72 shadow-2xl">
                    <div className="w-10 h-10 bg-rose-500 rounded-xl flex items-center justify-center shadow-lg"><MapPin size={24} color="white" /></div>
                    <div className="flex flex-col"><span className="text-white font-black text-sm uppercase">Global Node</span><span className="text-rose-400 text-[8px] font-bold uppercase">40.7128° N, 74.0060° W</span></div>
                </div>
            );
        case 'search_bar_glass':
            return (
                <div className="bg-white/5 border border-white/10 p-4 rounded-2xl w-[500px] flex items-center gap-4 px-6 shadow-2xl">
                    <Search size={20} className="text-white/40" /><span className="text-white/20 font-medium italic">Searching system logs...</span>
                </div>
            );
        case 'badge_collection':
            return (
                <div className="flex gap-3">
                    <div className="w-14 h-14 bg-indigo-600 rounded-2xl flex items-center justify-center border-2 border-white/20 shadow-xl"><Trophy size={28} color="white"/></div>
                    <div className="w-14 h-14 bg-emerald-600 rounded-2xl flex items-center justify-center border-2 border-white/20 shadow-xl"><Zap size={28} color="white"/></div>
                    <div className="w-14 h-14 bg-rose-600 rounded-2xl flex items-center justify-center border-2 border-white/20 shadow-xl"><Shield size={28} color="white"/></div>
                </div>
            );
        case 'data_download':
            return (
                <div className="bg-zinc-900 p-6 rounded-3xl border border-white/10 flex items-center gap-6 w-80">
                    <div className="w-12 h-12 bg-white/5 rounded-full flex items-center justify-center"><Download size={24} className="text-emerald-500" /></div>
                    <div className="flex-1"><div className="flex justify-between mb-1"><span className="text-white text-[10px] font-black uppercase">Downloading</span><span className="text-emerald-500 text-[10px] font-black">42%</span></div><div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden"><div className="h-full bg-emerald-500 rounded-full" style={{ width: '42%' }} /></div></div>
                </div>
            );
        case 'wifi_radar':
            return (
                <div className="relative w-40 h-40 flex items-center justify-center">
                    <div className="absolute inset-0 border border-blue-500/20 rounded-full animate-ping" />
                    <div className="absolute inset-4 border border-blue-500/40 rounded-full animate-ping" style={{ animationDelay: '0.5s' }} />
                    <Wifi size={48} className="text-blue-500 relative z-10" />
                </div>
            );
        case 'system_lock':
            return (
                <div className="bg-rose-600/10 border-2 border-rose-500/40 p-6 rounded-full flex items-center gap-6 pr-10 shadow-2xl">
                    <div className="w-14 h-14 bg-rose-500 rounded-full flex items-center justify-center shadow-lg"><Lock size={28} color="white" /></div>
                    <div className="flex flex-col"><span className="text-white font-black text-xl uppercase tracking-tighter leading-none">Firewall</span><span className="text-rose-500 text-[10px] font-black uppercase tracking-widest mt-1">Secured</span></div>
                </div>
            );
        case 'clock_modern':
            return (
                <div className="bg-black/40 backdrop-blur-xl p-8 rounded-[3rem] border border-white/10 flex items-center gap-8 shadow-2xl">
                    <Clock size={48} className="text-indigo-400" />
                    <div className="flex flex-col"><span className="text-white text-6xl font-black tabular-nums tracking-tighter">14:28</span><span className="text-white/20 text-[10px] font-bold uppercase tracking-widest">Standard Time</span></div>
                </div>
            );
        case 'status_grid':
            return (
                <div className="grid grid-cols-4 gap-2 w-48">
                    {[...Array(16)].map((_, i) => (<div key={i} className={cn("w-full h-8 rounded-sm", Math.random() > 0.3 ? "bg-emerald-500" : "bg-white/5")} />))}
                </div>
            );
        case 'floating_icon_text':
            return (
                <div className="bg-white p-1 rounded-3xl shadow-2xl rotate-3">
                    <div className="bg-zinc-950 px-8 py-4 rounded-[1.4rem] flex items-center gap-4">
                        <Star className="text-yellow-400 fill-yellow-400" size={24} /><span className="text-white font-black text-xl uppercase tracking-tight">System Prime</span>
                    </div>
                </div>
            );
        case 'mini_stat_card':
            return (
                <div className="bg-zinc-900/60 p-4 rounded-2xl border border-white/5 flex items-center gap-4 w-48 shadow-lg">
                    <div className="w-2 h-10 bg-indigo-500 rounded-full" /><div className="flex flex-col"><span className="text-white/40 text-[8px] font-bold uppercase">IO Load</span><span className="text-white font-black text-2xl tabular-nums leading-none">84%</span></div>
                </div>
            );
        case 'activity_dots':
            return (
                <div className="flex gap-2 items-center bg-black/40 px-6 py-4 rounded-full border border-white/10">
                    <Activity size={18} className="text-emerald-500" /><div className="flex gap-1">{[...Array(10)].map((_, i) => (<div key={i} className="w-2 h-2 bg-emerald-500 rounded-full" style={{ opacity: Math.sin(safeFrame * 0.2 + i) * 0.4 + 0.6 }} />))}</div>
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
