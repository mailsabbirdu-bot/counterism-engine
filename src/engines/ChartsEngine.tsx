import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, Easing } from 'remotion';
import { safeNumber } from '../lib/safeNumber';
import { ResponsiveLine } from '@nivo/line';
import { ResponsiveBar } from '@nivo/bar';
import { ResponsivePie } from '@nivo/pie';
import { ResponsiveTreeMap } from '@nivo/treemap';
import { ResponsiveSunburst } from '@nivo/sunburst';
import { ResponsiveBoxPlot } from '@nivo/boxplot';
import { ResponsiveScatterPlot } from '@nivo/scatterplot';
import { ResponsiveSankey } from '@nivo/sankey';
import { ResponsiveChord } from '@nivo/chord';
import { ResponsiveNetwork } from '@nivo/network';
import { ResponsiveBump } from '@nivo/bump';
import { ResponsiveAreaBump } from '@nivo/bump';
import { ResponsiveHeatMap } from '@nivo/heatmap';
import { ResponsiveRadar } from '@nivo/radar';
import { ResponsiveRadialBar } from '@nivo/radial-bar';
import { ResponsiveStream } from '@nivo/stream';
import { ResponsiveSwarmPlot } from '@nivo/swarmplot';
import { ResponsiveWaffle } from '@nivo/waffle';
import { ResponsiveFunnel } from '@nivo/funnel';
import { ResponsiveMarimekko } from '@nivo/marimekko';
import { ResponsiveCalendar } from '@nivo/calendar';
import { ResponsiveCirclePacking } from '@nivo/circle-packing';
import { ResponsiveVoronoi } from '@nivo/voronoi';
import { ResponsiveParallelCoordinates } from '@nivo/parallel-coordinates';

const ViolinPlot: React.FC<{ overlay: any; dataProgress: number; commonProps: any }> = ({ overlay, dataProgress }) => {
  if (!overlay?.data || !Array.isArray(overlay.data)) return null;
  return (
    <div className="flex justify-around items-center h-full w-full px-10">
       {overlay.data.map((group: any, i: number) => (
            <div key={i} className="relative flex flex-col items-center" style={{ width: '100px' }}>
               <div
                  className="bg-gradient-to-b from-blue-500/60 via-indigo-500/80 to-blue-500/60 border-2 border-white/30 shadow-[0_0_30px_rgba(59,130,246,0.3)]"
                  style={{
                    width: '60px',
                    height: `${(group.value || 0) * 4 * dataProgress}px`,
                    borderRadius: '50% 50% 50% 50% / 80% 80% 20% 20%',
                    transform: 'scaleX(1.2)',
                  }}
               />
               <div className="w-[2px] h-[300px] absolute bg-white/10 -z-10" />
               <span className="text-white/80 text-xs mt-6 font-black uppercase tracking-tighter" style={{ fontFamily: overlay.font || 'Inter' }}>{group.label}</span>
            </div>
       ))}
    </div>
  );
};

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

const CHART_PERSONALITIES: Record<string, any> = {
  scientific: { grid: true, scheme: 'cyan_blue', opacity: 0.8, border: 'rgba(34,211,238,0.3)', glow: '#22d3ee' },
  financial: { grid: true, scheme: 'greens', opacity: 0.9, border: 'rgba(16,185,129,0.3)', glow: '#10b981' },
  historical: { grid: false, scheme: 'red_grey', opacity: 0.7, border: 'rgba(245,158,11,0.2)', glow: '#f59e0b' },
  futuristic: { grid: true, scheme: 'nivo', opacity: 0.6, border: 'rgba(255,255,255,0.1)', glow: '#fff' }
};

