from typing import List
try:
    from ..schema import AnalysisFrame, RecommendedTextRegion, SafeTextRegion
except (ImportError, ValueError):
    try:
        from visual_eye.schema import AnalysisFrame, RecommendedTextRegion, SafeTextRegion
    except ImportError:
        from schema import AnalysisFrame, RecommendedTextRegion, SafeTextRegion

def recommend_text_region(frames: List[AnalysisFrame]) -> RecommendedTextRegion:
    """
    Find the most stable safe text region by calculating intersection and persistence.
    """
    try:
        if not frames:
            return RecommendedTextRegion(x=100, y=100, width=500, height=300, confidence=0.5, stability=0.0)

        # 1. Gather all unique safe region slots (from our 4x4 grid in Phase 1.5)
        grid_slots = {} # (x, y) -> {confidences: [], frames: []}

        for frame in frames:
            for region in frame.safe_text_regions:
                key = (round(region.x), round(region.y))
                if key not in grid_slots:
                    grid_slots[key] = {'confidences': [], 'frames': [], 'w': region.width, 'h': region.height}
                grid_slots[key]['confidences'].append(region.confidence)
                grid_slots[key]['frames'].append(frame.frame_index)

        if not grid_slots:
            return RecommendedTextRegion(x=100, y=100, width=800, height=300, confidence=0.5, stability=0.0)

        # 2. Calculate stability and average confidence for each slot
        scored_candidates = []
        total_sampled = len(frames)

        for key, data in grid_slots.items():
            avg_conf = sum(data['confidences']) / len(data['confidences'])
            # Stability = percentage of sampled frames where this region is safe
            stability = len(data['frames']) / float(total_sampled)

            # Final score weights stability heavily for text placement
            score = (stability * 0.7) + (avg_conf * 0.3)

            scored_candidates.append({
                'pos': key,
                'w': data['w'],
                'h': data['h'],
                'avg_conf': avg_conf,
                'stability': stability,
                'score': score
            })

        # 3. Pick the best region
        scored_candidates.sort(key=lambda x: x['score'], reverse=True)
        best = scored_candidates[0]

        return RecommendedTextRegion(
            x=float(best['pos'][0]),
            y=float(best['pos'][1]),
            width=float(best['w']),
            height=float(best['h']),
            confidence=float(best['avg_conf']),
            stability=float(best['stability'])
        )

    except Exception as e:
        print(f"⚠️ Text region recommendation error: {e}")
        return RecommendedTextRegion(x=100, y=100, width=500, height=300, confidence=0.5, stability=0.0)
