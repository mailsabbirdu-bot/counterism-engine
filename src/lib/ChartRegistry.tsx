import React from 'react';
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
import { ResponsiveBump, ResponsiveAreaBump } from '@nivo/bump';
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
import { interpolate } from 'remotion';

export interface ChartRendererProps {
    overlay: any;
    dataProgress: number;
    commonProps: any;
    activeHighlight?: any;
    frame: number;
    videoWidth: number;
    videoHeight: number;
}

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

const renderLineLike = (props: ChartRendererProps, options: { enableArea?: boolean; stacked?: boolean } = {}) => {
    const { overlay, dataProgress, commonProps, activeHighlight, frame } = props;
    const isFlat = Array.isArray(overlay.data) && overlay.data.length > 0 && !overlay.data[0].data;
    const seriesArray = isFlat ? [{ id: overlay.title || 'Data', data: overlay.data }] : (Array.isArray(overlay.data) ? overlay.data : []);

    const animatedData = seriesArray.map((series: any) => {
        if (!series || !Array.isArray(series.data)) return { id: 'Empty', data: [] };

        const getActivation = (node: any) => {
            const globalFrame = frame;
            const windows = node.active_windows || (node.active_at ? [[node.active_at, node.active_at + 60]] : null);
            if (!windows) return { isActive: !activeHighlight, isPast: false, isFuture: false };
            let isActive = false;
            let isPast = globalFrame > windows[windows.length - 1][1];
            let isFuture = globalFrame < windows[0][0];
            for (const [start, end] of windows) {
                if (globalFrame >= start && globalFrame <= end) {
                    isActive = true; isPast = false; isFuture = false; break;
                }
            }
            return { isActive, isPast, isFuture };
        };

        const isSeriesHighlighted = activeHighlight && series.id === activeHighlight.seriesId;
        const { isActive: seriesActive, isPast: seriesPast } = getActivation(series);
        const opacity = activeHighlight ? (isSeriesHighlighted ? 1 : 0.1) : (seriesActive ? 1 : seriesPast ? 0.3 : 0.1);

        return {
            ...series,
            color: isSeriesHighlighted ? activeHighlight.color : series.color,
            data: series.data.map((p: any, i: number) => {
                const reveal = interpolate(dataProgress * series.data.length, [i, i + 0.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                const y = typeof p.y === 'number' ? p.y : (p[overlay.keys?.[0] || 'value'] || 0);
                return { ...p, x: p.x || p.year || p.label || i, y: y * reveal, opacity, importance: series.importance || 1.0 };
            })
        };
    });

    return (
        <ResponsiveLine
            {...commonProps}
            data={animatedData}
            xScale={{ type: 'point' }}
            yScale={{ type: 'linear', min: overlay.minY ?? 0, max: overlay.maxY ?? 'auto', stacked: options.stacked || false }}
            curve={overlay.curve || "monotoneX"}
            enableArea={options.enableArea || false}
            areaOpacity={0.25}
            enableGridX={false}
            lineWidth={4}
            enableSlices="x"
            pointSize={(node: any) => {
                const s = animatedData.find((d: any) => d.id === (node as any).serieId);
                const imp = s?.importance || 1;
                return (imp >= 4 ? 14 : imp >= 2 ? 8 : 4) * dataProgress;
            }}
            pointColor="#09090b"
            pointBorderWidth={2}
            pointBorderColor={{ from: 'serieColor' }}
            defs={[
                {
                    id: 'gradientA',
                    type: 'linearGradient',
                    colors: [
                        { offset: 0, color: 'inherit' },
                        { offset: 100, color: 'inherit', opacity: 0 },
                    ],
                },
            ]}
            fill={[{ match: '*', id: 'gradientA' }]}
        />
    );
};

export const ChartRegistry: Record<string, React.FC<ChartRendererProps>> = {
    line: (props) => renderLineLike(props),
    multiLine: (props) => renderLineLike(props),
    area: (props) => renderLineLike(props, { enableArea: true }),
    forecast: (props) => renderLineLike(props, { enableArea: true }),
    stackedArea: (props) => renderLineLike(props, { enableArea: true, stacked: true }),
    bar: (props) => {
        const { overlay, dataProgress, commonProps } = props;
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
                padding={0.4}
                borderRadius={8}
                borderWidth={2}
                borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
            />
        );
    },
    horizontalBar: (props) => {
        const { overlay, dataProgress, commonProps } = props;
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
                layout="horizontal"
                padding={0.4}
                borderRadius={8}
                borderWidth={2}
                borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
            />
        );
    },
    verticalBar: (props) => ChartRegistry.bar(props),
    groupedBar: (props) => {
        const { overlay, dataProgress, commonProps } = props;
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
                groupMode="grouped"
                padding={0.4}
                borderRadius={8}
                borderWidth={2}
                borderColor={{ from: 'color', modifiers: [['darker', 1.6]] }}
            />
        );
    },
    stackedBar: (props) => ChartRegistry.bar(props),
    pie: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = overlay.data.map((item: any) => ({ ...item, value: (item.value || 0) * dataProgress }));
        return <ResponsivePie {...commonProps} data={animatedData} innerRadius={0} padAngle={0.7} cornerRadius={3} />;
    },
    donut: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = overlay.data.map((item: any) => ({ ...item, value: (item.value || 0) * dataProgress }));
        return <ResponsivePie {...commonProps} data={animatedData} innerRadius={0.6} padAngle={0.7} cornerRadius={3} />;
    },
    bump: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((series: any) => ({
            ...series,
            data: (series.data || []).map((p: any, i: number) => {
                const reveal = interpolate(dataProgress * series.data.length, [i, i + 0.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                return { ...p, y: (p.y || 0) * reveal };
            })
        }));
        return <ResponsiveBump {...commonProps} data={animatedData} />;
    },
    areaBump: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((series: any) => ({
            ...series,
            data: (series.data || []).map((p: any, i: number) => {
                const reveal = interpolate(dataProgress * series.data.length, [i, i + 0.8], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
                return { ...p, y: (p.y || 0) * reveal };
            })
        }));
        return <ResponsiveAreaBump {...commonProps} data={animatedData} />;
    },
    heatmap: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((row: any) => ({
            ...row,
            data: (row.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }))
        }));
        return <ResponsiveHeatMap {...commonProps} data={animatedData} colors="blues" />;
    },
    radar: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((item: any) => {
            const newItem = { ...item };
            (overlay.keys || ['value']).forEach((k: string) => { newItem[k] = (item[k] || 0) * dataProgress; });
            return newItem;
        });
        return <ResponsiveRadar {...commonProps} data={animatedData} keys={overlay.keys || ['value']} indexBy={overlay.indexBy || 'id'} />;
    },
    radialBar: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((series: any) => ({
            ...series,
            data: (series.data || []).map((d: any) => ({ ...d, y: (d.y || 0) * dataProgress }))
        }));
        return <ResponsiveRadialBar {...commonProps} data={animatedData} />;
    },
    stream: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((row: any) => {
            const newRow = { ...row };
            (overlay.keys || []).forEach((k: string) => { newRow[k] = (row[k] || 0) * dataProgress; });
            return newRow;
        });
        return <ResponsiveStream {...commonProps} data={animatedData} keys={overlay.keys || []} />;
    },
    swarmplot: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveSwarmPlot {...commonProps} data={animatedData} groups={overlay.groups || []} identity="id" value="value" />;
    },
    waffle: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveWaffle {...commonProps} data={animatedData} total={overlay.total || 100} rows={10} columns={10} />;
    },
    funnel: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveFunnel {...commonProps} data={animatedData} />;
    },
    marimekko: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveMarimekko {...commonProps} data={animatedData} id="id" value="value" dimensions={overlay.dimensions || []} />;
    },
    circlePacking: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
        return <ResponsiveCirclePacking {...commonProps} data={anim(overlay.data)} id="name" value="value" />;
    },
    calendar: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((d: any) => ({ ...d, value: (d.value || 0) * dataProgress }));
        return <ResponsiveCalendar {...commonProps} data={animatedData} from={overlay.from} to={overlay.to} />;
    },
    treemap: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
        return <ResponsiveTreeMap {...commonProps} data={anim(overlay.data)} identity="name" value="value" />;
    },
    sunburst: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const anim = (node: any): any => ({ ...node, value: typeof node.value === 'number' ? node.value * dataProgress : undefined, children: node.children ? node.children.map(anim) : undefined });
        return <ResponsiveSunburst {...commonProps} data={anim(overlay.data)} id="name" value="value" />;
    },
    scatter: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((series: any) => {
            if (!series || !Array.isArray(series.data)) return { ...series, data: [] };
            return {
                ...series,
                data: series.data.map((p: any) => ({ ...p, y: (p.y || 0) * dataProgress, z: (p.z || 10) * dataProgress }))
            };
        });
        return <ResponsiveScatterPlot {...commonProps} data={animatedData} xScale={{ type: 'linear', min: 0, max: 'auto' }} yScale={{ type: 'linear', min: 0, max: 'auto' }} nodeSize={(d: any) => d.data.z} />;
    },
    bubble: (props) => ChartRegistry.scatter(props),
    network: (props) => {
       const { overlay, dataProgress, commonProps } = props;
       if (!overlay.data?.nodes || !overlay.data?.links) return null;
       const animatedData = { nodes: overlay.data.nodes.map((n: any) => ({ ...n, size: (n.size || 12) * dataProgress })), links: overlay.data.links };
       return <ResponsiveNetwork {...(commonProps as any)} data={animatedData} linkDistance={e => (e as any).distance || 50} repulsivity={450} nodeColor={e => (e as any).color || '#ffffff'} linkThickness={n => (2 + 2 * ((n as any).target?.data?.index ?? 0)) * dataProgress} />;
    },
    chord: (props) => {
        const { overlay, dataProgress, commonProps } = props;
        const animatedData = (overlay.data || []).map((row: any) => (Array.isArray(row) ? row.map((val: number) => val * dataProgress) : []));
        return <ResponsiveChord {...commonProps} data={animatedData} keys={overlay.keys || []} />;
    },
    sankey: (props) => {
        const { overlay, commonProps } = props;
        if (!overlay.data?.nodes || !overlay.data?.links) return null;
        return <ResponsiveSankey {...commonProps} data={overlay.data} />;
    },
    boxplot: (props) => {
        const { overlay, commonProps } = props;
        if (!Array.isArray(overlay.data)) return null;
        return <ResponsiveBoxPlot {...commonProps} data={overlay.data} />;
    },
    violinPlot: (props) => <ViolinPlot {...props} />,
};
