export interface Point {
  x: number;
  y: number;
}

export const AnchorResolver = {
  resolve: (
    source: string | Point,
    overlays: any[] = [],
    anchorName: string = 'center'
  ): Point => {
    if (typeof source !== 'string') return source;

    const overlay = overlays.find(o => o.id === source);
    if (!overlay) {
      console.warn(`[AnchorResolver] Overlay not found: ${source}`);
      return { x: 0, y: 0 };
    }

    const x = overlay.position?.x ?? 960;
    const y = overlay.position?.y ?? 540;

    // Type-specific bounding boxes (from generator logic)
    const TYPE_SIZES: Record<string, [number, number]> = {
        'text': [800, 200], 'chart': [1000, 562], 'shadcn_chart': [1000, 562],
        'ui_panel': [800, 600], 'data_indicator': [500, 375], 'shadcn_indicator': [500, 375],
        'svg': [400, 400], 'kpi': [450, 400], 'kpi_card': [450, 400],
        'timeline': [1200, 300], 'hub_network': [800, 800], 'flow_diagram': [1000, 562], 'process': [1000, 562],
        'media': [960, 540], 'image': [960, 540], 'video': [960, 540],
        'label': [300, 100], 'callout': [400, 200], 'compositions': [1200, 675], 'groups': [1200, 675],
        'graph': [1000, 700], 'shape': [400, 400], 'data_emphasis': [600, 200], 'ambient_graphic': [1920, 1080],
        'connector': [400, 100]
    };

    const [w, h] = TYPE_SIZES[overlay.type] || [400, 400];
    const width = overlay.width || w;
    const height = overlay.height || h;

    switch (anchorName) {
      case 'top': return { x, y: y - height / 2 };
      case 'bottom': return { x, y: y + height / 2 };
      case 'left': return { x: x - width / 2, y };
      case 'right': return { x: x + width / 2, y };
      case 'center':
      default: return { x, y };
    }
  }
};
