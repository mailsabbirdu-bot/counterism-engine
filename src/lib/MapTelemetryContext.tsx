import { createContext, useContext, useRef } from 'react';

export interface MapTelemetry {
    pulseScreenCoords: { x: number, y: number } | null;
    focusScreenCoords: { x: number, y: number } | null;
    isArrived: boolean;
}

export const MapTelemetryContext = createContext<React.MutableRefObject<MapTelemetry> | null>(null);

export const useMapTelemetry = () => {
    return useContext(MapTelemetryContext);
};
