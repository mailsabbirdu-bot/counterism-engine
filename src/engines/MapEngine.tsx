import React, { useMemo, useEffect, useState, useRef } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing, continueRender, delayRender } from 'remotion';
import * as d3 from 'd3-geo';
import { feature } from 'topojson-client';

// Professional TopoJSON Sources
const WORLD_TOPO = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Global cache to prevent redundant fetches
const mapCache: Record<string, any> = {};

interface City {
  name: string;
  coords: [number, number]; // [lon, lat]
}

interface MapOverlayProps {
  overlay: {
    id: string;
    center?: [number, number];
    scale?: number;
    cities?: City[];
    routes?: { from: string; to: string; curve?: number; label?: string; type?: 'air' | 'sea' | 'land' }[];
    highlights?: string[];
    topojson_url?: string;
    object_name?: string;
    start: number;
    duration: number;
    position?: { x: number; y: number };
    width?: number;
    height?: number;
    zIndex?: number;
  };
}

export const MapEngine: React.FC<MapOverlayProps> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();
  const relativeFrame = frame - overlay.start;

  const width = overlay.width || 1200;
  const height = overlay.height || 800;

  const [mapData, setMapData] = useState<any>(null);
  const [handle] = useState(() => delayRender('Loading SVG Map Data'));

  useEffect(() => {
    const url = overlay.topojson_url || WORLD_TOPO;
    const objName = overlay.object_name || 'countries';
    const cacheKey = `${url}-${objName}`;

    if (mapCache[cacheKey]) {
      setMapData(mapCache[cacheKey]);
      continueRender(handle);
      return;
    }

    fetch(url)
      .then(res => res.json())
      .then(data => {
        const obj = data.objects[objName] || Object.values(data.objects)[0];
        if (!obj) throw new Error(`Object ${objName} not found in TopoJSON`);
        const geojson = feature(data, obj as any);
        mapCache[cacheKey] = geojson;
        setMapData(geojson);
        continueRender(handle);
      })
      .catch(err => {
        console.error("Map Data Fetch Error:", err);
        setMapData({ features: [] });
        continueRender(handle);
      });
  }, [overlay.topojson_url, overlay.object_name]);

  // 1. Precise Geodesic Projection
  const projection = useMemo(() => {
    return d3.geoMercator()
      .scale(overlay.scale || 200)
      .center(overlay.center || [0, 20])
      .translate([width / 2, height / 2]);
  }, [overlay.scale, overlay.center, width, height]);

  const pathGenerator = d3.geoPath().projection(projection);

  // 2. Cinematic Timings
  const entrance = spring({ frame: relativeFrame, fps, config: { damping: 20 } });
  const exitFrame = overlay.duration - 15;
  const exit = interpolate(relativeFrame, [exitFrame, exitFrame + 15], [1, 0], { extrapolateRight: 'clamp' });

  const borderDrawProgress = interpolate(relativeFrame, [20, 100], [0, 1], { extrapolateRight: 'clamp', easing: Easing.bezier(0.4, 0, 0.2, 1) });
  const travelProgress = interpolate(relativeFrame, [80, overlay.duration - 40], [0, 1], { extrapolateRight: 'clamp' });

  // 3. Helpers
  const getCityCoords = (name: string) => overlay.cities?.find(c => c.name === name)?.coords;

  const calculateDistance = (c1: [number, number], c2: [number, number]) => {
    const R = 6371;
    const dLat = (c2[1] - c1[1]) * Math.PI / 180;
    const dLon = (c2[0] - c1[0]) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(c1[1]*Math.PI/180) * Math.cos(c2[1]*Math.PI/180) * Math.sin(dLon/2)**2;
    return Math.round(R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a)));
  };

  if (frame < overlay.start || frame > overlay.start + overlay.duration || !mapData) return null;

  return (
    <div
      className="absolute bg-zinc-950/80 backdrop-blur-3xl rounded-[3rem] border-2 border-white/20 shadow-[0_60px_100px_rgba(0,0,0,0.8)] overflow-hidden"
      style={{
        width, height,
        left: `${overlay.position?.x ?? 960}px`,
        top: `${overlay.position?.y ?? 540}px`,
        opacity: entrance * exit,
        zIndex: overlay.zIndex ?? 30,
        transform: `translate(-50%, -50%) scale(${0.95 + entrance * 0.05})`,
      }}
    >
      {/* Technical Grid Overlay */}
      <div className="absolute inset-0 opacity-10 pointer-events-none"
           style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)', backgroundSize: '40px 40px' }} />

      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="relative z-10">
        {/* Animated Borders & Territories */}
        <g>
          {useMemo(() => mapData.features.map((feature: any, i: number) => {
            const countryName = feature.properties.name || feature.properties.NAME_1 || feature.id;
            const isHighlighted = overlay.highlights?.some(h => h.toLowerCase() === countryName?.toString().toLowerCase());
            const path = pathGenerator(feature);

            return (
              <path
                key={`border-${i}`}
                d={path || ''}
                fill={isHighlighted ? "rgba(59, 130, 246, 0.2)" : "rgba(255, 255, 255, 0.03)"}
                stroke={isHighlighted ? "rgba(59, 130, 246, 0.8)" : "rgba(255, 255, 255, 0.1)"}
                strokeWidth={isHighlighted ? "2" : "0.5"}
                pathLength="1"
                strokeDasharray="1"
                strokeDashoffset={1 - borderDrawProgress}
                style={{ transition: 'fill 0.5s ease' }}
              />
            );
          }), [mapData, borderDrawProgress, overlay.highlights, pathGenerator])}
        </g>

        {/* Dynamic Travel Routes */}
        <g>
          {overlay.routes?.map((route, i) => {
            const startCoords = getCityCoords(route.from);
            const endCoords = getCityCoords(route.to);
            if (!startCoords || !endCoords) return null;

            const [x1, y1] = projection(startCoords) || [0, 0];
            const [x2, y2] = projection(endCoords) || [0, 0];

            // Cinematic Arc
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dist = Math.sqrt(dx * dx + dy * dy);
            const dr = dist * (route.curve || 1.3);
            const pathData = `M${x1},${y1}A${dr},${dr} 0 0,1 ${x2},${y2}`;

            const routeReveal = interpolate(
              travelProgress * (overlay.routes?.length || 1),
              [i, i + 0.8],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            // Interpolate point along the path
            const t = routeReveal;
            const mx = (1-t)*(1-t)*x1 + 2*(1-t)*t*((x1+x2)/2) + t*t*x2;
            const my = (1-t)*(1-t)*y1 + 2*(1-t)*t*((y1+y2)/2 - dr/4) + t*t*y2;

            const km = calculateDistance(startCoords, endCoords);

            return (
              <g key={`route-${i}`}>
                {/* Background Shadow Path */}
                <path d={pathData} fill="none" stroke="rgba(0,0,0,0.5)" strokeWidth="4" />

                {/* Animated Line */}
                <path
                  d={pathData}
                  fill="none"
                  stroke={route.type === 'sea' ? "#0ea5e9" : "#3b82f6"}
                  strokeWidth="2"
                  strokeDasharray="8 4"
                  strokeDashoffset={-frame * 2}
                  opacity={routeReveal}
                />

                {/* The "Drawn" Path */}
                <path
                  d={pathData}
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  pathLength="1"
                  strokeDasharray="1"
                  strokeDashoffset={1 - routeReveal}
                />

                {/* Traveling Icon/Pulse */}
                {routeReveal > 0 && routeReveal < 1 && (
                  <g transform={`translate(${mx}, ${my})`}>
                    <circle r="15" fill="#3b82f6" className="animate-ping" style={{ opacity: 0.4 }} />
                    <circle r="5" fill="white" stroke="#3b82f6" strokeWidth="2" shadow-xl />
                  </g>
                )}

                {/* Real-time Telemetry */}
                {routeReveal > 0.05 && (
                  <text
                    x={(x1 + x2) / 2}
                    y={(y1 + y2) / 2 - 30}
                    fill="white"
                    fontSize="10"
                    fontWeight="900"
                    textAnchor="middle"
                    className="font-mono tracking-tighter"
                    style={{ opacity: routeReveal }}
                  >
                    {route.label || 'TRANSIT'}: {Math.round(km * routeReveal)} / {km} KM
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* City Infrastructure */}
        <g>
          {overlay.cities?.map((city, i) => {
            const coords = projection(city.coords);
            if (!coords) return null;
            const [cx, cy] = coords;

            const cityReveal = spring({
               frame: relativeFrame - (i * 10),
               fps,
               config: { stiffness: 200 }
            });

            return (
              <g key={`city-${i}`} style={{ opacity: cityReveal, transform: `scale(${cityReveal})` }}>
                <circle cx={cx} cy={cy} r="3" fill="white" />
                <circle cx={cx} cy={cy} r="8" fill="none" stroke="rgba(255,255,255,0.2)" strokeWidth="1" />
                <text
                  x={cx + 12}
                  y={cy + 4}
                  fill="white"
                  fontSize="12"
                  fontWeight="black"
                  className="font-mono uppercase tracking-tighter"
                  style={{ textShadow: '0 2px 10px rgba(0,0,0,1)' }}
                >
                  {city.name}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Documentary UI Chrome */}
      <div className="absolute top-12 left-12 flex items-center gap-6">
         <div className="w-16 h-16 rounded-full border-4 border-blue-500/30 flex items-center justify-center">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
         </div>
         <div>
            <h2 className="text-white font-black text-5xl tracking-tighter uppercase leading-none">Global Sector</h2>
            <p className="text-blue-400 font-mono text-xs mt-2 font-bold tracking-[0.5em] uppercase opacity-60 overflow-hidden whitespace-nowrap">
               Vector-Mapping Protocol: {Math.random().toString(16).slice(2, 10).toUpperCase()}
            </p>
         </div>
      </div>

      <div className="absolute bottom-12 right-12 text-right">
         <div className="text-blue-500 font-mono text-4xl font-black tabular-nums">
            {Math.round(travelProgress * 100)}%
         </div>
         <div className="text-white/30 font-mono text-[10px] uppercase tracking-widest font-bold">Simulation Progress</div>
      </div>
    </div>
  );
};
