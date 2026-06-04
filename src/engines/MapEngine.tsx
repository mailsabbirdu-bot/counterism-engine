import React, { useMemo } from 'react';
import { useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from 'remotion';
import * as d3 from 'd3-geo';
import worldData from '../../public/world.json';

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
    routes?: { from: string; to: string; curve?: number }[];
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

  // 1. Setup Projection
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
    [30, 120],
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

  if (frame < overlay.start || frame > overlay.start + overlay.duration) {
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
        {/* World Map Background */}
        <g className="map-base">
          {(worldData as any).features.map((feature: any, i: number) => (
            <path
              key={`country-${i}`}
              d={pathGenerator(feature) || ''}
              fill="rgba(255, 255, 255, 0.05)"
              stroke="rgba(255, 255, 255, 0.1)"
              strokeWidth="0.5"
            />
          ))}
        </g>

        {/* Sea Routes / Connections */}
        <g className="routes">
          {overlay.routes?.map((route, i) => {
            const startCoords = getCityCoords(route.from);
            const endCoords = getCityCoords(route.to);
            if (!startCoords || !endCoords) return null;

            const [x1, y1] = projection(startCoords) || [0, 0];
            const [x2, y2] = projection(endCoords) || [0, 0];

            // Create a curved path
            const dx = x2 - x1;
            const dy = y2 - y1;
            const dr = Math.sqrt(dx * dx + dy * dy) * (route.curve || 1.5);
            const pathData = `M${x1},${y1}A${dr},${dr} 0 0,1 ${x2},${y2}`;

            const routeReveal = interpolate(
              dataProgress * (overlay.routes?.length || 1),
              [i, i + 1],
              [0, 1],
              { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
            );

            // Calculate distance for the label
            const distance = calculateDistance(startCoords, endCoords);

            // Simple mid-point for marker/label (not perfect for arcs but good for viz)
            const mx = x1 + (x2 - x1) * routeReveal;
            const my = y1 + (y2 - y1) * routeReveal - (Math.sin(routeReveal * Math.PI) * dr * 0.2);

            return (
              <g key={`route-group-${i}`}>
                <path
                  key={`route-${i}`}
                  d={pathData}
                  fill="none"
                  stroke="rgba(59, 130, 246, 0.6)"
                  strokeWidth="3"
                  strokeDasharray="1000"
                  strokeDashoffset={1000 * (1 - routeReveal)}
                  style={{
                    filter: 'drop-shadow(0 0 8px rgba(59,130,246,0.4))',
                    opacity: routeReveal
                  }}
                />
                {routeReveal > 0 && routeReveal < 1 && (
                  <circle
                    cx={mx}
                    cy={my}
                    r="6"
                    fill="#white"
                    stroke="#3b82f6"
                    strokeWidth="2"
                    style={{ filter: 'drop-shadow(0 0 10px #3b82f6)' }}
                  />
                )}
                {routeReveal > 0.5 && (
                  <text
                    x={(x1 + x2) / 2}
                    y={(y1 + y2) / 2 - 20}
                    fill="rgba(59, 130, 246, 0.9)"
                    fontSize="12"
                    fontWeight="bold"
                    textAnchor="middle"
                    className="font-mono"
                    style={{ opacity: (routeReveal - 0.5) * 2 }}
                  >
                    {distance} KM
                  </text>
                )}
              </g>
            );
          })}
        </g>

        {/* Cities / Points of Interest */}
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
                {/* Glow Effect */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={8 * cityReveal}
                  fill="#3b82f6"
                  className="animate-pulse"
                  style={{ opacity: 0.4 }}
                />
                {/* Core Point */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={4 * cityReveal}
                  fill="white"
                  stroke="#3b82f6"
                  strokeWidth="2"
                />
                {/* Label */}
                <text
                  x={cx + 12}
                  y={cy + 4}
                  fill="white"
                  fontSize="14"
                  fontWeight="bold"
                  className="font-mono uppercase tracking-tighter"
                  style={{ textShadow: '0 0 10px rgba(0,0,0,0.8)' }}
                >
                  {city.name}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Map Header */}
      <div className="absolute top-10 left-10">
         <h2 className="text-white font-black text-4xl tracking-tighter uppercase">Geospatial Intelligence</h2>
         <p className="text-blue-400 font-mono text-xs mt-2 tracking-[0.3em] font-bold">Network & Route Analysis Active</p>
      </div>
    </div>
  );
};
