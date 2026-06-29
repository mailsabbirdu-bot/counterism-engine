import math
from typing import List, Dict, Any
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
    Production-grade object association and track merging.
    Implement IoU + Centroid matching with temporal consistency.
    """
    try:
        if not frames:
            return []

        tracks = {} # track_id -> info
        next_track_id = 1
        total_sampled = len(frames)

        for frame in frames:
            # Step 1: Association
            used_tracks = set()
            sorted_objs = sorted(frame.objects, key=lambda o: o.bbox.width * o.bbox.height, reverse=True)

            for obj in sorted_objs:
                # Confidence Gate: Ignore low-confidence detections
                if obj.confidence < 0.45:
                    # Check for persistence exception handled at final results stage
                    pass

                best_match_id = None
                best_score = 0

                for tid, tinfo in tracks.items():
                    if tid in used_tracks: continue
                    if tinfo['type'] != obj.type: continue

                    last_seen = tinfo['history'][-1]
                    gap = frame.frame_index - last_seen['frame_index']
                    if gap > 60: continue

                    iou = calculate_iou(last_seen['bbox'], obj.bbox)
                    dist = calculate_centroid_dist(last_seen['bbox'], obj.bbox)

                    size_a = last_seen['bbox'].width * last_seen['bbox'].height
                    size_b = obj.bbox.width * obj.bbox.height
                    size_sim = min(size_a, size_b) / max(size_a, size_b) if max(size_a, size_b) > 0 else 0

                    norm_dist = max(0, 1.0 - (dist / 400.0))
                    score = (iou * 0.5) + (norm_dist * 0.3) + (size_sim * 0.2)

                    if score > 0.35 and score > best_score:
                        best_score = score
                        best_match_id = tid

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

        # Step 2: Track Merging
        merged_tracks = {}
        all_ids = list(tracks.keys())
        merged_ids = set()

        for i in range(len(all_ids)):
            id1 = all_ids[i]
            if id1 in merged_ids: continue

            t1 = tracks[id1]
            base_track = t1

            for j in range(i + 1, len(all_ids)):
                id2 = all_ids[j]
                if id2 in merged_ids: continue

                t2 = tracks[id2]
                if t1['type'] != t2['type']: continue

                start1, end1 = t1['history'][0]['frame_index'], t1['history'][-1]['frame_index']
                start2, end2 = t2['history'][0]['frame_index'], t2['history'][-1]['frame_index']

                if max(start1, start2) <= min(end1, end2): continue

                if end1 < start2: box1, box2 = t1['history'][-1]['bbox'], t2['history'][0]['bbox']
                else: box1, box2 = t2['history'][-1]['bbox'], t1['history'][0]['bbox']

                dist = calculate_centroid_dist(box1, box2)
                if dist < 300:
                    base_track['history'].extend(t2['history'])
                    base_track['history'].sort(key=lambda x: x['frame_index'])
                    merged_ids.add(id2)

            merged_tracks[id1] = base_track

        # Step 3: Final Filtering and TrackedObject creation
        final_results = []
        for tid, info in merged_tracks.items():
            history = info['history']
            avg_conf = sum(h['confidence'] for h in history) / len(history)
            persistence = len(history) / float(total_sampled)

            # THE CONFIDENCE GATE
            if avg_conf < 0.45 and persistence <= 0.7:
                continue

            avg_x = sum(h['bbox'].x for h in history) / len(history)
            avg_y = sum(h['bbox'].y for h in history) / len(history)
            avg_w = sum(h['bbox'].width for h in history) / len(history)
            avg_h = sum(h['bbox'].height for h in history) / len(history)

            movement = 0
            for k in range(1, len(history)):
                movement += calculate_centroid_dist(history[k-1]['bbox'], history[k]['bbox'])

            final_results.append(TrackedObject(
                track_id=tid,
                type=info['type'],
                first_frame=history[0]['frame_index'],
                last_frame=history[-1]['frame_index'],
                frames_visible=len(history),
                average_confidence=float(avg_conf),
                average_bbox=BBox(x=float(avg_x), y=float(avg_y), width=float(avg_w), height=float(avg_h)),
                movement_distance=float(movement)
            ))

        return final_results
    except Exception as e:
        print(f"⚠️ Tracker Error: {e}")
        return []
