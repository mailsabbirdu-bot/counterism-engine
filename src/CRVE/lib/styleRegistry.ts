import { RelationshipGrammar, RelationshipStyle } from './types';

export const RELATIONSHIP_GRAMMAR: Record<string, RelationshipGrammar> = {
  'is_a': {
    type: 'containment',
    style: 'hud_line',
    color: '#3b82f6',
    speed: 1.0,
    width: 2,
    particles: false,
    glow: true
  },
  'builds': {
    type: 'construction_flow',
    style: 'particle_stream',
    color: '#f97316',
    speed: 1.5,
    width: 3,
    particles: true,
    glow: true
  },
  'hidden_under': {
    type: 'reveal',
    style: 'laser_beam',
    color: '#ef4444',
    speed: 2.0,
    width: 1.5,
    particles: false,
    glow: true
  },
  'produces': {
    type: 'energy_transfer',
    style: 'pulse_line',
    color: '#00F5FF',
    speed: 1.2,
    width: 2.5,
    particles: true,
    glow: true
  },
  'forms': {
    type: 'aggregation',
    style: 'liquid_flow',
    color: '#10b981',
    speed: 0.8,
    width: 4,
    particles: true,
    glow: false
  },
  'causes': {
    type: 'energy_transfer',
    style: 'electric_arc',
    color: '#f43f5e',
    speed: 2.5,
    width: 2,
    particles: true,
    glow: true
  }
};

export const getGrammar = (relationship: string): RelationshipGrammar => {
  return RELATIONSHIP_GRAMMAR[relationship] || {
    type: 'connection',
    style: 'hud_line',
    color: '#FFFFFF',
    speed: 1.0,
    width: 1,
    particles: false,
    glow: false
  };
};
