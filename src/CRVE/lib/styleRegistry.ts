import { RelationshipGrammar, RelationshipStyle } from './types';

export const RELATIONSHIP_GRAMMAR: Record<string, RelationshipGrammar> = {
  // 1. Causes and Energy Transitions (Electric Arcing / Sparks)
  'cause_effect': { type: 'energy_transfer', style: 'electric_arc', color: '#f43f5e', speed: 2.5, width: 2.5, particles: true, glow: true },
  'effect_cause': { type: 'energy_transfer', style: 'electric_arc', color: '#ef4444', speed: 2.5, width: 2.5, particles: true, glow: true },
  'trigger_response': { type: 'energy_transfer', style: 'electric_arc', color: '#ff4500', speed: 2.8, width: 3, particles: true, glow: true },
  'action_consequence': { type: 'energy_transfer', style: 'electric_arc', color: '#ff3e6c', speed: 2.6, width: 2.8, particles: true, glow: true },
  'feedback_loop': { type: 'energy_transfer', style: 'electric_arc', color: '#ec4899', speed: 2.2, width: 2, particles: true, glow: true },
  'influence': { type: 'energy_transfer', style: 'electric_arc', color: '#a855f7', speed: 1.8, width: 2, particles: true, glow: true },
  'causes': { type: 'energy_transfer', style: 'electric_arc', color: '#f43f5e', speed: 2.5, width: 2, particles: true, glow: true },
  'produces': { type: 'energy_transfer', style: 'electric_arc', color: '#f43f5e', speed: 2.5, width: 2, particles: true, glow: true },

  // 2. Flows & Inputs (Cyber Quantum Pipeline)
  'construction_flow': { type: 'construction_flow', style: 'particle_stream', color: '#00f5ff', speed: 1.8, width: 3.5, particles: true, glow: true },
  'builds': { type: 'construction_flow', style: 'particle_stream', color: '#00f5ff', speed: 1.8, width: 3.5, particles: true, glow: true },
  'input_output': { type: 'construction_flow', style: 'particle_stream', color: '#00ffcc', speed: 2.0, width: 3.5, particles: true, glow: true },
  'process_flow': { type: 'construction_flow', style: 'particle_stream', color: '#10b981', speed: 1.5, width: 3.0, particles: true, glow: true },
  'supply_chain': { type: 'construction_flow', style: 'particle_stream', color: '#22c55e', speed: 1.6, width: 3.0, particles: true, glow: true },
  'migration_flow': { type: 'construction_flow', style: 'particle_stream', color: '#06b6d4', speed: 2.2, width: 4.0, particles: true, glow: true },

  // 3. Logic and Evidence (Schematic Grid / Gold Trace)
  'evidence_conclusion': { type: 'reveal', style: 'laser_beam', color: '#fbbf24', speed: 1.4, width: 2, particles: false, glow: true },
  'claim_evidence': { type: 'reveal', style: 'laser_beam', color: '#f59e0b', speed: 1.4, width: 2, particles: false, glow: true },
  'fact_explanation': { type: 'reveal', style: 'laser_beam', color: '#fb7185', speed: 1.2, width: 2, particles: false, glow: true },
  'reason_result': { type: 'reveal', style: 'laser_beam', color: '#fbbf24', speed: 1.5, width: 2, particles: false, glow: true },
  'reveal': { type: 'reveal', style: 'laser_beam', color: '#fbbf24', speed: 1.5, width: 2, particles: false, glow: true },
  'hidden_under': { type: 'reveal', style: 'laser_beam', color: '#fbbf24', speed: 1.5, width: 2, particles: false, glow: true },

  // 4. Structure & Organization (HUD Double Outline)
  'containment': { type: 'containment', style: 'hud_line', color: '#3b82f6', speed: 1.0, width: 2, particles: false, glow: true },
  'is_a': { type: 'containment', style: 'hud_line', color: '#3b82f6', speed: 1.0, width: 2, particles: false, glow: true },
  'part_whole': { type: 'containment', style: 'hud_line', color: '#60a5fa', speed: 1.0, width: 2, particles: false, glow: true },
  'whole_parts': { type: 'containment', style: 'hud_line', color: '#60a5fa', speed: 1.0, width: 2, particles: false, glow: true },
  'hierarchy': { type: 'containment', style: 'hud_line', color: '#2563eb', speed: 1.0, width: 2.5, particles: false, glow: true },
  'membership': { type: 'containment', style: 'hud_line', color: '#1d4ed8', speed: 1.0, width: 2, particles: false, glow: true },
  'ownership': { type: 'containment', style: 'hud_line', color: '#3b82f6', speed: 1.0, width: 2, particles: false, glow: true },

  // 5. Lifecycles & Growth (Bio-Chemical Emerald Gradient)
  'lifecycle': { type: 'lifecycle', style: 'liquid_flow', color: '#10b981', speed: 1.2, width: 4.5, particles: true, glow: true },
  'transformation': { type: 'lifecycle', style: 'liquid_flow', color: '#059669', speed: 1.5, width: 5.0, particles: true, glow: true },
  'evolution': { type: 'lifecycle', style: 'liquid_flow', color: '#34d399', speed: 1.1, width: 4.5, particles: true, glow: true },
  'cycle': { type: 'lifecycle', style: 'liquid_flow', color: '#10b981', speed: 1.3, width: 4.0, particles: true, glow: true },

  // 6. Chronological / Dependency (Laser Pulse Lines)
  'timeline': { type: 'sequence', style: 'laser_sweep', color: '#8b5cf6', speed: 1.6, width: 2.5, particles: false, glow: true },
  'sequence': { type: 'sequence', style: 'laser_sweep', color: '#8b5cf6', speed: 1.6, width: 2.5, particles: false, glow: true },
  'dependency': { type: 'sequence', style: 'laser_sweep', color: '#7c3aed', speed: 1.8, width: 3.0, particles: false, glow: true },
  'dependency_chain': { type: 'sequence', style: 'laser_sweep', color: '#a78bfa', speed: 1.8, width: 2.8, particles: false, glow: true },
  'dependency_network': { type: 'sequence', style: 'laser_sweep', color: '#7c3aed', speed: 2.0, width: 3.0, particles: false, glow: true },

  // 7. Tension & Contrast (Opposing High-Energy Laser Sweep)
  'conflict': { type: 'conflict', style: 'laser_beam', color: '#dc2626', speed: 3.0, width: 3.5, particles: false, glow: true },
  'contrast': { type: 'conflict', style: 'laser_beam', color: '#f87171', speed: 2.2, width: 2.8, particles: false, glow: true },
  'trade_off': { type: 'conflict', style: 'laser_beam', color: '#ea580c', speed: 2.4, width: 3.0, particles: false, glow: true },
  'risk_impact': { type: 'conflict', style: 'laser_beam', color: '#e11d48', speed: 2.8, width: 3.2, particles: false, glow: true },

  // 8. General Context and Loose Associations (Translucent Sankey Conduit)
  'grouping': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.4)', speed: 0.8, width: 6.0, particles: false, glow: false },
  'classification': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.45)', speed: 0.9, width: 5.5, particles: false, glow: false },
  'comparison': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.5)', speed: 1.0, width: 5.0, particles: false, glow: false },
  'similarity': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.5)', speed: 1.0, width: 4.5, particles: false, glow: false },
  'analogy': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.4)', speed: 0.8, width: 5.0, particles: false, glow: false },
  'association': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.35)', speed: 0.7, width: 4.5, particles: false, glow: false },
  'correlation': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.4)', speed: 1.2, width: 5.0, particles: false, glow: false },
  'context': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.3)', speed: 0.6, width: 4.0, particles: false, glow: false },
  'reference': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.3)', speed: 0.8, width: 4.0, particles: false, glow: false },
  'semantic_link': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.3)', speed: 0.8, width: 4.0, particles: false, glow: false },
  'importance': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.55)', speed: 1.0, width: 5.0, particles: false, glow: false },
  'collaboration': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.5)', speed: 1.1, width: 5.5, particles: false, glow: false },
  'narrative_flow': { type: 'association', style: 'sankey_link', color: 'rgba(255, 255, 255, 0.4)', speed: 1.0, width: 4.5, particles: false, glow: false }
};

export const getGrammar = (relationship: string): RelationshipGrammar => {
  const normalized = (relationship || '').toLowerCase().trim();
  return RELATIONSHIP_GRAMMAR[normalized] || {
    type: 'connection',
    style: 'hud_line',
    color: '#FFFFFF',
    speed: 1.0,
    width: 1.5,
    particles: false,
    glow: false
  };
};
