import { LucideIcon } from 'lucide-react';

export interface CRVENodeData {
  id: string;
  label: string;
  type: string;
  importance: number;
  emotion?: string;
  scale?: number;
  active_windows?: [number, number][];
  scene_id?: string;
  font_size?: number;
  isCauseNode?: boolean;
  isHeaderNode?: boolean;
  rank?: number;
  x?: number;
  y?: number;
}

export interface CRVELinkData {
  id: string;
  source: string;
  target: string;
  relationship: string;
  strength: number;
  display_label?: string;
}

export type RelationshipStyle =
  | 'laser_beam'
  | 'particle_stream'
  | 'electric_arc'
  | 'hud_line'
  | 'neon_tube'
  | 'pulse_line'
  | 'liquid_flow'
  | 'energy_flow'
  | 'data_stream'
  | 'laser_sweep'
  | 'sankey_link';

export interface RelationshipGrammar {
  type: string;
  style: RelationshipStyle;
  color: string;
  speed: number;
  width: number;
  particles: boolean;
  glow: boolean;
  noise?: number;
}

export type SceneCompositionType =
  | 'radial'
  | 'orbit'
  | 'constellation'
  | 'molecule'
  | 'pipeline'
  | 'neural_network';
