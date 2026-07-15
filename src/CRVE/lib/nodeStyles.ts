export type CRVENodeStyle =
  | 'glass_disc'
  | 'neon_hexagon'
  | 'circuit_chip'
  | 'floating_cube'
  | 'orbital_rings'
  | 'core_pulse'
  | 'organic_blob'
  | 'tactical_triangle'
  | 'satellite_marker'
  | 'conceptual_symbol';

export interface NodeStyleConfig {
    shape: CRVENodeStyle;
    glow: boolean;
    rings: number;
    rotation: boolean;
    opacity: number;
}

export const NODE_PRESETS: Record<CRVENodeStyle, NodeStyleConfig> = {
    'glass_disc': { shape: 'glass_disc', glow: true, rings: 1, rotation: false, opacity: 0.9 },
    'neon_hexagon': { shape: 'neon_hexagon', glow: true, rings: 0, rotation: true, opacity: 1.0 },
    'circuit_chip': { shape: 'circuit_chip', glow: false, rings: 0, rotation: false, opacity: 1.0 },
    'floating_cube': { shape: 'floating_cube', glow: true, rings: 0, rotation: true, opacity: 0.8 },
    'orbital_rings': { shape: 'orbital_rings', glow: true, rings: 3, rotation: true, opacity: 1.0 },
    'core_pulse': { shape: 'core_pulse', glow: true, rings: 1, rotation: false, opacity: 1.0 },
    'organic_blob': { shape: 'organic_blob', glow: false, rings: 0, rotation: false, opacity: 0.7 },
    'tactical_triangle': { shape: 'tactical_triangle', glow: true, rings: 1, rotation: false, opacity: 1.0 },
    'satellite_marker': { shape: 'satellite_marker', glow: false, rings: 2, rotation: true, opacity: 1.0 },
    'conceptual_symbol': { shape: 'conceptual_symbol', glow: true, rings: 0, rotation: false, opacity: 0.9 }
};
