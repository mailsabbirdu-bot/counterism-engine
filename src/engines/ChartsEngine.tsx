import React from 'react';
import { interpolate, useCurrentFrame, useVideoConfig, spring, Easing } from 'remotion';
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
import { ResponsiveChoropleth } from '@nivo/geo';

const MapChart: React.FC<{ overlay: any; dataProgress: number; commonProps: any }> = ({ overlay, dataProgress, commonProps }) => {
   return (
      <div className="relative w-full h-full">
         <ResponsiveChoropleth
            {...commonProps}
            data={overlay.data}
            features={overlay.features.features}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            colors="nivo"
            domain={[0, 1000000]}
            unknownColor="#151515"
            label="properties.name"
            valueFormat=".2s"
            projectionScale={overlay.projectionScale || 150}
            projectionTranslation={overlay.projectionTranslation || [0.5, 0.5]}
            projectionRotation={[0, 0, 0]}
            enableGraticule={true}
            graticuleLineColor="#ffffff10"
            borderWidth={0.5}
            borderColor="#ffffff30"
         />
         {overlay.chart_type === 'bubbleMap' && overlay.bubbles && (
            <div className="absolute inset-0 pointer-events-none">
               {overlay.bubbles.map((b: any, i: number) => (
                  <div
                     key={i}
                     className="absolute bg-blue-500/60 rounded-full border border-blue-400"
                     style={{
                        left: `${b.x}%`,
                        top: `${b.y}%`,
                        width: `${b.size * dataProgress}px`,
                        height: `${b.size * dataProgress}px`,
                        transform: 'translate(-50%, -50%)',
                        boxShadow: '0 0 20px rgba(59,130,246,0.5)'
                     }}
                  />
               ))}
            </div>
         )}
      </div>
   );
};

