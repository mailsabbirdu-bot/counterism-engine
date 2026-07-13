import { getArrow } from 'perfect-arrows';

export interface Point {
  x: number;
  y: number;
}

export const getBezierPath = (s: Point, t: Point, curvature: number = 0.3): string => {
  const dx = t.x - s.x;
  const dy = t.y - s.y;
  const dist = Math.sqrt(dx * dx + dy * dy);

  const midX = (s.x + t.x) / 2 + (dy * curvature);
  const midY = (s.y + t.y) / 2 - (dx * curvature);

  return `M ${s.x} ${s.y} Q ${midX} ${midY} ${t.x} ${t.y}`;
};

export const getArrowData = (s: Point, t: Point) => {
  const arrow = getArrow(s.x, s.y, t.x, t.y, {
    bow: 0.2,
    stretch: 0.5,
    stretchMin: 0,
    stretchMax: 1,
    padStart: 0,
    padEnd: 20,
    flip: false,
    straights: false,
  });

  const [sx, sy, cx, cy, ex, ey, ae, as, ec] = arrow as any;

  return {
    path: `M ${sx} ${sy} Q ${cx} ${cy} ${ex} ${ey}`,
    headPath: `M ${as[0]} ${as[1]} L ${ex} ${ey} L ${ae[0]} ${ae[1]}`,
    center: { x: ec[0], y: ec[1] }
  };
};

export const samplePath = (path: string, precision: number = 50): Point[] => {
  // Simple implementation for quadratic bezier
  const match = path.match(/M ([\d.-]+) ([\d.-]+) Q ([\d.-]+) ([\d.-]+) ([\d.-]+) ([\d.-]+)/);
  if (!match) return [];

  const [, sx, sy, cx, cy, ex, ey] = match.map(Number);
  const points: Point[] = [];

  for (let i = 0; i <= precision; i++) {
    const t = i / precision;
    const x = (1 - t) * (1 - t) * sx + 2 * (1 - t) * t * cx + t * t * ex;
    const y = (1 - t) * (1 - t) * sy + 2 * (1 - t) * t * cy + t * t * ey;
    points.push({ x, y });
  }

  return points;
};