const ChartAnnotationLayer: React.FC<{ overlay: any; activeHighlight: any; relativeFrame: number }> = ({ overlay, activeHighlight, relativeFrame }) => {
    if (!activeHighlight) return null;

    const reveal = interpolate(relativeFrame - activeHighlight.start, [0, 15], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
    const color = activeHighlight.color || '#fff';

    return (
        <div className="absolute inset-0 pointer-events-none z-30" style={{ opacity: reveal }}>
            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                <div className="px-6 py-2 bg-black/80 border-2 rounded-lg text-white font-black uppercase tracking-widest text-lg" style={{ borderColor: color }}>
                    {activeHighlight.label}
                </div>
                <div className="w-1 h-20 mx-auto mt-2" style={{ background: `linear-gradient(to bottom, ${color}, transparent)` }} />
            </div>
        </div>
    );
};

export const ChartsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps, width: videoWidth, height: videoHeight } = useVideoConfig();
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

  const renderChart = () => {
    const font = overlay.font || 'Inter, sans-serif';
    const commonProps = {
      theme: {
        axis: {
          ticks: { text: { fill: '#ffffff80', fontSize: 16, fontFamily: font, fontWeight: 'bold' } },
          legend: { text: { fill: '#ffffffe0', fontSize: 20, fontFamily: font, fontWeight: '900' } }
        },
        grid: { line: { stroke: 'rgba(255,255,255,0.05)', strokeWidth: personality.grid ? 1 : 0 } },
        tooltip: { container: { background: '#09090b', color: '#fff', fontSize: 18, fontFamily: font, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' } },
        labels: { text: { fontSize: 14, fontWeight: 'bold', fill: '#fff', fontFamily: font } },
      },
      colors: overlay.colors || { scheme: personality.scheme },
      margin: { top: 40, right: 40, bottom: 60, left: 80 },
      animate: false,
    };

    // Staged Animation State
    const stage1 = interpolate(relativeFrame, [20, 60], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }); // Grid/Axes
    const stage2 = interpolate(relativeFrame, [50, 120], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 1, 0.68, 1) }); // Data
    const dataProgress = stage2;

    const highlights = overlay.highlights || [];
    const activeHighlight = highlights.find((h: any) => frame >= h.start && frame <= h.start + h.duration);

    if (!overlay?.data || (typeof overlay.data !== 'object')) {
        overlay.data = [{ id: "A", value: 10 }, { id: "B", value: 20 }];
    }

    // --- CHART DISPATCHER ---
    const renderDispatch = () => {
        if (['line', 'area', 'forecast', 'multiLine', 'stackedArea'].includes(type)) {
            const isFlat = Array.isArray(overlay.data) && overlay.data.length > 0 && !overlay.data[0].data;
            const seriesArray = isFlat ? [{ id: overlay.title || 'Data', data: overlay.data }] : (Array.isArray(overlay.data) ? overlay.data : []);

            const animatedData = seriesArray.map((series: any) => {
                if (!series || !Array.isArray(series.data)) return { id: 'Empty', data: [] };
                const isSeriesHighlighted = activeHighlight && series.id === activeHighlight.seriesId;
                const seriesOpacity = activeHighlight ? (isSeriesHighlighted ? 1 : 0.2) : 1;

                return {
                    ...series,
                    color: isSeriesHighlighted ? activeHighlight.color : series.color,
                    data: series.data.map((p: any, i: number) => {
                        const reveal = interpolate(dataProgress * series.data.length, [i, i + 0.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                        const y = typeof p.y === 'number' ? p.y : (p[overlay.keys?.[0] || 'value'] || 0);
                        return { ...p, x: p.x || p.year || p.label || i, y: y * reveal, opacity: seriesOpacity };
                    })
                };
            });

            return (
                <ResponsiveLine
                    {...commonProps}
                    data={animatedData}
                    xScale={{ type: 'point' }}
                    yScale={{ type: 'linear', min: overlay.minY ?? 0, max: overlay.maxY ?? 'auto', stacked: type === 'stackedArea' }}
                    curve={overlay.curve || "monotoneX"}
                    enableArea={['area', 'forecast', 'stackedArea'].includes(type)}
                    areaOpacity={0.25}
                    pointSize={type === 'forecast' ? 0 : 8}
                    pointColor="#09090b"
                    pointBorderWidth={2}
                    pointBorderColor={{ from: 'serieColor' }}
                    enableGridX={false}
                    lineWidth={4}
                    enableSlices="x"
                />
            );
        }
        return null;
    };

    return (
        <div className="w-full h-full relative">
            <div style={{ opacity: stage1 }}>{renderDispatch()}</div>
            <ChartAnnotationLayer overlay={overlay} activeHighlight={activeHighlight} relativeFrame={relativeFrame} />
        </div>
    );
  };

  const renderLegacyChart = () => {
    const font = overlay.font || 'Inter, sans-serif';
    const commonProps = {
      theme: {
        axis: {
          ticks: { text: { fill: '#ffffff80', fontSize: 16, fontFamily: font, fontWeight: 'bold' } },
          legend: { text: { fill: '#ffffffe0', fontSize: 20, fontFamily: font, fontWeight: '900' } }
        },
        grid: { line: { stroke: 'rgba(255,255,255,0.05)', strokeWidth: personality.grid ? 1 : 0 } },
        tooltip: { container: { background: '#09090b', color: '#fff', fontSize: 18, fontFamily: font, borderRadius: 8, border: '1px solid rgba(255,255,255,0.1)' } },
        labels: { text: { fontSize: 14, fontWeight: 'bold', fill: '#fff', fontFamily: font } },
      },
      colors: overlay.colors || { scheme: personality.scheme },
      margin: { top: 40, right: 40, bottom: 60, left: 80 },
      animate: false,
    };

    const stage2 = interpolate(relativeFrame, [50, 120], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 1, 0.68, 1) });
    const dataProgress = stage2;

    if (['bar', 'horizontalBar', 'verticalBar', 'groupedBar', 'stackedBar', 'barRace'].includes(type)) {
       if (!Array.isArray(overlay.data)) return null;
       const keys = overlay.keys || ['value'];
       const animatedData = overlay.data.map((item: any) => {
         const newItem = { ...item };
         keys.forEach((key: string) => { newItem[key] = (Number(item[key]) || 0) * dataProgress; });
         return newItem;
       });
       return (
         <ResponsiveBar
           {...commonProps}
           data={animatedData}
           keys={keys}
           indexBy={overlay.indexBy || 'id'}
           layout={type === 'horizontalBar' ? 'horizontal' : 'vertical'}
           groupMode={type === 'groupedBar' ? 'grouped' : 'stacked'}
           padding={0.4}
           borderRadius={8}
           borderWidth={2}
           borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
         />
       );
    }

    if (['pie', 'donut'].includes(type)) {
       if (!Array.isArray(overlay.data)) return null;
       const animatedData = overlay.data.map((item: any) => ({ ...item, value: (item.value || 0) * dataProgress }));
       return <ResponsivePie {...commonProps} data={animatedData} innerRadius={type === 'donut' ? 0.6 : 0} padAngle={0.7} cornerRadius={3} />;
    }

    if (type === 'bump' || type === 'areaBump') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((series: any) => ({
            ...series,
            data: (series.data || []).map((p: any, i: number) => {
                const reveal = interpolate(dataProgress * series.data.length, [i, i + 0.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                return { ...p, y: (p.y || 0) * reveal };
            })
        }));
        return type === 'bump' ? <ResponsiveBump {...commonProps} data={animatedData} /> : <ResponsiveAreaBump {...commonProps} data={animatedData} />;
    }

    if (type === 'heatmap') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((row: any) => ({
            ...row,
            data: (row.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }))
        }));
        return <ResponsiveHeatMap {...commonProps} data={animatedData} colors="blues" />;
    }

    if (type === 'radar') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((item: any) => {
            const newItem = { ...item };
            (overlay.keys || ['value']).forEach((k: string) => { newItem[k] = (item[k] || 0) * dataProgress; });
            return newItem;
        });
        return <ResponsiveRadar {...commonProps} data={animatedData} keys={overlay.keys || ['value']} indexBy={overlay.indexBy || 'id'} />;
    }

    if (type === 'radialBar') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((series: any) => ({
            ...series,
            data: (series.data || []).map((d: any) => ({ ...d, y: (d.y || 0) * dataProgress }))
        }));
        return <ResponsiveRadialBar {...commonProps} data={animatedData} />;
    }

    if (type === 'stream') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((row: any) => {
            const newRow = { ...row };
            (overlay.keys || []).forEach((k: string) => { newRow[k] = (row[k] || 0) * dataProgress; });
            return newRow;
        });
        return <ResponsiveStream {...commonProps} data={animatedData} keys={overlay.keys || []} />;
    }

    if (type === 'swarmplot') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveSwarmPlot {...commonProps} data={animatedData} groups={overlay.groups || []} identity="id" value="value" />;
    }

    if (type === 'waffle') {
        if (!Array.isArray(overlay.data)) return null;
        const total = overlay.total || 100;
        const animatedData = overlay.data.map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveWaffle {...commonProps} data={animatedData} total={total} rows={10} columns={10} />;
    }

    if (type === 'funnel') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveFunnel {...commonProps} data={animatedData} />;
    }

    if (type === 'marimekko') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveMarimekko {...commonProps} data={animatedData} id="id" value="value" dimensions={overlay.dimensions || []} />;
    }

    if (type === 'circlePacking') {
        if (!overlay.data) return null;
        const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
        return <ResponsiveCirclePacking {...commonProps} data={anim(overlay.data)} id="name" value="value" />;
    }

    if (type === 'calendar') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveCalendar {...commonProps} data={animatedData} from={overlay.from} to={overlay.to} />;
    }

    if (type === 'parallelCoordinates') {
        if (!Array.isArray(overlay.data)) return null;
        return <ResponsiveParallelCoordinates {...commonProps} data={overlay.data} variables={overlay.variables || []} />;
    }

    if (type === 'voronoi') {
        if (!Array.isArray(overlay.data)) return null;
        return <ResponsiveVoronoi {...commonProps} data={overlay.data} />;
    }

    if (type === 'treemap') {
       if (!overlay.data) return null;
       const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
       return <ResponsiveTreeMap {...commonProps} data={anim(overlay.data)} identity="name" value="value" />;
    }

    if (type === 'sunburst') {
       if (!overlay.data) return null;
       const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
       return <ResponsiveSunburst {...commonProps} data={anim(overlay.data)} id="name" value="value" />;
    }

    if (type === 'scatter' || type === 'bubble') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((series: any) => {
            if (!series || !Array.isArray(series.data)) return { ...series, data: [] };
            return {
                ...series,
                data: series.data.map((p: any) => ({ ...p, y: (p.y || 0) * dataProgress, z: (p.z || 10) * dataProgress }))
            };
        });
        return <ResponsiveScatterPlot {...commonProps} data={animatedData} xScale={{ type: 'linear', min: 0, max: 'auto' }} yScale={{ type: 'linear', min: 0, max: 'auto' }} nodeSize={type === 'bubble' ? (d: any) => d.data.z : 8} />;
    }

    if (type === 'network') {
       if (!overlay.data?.nodes || !overlay.data?.links || !Array.isArray(overlay.data.nodes)) return null;
       const animatedData = { nodes: overlay.data.nodes.map((n: any) => ({ ...n, size: (n.size || 12) * dataProgress })), links: overlay.data.links };
       return <ResponsiveNetwork {...(commonProps as any)} data={animatedData} linkDistance={e => (e as any).distance || 50} repulsivity={450} nodeColor={e => (e as any).color || '#ffffff'} linkThickness={n => (2 + 2 * ((n as any).target?.data?.index ?? 0)) * dataProgress} />;
    }

    if (type === 'chord') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((row: any) => (Array.isArray(row) ? row.map((val: number) => val * dataProgress) : []));
        return <ResponsiveChord {...commonProps} data={animatedData} keys={overlay.keys || []} />;
    }

    if (type === 'sankey') {
        if (!overlay.data?.nodes || !overlay.data?.links) return null;
        return <ResponsiveSankey {...commonProps} data={overlay.data} />;
    }

    if (type === 'boxplot') {
        if (!Array.isArray(overlay.data)) return null;
        return <ResponsiveBoxPlot {...commonProps} data={overlay.data} />;
    }

    if (type === 'violinPlot') return <ViolinPlot overlay={overlay} dataProgress={dataProgress} commonProps={commonProps} />;

    return null;
  };

  const renderContent = () => {
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
