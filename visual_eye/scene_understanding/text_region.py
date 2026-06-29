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
    Find the most stable safe text region across all sampled frames.
    """
    try:
        if not frames:
            return RecommendedTextRegion(x=100, y=100, width=500, height=300, confidence=0.5, stability=0.0)

        grid_stats = {}

        for frame in frames:
            for region in frame.safe_text_regions:
                key = (round(region.x, -1), round(region.y, -1))

                if key not in grid_stats: grid_stats[key] = []
                grid_stats[key].append(region.confidence)

        if not grid_stats:
            return RecommendedTextRegion(x=100, y=100, width=800, height=300, confidence=0.5, stability=0.0)

        candidates = []
        for key, confidences in grid_stats.items():
            avg_conf = sum(confidences) / len(confidences)
            stability = len(confidences) / len(frames)
            score = avg_conf * stability

            candidates.append({
                'key': key,
                'avg_conf': avg_conf,
                'stability': stability,
                'score': score
            })

        candidates.sort(key=lambda x: x['score'], reverse=True)
        best = candidates[0]

        orig = None
        for frame in frames:
            for region in frame.safe_text_regions:
                if (round(region.x, -1), round(region.y, -1)) == best['key']:
                    orig = region
                    break
            if orig: break

        return RecommendedTextRegion(
            x=orig.x if orig else best['key'][0],
            y=orig.y if orig else best['key'][1],
            width=orig.width if orig else 400,
            height=orig.height if orig else 200,
            confidence=best['avg_conf'],
            stability=best['stability']
        )

    except Exception as e:
        print(f"⚠️ Text region recommendation error: {e}")
        return RecommendedTextRegion(x=100, y=100, width=500, height=300, confidence=0.5, stability=0.0)
