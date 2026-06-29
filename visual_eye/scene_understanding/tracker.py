import math
from typing import List
try:
    from ..schema import AnalysisFrame, TrackedObject, BBox
except (ImportError, ValueError):
    try:
        from visual_eye.schema import AnalysisFrame, TrackedObject, BBox
    except ImportError:
        from schema import AnalysisFrame, TrackedObject, BBox

def calculate_iou(boxA, boxB):
    xA = max(boxA.x, boxB.x)
    yA = max(boxA.y, boxB.y)
    xB = min(boxA.x + boxA.width, boxB.x + boxB.width)
    yB = min(boxA.y + boxA.height, boxB.y + boxB.height)
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = boxA.width * boxA.height
    boxBArea = boxB.width * boxB.height
    iou = interArea / float(boxAArea + boxBArea - interArea) if (boxAArea + boxBArea - interArea) > 0 else 0
    return iou

def track_objects(frames: List[AnalysisFrame]) -> List[TrackedObject]:
    """
    Lightweight IoU/Centroid tracking across sampled frames.
    """
    tracks = {}
    next_track_id = 1

    for frame in frames:
        current_objects = frame.objects
        used_tracks = set()

        for obj in current_objects:
            best_match_id = None
            best_iou = 0.3 # Minimum IoU threshold

            for track_id, track_info in tracks.items():
                if track_id in used_tracks: continue
                if track_info['type'] != obj.type: continue

                # Compare with the last seen bbox of the track
                last_bbox = track_info['history'][-1]['bbox']
                iou = calculate_iou(last_bbox, obj.bbox)

                if iou > best_iou:
                    best_iou = iou
                    best_match_id = track_id

            if best_match_id:
                tracks[best_match_id]['history'].append({
                    'frame_index': frame.frame_index,
                    'bbox': obj.bbox,
                    'confidence': obj.confidence
                })
                used_tracks.add(best_match_id)
            else:
                # Create new track
                new_id = f"track_{next_track_id:03d}"
                tracks[new_id] = {
                    'type': obj.type,
                    'history': [{
                        'frame_index': frame.frame_index,
                        'bbox': obj.bbox,
                        'confidence': obj.confidence
                    }]
                }
                next_track_id += 1

    tracked_results = []
    for track_id, info in tracks.items():
        history = info['history']
        avg_conf = sum(h['confidence'] for h in history) / len(history)

        # Calculate average bbox
        avg_x = sum(h['bbox'].x for h in history) / len(history)
        avg_y = sum(h['bbox'].y for h in history) / len(history)
        avg_w = sum(h['bbox'].width for h in history) / len(history)
        avg_h = sum(h['bbox'].height for h in history) / len(history)

        # Movement distance (sum of Euclidean distances between consecutive centers)
        movement = 0
        for i in range(1, len(history)):
            c1 = (history[i-1]['bbox'].x + history[i-1]['bbox'].width/2, history[i-1]['bbox'].y + history[i-1]['bbox'].height/2)
            c2 = (history[i]['bbox'].x + history[i]['bbox'].width/2, history[i]['bbox'].y + history[i]['bbox'].height/2)
            movement += math.sqrt((c1[0]-c2[0])**2 + (c1[1]-c2[1])**2)

        tracked_results.append(TrackedObject(
            track_id=track_id,
            type=info['type'],
            first_frame=history[0]['frame_index'],
            last_frame=history[-1]['frame_index'],
            frames_visible=len(history),
            average_confidence=avg_conf,
            average_bbox=BBox(x=avg_x, y=avg_y, width=avg_w, height=avg_h),
            movement_distance=movement
        ))

    return tracked_results
