
import sys
import os
from typing import List
from pydantic import BaseModel

# Mocking the environment
sys.path.append(os.path.abspath('visual_eye'))

from schema import AnalysisFrame, DetectedObject, BBox, SceneAnalysis
from scene_understanding.tracker import track_objects
from scene_understanding.subject_ranker import rank_visual_subjects
from scene_understanding.narrative_ranker import rank_narrative_subjects
from scene_understanding.analyzer import combine_rankings, generate_summary

def test():
    # 1. Create Mock Frames with detections
    frame0 = AnalysisFrame(
        frame_index=0,
        objects=[
            DetectedObject(id="o1", type="person", confidence=0.9, bbox=BBox(x=100, y=100, width=50, height=100)),
            DetectedObject(id="o2", type="car", confidence=0.8, bbox=BBox(x=500, y=500, width=200, height=100))
        ],
        safe_text_regions=[]
    )
    frame10 = AnalysisFrame(
        frame_index=10,
        objects=[
            DetectedObject(id="o3", type="person", confidence=0.95, bbox=BBox(x=110, y=105, width=50, height=100)),
            DetectedObject(id="o4", type="car", confidence=0.85, bbox=BBox(x=520, y=500, width=200, height=100))
        ],
        safe_text_regions=[]
    )

    frames = [frame0, frame10]

    print("--- Testing Tracker ---")
    tracks = track_objects(frames)
    for t in tracks:
        print(f"Track: {t.track_id}, Type: {t.type}, Frames: {t.frames_visible}, Movement: {t.movement_distance:.2f}")

    print("\n--- Testing Visual Ranker ---")
    v_ranks = rank_visual_subjects(tracks, total_frames=100, sampled_frames_count=2)
    for r in v_ranks:
        print(f"Subject: {r.track_id}, Type: {r.type}, Visual Imp: {r.visual_importance:.2f}")

    print("\n--- Testing Narrative Ranker ---")
    context = {"script": "A person is walking near a vehicle.", "keywords": ["person"]}
    n_ranks = rank_narrative_subjects(tracks, context=context)
    for r in n_ranks:
        print(f"Subject: {r.track_id}, Type: {r.type}, Narrative Imp: {r.narrative_importance:.2f}")

    print("\n--- Testing Combined Ranking ---")
    main = combine_rankings(v_ranks, n_ranks)
    for m in main:
        print(f"Subject: {m.track_id}, Type: {m.type}, Final Imp: {m.final_importance:.2f}")

    print("\n--- Testing Summary Generation ---")
    # Partial analysis object for summary test
    analysis = SceneAnalysis(status="success")
    analysis.main_subjects = main
    # ... mock other fields ...
    summary = generate_summary(analysis)
    print(f"Main Subject: {summary.main_subject}")
    print(f"Reason: {summary.selection_reason}")

if __name__ == "__main__":
    test()
