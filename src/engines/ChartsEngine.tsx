import React from 'react';
import { interpolate, useCurrentFrame } from 'remotion';
import { ResponsiveLine } from '@nivo/line';

export const ChartsEngine: React.FC<{ overlay: any }> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const relativeFrame = frame - overlay.start;

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
    return null;
  }

  // Simple animation for Nivo data
  const animatedData = overlay.data.map((series: any) => ({
    ...series,
    data: series.data.slice(0, Math.floor(interpolate(relativeFrame, [0, 60], [0, series.data.length], { extrapolateRight: 'clamp' })))
  }));

  return (
    <div className="absolute bottom-20 right-20 w-[600px] h-[400px] bg-black/40 backdrop-blur-md rounded-3xl p-8 border border-white/10 shadow-2xl">
      <h4 className="text-white/60 font-mono text-[10px] uppercase tracking-[0.3em] mb-4">Real-time Analytics</h4>
      <div className="h-full w-full">
        <ResponsiveLine
          data={animatedData}
          margin={{ top: 10, right: 10, bottom: 50, left: 50 }}
          xScale={{ type: 'point' }}
          yScale={{ type: 'linear', min: 'auto', max: 'auto', stacked: true, reverse: false }}
          axisTop={null}
          axisRight={null}
          theme={{
            axis: {
              ticks: { text: { fill: '#ffffff40', fontSize: 10 } },
              legend: { text: { fill: '#ffffff40' } }
            },
            grid: { line: { stroke: '#ffffff10' } }
          }}
          colors={{ scheme: 'nivo' }}
          pointSize={10}
          pointColor={{ theme: 'background' }}
          pointBorderWidth={2}
          pointBorderColor={{ from: 'serieColor' }}
          enableArea={true}
          areaOpacity={0.15}
          useMesh={true}
        />
      </div>
    </div>
  );
};
