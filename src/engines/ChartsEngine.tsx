import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { ResponsiveLine } from '@nivo/line';
import { ResponsiveBar } from '@nivo/bar';

export const ChartsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  const renderChart = () => {
    const commonProps = {
      theme: {
        axis: {
          ticks: { text: { fill: '#ffffff60', fontSize: 10, fontFamily: 'monospace' } },
          legend: { text: { fill: '#ffffff60', fontSize: 12 } }
        },
        grid: { line: { stroke: 'rgba(255,255,255,0.05)', strokeWidth: 1 } },
        tooltip: { container: { background: '#18181b', color: '#fff', fontSize: 12, borderRadius: 8 } }
      },
      colors: overlay.colors || { scheme: 'nivo' },
      margin: { top: 40, right: 40, bottom: 60, left: 60 },
      animate: true,
      motionConfig: "gentle"
    };

    if (overlay.chart_type === 'line') {
      const animatedData = overlay.data.map((series: any) => ({
        ...series,
        data: series.data.slice(0, Math.floor(interpolate(relativeFrame, [0, 45], [0, series.data.length], { extrapolateRight: 'clamp' })))
      }));

      return (
        <ResponsiveLine
          {...commonProps}
          data={animatedData}
          xScale={{ type: 'point' }}
          yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: false }}
          curve="monotoneX"
          enableArea={true}
          areaOpacity={0.1}
          pointSize={8}
          pointColor="#18181b"
          pointBorderWidth={2}
          pointBorderColor={{ from: 'serieColor' }}
          enableGridX={false}
        />
      );
    }

    if (overlay.chart_type === 'bar') {
       const progress = interpolate(relativeFrame, [0, 45], [0, 1], { extrapolateRight: 'clamp' });
       const animatedData = overlay.data.map((item: any) => {
         const newItem = { ...item };
         Object.keys(item).forEach(key => {
           if (typeof item[key] === 'number') {
             newItem[key] = item[key] * progress;
           }
         });
         return newItem;
       });

       return (
         <ResponsiveBar
           {...commonProps}
           data={animatedData}
           keys={overlay.keys}
           indexBy={overlay.indexBy}
           padding={0.3}
           valueScale={{ type: 'linear' }}
           indexScale={{ type: 'band', round: true }}
           borderRadius={4}
           borderWidth={1}
           borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
           enableLabel={false}
         />
       );
    }

    return null;
  };

  return (
    <div
      className="absolute bg-zinc-950/40 backdrop-blur-xl rounded-[2rem] border border-white/10 shadow-2xl overflow-hidden p-8"
      style={{
        width: overlay.width || 800,
        height: overlay.height || 500,
        left: overlay.position?.x || 1000,
        top: overlay.position?.y || 500,
      }}
    >
      <div className="flex justify-between items-center mb-6">
        <div>
          <h3 className="text-white font-bold text-lg tracking-tight">{overlay.title || 'Data Analysis'}</h3>
          <p className="text-white/40 text-[10px] font-mono uppercase tracking-[0.2em]">{overlay.subtitle || 'System Telemetry'}</p>
        </div>
        <div className="px-3 py-1 bg-white/5 rounded-full border border-white/10 text-[10px] text-white/60 font-mono">
          LIVE_STREAM_V4
        </div>
      </div>
      <div className="h-[calc(100%-80px)] w-full">
        {renderChart()}
      </div>
    </div>
  );
};
