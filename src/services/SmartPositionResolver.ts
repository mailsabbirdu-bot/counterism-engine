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
  tracks?: Array<{
    track_id: string;
    type: string;
    frames: Array<{
      frame: number;
      x: number;
      y: number;
      width: number;
      height: number;
    }>;
  }>;
}

export function resolvePosition(
  overlay: any,
  analysis?: Analysis,
  frame?: number
): Position {
  try {
    // 0. Motion Tracking (High Priority Phase 3.2)
    if (overlay.tracking?.enabled && analysis?.tracks && frame !== undefined) {
      const target = overlay.tracking.target === 'hero_track' ? analysis.tracks[0]?.track_id : overlay.tracking.target;
      const track = analysis.tracks.find(t => t.track_id === target);
      if (track && track.frames.length > 0) {
        // Linear Interpolation for Smooth Follow
        const frames = track.frames.sort((a, b) => a.frame - b.frame);
        let prev = frames[0];
        let next = frames[frames.length - 1];

        for (let i = 0; i < frames.length; i++) {
          if (frames[i].frame <= frame) prev = frames[i];
          if (frames[i].frame >= frame) {
            next = frames[i];
            break;
          }
        }

        const offset = overlay.tracking.offset || { x: 0, y: 0 };
        let x, y, w, h;

        if (prev.frame === next.frame) {
          x = prev.x; y = prev.y; w = prev.width; h = prev.height;
        } else {
          const t = (frame - prev.frame) / (next.frame - prev.frame);
          x = prev.x + (next.x - prev.x) * t;
          y = prev.y + (next.y - prev.y) * t;
          w = prev.width + (next.width - prev.width) * t;
          h = prev.height + (next.height - prev.height) * t;
        }

        return {
          x: x + w / 2 + offset.x,
          y: y + h / 2 + offset.y,
        };
      }
    }

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
