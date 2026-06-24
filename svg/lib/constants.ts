/**
 * Motion Graphics Engine Constants
 */

export const ENGINE_CONSTANTS = {
  // Timing
  DEFAULT_SCENE_DURATION: 180,
  DEFAULT_ANIMATION_DURATION: 150,
  EXIT_BUFFER: 15,
  STAGGER_INTERVAL: 10,

  // Layout
  CANVAS_WIDTH: 1920,
  CANVAS_HEIGHT: 1080,
  CENTER_X: 960,
  CENTER_Y: 540,
  DEFAULT_SPACING: 250,
  HUB_RADIUS: 350,
  TIMELINE_WIDTH: 1200,

  // Visuals
  MAX_SVG_PATH_LENGTH: 5000,
  DEFAULT_STROKE_WIDTH: 2,
  GLASS_PANEL_BLUR: 20,
  GLOW_RADIUS: 20,

  // Layers (z-index)
  LAYERS: {
    background: 0,
    decorative: 10,
    secondary: 20,
    primary: 50,
    foreground: 80,
    overlay: 100
  }
};
