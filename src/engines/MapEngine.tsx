import React, { useMemo, useEffect, useState } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing, continueRender, delayRender, Img } from 'remotion';
import * as d3 from 'd3-geo';
import { feature } from 'topojson-client';
import { getBanglaName, fetchBoundary, fetchNeighbors } from '../lib/mapUtils';
import { useMapTelemetry } from '../lib/MapTelemetryContext';
import { resolveAsset } from '../lib/resolveAsset';

const WORLD_TOPO = "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

interface City {
  name: string;
  coords: [number, number];
  icon?: string;
}

interface Route {
  from: string;
  to: string;
  curve?: number;
  label?: string;
  type?: 'air' | 'sea' | 'land';
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
    focusDelay?: number;
    start: number;
    duration: number;
    position?: { x: number; y: number };
    width?: number;
    height?: number;
    zIndex?: number;
    depth?: number;
  };
}

const MarkerLayer: React.FC<{
  cities: City[];
  projection: d3.GeoProjection;
  progress: number;
}> = ({ cities, projection, progress }) => {
  return (
    <g>
      {cities.map((city, i) => {
        const coords = projection(city.coords);
        if (!coords) return null;

        const entrance = interpolate(progress, [0.1 + i * 0.05, 0.3 + i * 0.05], [0, 1], { extrapolateRight: 'clamp' });
        const scale = spring({ frame: progress * 100, fps: 30, config: { damping: 12 } });

        return (
          <g key={i} transform={`translate(${coords[0]}, ${coords[1]}) scale(${entrance * scale})`} style={{ opacity: entrance }}>
            {/* Outer Ring */}
            <circle r="12" fill="none" stroke="white" strokeWidth="2" opacity={0.5}>
               <animate attributeName="r" values="12;20;12" dur="2s" repeatCount="indefinite" />
               <animate attributeName="opacity" values="0.5;0;0.5" dur="2s" repeatCount="indefinite" />
            </circle>
            {/* Core */}
            {city.icon ? (
               <text fontSize="24" textAnchor="middle" dominantBaseline="middle" style={{ filter: 'drop-shadow(0 0 5px rgba(0,0,0,0.5))' }}>
                 {city.icon}
               </text>
            ) : (
               <circle r="6" fill="#4ade80" stroke="white" strokeWidth="2" />
            )}
            <text
              y="-18"
              fill="white"
              fontSize="14"
              fontWeight="900"
              textAnchor="middle"
              className="uppercase tracking-wider"
              style={{ filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.8))' }}
            >
              {city.name}
            </text>
          </g>
        );
      })}
    </g>
  );
};

const RouteLayer: React.FC<{
  routes: Route[];
  cities: City[];
  projection: d3.GeoProjection;
  progress: number;
}> = ({ routes, cities, projection, progress }) => {
  return (
    <g>
      {routes.map((route, i) => {
        const startCity = cities.find(c => c.name === route.from);
        const endCity = cities.find(c => c.name === route.to);
        if (!startCity || !endCity) return null;

        const p1 = projection(startCity.coords);
        const p2 = projection(endCity.coords);
        if (!p1 || !p2) return null;

        const mid: [number, number] = [
          (p1[0] + p2[0]) / 2,
          (p1[1] + p2[1]) / 2 - (route.curve || 0)
        ];

        const path = `M ${p1[0]} ${p1[1]} Q ${mid[0]} ${mid[1]} ${p2[0]} ${p2[1]}`;

        return (
          <g key={i}>
            {/* Glow Track */}
            <path
              d={path}
              fill="none"
              stroke="#4ade80"
              strokeWidth="4"
              style={{ opacity: progress * 0.2, filter: 'blur(4px)' }}
            />
            {/* Dashed Line */}
            <path
              d={path}
              fill="none"
              stroke="white"
              strokeWidth="2"
              strokeDasharray="8 4"
              pathLength="1"
              strokeDashoffset={1 - progress}
              style={{ opacity: 0.6 }}
            />
            {/* The moving pulse */}
            {(() => {
               const t = progress;
               const x = (1 - t) * (1 - t) * p1[0] + 2 * (1 - t) * t * mid[0] + t * t * p2[0];
               const y = (1 - t) * (1 - t) * p1[1] + 2 * (1 - t) * t * mid[1] + t * t * p2[1];

               return (
                 <g transform={`translate(${x}, ${y})`}>
                    <circle r="15" fill="#4ade80" opacity="0.3">
                      <animate attributeName="r" values="10;20;10" dur="1s" repeatCount="indefinite" />
                    </circle>
                    <circle r="5" fill="#4ade80" stroke="white" strokeWidth="2" />
                 </g>
               );
            })()}
          </g>
        );
      })}
    </g>
  );
};

