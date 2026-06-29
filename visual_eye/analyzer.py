import os
import json
import cv2
import numpy as np
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# Import fix for both module and standalone run
try:
    from .schema import SceneAnalysis, AnalysisFrame, DetectedObject, SafeTextRegion
except (ImportError, ValueError):
    try:
        from visual_eye.schema import SceneAnalysis, AnalysisFrame, DetectedObject, SafeTextRegion
    except ImportError:
        from schema import SceneAnalysis, AnalysisFrame, DetectedObject, SafeTextRegion

try:
    from .detector import detect_objects, classify_scene
    from .safe_zone import detect_safe_text_regions
    from .fallback import get_empty_analysis
except (ImportError, ValueError):
    try:
        from visual_eye.detector import detect_objects, classify_scene
        from visual_eye.safe_zone import detect_safe_text_regions
        from visual_eye.fallback import get_empty_analysis
    except ImportError:
        from detector import detect_objects, classify_scene
        from safe_zone import detect_safe_text_regions
        from fallback import get_empty_analysis

try:
    from .scene_understanding.analyzer import perform_scene_understanding
except (ImportError, ValueError):
    try:
        from visual_eye.scene_understanding.analyzer import perform_scene_understanding
    except ImportError:
        try:
            from scene_understanding.analyzer import perform_scene_understanding
        except ImportError:
            def perform_scene_understanding(analysis, video_path, context=None): return analysis

def get_sampling_indices(total_frames: int) -> List[int]:
    """
    Adaptive sampling: 5-40 frames based on video length.
    """
    if total_frames <= 0:
        return []

    # 30 fps = 1 sec
    duration_secs = total_frames / 30.0

    if duration_secs < 5: n_samples = 5
    elif duration_secs < 15: n_samples = 15
    elif duration_secs < 60: n_samples = 25
    else: n_samples = 40

    n_samples = min(n_samples, total_frames)
    indices = np.linspace(0, total_frames - 1, n_samples, dtype=int).tolist()
    return indices

def draw_debug_info(frame: np.ndarray, frame_idx: int, objects: List[DetectedObject], safe_regions: List[SafeTextRegion]) -> np.ndarray:
    debug_frame = frame.copy()
    for i, region in enumerate(safe_regions):
        color = (0, 255, 0) if i == 0 else (0, 200, 0)
        x1, y1 = int(region.x), int(region.y)
        x2, y2 = int(region.x + region.width), int(region.y + region.height)
        cv2.rectangle(debug_frame, (x1, y1), (x2, y2), color, 2 if i==0 else 1)
    for obj in objects:
        x, y, bw, bh = int(obj.bbox.x), int(obj.bbox.y), int(obj.bbox.width), int(obj.bbox.height)
        cv2.rectangle(debug_frame, (x, y), (x + bw, y + bh), (255, 0, 0), 2)
    return debug_frame

def analyze_video(video_path: str, output_dir: str, debug: bool = False, context: Optional[Dict[str, Any]] = None) -> SceneAnalysis:
    """
    Performs multi-stage video analysis and produces dual outputs:
    Full Analysis (Debug) and Compact Summary (AI).
    """
    try:
        if not os.path.exists(video_path):
            return get_empty_analysis()

        video_name = os.path.splitext(os.path.basename(video_path))[0]
        analysis_path = os.path.join(output_dir, f"{video_name}.analysis.json")
        summary_path = os.path.join(output_dir, f"{video_name}.summary.json")

        # 1. Version Check & Cache (Phase 3.1)
        if os.path.exists(analysis_path):
            try:
                with open(analysis_path, 'r') as f:
                    data = json.load(f)
                    if data.get("version", "1.0") >= "3.1":
                         # Also ensure summary exists
                         if os.path.exists(summary_path):
                             print(f"📦 Loading cached analysis: {analysis_path}")
                             return SceneAnalysis.model_validate(data)
            except: pass

        # 2. Base Detection Stage
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0: return get_empty_analysis()

        sample_indices = get_sampling_indices(total_frames)
        analysis_frames = []

        print(f"🚀 Analyzing {video_name} (Sampling {len(sample_indices)} frames)...")
        all_scene_types = []

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret: continue

            objs = detect_objects(frame)
            s_type = classify_scene(frame, objs)
            all_scene_types.append(s_type)
            s_regions = detect_safe_text_regions(frame, objs)

            analysis_frames.append(AnalysisFrame(frame_index=idx, objects=objs, safe_text_regions=s_regions))

        cap.release()
        if not analysis_frames: return get_empty_analysis()

        # Consensus for scene type
        final_scene_type = "unknown"
        if all_scene_types:
            from collections import Counter
            final_scene_type = Counter(all_scene_types).most_common(1)[0][0]

        first_frame = analysis_frames[0]
        analysis = SceneAnalysis(
            version="3.1",
            status="success",
            scene_type=final_scene_type,
            objects=first_frame.objects,
            safe_text_regions=first_frame.safe_text_regions,
            frames=analysis_frames,
            total_frames=total_frames,
            sampled_frames=len(analysis_frames)
        )

        # 3. Scene Understanding & AI Summary Stage
        print(f"🧠 Extracting Semantic Summary for {video_name}...")
        analysis = perform_scene_understanding(analysis, video_path, context)

        # 4. Save Dual Outputs
        os.makedirs(output_dir, exist_ok=True)

        # A. Full Debug Analysis
        with open(analysis_path, 'w') as f:
            f.write(analysis.model_dump_json(indent=2))

        # B. Compact AI Summary
        if analysis.ai_summary:
            with open(summary_path, 'w') as f:
                f.write(analysis.ai_summary.model_dump_json(indent=2))

        print(f"✅ Analysis saved to {analysis_path}")
        print(f"✨ AI Summary created: {summary_path}")

        return analysis

    except Exception as e:
        print(f"⚠️ Analysis error: {e}")
        import traceback
        traceback.print_exc()
        return get_empty_analysis()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("out", help="Output directory")
    args = parser.parse_args()
    analyze_video(args.video, args.out)
