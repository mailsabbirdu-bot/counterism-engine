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

export const ChartsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { fps, width: videoWidth, height: videoHeight } = useVideoConfig();
  const start = safeNumber(overlay.start, 0);
  const duration = safeNumber(overlay.duration, 120);
  const relativeFrame = frame - start;

  if (frame % 30 === 0) {
    console.log(`[ChartsEngine] Scene: ${overlay.scene_id} Overlay: ${overlay.id} Type: ${overlay.chart_type} Visible: ${frame >= start && frame <= start + duration} Pos: (${overlay.position?.x}, ${overlay.position?.y})`);
  }

  if (frame < start || frame > start + duration) {
    return null;
  }

  const entrance = interpolate(isNaN(relativeFrame) ? 0 : relativeFrame, [0, 30], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.2, 0, 0.2, 1) });
  const exitFrame = duration - 20;
  const exit = interpolate(isNaN(relativeFrame) ? 0 : relativeFrame, [exitFrame, exitFrame + 20], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 1, 1) });
  const progress = entrance * exit;

  const renderChart = () => {
    const font = overlay.font || 'Inter, sans-serif';
    const commonProps = {
      theme: {
        axis: {
          ticks: { text: { fill: '#ffffffb0', fontSize: 20, fontFamily: font, fontWeight: 'bold' } },
          legend: { text: { fill: '#ffffffe0', fontSize: 24, fontFamily: font, fontWeight: '900' } }
        },
        grid: { line: { stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 } },
        tooltip: { container: { background: '#09090b', color: '#fff', fontSize: 20, fontFamily: font, borderRadius: 12, border: '1px solid rgba(255,255,255,0.2)', boxShadow: '0 10px 30px rgba(0,0,0,0.5)' } },
        labels: { text: { fontSize: 18, fontWeight: 'bold', fill: '#fff', fontFamily: font } },
        dots: { text: { fontSize: 14, fontFamily: font } },
        legends: { text: { fontSize: 16, fontFamily: font } },
        annotations: { text: { fontFamily: font, fontSize: 18, fontWeight: 'bold', fill: '#fff' } },
        arcLabels: { text: { fontFamily: font, fontSize: 20, fontWeight: 'bold', fill: '#fff' } },
        arcLinkLabels: { text: { fontFamily: font, fontSize: 16, fill: '#fff' } }
      },
      colors: overlay.colors || { scheme: 'nivo' },
      margin: { top: 60, right: 60, bottom: 80, left: 100 },
      animate: false,
    };

    const animationStart = 45;
    const animationEnd = Math.min(duration - 30, 180);
    const dataProgress = interpolate(isNaN(relativeFrame) ? 0 : relativeFrame, [animationStart, animationEnd], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.33, 1, 0.68, 1) });

  if (!overlay?.data || !Array.isArray(overlay.data)) {
      // Inject placeholder data to prevent crash
      overlay.data = [{ id: "A", value: 10 }, { id: "B", value: 20 }];
  }

    if (['line', 'multiLine', 'area', 'stackedArea', 'forecast'].includes(overlay.chart_type)) {
      const isFlat = Array.isArray(overlay.data) && overlay.data.length > 0 && !overlay.data[0].data;
      const seriesArray = isFlat ? [{ id: overlay.title || 'Data', data: overlay.data }] : (Array.isArray(overlay.data) ? overlay.data : []);

      const animatedData = seriesArray.map((series: any) => {
        if (!series || !Array.isArray(series.data)) return { id: 'Empty', data: [] };
        return {
          ...series,
          data: series.data.map((p: any, i: number) => {
            const reveal = interpolate(dataProgress * series.data.length, [i, i + 0.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
            const y = typeof p.y === 'number' ? p.y : (p[overlay.keys?.[0] || 'value'] || 0);
            return { ...p, x: p.x || p.year || p.label || i, y: y * reveal };
          })
        };
      });

      return (
        <ResponsiveLine
          {...commonProps}
          data={animatedData}
          xScale={{ type: 'point' }}
          yScale={{ type: 'linear', min: overlay.minY ?? 0, max: overlay.maxY ?? 'auto', stacked: overlay.chart_type === 'stackedArea' }}
          curve={overlay.curve || "monotoneX"}
          enableArea={['area', 'stackedArea', 'forecast'].includes(overlay.chart_type)}
          areaOpacity={0.25}
          pointSize={overlay.chart_type === 'forecast' ? 0 : 8}
          pointColor="#09090b"
          pointBorderWidth={2}
          pointBorderColor={{ from: 'serieColor' }}
          enableGridX={false}
          lineWidth={4}
          enableSlices="x"
        />
      );
    }

    if (['bar', 'horizontalBar', 'verticalBar', 'groupedBar', 'stackedBar', 'barRace'].includes(overlay.chart_type)) {
       if (!Array.isArray(overlay.data)) return null;

       const keys = overlay.keys || ['value'];
       const animatedData = overlay.data.map((item: any) => {
         if (!item) return {};
         const newItem = { ...item };
         keys.forEach((key: string) => {
            const baseVal = Number(item[key]) || 0;
            newItem[key] = baseVal * dataProgress;
         });
         return newItem;
       });

       return (
         <ResponsiveBar
           {...commonProps}
           data={animatedData}
           keys={keys}
           indexBy={overlay.indexBy || 'id'}
           layout={overlay.chart_type === 'horizontalBar' ? 'horizontal' : 'vertical'}
           groupMode={overlay.chart_type === 'groupedBar' ? 'grouped' : 'stacked'}
           padding={0.5} // Increased padding to avoid "box-like" look
           innerPadding={4}
           borderRadius={12}
           borderWidth={2}
           borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
           enableLabel={true}
           labelSkipWidth={12}
           labelSkipHeight={12}
           labelTextColor={{ from: 'color', modifiers: [['brighter', 1.6]] }}
         />
       );
    }

    if (['pie', 'donut'].includes(overlay.chart_type)) {
       if (!Array.isArray(overlay.data)) return null;
       const animatedData = overlay.data.map((item: any) => {
           if (!item) return {};
           return { ...item, value: (item.value || 0) * dataProgress };
       });
       return <ResponsivePie {...commonProps} data={animatedData} innerRadius={overlay.chart_type === 'donut' ? 0.6 : 0} padAngle={0.7} cornerRadius={3} />;
    }

    if (overlay.chart_type === 'treemap') {
       if (!overlay.data) return null;
       const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
       return <ResponsiveTreeMap {...commonProps} data={anim(overlay.data)} identity="name" value="value" />;
    }

    if (overlay.chart_type === 'sunburst') {
       if (!overlay.data) return null;
       const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
       return <ResponsiveSunburst {...commonProps} data={anim(overlay.data)} id="name" value="value" />;
    }

    if (overlay.chart_type === 'scatter' || overlay.chart_type === 'bubble') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((series: any) => {
            if (!series || !Array.isArray(series.data)) return { ...series, data: [] };
            return {
                ...series,
                data: series.data.map((p: any) => ({ ...p, y: (p.y || 0) * dataProgress, z: (p.z || 10) * dataProgress }))
            };
        });
        return <ResponsiveScatterPlot {...commonProps} data={animatedData} xScale={{ type: 'linear', min: 0, max: 'auto' }} yScale={{ type: 'linear', min: 0, max: 'auto' }} nodeSize={overlay.chart_type === 'bubble' ? (d: any) => d.data.z : 8} />;
    }

    if (overlay.chart_type === 'network') {
       if (!overlay.data?.nodes || !overlay.data?.links || !Array.isArray(overlay.data.nodes)) return null;
       const animatedData = { nodes: overlay.data.nodes.map((n: any) => ({ ...n, size: (n.size || 12) * dataProgress })), links: overlay.data.links };
       return <ResponsiveNetwork {...(commonProps as any)} data={animatedData} linkDistance={e => (e as any).distance || 50} repulsivity={450} nodeColor={e => (e as any).color || '#ffffff'} linkThickness={n => (2 + 2 * ((n as any).target?.data?.index ?? 0)) * dataProgress} />;
    }

    if (overlay.chart_type === 'chord') {
        if (!Array.isArray(overlay.data)) return null;
        const animatedData = overlay.data.map((row: any) => (Array.isArray(row) ? row.map((val: number) => val * dataProgress) : []));
        return <ResponsiveChord {...commonProps} data={animatedData} keys={overlay.keys || []} />;
    }

    if (overlay.chart_type === 'violinPlot') return <ViolinPlot overlay={overlay} dataProgress={dataProgress} commonProps={commonProps} />;

    return null;
  };

  return (
    <div
      className="absolute bg-zinc-950/80 backdrop-blur-3xl rounded-[3rem] border-2 border-white/20 shadow-[0_40px_80px_rgba(0,0,0,0.7)] overflow-hidden p-12"
      style={{
        fontFamily: overlay.font || 'Inter, sans-serif',
        width: safeNumber(overlay.width, 1000),
        height: safeNumber(overlay.height, 650),
        left: `${safeNumber(overlay.position?.x, videoWidth / 2)}px`,
        top: `${safeNumber(overlay.position?.y, videoHeight / 2)}px`,
        opacity: progress,
        zIndex: safeNumber(overlay.zIndex, 30),
        transform: `translate(-50%, -50%) scale(${0.98 + progress * 0.02})`,
        // Fix: Apply blur only during transition (when progress < 1)
        filter: progress < 1 ? `blur(${(1 - progress) * 10}px)` : 'none'
      }}
    >
      <div className="flex justify-between items-center mb-10">
        <div>
          <h3 className="text-white font-black text-3xl tracking-tighter leading-tight">{overlay.title || 'Data Analysis'}</h3>
          <p className="text-white/60 text-sm font-mono uppercase tracking-[0.4em] mt-2 font-bold">{overlay.subtitle || 'System Telemetry'}</p>
        </div>
        <div className="px-6 py-3 bg-blue-500/10 rounded-2xl border-2 border-blue-500/20 text-sm text-blue-400 font-mono font-black shadow-xl uppercase tracking-widest">Telemetry Active</div>
      </div>
      <div className="h-[calc(100%-120px)] w-full">{renderChart()}</div>
    </div>
  );
};
