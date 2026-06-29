export interface Position {
  x: number;
  y: number;
}

export interface VisualAnchor {
  enabled: boolean;
  prefer: 'safe_text_region' | 'object';
  targetObjectId?: string;
}

export interface Analysis {
  safe_text_regions: Array<{
    x: number;
    y: number;
    width: number;
    height: number;
    confidence: number;
  }>;
  objects: Array<{
    id: string;
    type: string;
    bbox: {
      x: number;
      y: number;
      width: number;
      height: number;
    };
  }>;
}

export function resolvePosition(
  overlay: any,
  analysis?: Analysis
): Position {
  try {
    // 1. Visual Eye suggestion (if enabled)
    if (overlay.visual_anchor?.enabled && analysis) {
      if (overlay.visual_anchor.prefer === 'safe_text_region' && analysis.safe_text_regions?.length > 0) {
        const region = analysis.safe_text_regions[0];
        return {
          x: region.x + region.width / 2,
          y: region.y + region.height / 2,
        };
      }

      if (overlay.visual_anchor.prefer === 'object' && analysis.objects?.length > 0) {
        const targetId = overlay.visual_anchor.targetObjectId;
        const obj = targetId
          ? analysis.objects.find((o: any) => o.id === targetId)
          : analysis.objects[0];

        if (obj) {
          return {
            x: obj.bbox.x + obj.bbox.width / 2,
            y: obj.bbox.y + obj.bbox.height / 2,
          };
        }
      }
    }

    // 2. Manual override from JSON (explicit position)
    if (overlay.position) {
      return overlay.position;
    }

    // 3. Fallback to default center
    return { x: 960, y: 540 };
  } catch (error) {
    console.warn("Visual Eye position resolution failed, using fallback.", error);
    return overlay.position || { x: 960, y: 540 };
  }
}
