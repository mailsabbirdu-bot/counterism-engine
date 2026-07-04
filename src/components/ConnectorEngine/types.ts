import { AnchorResolver } from './AnchorResolver';
import { PathGenerator } from './PathGenerator';
import { ConnectorPresets } from './ConnectorPresets';

export interface ConnectorProps {
  source: string | { x: number, y: number };
  target: string | { x: number, y: number };
  preset?: keyof typeof ConnectorPresets;
  overlays?: any[];
  animation?: {
    draw?: boolean;
    duration?: number;
    particle?: boolean;
    opacity?: boolean;
  };
  style?: {
    width?: number;
    color?: string;
    glow?: boolean;
    dashArray?: string;
  };
  label?: string;
  pulse?: boolean;
  sourceAnchor?: 'top' | 'bottom' | 'left' | 'right' | 'center';
  targetAnchor?: 'top' | 'bottom' | 'left' | 'right' | 'center';
}

export type ConnectorConfig = ConnectorProps & {
  type: 'connector';
  id?: string;
  start?: number;
  duration?: number;
};
