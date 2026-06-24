export type SvgProvider = 'iconify' | 'lucide' | 'tabler';

export type AnimationType =
  | 'fade'
  | 'scale'
  | 'pop'
  | 'slideLeft'
  | 'slideRight'
  | 'slideUp'
  | 'slideDown'
  | 'rotate'
  | 'bounce'
  | 'draw';

export interface SvgElement {
  id: string;
  type: 'svg';
  query: string;
  provider: SvgProvider;
  animation: AnimationType;
  startFrame: number;
  durationInFrames: number;
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  strokeWidth?: number;
}

export interface SvgScene {
  elements: SvgElement[];
}
