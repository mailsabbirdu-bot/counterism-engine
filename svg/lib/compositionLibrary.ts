import { CompositionType, SvgElement, InfographicLine, SvgProvider, AnimationType, SvgStyle, Importance } from '../types';

export interface CompositionDefinition {
  elements: {
      id: string;
      type: 'svg';
      query: string;
      width: number;
      height: number;
      offsetX: number;
      offsetY: number;
      importance?: Importance;
      style?: SvgStyle;
      animation?: AnimationType;
      glow?: boolean;
      provider?: SvgProvider;
  }[];
  lines?: { from: string, to: string, type?: string }[];
}

export const COMPOSITIONS: Record<CompositionType, CompositionDefinition> = {
  suburban_home: {
    elements: [
      { id: 'house', type: 'svg', query: 'home', width: 200, height: 200, offsetX: 0, offsetY: 0, importance: 'primary', style: 'infographic' },
      { id: 'tree1', type: 'svg', query: 'tree-pine', width: 80, height: 80, offsetX: -120, offsetY: 40, importance: 'decorative' },
      { id: 'tree2', type: 'svg', query: 'tree-pine', width: 60, height: 60, offsetX: 130, offsetY: 50, importance: 'decorative' },
      { id: 'car', type: 'svg', query: 'car', width: 100, height: 60, offsetX: -80, offsetY: 100, importance: 'secondary' }
    ]
  },
  city_block: {
    elements: [
      { id: 'b1', type: 'svg', query: 'building-2', width: 150, height: 250, offsetX: -160, offsetY: 0, style: 'tech' },
      { id: 'b2', type: 'svg', query: 'building', width: 200, height: 350, offsetX: 0, offsetY: -50, importance: 'primary', style: 'tech' },
      { id: 'b3', type: 'svg', query: 'building-2', width: 150, height: 200, offsetX: 160, offsetY: 20, style: 'tech' }
    ]
  },
  factory_cluster: {
    elements: [
      { id: 'f1', type: 'svg', query: 'factory', width: 180, height: 180, offsetX: -150, offsetY: 0, style: 'corporate' },
      { id: 'f2', type: 'svg', query: 'factory', width: 180, height: 180, offsetX: 150, offsetY: 0, style: 'corporate' },
      { id: 'truck', type: 'svg', query: 'truck', width: 100, height: 80, offsetX: 0, offsetY: 120, importance: 'secondary' }
    ],
    lines: [
        { from: 'f1', to: 'truck', type: 'arrow' },
        { from: 'f2', to: 'truck', type: 'arrow' }
    ]
  },
  office_workspace: {
    elements: [
      { id: 'desk', type: 'svg', query: 'monitor', width: 150, height: 150, offsetX: 0, offsetY: 0, importance: 'primary' },
      { id: 'chair', type: 'svg', query: 'armchair', width: 100, height: 100, offsetX: 0, offsetY: 100, importance: 'secondary' },
      { id: 'lamp', type: 'svg', query: 'lamp', width: 60, height: 80, offsetX: 120, offsetY: -20, importance: 'decorative' }
    ]
  },
  supply_chain: {
    elements: [
      { id: 'raw', type: 'svg', query: 'package-search', width: 120, height: 120, offsetX: -300, offsetY: 0 },
      { id: 'factory', type: 'svg', query: 'factory', width: 150, height: 150, offsetX: 0, offsetY: 0, importance: 'primary' },
      { id: 'dist', type: 'svg', query: 'truck', width: 120, height: 120, offsetX: 300, offsetY: 0 }
    ],
    lines: [
        { from: 'raw', to: 'factory', type: 'arrow' },
        { from: 'factory', to: 'dist', type: 'arrow' }
    ]
  },
  transport_network: {
    elements: [
      { id: 'hub', type: 'svg', query: 'map-pin', width: 100, height: 100, offsetX: 0, offsetY: 0, importance: 'primary' },
      { id: 'plane', type: 'svg', query: 'plane', width: 80, height: 80, offsetX: -200, offsetY: -150 },
      { id: 'train', type: 'svg', query: 'train-front', width: 80, height: 80, offsetX: 200, offsetY: 150 },
      { id: 'ship', type: 'svg', query: 'ship', width: 80, height: 80, offsetX: 200, offsetY: -150 }
    ],
    lines: [
        { from: 'plane', to: 'hub', type: 'dotted' },
        { from: 'train', to: 'hub', type: 'dotted' },
        { from: 'ship', to: 'hub', type: 'dotted' }
    ]
  },
  ecommerce_flow: {
    elements: [
      { id: 'cart', type: 'svg', query: 'shopping-cart', width: 120, height: 120, offsetX: -250, offsetY: 0 },
      { id: 'card', type: 'svg', query: 'credit-card', width: 120, height: 120, offsetX: 0, offsetY: 0, importance: 'primary' },
      { id: 'box', type: 'svg', query: 'box', width: 120, height: 120, offsetX: 250, offsetY: 0 }
    ],
    lines: [
        { from: 'cart', to: 'card', type: 'arrow' },
        { from: 'card', to: 'box', type: 'arrow' }
    ]
  },
  cloud_infrastructure: {
    elements: [
      { id: 'cloud', type: 'svg', query: 'cloud', width: 250, height: 180, offsetX: 0, offsetY: -100, importance: 'primary', style: 'tech', glow: true },
      { id: 's1', type: 'svg', query: 'server', width: 100, height: 100, offsetX: -180, offsetY: 120, style: 'tech' },
      { id: 's2', type: 'svg', query: 'server', width: 100, height: 100, offsetX: 0, offsetY: 120, style: 'tech' },
      { id: 's3', type: 'svg', query: 'server', width: 100, height: 100, offsetX: 180, offsetY: 120, style: 'tech' }
    ],
    lines: [
        { from: 's1', to: 'cloud', type: 'dotted' },
        { from: 's2', to: 'cloud', type: 'dotted' },
        { from: 's3', to: 'cloud', type: 'dotted' }
    ]
  },
  server_cluster: {
    elements: [
      { id: 'rack1', type: 'svg', query: 'server', width: 120, height: 150, offsetX: -140, offsetY: -80, style: 'tech' },
      { id: 'rack2', type: 'svg', query: 'server', width: 120, height: 150, offsetX: 140, offsetY: -80, style: 'tech' },
      { id: 'rack3', type: 'svg', query: 'server', width: 120, height: 150, offsetX: -140, offsetY: 80, style: 'tech' },
      { id: 'rack4', type: 'svg', query: 'server', width: 120, height: 150, offsetX: 140, offsetY: 80, style: 'tech' }
    ]
  },
  ai_pipeline: {
    elements: [
      { id: 'data', type: 'svg', query: 'database', width: 100, height: 100, offsetX: -300, offsetY: 0 },
      { id: 'brain', type: 'svg', query: 'cpu', width: 180, height: 180, offsetX: 0, offsetY: 0, importance: 'primary', style: 'tech', glow: true },
      { id: 'output', type: 'svg', query: 'sparkles', width: 120, height: 120, offsetX: 300, offsetY: 0, style: 'tech' }
    ],
    lines: [
        { from: 'data', to: 'brain', type: 'arrow' },
        { from: 'brain', to: 'output', type: 'arrow' }
    ]
  },
  healthcare_system: {
    elements: [
      { id: 'hosp', type: 'svg', query: 'hospital', width: 200, height: 200, offsetX: 0, offsetY: 0, importance: 'primary' },
      { id: 'pulse', type: 'svg', query: 'activity', width: 80, height: 80, offsetX: -200, offsetY: 0 },
      { id: 'doc', type: 'svg', query: 'user-round-check', width: 80, height: 80, offsetX: 200, offsetY: 0 }
    ],
    lines: [
        { from: 'pulse', to: 'hosp', type: 'solid' },
        { from: 'doc', to: 'hosp', type: 'solid' }
    ]
  },
  education_system: {
    elements: [
      { id: 'school', type: 'svg', query: 'school', width: 200, height: 200, offsetX: 0, offsetY: 0, importance: 'primary' },
      { id: 'book', type: 'svg', query: 'book-open', width: 100, height: 100, offsetX: -220, offsetY: 100 },
      { id: 'grad', type: 'svg', query: 'graduation-cap', width: 100, height: 100, offsetX: 220, offsetY: 100 }
    ]
  },
  financial_flow: {
    elements: [
      { id: 'bank', type: 'svg', query: 'landmark', width: 180, height: 180, offsetX: 0, offsetY: 0, importance: 'primary', style: 'corporate' },
      { id: 'wallet', type: 'svg', query: 'wallet', width: 100, height: 100, offsetX: -280, offsetY: 50 },
      { id: 'coins', type: 'svg', query: 'coins', width: 100, height: 100, offsetX: 280, offsetY: 50 }
    ],
    lines: [
        { from: 'bank', to: 'wallet', type: 'arrow' },
        { from: 'wallet', to: 'coins', type: 'arrow' }
    ]
  }
};
