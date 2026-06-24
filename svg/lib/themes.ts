import { InfographicTheme } from '../types';

export interface ThemeConfig {
  primaryColor: string;
  secondaryColor: string;
  accentColor: string;
  backgroundColor: string;
  gridColor: string;
  glowIntensity: number;
  glassOpacity: number;
  lineStyle: 'solid' | 'dotted' | 'dashed';
  fontFamily: string;
}

export const INFOGRAPHIC_THEMES: Record<InfographicTheme, ThemeConfig> = {
  tech: {
    primaryColor: '#00F5FF', // Cyan
    secondaryColor: '#7B68EE', // Iris
    accentColor: '#00FFAB', // Neon Mint
    backgroundColor: '#050505',
    gridColor: 'rgba(0, 245, 255, 0.1)',
    glowIntensity: 0.8,
    glassOpacity: 0.1,
    lineStyle: 'dashed',
    fontFamily: 'Inter, sans-serif'
  },
  corporate: {
    primaryColor: '#2563eb', // Blue
    secondaryColor: '#64748b', // Slate
    accentColor: '#f59e0b', // Amber
    backgroundColor: '#ffffff',
    gridColor: 'rgba(0, 0, 0, 0.05)',
    glowIntensity: 0.3,
    glassOpacity: 0.05,
    lineStyle: 'solid',
    fontFamily: 'Inter, sans-serif'
  },
  finance: {
    primaryColor: '#10b981', // Emerald
    secondaryColor: '#064e3b', // Deep Green
    accentColor: '#fbbf24', // Gold
    backgroundColor: '#022c22',
    gridColor: 'rgba(16, 185, 129, 0.1)',
    glowIntensity: 0.6,
    glassOpacity: 0.15,
    lineStyle: 'solid',
    fontFamily: 'Roboto Mono, monospace'
  },
  documentary: {
    primaryColor: '#ffffff',
    secondaryColor: '#a1a1aa',
    accentColor: '#ef4444', // Red
    backgroundColor: '#18181b',
    gridColor: 'rgba(255, 255, 255, 0.05)',
    glowIntensity: 0.4,
    glassOpacity: 0.2,
    lineStyle: 'dotted',
    fontFamily: 'Playfair Display, serif'
  },
  education: {
    primaryColor: '#8b5cf6', // Violet
    secondaryColor: '#ec4899', // Pink
    accentColor: '#f97316', // Orange
    backgroundColor: '#fafafa',
    gridColor: 'rgba(139, 92, 246, 0.05)',
    glowIntensity: 0.5,
    glassOpacity: 0.1,
    lineStyle: 'solid',
    fontFamily: 'Quicksand, sans-serif'
  },
  healthcare: {
    primaryColor: '#0ea5e9', // Sky
    secondaryColor: '#2dd4bf', // Teal
    accentColor: '#f43f5e', // Rose
    backgroundColor: '#f0f9ff',
    gridColor: 'rgba(14, 165, 233, 0.1)',
    glowIntensity: 0.7,
    glassOpacity: 0.08,
    lineStyle: 'solid',
    fontFamily: 'Inter, sans-serif'
  }
};

export const getTheme = (themeName?: InfographicTheme): ThemeConfig => {
  return INFOGRAPHIC_THEMES[themeName || 'tech'];
};
