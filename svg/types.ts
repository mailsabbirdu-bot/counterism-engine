export type SvgProvider =
  | 'iconify'
  | 'lucide'
  | 'tabler'
  | 'solar'
  | 'phosphor'
  | 'hugeicons'
  | 'material-symbols';

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
  | 'glowPulse'
  | 'typewriter'
  | 'countUp';

export type SvgStyle = 'outline' | 'fill' | 'tech' | 'corporate' | 'infographic';

export type Importance = 'primary' | 'secondary' | 'decorative';

export type LayerType = 'background' | 'decorative' | 'secondary' | 'primary' | 'foreground' | 'overlay';

export type InfographicTheme = 'tech' | 'corporate' | 'finance' | 'documentary' | 'education' | 'healthcare';

export type BackgroundType = 'tech_grid' | 'blueprint_grid' | 'dotted_pattern' | 'network_pattern' | 'radial_glow';

export type CompositionType =
  | 'suburban_home'
  | 'city_block'
  | 'factory_cluster'
  | 'office_workspace'
  | 'supply_chain'
  | 'transport_network'
  | 'ecommerce_flow'
  | 'cloud_infrastructure'
  | 'server_cluster'
  | 'ai_pipeline'
  | 'healthcare_system'
  | 'education_system'
  | 'financial_flow';

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
  provider?: SvgProvider;
  animation?: AnimationType;
  startFrame?: number;
  durationInFrames?: number;
  x: number;
  y: number;
  width: number;
  height: number;
  color?: string;
  strokeWidth?: number;

  // Professional Styling
  style?: SvgStyle;
  importance?: Importance;
  glow?: boolean | GlowConfig;
  depth?: boolean;
  container?: 'glass_panel';
  gradient?: GradientConfig;

  // Composition
  groupId?: string;
  layer?: LayerType;
}

export interface SvgGroup {
  id: string;
  layout?: 'horizontal' | 'vertical' | 'grid' | 'orbit' | 'radial' | 'cluster' | 'timeline' | 'pyramid' | 'funnel';
  x?: number;
  y?: number;
  scale?: number;
  spacing?: number;
  rotationSpeed?: number;
  backgroundRing?: boolean;
  connectionStyle?: 'solid' | 'dotted' | 'arrow';
  enterAnimation?: AnimationType;
  exitAnimation?: AnimationType;
  theme?: InfographicTheme;
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

export interface ConnectionLineProps {
    startFrame?: number;
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

// --- NEW HIGH-LEVEL ELEMENTS ---

export interface HubNetworkElement {
  type: 'hub_network';
  id: string;
  centerSvg: string;
  provider?: SvgProvider;
  x: number;
  y: number;
  radius: number;
  nodes: string[];
  connectionStyle?: 'solid' | 'dotted' | 'arrow';
  animation?: AnimationType;
  startFrame?: number;
}

export interface FlowDiagramElement {
  type: 'flow_diagram';
  id: string;
  steps: string[];
  layout?: 'horizontal' | 'vertical';
  arrowStyle?: 'solid' | 'dotted' | 'glow';
  spacing?: number;
  x: number;
  y: number;
  startFrame?: number;
}

export interface ProcessElement {
  type: 'process';
  id: string;
  steps: string[];
  x: number;
  y: number;
  startFrame?: number;
}

export interface LabelElement {
  type: 'label';
  id: string;
  target: string; // ID
  text: string;
  position?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  fontSize?: number;
  color?: string;
  animation?: AnimationType;
  startFrame?: number;
}

export interface CalloutElement {
  type: 'callout';
  id: string;
  target: string; // ID
  title: string;
  body: string;
  direction?: 'top' | 'bottom' | 'left' | 'right';
  x?: number;
  y?: number;
  startFrame?: number;
}

export interface KpiElement {
  type: 'kpi';
  id: string;
  title: string;
  value: string | number;
  trend?: string;
  subtitle?: string;
  icon?: string;
  x: number;
  y: number;
  startFrame?: number;
}

export interface ChartElement {
  type: 'line_chart' | 'bar_chart' | 'pie_chart' | 'area_chart';
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  data: any[];
  startFrame?: number;
}

export interface TimelineEvent {
  year: string;
  label: string;
}

export interface TimelineElement {
  type: 'timeline';
  id: string;
  events: TimelineEvent[];
  x: number;
  y: number;
  startFrame?: number;
}

export interface CompositionElement {
  type: 'composition';
  id: string;
  compositionType: CompositionType;
  x: number;
  y: number;
  scale?: number;
  enterAnimation?: AnimationType;
  theme?: InfographicTheme;
  startFrame?: number;
}

export type StorytellingElement =
  | SvgElement
  | HubNetworkElement
  | FlowDiagramElement
  | ProcessElement
  | LabelElement
  | CalloutElement
  | KpiElement
  | ChartElement
  | TimelineElement
  | CompositionElement;

export interface SvgScene {
  elements: StorytellingElement[];
  groups?: SvgGroup[];
  infographic_lines?: InfographicLine[];
  infographic_nodes?: InfographicNode[];
  background?: BackgroundType;
  theme?: InfographicTheme;
  sceneIconTheme?: SvgProvider;
}
