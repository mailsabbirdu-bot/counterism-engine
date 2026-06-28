import os
import json
import cv2
try:
    from .detector import detect_objects, classify_scene
    from .safe_zone import detect_safe_text_regions
    from .schema import SceneAnalysis
    from .fallback import get_empty_analysis
except ImportError:
    from detector import detect_objects, classify_scene
    from safe_zone import detect_safe_text_regions
    from schema import SceneAnalysis
    from fallback import get_empty_analysis

def analyze_video(video_path: str, output_dir: str) -> SceneAnalysis:
    """
    Analyzes a video file and saves the result to a JSON file.
    """
    try:
        if not os.path.exists(video_path):
            print(f"Video not found: {video_path}")
            return get_empty_analysis()

        cap = cv2.VideoCapture(video_path)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            print(f"Failed to read frame from: {video_path}")
            return get_empty_analysis()

        objects = detect_objects(frame)
        scene_type = classify_scene(frame)
        safe_regions = detect_safe_text_regions(frame, objects)

        analysis = SceneAnalysis(
            status="success",
            scene_type=scene_type,
            objects=objects,
            safe_text_regions=safe_regions
        )

        # Output path handling
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{video_name}_analysis.json")
        os.makedirs(output_dir, exist_ok=True)

        with open(output_path, 'w') as f:
            f.write(analysis.model_dump_json(indent=2))

        return analysis

    except Exception as e:
        print(f"Analysis error: {e}")
        return get_empty_analysis()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        analyze_video(sys.argv[1], sys.argv[2])
