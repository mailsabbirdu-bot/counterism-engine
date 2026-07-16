export type CinematicMood =
  | 'minimal'
  | 'military'
  | 'scientific'
  | 'cyberpunk'
  | 'luxury_hud'
  | 'organic'
  | 'documentary'
  | 'laboratory'
  | 'danger'
  | 'dream';

export interface MoodConfig {
    colors: {
        primary: string;
        secondary: string;
        accent: string;
        background: string;
        text: string;
    };
    glowIntensity: number;
    blurAmount: number;
    noiseOpacity: number;
    gridOpacity: number;
}

export const MOOD_REGISTRY: Record<CinematicMood, MoodConfig> = {
    'minimal': {
        colors: { primary: '#FFFFFF', secondary: '#A1A1AA', accent: '#3b82f6', background: '#000000', text: '#FFFFFF' },
        glowIntensity: 0.2, blurAmount: 0, noiseOpacity: 0.05, gridOpacity: 0.1
    },
    'military': {
        colors: { primary: '#22c55e', secondary: '#166534', accent: '#ef4444', background: '#022c22', text: '#22c55e' },
        glowIntensity: 0.5, blurAmount: 1, noiseOpacity: 0.15, gridOpacity: 0.4
    },
    'scientific': {
        colors: { primary: '#00F5FF', secondary: '#00D1FF', accent: '#f43f5e', background: '#001a1a', text: '#00F5FF' },
        glowIntensity: 1.0, blurAmount: 2, noiseOpacity: 0.08, gridOpacity: 0.2
    },
    'cyberpunk': {
        colors: { primary: '#f0abfc', secondary: '#d946ef', accent: '#22d3ee', background: '#2e1065', text: '#f0abfc' },
        glowIntensity: 1.5, blurAmount: 4, noiseOpacity: 0.2, gridOpacity: 0.3
    },
    'luxury_hud': {
        colors: { primary: '#fbbf24', secondary: '#b45309', accent: '#FFFFFF', background: '#1c1917', text: '#fbbf24' },
        glowIntensity: 0.8, blurAmount: 1, noiseOpacity: 0.05, gridOpacity: 0.15
    },
    'organic': {
        colors: { primary: '#4ade80', secondary: '#16a34a', accent: '#fbbf24', background: '#064e3b', text: '#4ade80' },
        glowIntensity: 0.3, blurAmount: 5, noiseOpacity: 0.1, gridOpacity: 0
    },
    'documentary': {
        colors: { primary: '#FFFFFF', secondary: '#D1D5DB', accent: '#3b82f6', background: '#030712', text: '#FFFFFF' },
        glowIntensity: 0.4, blurAmount: 0.5, noiseOpacity: 0.1, gridOpacity: 0.2
    },
    'laboratory': {
        colors: { primary: '#cbd5e1', secondary: '#64748b', accent: '#0ea5e9', background: '#f8fafc', text: '#0f172a' },
        glowIntensity: 0.1, blurAmount: 0, noiseOpacity: 0.02, gridOpacity: 0.5
    },
    'danger': {
        colors: { primary: '#ef4444', secondary: '#7f1d1d', accent: '#fbbf24', background: '#450a0a', text: '#ef4444' },
        glowIntensity: 1.2, blurAmount: 2, noiseOpacity: 0.3, gridOpacity: 0.6
    },
    'dream': {
        colors: { primary: '#c084fc', secondary: '#818cf8', accent: '#f472b6', background: '#1e1b4b', text: '#FFFFFF' },
        glowIntensity: 1.0, blurAmount: 10, noiseOpacity: 0.05, gridOpacity: 0
    }
};
