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

def calculate_centroid_dist(boxA, boxB):
    c1 = (boxA.x + boxA.width / 2, boxA.y + boxA.height / 2)
    c2 = (boxB.x + boxB.width / 2, boxB.y + boxB.height / 2)
    return math.sqrt((c1[0] - c2[0])**2 + (c1[1] - c2[1])**2)

def track_objects(frames: List[AnalysisFrame]) -> List[TrackedObject]:
    """
    Enhanced lightweight IoU + Centroid tracking across sampled frames.
    """
    try:
        tracks = {}
        next_track_id = 1

        for frame in frames:
            current_objects = frame.objects
            used_tracks = set()

            # Sort current objects by area (process larger objects first)
            sorted_objs = sorted(current_objects, key=lambda o: o.bbox.width * o.bbox.height, reverse=True)

            for obj in sorted_objs:
                best_match_id = None
                best_score = 0

                for track_id, track_info in tracks.items():
                    if track_id in used_tracks: continue
                    if track_info['type'] != obj.type: continue

                    last_seen = track_info['history'][-1]
                    # Don't match if the track hasn't been seen in a long time (max 10 sampled frames jump)
                    # However, since we sample few frames, we allow more flexibility

                    iou = calculate_iou(last_seen['bbox'], obj.bbox)
                    dist = calculate_centroid_dist(last_seen['bbox'], obj.bbox)

                    # Score combines IoU and normalized centroid distance
                    # 1920x1080 screen diagonal is ~2200
                    norm_dist = max(0, 1.0 - (dist / 500.0))
                    score = (iou * 0.7) + (norm_dist * 0.3)

                    if score > 0.4 and score > best_score:
                        best_score = score
                        best_match_id = track_id

                if best_match_id:
                    tracks[best_match_id]['history'].append({
                        'frame_index': frame.frame_index,
                        'bbox': obj.bbox,
                        'confidence': obj.confidence
                    })
                    used_tracks.add(best_match_id)
                else:
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

            avg_x = sum(h['bbox'].x for h in history) / len(history)
            avg_y = sum(h['bbox'].y for h in history) / len(history)
            avg_w = sum(h['bbox'].width for h in history) / len(history)
            avg_h = sum(h['bbox'].height for h in history) / len(history)

            movement = 0
            for i in range(1, len(history)):
                movement += calculate_centroid_dist(history[i-1]['bbox'], history[i]['bbox'])

            tracked_results.append(TrackedObject(
                track_id=track_id,
                type=info['type'],
                first_frame=history[0]['frame_index'],
                last_frame=history[-1]['frame_index'],
                frames_visible=len(history),
                average_confidence=float(avg_conf),
                average_bbox=BBox(x=float(avg_x), y=float(avg_y), width=float(avg_w), height=float(avg_h)),
                movement_distance=float(movement)
            ))

        return tracked_results
    except Exception as e:
        print(f"⚠️ Tracking error: {e}")
        return []
