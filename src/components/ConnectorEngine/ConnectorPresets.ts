export const ConnectorPresets = {
  smooth_curve: {
    pathType: 'smoothCurve',
    style: { width: 3, color: '#00F5FF', glow: true },
    animation: { draw: true, particle: false }
  },
  soft_arc: {
    pathType: 'arc',
    style: { width: 2, color: '#FFFFFF', glow: false },
    animation: { draw: true, particle: false }
  },
  straight_flow: {
    pathType: 'straight',
    style: { width: 4, color: '#00FFAB', glow: true },
    animation: { draw: true, particle: true }
  },
  energy_flow: {
    pathType: 'smoothCurve',
    style: { width: 4, color: '#FFD700', glow: true },
    animation: { draw: true, particle: true, particleCount: 3 }
  },
  signal_beam: {
    pathType: 'straight',
    style: { width: 1, color: '#00F5FF', glow: true },
    animation: { draw: true, particle: true, particleType: 'beam' }
  },
  data_stream: {
    pathType: 'smoothCurve',
    style: { width: 2, color: '#3b82f6', glow: true },
    animation: { draw: true, particle: true, particleCount: 8 }
  },
  s_curve: {
    pathType: 'sCurve',
    style: { width: 3, color: '#8b5cf6', glow: true },
    animation: { draw: true, particle: false }
  },
  zigzag_soft: {
    pathType: 'zigzag',
    style: { width: 3, color: '#f43f5e', glow: true },
    animation: { draw: true, particle: false }
  },
  multi_branch: {
    pathType: 'branch',
    style: { width: 2, color: '#10b981', glow: true },
    animation: { draw: true, particle: false }
  },
  network_web: {
    pathType: 'straight',
    style: { width: 1, color: 'rgba(255,255,255,0.3)', glow: false },
    animation: { draw: true, particle: false }
  },
  callout_line: {
    pathType: 'zigzag',
    style: { width: 2, color: '#FFFFFF', glow: false, dashArray: '5,5' },
    animation: { draw: true, particle: false }
  },
  camera_focus: {
    pathType: 'arc',
    style: { width: 4, color: '#FF3E6C', glow: true },
    animation: { draw: true, particle: false }
  },
  timeline_path: {
    pathType: 'straight',
    style: { width: 6, color: '#333333', glow: false },
    animation: { draw: true, particle: false }
  },
  route_path: {
    pathType: 'smoothCurve',
    style: { width: 4, color: '#fbbf24', glow: true, dashArray: '10,10' },
    animation: { draw: true, particle: false }
  },
  curved_route: {
    pathType: 'arc',
    style: { width: 4, color: '#f97316', glow: true },
    animation: { draw: true, particle: true }
  },
  neon_connector: {
    pathType: 'smoothCurve',
    style: { width: 5, color: '#FF00FF', glow: true },
    animation: { draw: true, particle: true }
  },
  blueprint_connector: {
    pathType: 'zigzag',
    style: { width: 1, color: '#3b82f6', glow: false, dashArray: '2,2' },
    animation: { draw: true, particle: false }
  },
  organic_connector: {
    pathType: 'smoothCurve',
    style: { width: 3, color: '#10b981', glow: true },
    animation: { draw: true, particle: false, organic: true }
  }
} as const;
