export interface CameraFocus {
    zoom?: number;
    offsetX?: number;
    offsetY?: number;
    padding?: number;
    preferredDuration?: number;
    moveStyle?: 'smooth' | 'whip' | 'dramatic';
    fitMode?: 'contain' | 'cover';
    focusBounds?: boolean;
}

export interface Overlay {
    id: string;
    type: 'text' | 'ui_panel' | 'shape' | 'chart' | 'graph' | 'video' | 'image' | 'data_indicator' | 'map';
    start: number;
    duration: number;
    zIndex?: number;
    depth?: number;
    position?: { x: number, y: number };
    width?: number;
    height?: number;
    cameraFocus?: CameraFocus;
    nodes?: any[];
    links?: any[];
    label?: string;
    pulse?: boolean;
    [key: string]: any;
}
