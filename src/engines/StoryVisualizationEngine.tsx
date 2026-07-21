import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import { safeNumber } from '../lib/safeNumber';
import { ChartThemeBuilder } from '../lib/ChartThemeBuilder';
import { ChartRegistry } from '../lib/ChartRegistry';


// --- SEMANTIC REGISTRY ---
const SEMANTIC_ROLES: Record<string, string[]> = {
  trend: ['area', 'line', 'forecast', 'stream'],
  comparison: ['bar', 'horizontalBar', 'waffle', 'marimekko'],
  proportion: ['pie', 'donut', 'sunburst', 'treemap'],
  hierarchy: ['circlePacking', 'sunburst', 'treemap'],
  flow: ['sankey', 'chord', 'network'],
  distribution: ['boxplot', 'violinPlot', 'swarmplot', 'heatmap'],
  relationship: ['scatter', 'bubble', 'voronoi', 'radar']
};

const DOCUMENTARY_PRESETS: Record<string, any> = {
  nasa: { grid: true, scheme: 'cyan_blue', border: 'rgba(0,255,255,0.2)', glow: '#00F5FF', font: 'Audiowide', effects: ['scanlines', 'crosshairs'] },
  bloomberg: { grid: true, scheme: 'greens', border: 'rgba(0,255,0,0.1)', glow: '#10b981', font: 'Inter', effects: ['ticker'] },
  cyberpunk: { grid: true, scheme: 'red_grey', border: 'rgba(255,0,255,0.3)', glow: '#FF00FF', font: 'Orbitron', effects: ['chromatic', 'glitch'] },
  minimal_apple: { grid: false, scheme: 'nivo', border: 'rgba(255,255,255,0.05)', glow: '#fff', font: 'Inter', effects: ['blur'] },
  bbc: { grid: true, scheme: 'set1', border: 'rgba(255,255,255,0.1)', glow: '#fff', font: 'Inter', effects: ['vignette'] },
  military: { grid: true, scheme: 'reds', border: 'rgba(255,0,0,0.4)', glow: '#ff0000', font: 'Inter', effects: ['threat_overlay', 'coordinates'] },
  nat_geo: { grid: false, scheme: 'yellow_orange_brown', border: 'rgba(255,215,0,0.2)', glow: '#FFD700', font: 'Inter', effects: ['organic_grain'] },
  archive: { grid: false, scheme: 'greys', border: 'rgba(245,245,220,0.1)', glow: '#F5F5DC', font: 'Spectral', effects: ['film_scratches'] }
};

// Map legacy personalities to new presets
const CHART_PERSONALITIES: Record<string, any> = {
    ...DOCUMENTARY_PRESETS,
    scientific: DOCUMENTARY_PRESETS.nasa,
    financial: DOCUMENTARY_PRESETS.bloomberg,
    historical: DOCUMENTARY_PRESETS.bbc,
    futuristic: DOCUMENTARY_PRESETS.cyberpunk
};

const ChartAnnotationLayer: React.FC<{ overlay: any; activeHighlight: any; relativeFrame: number }> = ({ overlay, activeHighlight, relativeFrame }) => {
    if (!activeHighlight) return null;

    const reveal = interpolate(relativeFrame - activeHighlight.start, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const color = activeHighlight.color || '#fff';

    return (
        <div className="absolute inset-0 pointer-events-none z-30" style={{ opacity: reveal }}>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="px-6 py-2 bg-black/80 border-2 rounded-lg text-white font-black uppercase tracking-widest text-lg shadow-[0_0_30px_rgba(0,0,0,0.5)]" style={{ borderColor: color }}>
                    {activeHighlight.label}
                </div>
                {/* HUD Focal Line */}
                <div className="w-[1px] h-32 mx-auto mt-2" style={{ background: `linear-gradient(to bottom, ${color}, transparent)` }} />
            </div>
        </div>
    );
};

const SemanticVisualOverlays: React.FC<{ role: string; color: string; progress: number; frame: number }> = ({ role, color, progress, frame }) => {
    if (progress <= 0) return null;

    return (
        <div className="absolute inset-0 pointer-events-none overflow-hidden" style={{ opacity: progress * 0.4 }}>
            {role === 'trend' && (
                <div className="absolute inset-0">
                    {/* Floating Data Particles */}
                    {[...Array(5)].map((_, i) => (
                        <div
                            key={i}
                            className="absolute w-1 h-1 rounded-full bg-white"
                            style={{
                                left: `${(i * 25 + frame * 0.5) % 100}%`,
                                top: `${50 + Math.sin(frame * 0.05 + i) * 20}%`,
                                boxShadow: `0 0 10px white`
                            }}
                        />
                    ))}
                </div>
            )}

            {role === 'comparison' && (
                <div className="absolute left-10 top-0 bottom-0 w-8 border-l border-r border-white/10 flex flex-col justify-around py-10">
                    {[...Array(10)].map((_, i) => (
                        <div key={i} className="w-full h-[1px] bg-white/20" style={{ width: i % 5 === 0 ? '100%' : '50%' }} />
                    ))}
                </div>
            )}

            {role === 'proportion' && (
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] border border-white/5 rounded-full">
                    <div className="absolute inset-[-20px] border border-dashed border-white/5 rounded-full animate-spin" style={{ animationDuration: '20s' }} />
                </div>
            )}
        </div>
    );
};

