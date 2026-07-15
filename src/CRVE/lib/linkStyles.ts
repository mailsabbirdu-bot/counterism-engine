export type CRVELinkStyle =
  | 'laser_beam'
  | 'particle_stream'
  | 'electric_arc'
  | 'neon_tube'
  | 'pulse_line'
  | 'liquid_flow'
  | 'circuit_path'
  | 'satellite_orbit'
  | 'dashed_motion'
  | 'organic_vine';

export interface LinkStyleConfig {
    renderer: string;
    glow: boolean;
    particles: boolean;
    speed: number;
    width: number;
    dashArray?: string;
    blur?: number;
}

export const LINK_PRESETS: Record<CRVELinkStyle, LinkStyleConfig> = {
    'laser_beam': { renderer: 'laser', glow: true, particles: false, speed: 2.0, width: 2 },
    'particle_stream': { renderer: 'particles', glow: true, particles: true, speed: 1.5, width: 3 },
    'electric_arc': { renderer: 'electric', glow: true, particles: true, speed: 2.5, width: 2 },
    'neon_tube': { renderer: 'neon', glow: true, particles: false, speed: 1.0, width: 4 },
    'pulse_line': { renderer: 'pulse', glow: true, particles: true, speed: 1.2, width: 3 },
    'liquid_flow': { renderer: 'liquid', glow: false, particles: true, speed: 0.8, width: 5 },
    'circuit_path': { renderer: 'circuit', glow: false, particles: false, speed: 1.0, width: 1, dashArray: '4 4' },
    'satellite_orbit': { renderer: 'orbit', glow: true, particles: true, speed: 0.5, width: 1 },
    'dashed_motion': { renderer: 'dashed', glow: false, particles: false, speed: 1.2, width: 2, dashArray: '10 10' },
    'organic_vine': { renderer: 'vine', glow: false, particles: false, speed: 0.3, width: 2 }
};