const AreaPath = React.memo(({ feature, pathGenerator, borderDrawProgress, fill, stroke, opacity, isFocus, isArrived, arrivalColor }: any) => {
   const isDone = borderDrawProgress > 0.95;
   const d = useMemo(() => pathGenerator(feature) || '', [feature, pathGenerator]);

   const finalFill = isFocus && isArrived && arrivalColor ? arrivalColor : fill;
   const finalStroke = isFocus && isArrived && arrivalColor ? arrivalColor : stroke;

   let strokeWidth = isFocus ? (isArrived ? "10" : (isDone ? "6" : "3")) : "0.5";

   return (
      <path
        d={d}
        fill={finalFill}
        stroke={finalStroke}
        strokeWidth={strokeWidth}
        pathLength="1"
        strokeDasharray="1"
        strokeDashoffset={1 - borderDrawProgress}
        style={{
          opacity,
          transition: 'stroke-width 0.5s cubic-bezier(0.34, 1.56, 0.64, 1), stroke 0.5s ease',
          filter: (isFocus && isArrived) ? `drop-shadow(0 0 25px ${stroke})` : 'none'
        }}
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
  // Standard zoom level formula for Mercator
  const zoom = Math.max(0, Math.min(19, Math.round(Math.log2((scale * Math.PI) / 128))));

  const tiles = useMemo(() => {
    if (!projection.invert) return [];

    const centerLonLat = projection.invert([width / 2, height / 2]);
    if (!centerLonLat) return [];

    const lonToTileX = (lon: number, z: number) => (lon + 180) / 360 * Math.pow(2, z);
    const latToTileY = (lat: number, z: number) => (1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, z);

    const centerX = lonToTileX(centerLonLat[0], zoom);
    const centerY = latToTileY(centerLonLat[1], zoom);

    // Calculate how many tiles we need to cover the viewport
    // A tile is 256px at zoom Z. But we are at 'scale'.
    const tilesToCoverX = Math.ceil(width / 256) + 2;
    const tilesToCoverY = Math.ceil(height / 256) + 2;

    const t = [];
    for (let x = Math.floor(centerX - tilesToCoverX / 2); x <= Math.ceil(centerX + tilesToCoverX / 2); x++) {
      for (let y = Math.floor(centerY - tilesToCoverY / 2); y <= Math.ceil(centerY + tilesToCoverY / 2); y++) {
        t.push({ x, y, z: zoom });
      }
    }
    return t;
  }, [projection, width, height, zoom]);

  const filter = useMemo(() => {
    switch (theme) {
      case 'cinematic': return 'invert(100%) hue-rotate(180deg) brightness(0.8) contrast(1.2) saturate(0.8)';
      case 'light': return 'none';
      default: return 'invert(100%) hue-rotate(180deg) brightness(0.7) contrast(1.2)';
    }
  }, [theme]);

  return (
    <div className="absolute inset-0 pointer-events-none bg-zinc-900" style={{ filter }}>
      {tiles.map(tile => {
        const tileToLon = (x: number, z: number) => (x / Math.pow(2, z)) * 360 - 180;
        const tileToLat = (y: number, z: number) => {
          const n = Math.PI - (2 * Math.PI * y) / Math.pow(2, z);
          return (180 / Math.PI) * Math.atan(0.5 * (Math.exp(n) - Math.exp(-n)));
        };

        const [px, py] = projection([tileToLon(tile.x, tile.z), tileToLat(tile.y, tile.z)]) || [0, 0];
        const [nx, ny] = projection([tileToLon(tile.x + 1, tile.z), tileToLat(tile.y + 1, tile.z)]) || [0, 0];

        const w = nx - px;
        const h = ny - py;
        const wrappedX = (tile.x % Math.pow(2, tile.z) + Math.pow(2, tile.z)) % Math.pow(2, tile.z);

        if (tile.y < 0 || tile.y >= Math.pow(2, tile.z)) return null;

        return (
          <Img
            key={`${tile.z}/${tile.x}/${tile.y}`}
            src={`https://tile.openstreetmap.org/${tile.z}/${wrappedX}/${tile.y}.png`}
            style={{
              position: 'absolute',
              left: px,
              top: py,
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
  const telemetry = useMapTelemetry();
  const { width: videoWidth, height: videoHeight, fps } = useVideoConfig();

  const config = useMemo(() => ({
    useOsmTiles: true,
    showNeighbors: true,
    mapTheme: 'dark',
    ...overlay,
    ...(overlay as any).config
  }), [overlay]);
  const relativeFrame = frame - (overlay.start || 0);
  const width = overlay.width || config.width || videoWidth;
  const height = overlay.height || config.height || videoHeight;

  const [mapData, setMapData] = useState<any>(null);
  const [neighborData, setNeighborData] = useState<any[]>([]);
  const [worldData, setWorldData] = useState<any>(null);
  const [handle] = useState(() => delayRender('MapEngine Data Load'));

  useEffect(() => {
    const load = async () => {
      try {
        console.log(`[MapEngine] Loading data for ${config.focus || 'world'}...`);
        // Load background world context always for transitions
        const worldRes = await fetch(WORLD_TOPO);
        const worldRaw = await worldRes.json();
        setWorldData(feature(worldRaw, worldRaw.objects.countries as any));

        let mainData = null;
        if (config.focus && config.focus !== 'world') {
          mainData = await fetchBoundary(config.focus);
          console.log(`[MapEngine] Focus boundary loaded for ${config.focus}`);

          let neighbors: any[] = [];
          if (config.showNeighbors && mainData) {
            neighbors = await fetchNeighbors(mainData);
            console.log(`[MapEngine] Neighbors loaded: ${neighbors.length}`);
          }
          setNeighborData(neighbors);
          setMapData(mainData);
        } else if (config.topojson_url) {
          const res = await fetch(resolveAsset(config.topojson_url));
          const data = await res.json();
          const objName = config.object_name || 'countries';
          setMapData(feature(data, data.objects[objName] || Object.values(data.objects)[0] as any));
        } else {
          setMapData(feature(worldRaw, worldRaw.objects.countries as any));
        }
        continueRender(handle);
      } catch (e) {
        console.error("Map Load Error", e);
        continueRender(handle);
      }
    };
    load();
  }, [config.focus, config.topojson_url]);

  const { projection, pathGenerator } = useMemo(() => {
    const proj = d3.geoMercator().translate([width / 2, height / 2]);
    const pathGen = d3.geoPath().projection(proj);

    if (!mapData) {
       proj.scale(config.scale || 100).center(config.center || [0, 0]);
       return { projection: proj, pathGenerator: pathGen };
    }

    const features = mapData.features || [mapData];

    if (config.focus && config.focus !== 'world' && features.length > 0) {
      const focusFeature = features.find((f: any) => {
        const name = (f.properties?.name || f.properties?.NAME_1 || f.properties?.display_name || f.id || "").toString().toLowerCase();
        const search = config.focus!.toLowerCase();
        return name.includes(search) || search.includes(name.split(',')[0].toLowerCase());
      }) || features[0];

      if (config.scale) {
        proj.scale(config.scale).center(config.center || d3.geoCentroid(focusFeature));
      } else if (config.zoom) {
        const z = typeof config.zoom === 'string' ? parseFloat(config.zoom) : config.zoom;
        const s = (width * Math.pow(2, z)) / (2 * Math.PI);
        proj.scale(s).center(config.center || d3.geoCentroid(focusFeature));
      } else {
        proj.fitSize([width * 0.8, height * 0.8], focusFeature);
      }
    } else {
      if (config.zoom) {
        const z = typeof config.zoom === 'string' ? parseFloat(config.zoom) : config.zoom;
        const s = (width * Math.pow(2, z)) / (2 * Math.PI);
        proj.scale(s).center(config.center || [0, 20]);
      } else {
        proj.scale(config.scale || width / 6.5).center(config.center || [0, 20]);
      }
    }

    return { projection: proj, pathGenerator: pathGen };
  }, [mapData, width, height, config.focus, config.scale, config.zoom, config.center]);

  // Animations
  const entrance = spring({ frame: Math.max(0, relativeFrame), fps, config: { damping: 20 } });

  const duration = overlay.duration || 100;
  const exitStart = Math.max(0, duration - 15);
  const exitEnd = Math.max(exitStart + 1, duration);
  const exit = interpolate(relativeFrame, [exitStart, exitEnd], [1, 0], { extrapolateRight: 'clamp' });

  const drawStart = 10;
  const drawEnd = Math.max(drawStart + 1, Math.min(60, duration - 10));
  const drawProg = interpolate(relativeFrame, [drawStart, drawEnd], [0, 1], { extrapolateRight: 'clamp' });

  const travelStart = 60;
  const travelEnd = Math.max(travelStart + 1, duration - 10);
  const travelProg = interpolate(relativeFrame, [travelStart, travelEnd], [0, 1], { extrapolateRight: 'clamp' });
  const isArrived = travelProg > 0.99;

  // Telemetry
  useEffect(() => {
    if (!telemetry?.current || !mapData) return;
    const ox = overlay.position?.x ?? 960;
    const oy = overlay.position?.y ?? 540;

    telemetry.current.focusScreenCoords = { x: ox, y: oy };

    if (config.routes?.length > 0) {
      const r = config.routes[0];
      const startCity = config.cities?.find((c:any) => c.name === r.from);
      const endCity = config.cities?.find((c:any) => c.name === r.to);

      if (startCity && endCity) {
        const p1 = projection(startCity.coords);
        const p2 = projection(endCity.coords);

        if (p1 && p2) {
          const t = travelProg;
          const mid: [number, number] = [
            (p1[0] + p2[0]) / 2,
            (p1[1] + p2[1]) / 2 - (r.curve || 0)
          ];

          // Quadratic Bezier interpolation for screen-space sync
          const sx = (1 - t) * (1 - t) * p1[0] + 2 * (1 - t) * t * mid[0] + t * t * p2[0];
          const sy = (1 - t) * (1 - t) * p1[1] + 2 * (1 - t) * t * mid[1] + t * t * p2[1];

          telemetry.current.pulseScreenCoords = {
            x: ox + sx - width/2,
            y: oy + sy - height/2
          };
        }
      }
    }
  }, [frame, travelProg, projection, mapData]);

  if (relativeFrame < 0 || relativeFrame > (overlay.duration || Infinity)) return null;

  return (
    <div
      className="absolute overflow-hidden rounded-[3rem] border-2 border-white/20 shadow-2xl bg-black"
      style={{
        width, height,
        left: overlay.position?.x ?? 960,
        top: overlay.position?.y ?? 540,
        opacity: entrance * exit,
        transform: `translate(-50%, -50%) scale(${0.9 + entrance * 0.1})`,
        zIndex: overlay.zIndex || 30
      }}
    >
      {config.useOsmTiles && <TileLayer projection={projection} width={width} height={height} theme={config.mapTheme} />}

      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="relative z-10">
        {worldData && !config.useOsmTiles && (
          <g opacity={0.1}>
            {worldData.features.map((f: any, i: number) => (
              <path key={i} d={pathGenerator(f) || ''} fill="white" stroke="white" strokeWidth="0.5" />
            ))}
          </g>
        )}

        <g>
          {neighborData && neighborData.map((f: any, i: number) => (
             <AreaPath
                key={`neighbor-${i}`}
                feature={f}
                pathGenerator={pathGenerator}
                borderDrawProgress={drawProg * 0.8}
                fill="rgba(255,255,255,0.02)"
                stroke="rgba(255,255,255,0.1)"
                opacity={0.3}
                isFocus={false}
             />
          ))}
          {mapData && (mapData.features || [mapData]).map((f: any, i: number) => {
            const name = (f.properties?.name || f.properties?.NAME_1 || f.properties?.display_name || f.id || "").toString().toLowerCase();
            const isFocus = config.focus && (name.includes(config.focus.toLowerCase()) || config.focus.toLowerCase().includes(name));
            return (
              <AreaPath
                key={i}
                feature={f}
                pathGenerator={pathGenerator}
                borderDrawProgress={drawProg}
                fill={isFocus ? "rgba(74, 222, 128, 0.1)" : "rgba(255,255,255,0.05)"}
                stroke={isFocus ? "#4ade80" : "rgba(255,255,255,0.3)"}
                opacity={isFocus ? 1 : 0.4}
                isFocus={isFocus}
                isArrived={isArrived}
              />
            );
          })}
        </g>

        {config.cities && (
           <MarkerLayer
             cities={config.cities}
             projection={projection}
             progress={drawProg}
           />
        )}

        {config.routes && config.cities && (
           <RouteLayer
              routes={config.routes}
              cities={config.cities}
              projection={projection}
              progress={travelProg}
           />
        )}

        {config.showLabels && mapData && (mapData.features || [mapData]).map((f: any, i: number) => {
          const coords = projection(d3.geoCentroid(f));
          if (!coords) return null;
          return (
            <text
              key={i}
              x={coords[0]}
              y={coords[1]}
              fill="white"
              fontSize={24}
              fontWeight="bold"
              textAnchor="middle"
              style={{ opacity: drawProg, textShadow: '0 2px 10px black' }}
            >
              {getBanglaName(f.properties) || f.properties?.name || f.id}
            </text>
          );
        })}
      </svg>

        {config.useOsmTiles && config.focus && (
         <div className="absolute top-10 left-10 p-4 bg-black/60 backdrop-blur-md rounded-xl border border-white/20 z-20">
            <div className="text-[10px] text-blue-400 font-mono tracking-widest uppercase">Live Geo Intel</div>
            <div className="text-white font-bold text-xl uppercase">{config.focus}</div>
         </div>
      )}
    </div>
  );
};