const ViolinPlot: React.FC<{ overlay: any; dataProgress: number; commonProps: any }> = ({ overlay, dataProgress }) => {
  return (
    <div className="flex justify-around items-end h-full w-full pb-10">
       {overlay.data.map((group: any, i: number) => (
            <div key={i} className="relative flex flex-col items-center" style={{ width: '60px' }}>
               <div
                  className="bg-blue-500/40 border-2 border-blue-400"
                  style={{
                    width: '40px',
                    height: `${group.value * 4 * dataProgress}px`,
                    borderRadius: '50% 50% 50% 50% / 60% 60% 40% 40%',
                    transform: 'scaleX(1.5)',
                  }}
               />
               <div className="w-1 h-full absolute bg-white/20 -z-10" />
               <span className="text-white/60 text-[10px] mt-4 font-bold uppercase">{group.label}</span>
            </div>
       ))}
    </div>
  );
};

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

  const exitFrame = overlay.duration - 15;
  const exit = interpolate(
    relativeFrame,
    [exitFrame, exitFrame + 15],
    [1, 0],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
  );

  const progress = entrance * exit;

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

    if (['line', 'multiLine', 'area', 'stackedArea', 'forecast'].includes(overlay.chart_type)) {
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
          yScale={{
            type: 'linear',
            min: overlay.minY ?? 0,
            max: overlay.maxY ?? 'auto',
            stacked: overlay.chart_type === 'stackedArea'
          }}
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
       let chartData = [...overlay.data];

       // Bar Race sorting logic
       if (overlay.chart_type === 'barRace') {
         const sortKey = overlay.keys[0];
         chartData.sort((a, b) => (b[sortKey] || 0) - (a[sortKey] || 0));
       }

       const animatedData = chartData.map((item: any) => {
         const newItem = { ...item };
         overlay.keys.forEach((key: string) => {
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
           layout={overlay.chart_type === 'horizontalBar' || (overlay.chart_type === 'barRace' && overlay.layout !== 'vertical') ? 'horizontal' : 'vertical'}
           groupMode={overlay.chart_type === 'groupedBar' ? 'grouped' : 'stacked'}
           padding={0.3}
           valueScale={{ type: 'linear' }}
           indexScale={{ type: 'band', round: true }}
           borderRadius={8}
           borderWidth={1}
           borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
           enableLabel={overlay.chart_type === 'barRace'}
           labelTextColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
           motionConfig="gentle"
         />
       );
    }

    if (['pie', 'donut'].includes(overlay.chart_type)) {
       const animatedData = overlay.data.map((item: any) => ({
          ...item,
          value: item.value * dataProgress
       }));

       return (
         <ResponsivePie
           {...commonProps}
           data={animatedData}
           innerRadius={overlay.chart_type === 'donut' ? 0.6 : 0}
           padAngle={0.7}
           cornerRadius={3}
           activeOuterRadiusOffset={8}
           borderWidth={1}
           borderColor={{ from: 'color', modifiers: [['darker', 0.2]] }}
           enableArcLinkLabels={true}
           arcLinkLabelsTextColor="#ffffffb0"
           arcLabelsTextColor={{ from: 'color', modifiers: [['darker', 2]] }}
         />
       );
    }

    if (overlay.chart_type === 'treemap') {
       return (
         <ResponsiveTreeMap
            {...commonProps}
            data={overlay.data}
            identity="name"
            value="value"
            valueFormat=".02s"
            margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
            labelSkipSize={12}
            labelTextColor={{ from: 'color', modifiers: [['darker', 1.2]] }}
            parentLabelPosition="left"
            parentLabelTextColor={{ from: 'color', modifiers: [['darker', 2]] }}
            borderColor={{ from: 'color', modifiers: [['darker', 0.1]] }}
         />
       );
    }

    if (overlay.chart_type === 'sunburst') {
       return (
         <ResponsiveSunburst
            {...commonProps}
            data={overlay.data}
            margin={{ top: 10, right: 10, bottom: 10, left: 10 }}
            id="name"
            value="value"
            cornerRadius={2}
            borderColor={{ from: 'color', modifiers: [['darker', 0.3]] }}
            arcLabelsSkipAngle={10}
            arcLabelsTextColor={{ from: 'color', modifiers: [['darker', 1.4]] }}
         />
       );
    }

    if (overlay.chart_type === 'histogram') {
        const animatedData = overlay.data.map((item: any) => ({
           ...item,
           count: item.count * dataProgress
        }));

        return (
          <ResponsiveBar
            {...commonProps}
            data={animatedData}
            keys={['count']}
            indexBy="bin"
            padding={0}
            colors={{ scheme: 'spectral' }}
            borderRadius={0}
            borderWidth={1}
            borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
            enableLabel={false}
          />
        );
    }

    if (overlay.chart_type === 'boxPlot') {
        return (
          <ResponsiveBoxPlot
            {...commonProps}
            data={overlay.data}
            layout="vertical"
            padding={0.12}
            valueScale={{ type: 'linear' }}
            indexScale={{ type: 'band', round: true }}
            colors={{ scheme: 'nivo' }}
            borderWidth={2}
            borderColor={{ from: 'color', modifiers: [['darker', 0.6]] }}
            medianWidth={2}
            medianColor={{ from: 'color', modifiers: [['darker', 3]] }}
            whiskerWidth={2}
            whiskerColor={{ from: 'color', modifiers: [['darker', 0.6]] }}
          />
        );
    }

    if (overlay.chart_type === 'violinPlot') {
       return <ViolinPlot overlay={overlay} dataProgress={dataProgress} commonProps={commonProps} />;
    }

    if (['scatter', 'bubble'].includes(overlay.chart_type)) {
       const animatedData = overlay.data.map((series: any) => ({
          ...series,
          data: series.data.map((p: any) => ({
             ...p,
             y: p.y * dataProgress,
             z: (p.z || 10) * dataProgress
          }))
       }));

       return (
         <ResponsiveScatterPlot
           {...commonProps}
           data={animatedData}
           xScale={{ type: 'linear', min: 0, max: 'auto' }}
           yScale={{ type: 'linear', min: 0, max: 'auto' }}
           nodeSize={overlay.chart_type === 'bubble' ? { key: 'z' } : 8}
           blendMode="multiply"
           axisTop={null}
           axisRight={null}
         />
       );
    }

    if (overlay.chart_type === 'sankey') {
       return (
         <ResponsiveSankey
            {...commonProps}
            data={overlay.data}
            margin={{ top: 40, right: 160, bottom: 40, left: 50 }}
            align="justify"
            colors={{ scheme: 'nivo' }}
            nodeOpacity={1}
            nodeThickness={18}
            nodeInnerPadding={3}
            nodeSpacing={24}
            nodeBorderWidth={0}
            nodeBorderColor={{ from: 'color', modifiers: [['darker', 0.8]] }}
            linkOpacity={0.5}
            linkHoverOpacity={1}
            linkHoverOthersOpacity={0.1}
            enableLinkGradient={true}
            labelPosition="outside"
            labelOrientation="vertical"
            labelPadding={16}
            labelTextColor={{ from: 'color', modifiers: [['darker', 1]] }}
         />
       );
    }

    if (overlay.chart_type === 'chord') {
       return (
         <ResponsiveChord
            {...commonProps}
            data={overlay.data}
            keys={overlay.keys}
            margin={{ top: 60, right: 60, bottom: 90, left: 60 }}
            padAngle={0.02}
            innerRadiusRatio={0.96}
            innerRadiusOffset={0.02}
            arcOpacity={1}
            arcBorderWidth={1}
            arcBorderColor={{ from: 'color', modifiers: [['darker', 0.4]] }}
            ribbonOpacity={0.5}
            ribbonBorderWidth={1}
            ribbonBorderColor={{ from: 'color', modifiers: [['darker', 0.4]] }}
            enableLabel={true}
            label="id"
            labelOffset={12}
            labelRotation={-90}
            labelTextColor={{ from: 'color', modifiers: [['darker', 1]] }}
         />
       );
    }

    if (overlay.chart_type === 'network') {
       return (
         <ResponsiveNetwork
            {...commonProps}
            nodes={overlay.data.nodes}
            links={overlay.data.links}
            margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
            linkDistance={e => (e as any).distance}
            centeringStrength={0.3}
            repulsionStrength={450}
            nodeColor={e => (e as any).color}
            nodeBorderWidth={1}
            nodeBorderColor={{ from: 'color', modifiers: [['darker', 0.8]] }}
            linkThickness={n => 2 + 2 * (n as any).target.data.index}
            linkColor={{ from: 'source.color' }}
            motionConfig="molasses"
         />
       );
    }

    if (['choropleth', 'bubbleMap'].includes(overlay.chart_type)) {
       return <MapChart overlay={overlay} dataProgress={dataProgress} commonProps={commonProps} />;
    }

    return null;
  };

  return (
    <div
      className="absolute bg-zinc-950/80 backdrop-blur-3xl rounded-[3rem] border-2 border-white/20 shadow-[0_40px_80px_rgba(0,0,0,0.7)] overflow-hidden p-12"
      style={{
        width: overlay.width || 1000,
        height: overlay.height || 650,
        left: `${overlay.position?.x ?? 960}px`,
        top: `${overlay.position?.y ?? 540}px`,
        opacity: progress,
        zIndex: overlay.zIndex ?? 30,
        transform: `translate(-50%, -50%) scale(${0.9 + progress * 0.1}) translateY(${(1 - entrance) * 100 + (1 - exit) * -100}px)`,
        filter: `blur(${(1 - exit) * 20}px)`
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
