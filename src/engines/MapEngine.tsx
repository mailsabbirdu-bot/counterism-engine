import React, { useMemo, useEffect, useState } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing, continueRender, delayRender } from 'remotion';
import * as d3 from 'd3-geo';
import { feature } from 'topojson-client';

// Standard high-quality world TopoJSON URL
const DEFAULT_TOPOJSON = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface City {
  name: string;
  coords: [number, number]; // [lon, lat]
}

interface MapOverlayProps {
  overlay: {
    id: string;
    map_type?: 'world' | 'region';
    center?: [number, number];
    scale?: number;
    cities?: City[];
    routes?: { from: string; to: string; curve?: number; label?: string }[];
    highlights?: string[]; // IDs or names of countries to highlight
    topojson_url?: string;
    object_name?: string; // e.g. 'countries' or 'districts'
    start: number;
    duration: number;
    position?: { x: number; y: number };
    width?: number;
    height?: number;
    zIndex?: number;
    theme?: 'dark' | 'light' | 'blueprint';
  };
}

export const MapEngine: React.FC<MapOverlayProps> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  const width = overlay.width || 1200;
  const height = overlay.height || 800;

  const [mapData, setMapData] = useState<any>(null);
  const [handle] = useState(() => delayRender('Loading Map Topology'));

  useEffect(() => {
    const url = overlay.topojson_url || DEFAULT_TOPOJSON;
    const objName = overlay.object_name || 'countries';

    fetch(url)
      .then(res => res.json())
      .then(data => {
        // Handle different TopoJSON object keys
        const obj = data.objects[objName] || Object.values(data.objects)[0];
        if (!obj) throw new Error(`Object ${objName} not found in TopoJSON`);

        const geojson = feature(data, obj as any);
        setMapData(geojson);
        continueRender(handle);
      })
      .catch(err => {
        console.error("Map Data Fetch Error:", err);
        setMapData({ features: [] }); // Fallback to empty map to prevent engine crash
        continueRender(handle);
      });
  }, [overlay.topojson_url, overlay.object_name]);

  // 1. Setup Projection (Smoothly animates center/scale if needed)
  const projection = useMemo(() => {
    return d3.geoMercator()
      .scale(overlay.scale || 200)
      .center(overlay.center || [0, 20])
      .translate([width / 2, height / 2]);
  }, [overlay.scale, overlay.center, width, height]);

  const pathGenerator = d3.geoPath().projection(projection);

  // 2. Animations
  const entrance = spring({
    frame: relativeFrame,
    fps,
    config: { damping: 20 },
  });

  const exitFrame = overlay.duration - 15;
  const exit = interpolate(relativeFrame, [exitFrame, exitFrame + 15], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const progress = entrance * exit;

  // Staggered reveal for cities and routes
  const dataProgress = interpolate(
    relativeFrame,
    [30, overlay.duration - 30],
    [0, 1],
    { extrapolateLeft: 'clamp', extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.2, 1) }
  );

  // 3. Helpers
  const getCityCoords = (name: string) => {
    return overlay.cities?.find(c => c.name === name)?.coords;
  };

  const calculateDistance = (coords1: [number, number], coords2: [number, number]) => {
    const R = 6371; // km
    const dLat = (coords2[1] - coords1[1]) * Math.PI / 180;
    const dLon = (coords2[0] - coords1[0]) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(coords1[1] * Math.PI / 180) * Math.cos(coords2[1] * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return Math.round(R * c);
  };

  if (frame < overlay.start || frame > overlay.start + overlay.duration || !mapData) {
    return null;
  }

  return (
    <div
      className="absolute bg-zinc-950/40 backdrop-blur-2xl rounded-[3rem] border-2 border-white/10 shadow-[0_40px_80px_rgba(0,0,0,0.5)] overflow-hidden p-8"
      style={{
        width,
        height,
        left: `${overlay.position?.x ?? 960}px`,
        top: `${overlay.position?.y ?? 540}px`,
        opacity: progress,
        zIndex: overlay.zIndex ?? 30,
        transform: `translate(-50%, -50%) scale(${0.9 + progress * 0.1})`,
      }}
    >
      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`}>
        {/* World Map SVG Paths */}
        <g className="map-base">
          {mapData.features.map((feature: any, i: number) => {
             const name = feature.properties.name || feature.properties.NAME_1 || feature.properties.NAME || feature.id;
             const isHighlighted = overlay.highlights?.some(h =>
                h.toLowerCase() === name?.toString().toLowerCase()
             );

             return (
                <path
                  key={`country-${i}`}
                  d={pathGenerator(feature) || ''}
                  fill={isHighlighted ? "rgba(59, 130, 246, 0.2)" : "rgba(255, 255, 255, 0.05)"}
                  stroke={isHighlighted ? "rgba(59, 130, 246, 0.5)" : "rgba(255, 255, 255, 0.1)"}
                  strokeWidth={isHighlighted ? "1.5" : "0.5"}
                  className="transition-all duration-500"
                />
             );
          })}
        </g>

        {/* Travel Routes */}
        <g className="routes">
          {overlay.routes?.map((route, i) => {
            const startCoords = getCityCoords(route.from);
            const endCoords = getCityCoords(route.to);
            if (!startCoords || !endCoords) return null;

            const [x1, y1] = projection(startCoords) || [0, 0];
            const [x2, y2] = projection(endCoords) || [0, 0];

            // Documentary Arc calculation
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const dr = dist * (route.curve || 1.2);
            const pathData = `M${x1},${y1}A${dr},${dr} 0 0,1 ${x2},${y2}`;

            const routeReveal = interpolate(
              dataProgress * (overlay.routes?.length || 1),
              [i, i + 0.8],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            // Traveling point interpolation
            const totalDistance = calculateDistance(startCoords, endCoords);
            const currentDistance = Math.round(totalDistance * routeReveal);

            // Simple Bezier-like midpoint for the pulse
            const t = routeReveal;
            const mx = (1-t)*(1-t)*x1 + 2*(1-t)*t*((x1+x2)/2) + t*t*x2;
            const my = (1-t)*(1-t)*y1 + 2*(1-t)*t*((y1+y2)/2 - dr/4) + t*t*y2;

            return (
              <g key={`route-group-${i}`}>
                <path
                  key={`route-${i}`}
                  d={pathData}
                  fill="none"
                  stroke="rgba(59, 130, 246, 0.4)"
                  strokeWidth="2"
                  strokeDasharray="1000"
                  strokeDashoffset={1000 * (1 - routeReveal)}
                  style={{ filter: 'drop-shadow(0 0 5px rgba(59,130,246,0.3))' }}
                />

                {/* Traveling Marker */}
                {routeReveal > 0 && routeReveal < 1 && (
                  <g transform={`translate(${mx}, ${my})`}>
                    <circle r="12" fill="#3b82f6" className="animate-pulse" style={{ opacity: 0.3 }} />
                    <circle r="4" fill="white" stroke="#3b82f6" strokeWidth="2" />
                  </g>
                )}

                {/* Distance Telemetry */}
                {routeReveal > 0.1 && (
                  <text
                    x={(x1 + x2) / 2}
                    y={(y1 + y2) / 2 - 40}
                    fill="#3b82f6"
                    fontSize="12"
                    fontWeight="black"
                    textAnchor="middle"
                    className="font-mono tabular-nums uppercase tracking-widest"
                    style={{ opacity: routeReveal }}
                  >
                    {route.label || 'TRANSFER'}: {currentDistance} / {totalDistance} KM
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* City Nodes */}
        <g className="cities">
          {overlay.cities?.map((city, i) => {
            const coords = projection(city.coords);
            if (!coords) return null;
            const [cx, cy] = coords;

            const cityReveal = interpolate(
               dataProgress,
               [0.1 * i, 0.1 * i + 0.3],
               [0, 1],
               { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            return (
              <g key={`city-${i}`} style={{ opacity: cityReveal }}>
                <circle cx={cx} cy={cy} r="3" fill="white" />
                <text
                  x={cx + 10}
                  y={cy + 4}
                  fill="white"
                  fontSize="12"
                  fontWeight="bold"
                  className="font-mono uppercase"
                  style={{ textShadow: '0 0 10px rgba(0,0,0,0.8)' }}
                >
                  {city.name}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Documentary UI Layer */}
      <div className="absolute top-10 right-10 flex flex-col items-end gap-2">
         <div className="px-4 py-1 bg-blue-500/20 border border-blue-500/40 text-blue-400 font-mono text-[10px] font-black uppercase tracking-widest">
            Geospatial Analysis V4.2
         </div>
         <div className="text-white/40 font-mono text-[8px] uppercase tracking-tighter">
            COORD_SYS: WGS-84 / Mercator<br/>
            SCAN_SYNC: {Math.round(dataProgress * 100)}% COMPLETE
         </div>
      </div>

      <div className="absolute bottom-10 left-10">
         <h2 className="text-white font-black text-3xl tracking-tighter uppercase leading-none">{overlay.id}</h2>
         <p className="text-blue-500/60 font-mono text-[10px] mt-2 font-bold uppercase tracking-[0.5em]">Real-time Vector Simulation</p>
      </div>
    </div>
  );
};
