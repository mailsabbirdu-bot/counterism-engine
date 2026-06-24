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
  | 'draw'
  | 'trace'
  | 'pulse'
  | 'float'
  | 'orbit'
  | 'reveal'
  | 'glowPulse';

export type SvgStyle = 'outline' | 'fill' | 'tech' | 'corporate' | 'infographic';

export type Importance = 'primary' | 'secondary' | 'decorative';

export type BackgroundType = 'tech_grid' | 'blueprint_grid' | 'dotted_pattern' | 'network_pattern' | 'radial_glow';

export interface GradientConfig {
  start: string;
  end: string;
}

export interface GlowConfig {
  color?: string;
  intensity?: number;
  radius?: number;
}

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

  // New Professional Visual Properties
  style?: SvgStyle;
  importance?: Importance;
  glow?: boolean | GlowConfig;
  depth?: boolean;
  container?: 'glass_panel';
  gradient?: GradientConfig;

  // Composition
  groupId?: string;
}

export interface SvgGroup {
    id: string;
    animation?: AnimationType;
    x?: number;
    y?: number;
    scale?: number;
    layout?: 'horizontal' | 'vertical' | 'grid' | 'orbit';
    spacing?: number;
}

export interface InfographicLine {
  start_pos?: { x: number; y: number };
  end_pos?: { x: number; y: number };
  from?: string; // element ID
  to?: string;   // element ID
  start?: number;
  duration?: number;
  color?: string;
  type?: 'solid' | 'dotted' | 'arrow';
}

export interface InfographicNode {
  x: number;
  y: number;
  start?: number;
  color?: string;
  type?: 'glow' | 'pulse' | 'signal';
  radius?: number;
}

export interface SvgScene {
  elements: SvgElement[];
  groups?: SvgGroup[];
  infographic_lines?: InfographicLine[];
  infographic_nodes?: InfographicNode[];
  background?: BackgroundType;
}
