import { Point } from './AnchorResolver';

export const PathGenerator = {
  generateSmoothCurve: (start: Point, end: Point): string => {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const cp1x = start.x + dx * 0.5;
    const cp1y = start.y;
    const cp2x = start.x + dx * 0.5;
    const cp2y = end.y;
    return `M ${start.x} ${start.y} C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${end.x} ${end.y}`;
  },

  generateSPath: (start: Point, end: Point): string => {
    const midY = (start.y + end.y) / 2;
    return `M ${start.x} ${start.y} C ${start.x} ${midY}, ${end.x} ${midY}, ${end.x} ${end.y}`;
  },

  generateZigzagPath: (start: Point, end: Point): string => {
    const midX = (start.x + end.x) / 2;
    return `M ${start.x} ${start.y} L ${midX} ${start.y} L ${midX} ${end.y} L ${end.x} ${end.y}`;
  },

  generateArcPath: (start: Point, end: Point): string => {
    const dx = end.x - start.x;
    const dy = end.y - start.y;
    const dr = Math.sqrt(dx * dx + dy * dy);
    return `M ${start.x} ${start.y} A ${dr} ${dr} 0 0 1 ${end.x} ${end.y}`;
  },

  generateBranchPath: (start: Point, end: Point): string => {
    // Simple implementation for multi-branch start
    return `M ${start.x} ${start.y} L ${start.x + 50} ${start.y} L ${end.x} ${end.y}`;
  },

  generateStraightPath: (start: Point, end: Point): string => {
    return `M ${start.x} ${start.y} L ${end.x} ${end.y}`;
  }
};