const MountainMetaphor: React.FC<{ data: any; progress: number; color: string; font: string; emotion: string }> = ({ data, progress, color, font, emotion }) => {
    if (!Array.isArray(data) || data.length === 0) return null;
    const series = data[0].data || [];
    const width = 1000;
    const height = 400;

    const points = series.map((p: any, i: number) => {
        const x = (i / (series.length - 1)) * width;
        const y = height - (p.y * height / 100) * progress;
        return `${x},${y}`;
    }).join(' ');

    const path = `M 0,${height} L ${points} L ${width},${height} Z`;

    return (
        <div className="relative w-full h-full flex items-end">
            <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full overflow-visible">
                <defs>
                    <linearGradient id="mountainFill" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor={color} stopOpacity={0.6} />
                        <stop offset="100%" stopColor={color} stopOpacity={0} />
                    </linearGradient>
                    <filter id="peakGlow">
                        <feGaussianBlur stdDeviation="10" result="blur" />
                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                    </filter>
                </defs>

                {/* Mountain Silhouette */}
                <path d={path} fill="url(#mountainFill)" stroke={color} strokeWidth="3" filter="url(#peakGlow)" />

                {/* Data Labels at Peaks */}
                {series.map((p: any, i: number) => {
                    const x = (i / (series.length - 1)) * width;
                    const y = height - (p.y * height / 100) * progress;
                    if (i % 2 !== 0 || progress < 0.8) return null;
                    return (
                        <g key={i} transform={`translate(${x}, ${y - 20})`}>
                            <text fill="white" fontSize="14" fontWeight="900" textAnchor="middle" style={{ fontFamily: font }}>{p.y}</text>
                            <circle r="4" fill={color} />
                        </g>
                    );
                })}
            </svg>
            {/* Cinematic Fog */}
            <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60" />
        </div>
    );
};

const SkyscraperMetaphor: React.FC<{ data: any; progress: number; color: string; font: string }> = ({ data, progress, color, font }) => {
    if (!Array.isArray(data)) return null;
    return (
        <div className="flex items-end justify-around w-full h-full px-10 gap-4">
            {data.map((item: any, i: number) => {
                const h = (item.value || 0) * progress * 4;
                return (
                    <div key={i} className="relative flex flex-col items-center group" style={{ width: '80px' }}>
                        {/* Skyscraper Body */}
                        <div
                            className="w-full bg-zinc-900 border-t-4 border-x-2 relative shadow-2xl"
                            style={{ height: `${h}px`, borderColor: color, boxShadow: `0 0 30px ${color}33` }}
                        >
                            {/* Windows */}
                            <div className="grid grid-cols-2 gap-1 p-2 opacity-20">
                                {[...Array(Math.floor(h/20))].map((_, j) => <div key={j} className="h-1 bg-white/40" />)}
                            </div>
                            {/* Top Searchlight */}
                            {progress > 0.9 && (
                                <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-full w-[2px] h-40 bg-gradient-to-t from-white to-transparent opacity-40 blur-sm" />
                            )}
                        </div>
                        <span className="text-white font-black uppercase text-[10px] mt-4 tracking-widest text-center" style={{ fontFamily: font }}>{item.label || item.id}</span>
                    </div>
                );
            })}
        </div>
    );
};

