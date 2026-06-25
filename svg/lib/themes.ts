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
    primaryColor: '#00F5FF', // Ultra Cyan
    secondaryColor: '#FFD700', // High-Contrast Gold
    accentColor: '#FFFFFF', // Clean White
    backgroundColor: '#050505', // True Deep Black (Max Contrast)
    gridColor: 'rgba(0, 245, 255, 0.1)',
    glowIntensity: 0.8,
    glassOpacity: 0.1,
    lineStyle: 'solid',
    fontFamily: 'Inter, sans-serif'
  },
  corporate: {
    primaryColor: '#3B82F6',
    secondaryColor: '#1E293B',
    accentColor: '#F59E0B',
    backgroundColor: '#F8FAFC',
    gridColor: 'rgba(59, 130, 246, 0.03)',
    glowIntensity: 0.3,
    glassOpacity: 0.08,
    lineStyle: 'solid',
    fontFamily: 'Inter, sans-serif'
  },
  finance: {
    primaryColor: '#10b981',
    secondaryColor: '#064e3b',
    accentColor: '#fbbf24',
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
    accentColor: '#ef4444',
    backgroundColor: '#18181b',
    gridColor: 'rgba(255, 255, 255, 0.05)',
    glowIntensity: 0.4,
    glassOpacity: 0.2,
    lineStyle: 'dotted',
    fontFamily: 'Playfair Display, serif'
  },
  education: {
    primaryColor: '#8b5cf6',
    secondaryColor: '#ec4899',
    accentColor: '#f97316',
    backgroundColor: '#fafafa',
    gridColor: 'rgba(139, 92, 246, 0.05)',
    glowIntensity: 0.5,
    glassOpacity: 0.1,
    lineStyle: 'solid',
    fontFamily: 'Quicksand, sans-serif'
  },
  healthcare: {
    primaryColor: '#0ea5e9',
    secondaryColor: '#2dd4bf',
    accentColor: '#f43f5e',
    backgroundColor: '#f0f9ff',
    gridColor: 'rgba(14, 165, 233, 0.1)',
    glowIntensity: 0.7,
    glassOpacity: 0.08,
    lineStyle: 'solid',
    fontFamily: 'Inter, sans-serif'
  },
  medical: {
    primaryColor: '#f43f5e',
    secondaryColor: '#fda4af',
    accentColor: '#3b82f6',
    backgroundColor: '#fff1f2',
    gridColor: 'rgba(244, 63, 94, 0.1)',
    glowIntensity: 0.6,
    glassOpacity: 0.1,
    lineStyle: 'solid',
    fontFamily: 'Inter, sans-serif'
  },
  cyberpunk: {
    primaryColor: '#fde047', // Yellow
    secondaryColor: '#db2777', // Pink
    accentColor: '#06b6d4', // Cyan
    backgroundColor: '#0f172a',
    gridColor: 'rgba(253, 224, 71, 0.15)',
    glowIntensity: 1.0,
    glassOpacity: 0.2,
    lineStyle: 'dashed',
    fontFamily: 'Orbitron, sans-serif'
  },
  minimal: {
    primaryColor: '#000000',
    secondaryColor: '#4b5563',
    accentColor: '#9ca3af',
    backgroundColor: '#ffffff',
    gridColor: 'rgba(0, 0, 0, 0.02)',
    glowIntensity: 0.1,
    glassOpacity: 0.02,
    lineStyle: 'solid',
    fontFamily: 'Helvetica, sans-serif'
  }
};

export const getTheme = (themeName?: InfographicTheme): ThemeConfig => {
  return INFOGRAPHIC_THEMES[themeName || 'tech'];
};
