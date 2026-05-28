import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring, Easing } from 'remotion';
import { ResponsiveLine } from '@nivo/line';
import { ResponsiveBar } from '@nivo/bar';

export const ChartsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  // Smooth entrance animation for the whole container
  const entrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 20, stiffness: 60 },
  });

  const renderChart = () => {
    const commonProps = {
      theme: {
        axis: {
          ticks: { text: { fill: '#ffffffb0', fontSize: 14, fontFamily: 'Inter, sans-serif', fontWeight: 'bold' } },
          legend: { text: { fill: '#ffffffe0', fontSize: 16, fontWeight: '900' } }
        },
        grid: { line: { stroke: 'rgba(255,255,255,0.1)', strokeWidth: 1 } },
        tooltip: {
          container: {
            background: '#09090b',
            color: '#fff',
            fontSize: 16,
            borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.2)',
            boxShadow: '0 10px 30px rgba(0,0,0,0.5)'
          }
        }
      },
      colors: overlay.colors || { scheme: 'nivo' },
      margin: { top: 40, right: 40, bottom: 60, left: 80 },
      animate: false,
    };

    // Smoother data reveal over 150 frames
    const dataProgress = interpolate(
      relativeFrame,
      [20, 150],
      [0, 1],
      { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.2, 1) }
    );

    if (overlay.chart_type === 'line') {
      const animatedData = overlay.data.map((series: any) => {
        return {
          ...series,
          data: series.data.map((p: any, i: number) => {
            const pointReveal = interpolate(
              dataProgress * series.data.length,
              [i, i + 0.8],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );
            return { ...p, y: p.y * pointReveal };
          })
        };
      });

      return (
        <ResponsiveLine
          {...commonProps}
          data={animatedData}
          xScale={{ type: 'point' }}
          yScale={{ type: 'linear', min: 0, max: 'auto', stacked: false }}
          curve="monotoneX"
          enableArea={true}
          areaOpacity={0.25}
          pointSize={12}
          pointColor="#09090b"
          pointBorderWidth={4}
          pointBorderColor={{ from: 'serieColor' }}
          enableGridX={false}
          lineWidth={4}
        />
      );
    }

    if (overlay.chart_type === 'bar') {
       const animatedData = overlay.data.map((item: any) => {
         const newItem = { ...item };
         Object.keys(item).forEach(key => {
           if (typeof item[key] === 'number') {
             newItem[key] = item[key] * dataProgress;
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
           borderRadius={12}
           borderWidth={2}
           borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
           enableLabel={false}
         />
       );
    }

    return null;
  };

  return (
    <div
      className="absolute bg-zinc-950/80 backdrop-blur-3xl rounded-[3rem] border-2 border-white/20 shadow-[0_40px_80px_rgba(0,0,0,0.7)] overflow-hidden p-12"
      style={{
        width: overlay.width || 1000,
        height: overlay.height || 650,
        left: overlay.position?.x || 1000,
        top: overlay.position?.y || 500,
        opacity: entrance,
        transform: `scale(${0.9 + entrance * 0.1}) translateY(${(1 - entrance) * 100}px)`,
        zIndex: overlay.zIndex ?? 40
      }}
    >
      <div className="flex justify-between items-center mb-10">
        <div>
          <h3 className="text-white font-black text-3xl tracking-tighter leading-tight">{overlay.title || 'Data Analysis'}</h3>
          <p className="text-white/60 text-sm font-mono uppercase tracking-[0.4em] mt-2 font-bold">{overlay.subtitle || 'System Telemetry'}</p>
        </div>
        <div className="px-6 py-3 bg-blue-500/10 rounded-2xl border-2 border-blue-500/20 text-sm text-blue-400 font-mono font-black shadow-xl uppercase tracking-widest">
          Telemetry Active
        </div>
      </div>
      <div className="h-[calc(100%-120px)] w-full">
        {renderChart()}
      </div>
    </div>
  );
};