export const StoryVisualizationEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight } = useVideoConfig();
  const start = safeNumber(overlay.start, 0);
  const duration = safeNumber(overlay.duration, 120);
  const relativeFrame = frame - start;

  if (frame < start || frame > start + duration) return null;

  // Cinematic HUD Animation
  const entrance = interpolate(relativeFrame, [0, 40], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.25, 0.1, 0.25, 1) });
  const exitFrame = duration - 15;
  const exit = interpolate(relativeFrame, [exitFrame, exitFrame + 15], [1, 0], { extrapolateLeft: 'clamp' });
  const masterProgress = entrance * exit;

  const personality = CHART_PERSONALITIES[overlay.personality || 'futuristic'];
  const role = overlay.semantic_role || 'trend';
  const type = overlay.chart_type || SEMANTIC_ROLES[role][0];
  const beat = overlay.story_beat || 'introduction';

  // --- GLOBAL ANIMATION STATES ---
  const stage1 = interpolate(relativeFrame, [10, 50], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

  let dataProgress = interpolate(relativeFrame, [40, 110], [0, 1], {
      extrapolateLeft: 'clamp', extrapolateRight: 'clamp',
      easing: beat === 'growth' ? Easing.bezier(0.8, 0, 0.2, 1) : Easing.bezier(0.33, 1, 0.68, 1)
  });

  if (beat === 'forecast') {
      dataProgress = interpolate(relativeFrame, [40, 150], [0, 1], { extrapolateLeft: 'clamp' });
  }

  const highlights = overlay.highlights || [];
  const activeHighlight = highlights.find((h: any) => frame >= h.start && frame <= h.start + h.duration);

  const renderChart = () => {
    const commonProps = ChartThemeBuilder(overlay, personality);

    if (!overlay?.data || (typeof overlay.data !== 'object')) {
        overlay.data = [{ id: "A", value: 10 }, { id: "B", value: 20 }];
    }

    // --- CHART DISPATCHER ---
    const renderDispatch = () => {
        let focusX = safeNumber(overlay.position?.x, videoWidth / 2);
        let focusY = safeNumber(overlay.position?.y, videoHeight / 2);

        // Attempt to get focus coordinates from data (Legacy behavior)
        if (Array.isArray(overlay.data) && overlay.data.length > 0) {
            const chartW = safeNumber(overlay.width, 1100);
            const chartH = safeNumber(overlay.height, 700);
            const margin = commonProps.margin;
            focusX = (overlay.position?.x - chartW/2) + margin.left + (chartW - margin.left - margin.right) * dataProgress;
        }

        const Renderer = ChartRegistry[type] || ChartRegistry.line;
        const content = <Renderer
            overlay={overlay}
            dataProgress={dataProgress}
            commonProps={commonProps}
            activeHighlight={activeHighlight}
            frame={frame}
            videoWidth={videoWidth}
            videoHeight={videoHeight}
        />;

        return { fX: focusX, fY: focusY, content };
    };

    const { content, fX, fY } = renderDispatch();

    return (
        <div className="w-full h-full relative">
            <div style={{ opacity: stage1 }} className="w-full h-full">{content}</div>
            <ChartAnnotationLayer overlay={overlay} activeHighlight={activeHighlight} relativeFrame={relativeFrame} />

            {/* Camera Tracking Focus Hub - Follows the leading data point of active series */}
            <div
                id="active-focus-pos"
                data-x={fX}
                data-y={fY}
                style={{ display: 'none' }}
            />
        </div>
    );
  };

  const renderLegacyChart = () => {
    const commonProps = ChartThemeBuilder(overlay, personality);

    const Renderer = ChartRegistry[type] || ChartRegistry.line;
    return <Renderer
        overlay={overlay}
        dataProgress={dataProgress}
        commonProps={commonProps}
        activeHighlight={activeHighlight}
        frame={frame}
        videoWidth={videoWidth}
        videoHeight={videoHeight}
    />;
  };

  const renderContent = () => {
    const font = overlay.font || 'Inter, sans-serif';
    const color = personality.glow;
    const metaphor = overlay.visual_metaphor;

    if (metaphor === 'mountain') return <MountainMetaphor data={overlay.data} progress={dataProgress} color={color} font={font} emotion={overlay.emotion} />;
    if (metaphor === 'skyscraper') return <SkyscraperMetaphor data={overlay.data} progress={dataProgress} color={color} font={font} />;

    if (['line', 'area', 'forecast', 'multiLine', 'stackedArea'].includes(type)) return renderChart();
    return renderLegacyChart();
  };

  return (
    <div
      className="absolute overflow-hidden p-12 rounded-[2rem]"
      style={{
        width: safeNumber(overlay.width, 1100),
        height: safeNumber(overlay.height, 700),
        left: `${safeNumber(overlay.position?.x, videoWidth / 2)}px`,
        top: `${safeNumber(overlay.position?.y, videoHeight / 2)}px`,
        opacity: masterProgress,
        zIndex: safeNumber(overlay.zIndex, 30),
        transform: `translate(-50%, -50%) scale(${0.9 + masterProgress * 0.1})`,
        background: 'rgba(5, 5, 5, 0.8)',
        backdropFilter: 'blur(20px)',
        border: `1px solid ${personality.border}`,
        boxShadow: `0 0 40px ${personality.glow}22`
      }}
    >
      {/* Background HUD Grid */}
      <div className="absolute inset-0 opacity-10 pointer-events-none" style={{
          backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)',
          backgroundSize: '40px 40px'
      }} />

      <div className="relative flex justify-between items-start mb-12 text-left">
        <div style={{ opacity: interpolate(relativeFrame, [10, 30], [0, 1], { extrapolateLeft: 'clamp' }) }}>
          <div className="flex items-center gap-3 mb-2">
              <div className="w-8 h-[2px]" style={{ background: personality.glow }} />
              <span className="text-[10px] font-black uppercase tracking-[0.4em]" style={{ color: personality.glow }}>{overlay.personality || 'System'} Telemetry</span>
          </div>
          <h3 className="text-white font-black text-4xl tracking-tighter leading-tight uppercase">{overlay.title || 'Data Analysis'}</h3>
        </div>

        {/* Technical Status Badge */}
        <div
            className="flex items-center gap-4 px-6 py-3 rounded-lg border bg-black/40"
            style={{
                borderColor: personality.border,
                opacity: interpolate(relativeFrame, [20, 40], [0, 1], { extrapolateLeft: 'clamp' })
            }}
        >
            <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: personality.glow }} />
            <span className="text-[10px] text-white/60 font-mono font-bold uppercase tracking-widest">Semantic: {role}</span>
        </div>
      </div>

      <div className="h-[calc(100%-140px)] w-full relative">
          <SemanticVisualOverlays role={role} color={personality.glow} progress={stage1} frame={frame} />

          {/* Documentary Effects Layer */}
          {personality.effects.includes('threat_overlay') && (
              <div className="absolute inset-0 bg-red-900/10 z-20 pointer-events-none mix-blend-overlay animate-pulse" />
          )}

          {personality.effects.includes('film_scratches') && (
              <div className="absolute inset-0 opacity-20 z-20 pointer-events-none" style={{ background: 'url(https://www.transparenttextures.com/patterns/p6.png)' }} />
          )}

          {personality.effects.includes('scanlines') && (
            <div className="absolute inset-0 pointer-events-none opacity-20 z-20" style={{
                backgroundImage: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
                backgroundSize: '100% 2px, 3px 100%'
            }} />
          )}

          {personality.effects.includes('crosshairs') && (
              <div className="absolute inset-0 pointer-events-none z-20 overflow-hidden opacity-30">
                  <div className="absolute top-0 left-0 w-10 h-10 border-t-2 border-l-2" style={{ borderColor: personality.glow }} />
                  <div className="absolute top-0 right-0 w-10 h-10 border-t-2 border-r-2" style={{ borderColor: personality.glow }} />
                  <div className="absolute bottom-0 left-0 w-10 h-10 border-b-2 border-l-2" style={{ borderColor: personality.glow }} />
                  <div className="absolute bottom-0 right-0 w-10 h-10 border-b-2 border-r-2" style={{ borderColor: personality.glow }} />
              </div>
          )}

          {/* Subtle Scanning Line */}
          <div className="absolute left-0 right-0 h-[1px] bg-white/10 z-20 pointer-events-none" style={{
              top: `${interpolate(frame % 120, [0, 120], [0, 100])}%`,
              boxShadow: `0 0 10px white`
          }} />
          {renderContent()}
      </div>
    </div>
  );
};
