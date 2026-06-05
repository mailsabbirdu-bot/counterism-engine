import React, { useMemo, useEffect, useState, useRef } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing, continueRender, delayRender, staticFile } from 'remotion';
import * as d3 from 'd3-geo';
import { feature } from 'topojson-client';

// Professional TopoJSON Sources
const WORLD_TOPO = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Global cache to prevent redundant fetches
const mapCache: Record<string, any> = {};
let metadataCache: any = null;

interface City {
  name: string;
  coords: [number, number]; // [lon, lat]
}

interface MapOverlayProps {
  overlay: {
    id: string;
    center?: [number, number];
    scale?: number;
    focus?: string;
    zoom?: string | number;
    useOsmTiles?: boolean;
    mapTheme?: 'dark' | 'light' | 'cinematic';
    showNeighbors?: boolean;
    showLabels?: boolean;
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

const AreaPath = React.memo(({ feature, pathGenerator, isHighlighted, borderDrawProgress, fill, stroke, opacity, isFocus }: any) => {
   return (
      <path
        d={pathGenerator(feature) || ''}
        fill={fill}
        stroke={stroke}
        strokeWidth={isFocus ? "2" : "0.5"}
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={1 - borderDrawProgress}
        style={{ opacity, transition: 'all 0.5s ease' }}
      />
   );
});

const TileLayer: React.FC<{
  projection: d3.GeoProjection;
  width: number;
  height: number;
  theme?: string;
}> = ({ projection, width, height, theme }) => {
  const scale = projection.scale();

  // OSM zoom level calculation for D3 Mercator
  const zoom = Math.max(0, Math.min(19, Math.floor(Math.log2((scale * Math.PI) / 128))));

  const tiles = useMemo(() => {
    if (!projection.invert) return [];
    const tl = projection.invert([0, 0]);
    const br = projection.invert([width, height]);
    if (!tl || !br) return [];

    const lonToTileX = (lon: number, z: number) => (lon + 180) / 360 * Math.pow(2, z);
    const latToTileY = (lat: number, z: number) => (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, z);

    const x0 = Math.floor(lonToTileX(tl[0], zoom));
    const x1 = Math.floor(lonToTileX(br[0], zoom));
    const y0 = Math.floor(latToTileY(tl[1], zoom));
    const y1 = Math.floor(latToTileY(br[1], zoom));

    const t = [];
    for (let x = x0; x <= x1; x++) {
      for (let y = Math.min(y0, y1); y <= Math.max(y0, y1); y++) {
        t.push({ x, y, z: zoom });
      }
    }
    return t;
  }, [projection, width, height, zoom]);

  const getTileStyles = () => {
    switch (theme) {
      case 'cinematic':
        return { filter: 'invert(100%) hue-rotate(180deg) brightness(0.6) contrast(1.2) saturate(0.5)' };
      case 'light':
        return { filter: 'none' };
      default: // dark
        return { filter: 'invert(100%) hue-rotate(180deg) brightness(0.6) contrast(1.2)' };
    }
  };

  return (
    <div className="absolute inset-0 pointer-events-none overflow-hidden" style={getTileStyles()}>
      {tiles.map(tile => {
        const tileToLon = (x: number, z: number) => (x / Math.pow(2, z)) * 360 - 180;
        const tileToLat = (y: number, z: number) => {
          const n = Math.PI - (2 * Math.PI * y) / Math.pow(2, z);
          return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
        };

        const lon = tileToLon(tile.x, tile.z);
        const lat = tileToLat(tile.y, tile.z);
        const [px, py] = projection([lon, lat]) || [0, 0];

        const nextLon = tileToLon(tile.x + 1, tile.z);
        const nextLat = tileToLat(tile.y + 1, tile.z);
        const [npx, npy] = projection([nextLon, nextLat]) || [0, 0];

        const w = npx - px;
        const h = npy - py;
        const wrappedX = (tile.x % Math.pow(2, tile.z) + Math.pow(2, tile.z)) % Math.pow(2, tile.z);

        return (
          <img
            key={`${tile.z}/${tile.x}/${tile.y}`}
            src={`https://tile.openstreetmap.org/${tile.z}/${wrappedX}/${tile.y}.png`}
            loading="eager"
            style={{
              position: 'absolute',
              left: px - 0.5,
              top: py - 0.5,
              width: Math.abs(w) + 1,
              height: Math.abs(h) + 1,
            }}
          />
        );
      })}
    </div>
  );
};

export const MapEngine: React.FC<MapOverlayProps> = ({ overlay }) => {
  const frame = useCurrentFrame();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();
  const [metadata, setMetadata] = useState<any>(null);
  const relativeFrame = frame - overlay.start;

  const width = overlay.width || 1200;
  const height = overlay.height || 800;

  const [mapData, setMapData] = useState<any>(null);
  const [neighborsData, setNeighborsData] = useState<any[]>([]);
  const [handle] = useState(() => delayRender('Loading Map Geometry'));

  useEffect(() => {
    const loadMapData = async () => {
      try {
        // 1. Fetch Metadata
        let currentMetadata = metadataCache;
        if (!currentMetadata) {
          try {
            const res = await fetch(staticFile('/maps/metadata.json'));
            currentMetadata = await res.json();
            metadataCache = currentMetadata;
          } catch (e) {
            console.warn("Metadata load failed", e);
          }
        }
        setMetadata(currentMetadata);

        const focusEntry = currentMetadata ? currentMetadata[overlay.focus || ''] : null;
        const features: any[] = [];

        // 2. Load Focus Area (from cache if available)
        if (focusEntry) {
          const cacheUrl = staticFile(`/maps/cache/${focusEntry.id}.geojson`);
          if (mapCache[cacheUrl]) {
            features.push(...mapCache[cacheUrl].features);
          } else {
            const res = await fetch(cacheUrl);
            const data = await res.json();
            mapCache[cacheUrl] = data;
            features.push(...data.features);
          }

          // 3. Load Neighbors if requested
          if (overlay.showNeighbors && focusEntry.neighbors) {
            const nData = [];
            for (const neighborName of focusEntry.neighbors) {
              const nEntry = currentMetadata[neighborName];
              if (nEntry) {
                const nUrl = staticFile(`/maps/cache/${nEntry.id}.geojson`);
                if (mapCache[nUrl]) {
                  nData.push(...mapCache[nUrl].features);
                } else {
                  try {
                    const res = await fetch(nUrl);
                    const data = await res.json();
                    mapCache[nUrl] = data;
                    nData.push(...data.features);
                  } catch (e) {
                    console.warn(`Failed to load neighbor: ${neighborName}`);
                  }
                }
              }
            }
            setNeighborsData(nData);
          }
        }

        // 4. Fallback to TopoJSON if no focus features found
        if (features.length === 0) {
          const url = overlay.topojson_url || WORLD_TOPO;
          const objName = overlay.object_name || 'countries';
          const cacheKey = `${url}-${objName}`;

          if (mapCache[cacheKey]) {
            setMapData(mapCache[cacheKey]);
          } else {
            const res = await fetch(url);
            const data = await res.json();
            const obj = data.objects[objName] || Object.values(data.objects)[0];
            const geojson = feature(data, obj as any);
            mapCache[cacheKey] = geojson;
            setMapData(geojson);
          }
        } else {
          setMapData({ type: 'FeatureCollection', features });
        }

        continueRender(handle);
      } catch (err) {
        console.error("Map Data Loading Error:", err);
        setMapData({ type: 'FeatureCollection', features: [] });
        continueRender(handle);
      }
    };

    loadMapData();
  }, [overlay.topojson_url, overlay.object_name, overlay.focus, overlay.showNeighbors]);

  // 1. Precise Geodesic Projection with Auto-Fit capability
  const { projection, pathGenerator } = useMemo(() => {
    const proj = d3.geoMercator();
    const pathGen = d3.geoPath().projection(proj);

    if (overlay.focus && mapData) {
       const focusFeature = mapData.features.find((f: any) =>
          (f.properties.name || f.properties.NAME_1 || f.id)?.toString().toLowerCase() === overlay.focus?.toLowerCase()
       );
       if (focusFeature) {
          proj.fitSize([width, height], focusFeature);
          // Apply a bit of padding/zoom margin if requested
          if (overlay.zoom === 'auto') {
             const currentScale = proj.scale();
             proj.scale(currentScale * 0.8);
          }
       } else {
          proj.scale(overlay.scale || 200)
              .center(overlay.center || [0, 20])
              .translate([width / 2, height / 2]);
       }
    } else {
       proj.scale(overlay.scale || 200)
           .center(overlay.center || [0, 20])
           .translate([width / 2, height / 2]);
    }

    return { projection: proj, pathGenerator: pathGen };
  }, [overlay.scale, overlay.center, overlay.focus, overlay.zoom, width, height, mapData]);

  // 2. Cinematic Timings
  const entrance = spring({ frame: relativeFrame, fps, config: { damping: 20 } });
  const exitFrame = overlay.duration - 15;
  const exit = interpolate(relativeFrame, [exitFrame, exitFrame + 15], [1, 0], { extrapolateRight: 'clamp' });

  const borderDrawProgress = interpolate(relativeFrame, [10, Math.min(120, overlay.duration - 30)], [0, 1], { extrapolateRight: 'clamp', easing: Easing.bezier(0.22, 1, 0.36, 1) });
  const travelProgress = interpolate(relativeFrame, [60, overlay.duration - 30], [0, 1], { extrapolateRight: 'clamp' });

  // Staggered opacity for "ping" effect using Remotion
  const pingScale = interpolate((relativeFrame % 30), [0, 30], [1, 3], { extrapolateRight: 'clamp' });
  const pingOpacity = interpolate((relativeFrame % 30), [0, 30], [0.6, 0], { extrapolateRight: 'clamp' });

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
      {/* 1. Tile Layer (OSM) */}
      {overlay.useOsmTiles && (
        <TileLayer projection={projection} width={width} height={height} theme={overlay.mapTheme} />
      )}

      {/* Technical Grid Overlay */}
      <div className="absolute inset-0 opacity-10 pointer-events-none"
           style={{ backgroundImage: 'radial-gradient(circle at 2px 2px, rgba(255,255,255,0.15) 1px, transparent 0)', backgroundSize: '40px 40px' }} />

      <svg width="100%" height="100%" viewBox={`0 0 ${width} ${height}`} className="relative z-10">
        {/* Animated Borders & Territories */}
        <g>
          {/* 1. Neighbors Layer */}
          {neighborsData.map((feature: any, i: number) => (
             <AreaPath
                key={`neighbor-${i}`}
                feature={feature}
                pathGenerator={pathGenerator}
                isFocus={false}
                fill="rgba(59, 130, 246, 0.1)"
                stroke="rgba(59, 130, 246, 0.3)"
                opacity={0.4}
                borderDrawProgress={borderDrawProgress}
              />
          ))}

          {/* 2. Primary Features Layer */}
          {mapData.features.map((feature: any, i: number) => {
            const countryName = feature.properties.name || feature.properties.NAME_1 || feature.id;
            const isFocus = overlay.focus && countryName?.toString().toLowerCase() === overlay.focus.toLowerCase();

            const isHighlighted = overlay.highlights?.some(h => h.toLowerCase() === countryName?.toString().toLowerCase()) || isFocus;

            // Documentary highlight style
            const opacity = isFocus ? 1 : 0.1;
            const fill = isFocus ? "rgba(59, 130, 246, 0.4)" : "rgba(255, 255, 255, 0.03)";
            const stroke = isFocus ? "rgba(59, 130, 246, 1)" : "rgba(255, 255, 255, 0.1)";

            return (
               <AreaPath
                key={`border-${i}`}
                feature={feature}
                pathGenerator={pathGenerator}
                isFocus={isFocus}
                isHighlighted={isHighlighted}
                fill={fill}
                stroke={stroke}
                opacity={opacity}
                borderDrawProgress={borderDrawProgress}
              />
            );
          })}
        </g>

        {/* Dynamic Travel Routes */}
        <g>
          {overlay.routes?.map((route, i) => {
            const startCoords = getCityCoords(route.from);
            const endCoords = getCityCoords(route.to);
            if (!startCoords || !endCoords) return null;

            const [x1, y1] = projection(startCoords) || [0, 0];
            const [x2, y2] = projection(endCoords) || [0, 0];

            // High-Resolution Geodesic Path (for curvature on long routes)
            const interpolator = d3.geoInterpolate(startCoords, endCoords);
            const samples = 50;
            const geojsonLine = {
              type: 'LineString',
              coordinates: Array.from({ length: samples + 1 }, (_, i) => interpolator(i / samples))
            };
            const pathData = pathGenerator(geojsonLine as any);

            const routeReveal = interpolate(
              travelProgress * (overlay.routes?.length || 1),
              [i, i + 0.8],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            // Geodesic interpolation for the traveling marker
            const currentCoords = interpolator(routeReveal);
            const [mx, my] = projection(currentCoords) || [0, 0];

            const km = calculateDistance(startCoords, endCoords);

            return (
              <g key={`route-${i}`}>
                {/* Background Shadow Path */}
                <path d={pathData || ''} fill="none" stroke="rgba(0,0,0,0.5)" strokeWidth="4" />

                {/* Animated Line */}
                <path
                  d={pathData || ''}
                  fill="none"
                  stroke={route.type === 'sea' ? "#0ea5e9" : "#3b82f6"}
                  strokeWidth={route.type === 'sea' ? "3" : "2"}
                  strokeDasharray={route.type === 'sea' ? "10 5" : "8 4"}
                  strokeDashoffset={-frame * (route.type === 'sea' ? 1.5 : 2.5)}
                  opacity={routeReveal * 0.6}
                />

                {/* The "Drawn" Path */}
                <path
                  d={pathData || ''}
                  fill="none"
                  stroke="white"
                  strokeWidth="2"
                  pathLength="1"
                  strokeDasharray="1"
                  strokeDashoffset={1 - routeReveal}
                />

                {/* Start Marker */}
                <g transform={`translate(${x1}, ${y1})`}>
                   <circle r={8 * pingScale} fill="#3b82f6" style={{ opacity: pingOpacity }} />
                   <circle r="4" fill="white" stroke="#3b82f6" strokeWidth="2" />
                </g>

                {/* End Marker */}
                <g transform={`translate(${x2}, ${y2})`}>
                   {routeReveal > 0.95 && <circle r={12 * pingScale} fill="#10b981" style={{ opacity: pingOpacity }} />}
                   <circle r="4" fill={routeReveal > 0.95 ? "#10b981" : "white"} stroke="white" strokeWidth="2" />
                </g>

                {/* Traveling Icon/Pulse */}
                {routeReveal > 0 && routeReveal < 1 && (
                  <g transform={`translate(${mx}, ${my})`}>
                    <circle r={10 * pingScale} fill="#3b82f6" style={{ opacity: pingOpacity }} />
                    <circle r="6" fill="white" stroke="#3b82f6" strokeWidth="2" />
                    {/* Direction Indicator */}
                    <path d="M -4 -4 L 4 0 L -4 4 Z" fill="#3b82f6" transform={`rotate(${Math.atan2(y2-y1, x2-x1) * 180 / Math.PI})`} />
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

        {/* Automatic Labels from Metadata */}
        <g>
           {overlay.showLabels && metadata && Object.entries(metadata).map(([name, data]: [string, any], i) => {
              if (!data.centroid) return null;
              const coords = projection(data.centroid);
              if (!coords) return null;
              const [lx, ly] = coords;

              const isFocus = overlay.focus && name.toLowerCase() === overlay.focus.toLowerCase();
              const isNeighbor = overlay.showNeighbors && metadata?.[overlay.focus || '']?.neighbors?.some(
                (n: string) => n.toLowerCase() === name.toLowerCase()
              );

              if (!isFocus && !isNeighbor) return null;

              return (
                <text
                  key={`label-${i}`}
                  x={lx}
                  y={ly}
                  fill="white"
                  fontSize={isFocus ? "14" : "10"}
                  fontWeight={isFocus ? "black" : "normal"}
                  textAnchor="middle"
                  className="font-mono uppercase"
                  style={{ opacity: borderDrawProgress, textShadow: '0 0 10px black' }}
                >
                  {name}
                </text>
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
