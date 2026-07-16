declare module 'react-xarrows' {
  import React from 'react';

  export interface XarrowProps {
    start: any;
    end: any;
    startAnchor?: any;
    endAnchor?: any;
    labels?: any;
    color?: string;
    lineColor?: string | null;
    headColor?: string | null;
    tailColor?: string | null;
    strokeWidth?: number;
    showHead?: boolean;
    headSize?: number;
    showTail?: boolean;
    tailSize?: number;
    path?: 'smooth' | 'grid' | 'straight';
    showXarrow?: boolean;
    curveness?: number;
    gridBreak?: string;
    dashness?: boolean | {
        strokeLen?: number;
        nonStrokeLen?: number;
        animation?: boolean | number;
    };
    headShape?: string | object;
    tailShape?: string | object;
    animateDrawing?: boolean | number;
    zIndex?: number;
    passProps?: any;
    SVGcanvasProps?: any;
    arrowBodyProps?: any;
    arrowHeadProps?: any;
    arrowTailProps?: any;
    divContainerProps?: any;
    SVGcanvasStyle?: React.CSSProperties;
    divContainerStyle?: React.CSSProperties;
    _extendSVGcanvas?: number;
    _debug?: boolean;
  }

  const Xarrow: React.FC<XarrowProps>;
  export default Xarrow;
  export const Xwrapper: React.FC<{ children: React.ReactNode }>;
  export function useXarrow(): () => void;
}
