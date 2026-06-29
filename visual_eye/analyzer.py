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

    if duration_secs < 5:
        n_samples = 5
    elif duration_secs < 15:
        n_samples = 15
    elif duration_secs < 60:
        n_samples = 25
    else:
        n_samples = 40

    n_samples = min(n_samples, total_frames)
    indices = np.linspace(0, total_frames - 1, n_samples, dtype=int).tolist()
    return indices

def draw_debug_info(frame: np.ndarray, frame_idx: int, objects: List[DetectedObject], safe_regions: List[SafeTextRegion]) -> np.ndarray:
    """
    Annotates frame with detection and safe region info for debugging.
    """
    debug_frame = frame.copy()
    h, w = debug_frame.shape[:2]

    # 1. Draw Safe Regions (Green)
    for i, region in enumerate(safe_regions):
        color = (0, 255, 0) if i == 0 else (0, 200, 0)
        thickness = 2 if i == 0 else 1
        alpha = 0.3 if i == 0 else 0.1

        x1, y1 = int(region.x), int(region.y)
        x2, y2 = int(region.x + region.width), int(region.y + region.height)

        # Overlay with transparency
        overlay = debug_frame.copy()
        cv2.rectangle(overlay, (x1, y1), (x2, y2), color, -1)
        cv2.addWeighted(overlay, alpha, debug_frame, 1 - alpha, 0, debug_frame)
        cv2.rectangle(debug_frame, (x1, y1), (x2, y2), color, thickness)

        label = f"Safe {i} ({region.confidence:.2f})"
        cv2.putText(debug_frame, label, (x1 + 5, y1 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

    # 2. Draw Objects (Blue/Red)
    for obj in objects:
        x, y, bw, bh = int(obj.bbox.x), int(obj.bbox.y), int(obj.bbox.width), int(obj.bbox.height)
        cv2.rectangle(debug_frame, (x, y), (x + bw, y + bh), (255, 0, 0), 2)
        label = f"{obj.type} {obj.confidence:.2f}"
        cv2.putText(debug_frame, label, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    # 3. Draw Frame Index
    cv2.putText(debug_frame, f"Frame: {frame_idx}", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    return debug_frame

def analyze_video(video_path: str, output_dir: str, debug: bool = False, context: Optional[Dict[str, Any]] = None) -> SceneAnalysis:
    """
    Performs real multi-frame video analysis and caches results.
    """
    try:
        if not os.path.exists(video_path):
            print(f"⚠️ Video not found: {video_path}")
            return get_empty_analysis()

        # Cache Check
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{video_name}_analysis.json")

        if os.path.exists(output_path):
            print(f"📦 Loading cached analysis: {output_path}")
            try:
                with open(output_path, 'r') as f:
                    data = json.load(f)
                    if data.get("version", "1.0") >= "2.0": # Upgraded version check
                         return SceneAnalysis.model_validate(data)
                    else:
                         print(f"🔄 Old analysis version ({data.get('version')}) found. Re-analyzing for Phase 2...")
            except Exception as e:
                print(f"⚠️ Cache read error: {e}. Re-analyzing...")

        # Real Analysis
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        if total_frames <= 0:
            cap.release()
            return get_empty_analysis()

        sample_indices = get_sampling_indices(total_frames)
        analysis_frames = []

        debug_dir = os.path.join(output_dir, "debug", video_name) if debug else None
        if debug_dir: os.makedirs(debug_dir, exist_ok=True)

        print(f"🚀 Analyzing {video_name} ({total_frames} frames, sampling {len(sample_indices)})...")

        all_scene_types = []

        for idx in sample_indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret: continue

            objs = detect_objects(frame)
            s_type = classify_scene(frame, objs)
            all_scene_types.append(s_type)
            s_regions = detect_safe_text_regions(frame, objs)

            analysis_frames.append(AnalysisFrame(
                frame_index=idx,
                objects=objs,
                safe_text_regions=s_regions
            ))

            if debug_dir:
                debug_img = draw_debug_info(frame, idx, objs, s_regions)
                cv2.imwrite(os.path.join(debug_dir, f"frame_{idx:04d}.jpg"), debug_img)

        cap.release()

        if not analysis_frames:
            return get_empty_analysis()

        # Consensus for scene type
        final_scene_type = "unknown"
        if all_scene_types:
            from collections import Counter
            final_scene_type = Counter(all_scene_types).most_common(1)[0][0]

        # Use the first frame for root-level fields (backward compatibility)
        first_frame = analysis_frames[0]

        analysis = SceneAnalysis(
            version="2.0",
            status="success",
            scene_type=final_scene_type,
            objects=first_frame.objects,
            safe_text_regions=first_frame.safe_text_regions,
            frames=analysis_frames,
            total_frames=total_frames,
            sampled_frames=len(analysis_frames)
        )

        # Stage 2: Scene Understanding Layer
        print(f"🧠 Performing Scene Understanding for {video_name}...")
        analysis = perform_scene_understanding(analysis, video_path, context)

        os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(analysis.model_dump_json(indent=2))

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
    parser.add_argument("--debug", action="store_true", help="Enable debug visualization")
    args = parser.parse_args()

    analyze_video(args.video, args.out, debug=args.debug)
